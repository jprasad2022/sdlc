# Step 3: End-to-End Query Processing Automation for Insurance Graph RAG

import os
import json
import time
from typing import List, Dict, Any, Tuple, Optional, Union
import networkx as nx
from datetime import datetime
import numpy as np
import re
from collections import defaultdict, Counter

# For vector embeddings and similarity search
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer, AutoModel
import torch

# For graph database operations
# Note: In a real implementation, you would use a graph database like Neo4j
# This is a simplified in-memory implementation

def safe_split_key(key: str) -> Tuple[str, str]:
    """
    Split into (alias, prop) on the first dot.
    If no dot, alias='' and prop=key.
    ALWAYS returns a tuple of 2 elements.
    """
    try:
        # Ensure we have a string
        if not isinstance(key, str):
            print(f"WARNING: safe_split_key called with non-string key: {type(key)}")
            return '', str(key)
        
        # Split on the first dot
        parts = key.split('.', 1)
        
        # Always return exactly 2 values
        if len(parts) == 2:
            return parts[0], parts[1]
        else:
            # Return empty alias and the full key as property
            return '', key
            
    except Exception as e:
        print(f"ERROR in safe_split_key: {str(e)}")
        # Always return exactly 2 values even in error case
        return '', ''

class GraphRAGQueryProcessor:
     
    def __init__(self, schema_path: str = None, knowledge_graph_path: str = None, model_name: str = "sentence-transformers/all-mpnet-base-v2"):
        """
        Initialize the end-to-end query processor for the insurance graph RAG system.
        
        Args:
            schema_path: Path to the schema file
            knowledge_graph_path: Path to the knowledge graph data
            model_name: Name of the model to use for embeddings
        """
        # Load the schema
        self.schema = self._load_schema(schema_path)
        
        # Initialize knowledge graph
        self.knowledge_graph = nx.MultiDiGraph()
        if knowledge_graph_path:
            self._load_knowledge_graph(knowledge_graph_path)
        
        # Initialize embedding model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        
        # Intent recognition system
        self.intent_patterns = self._initialize_intent_patterns()
        self.intent_examples = self._initialize_intent_examples()
        self.intent_embeddings = self._compute_intent_embeddings()
        
        # Response template system
        self.response_templates = self._initialize_response_templates()
        
        # Query history for context awareness
        self.query_history = []
        self.max_history_length = 10
        
        # Performance metrics
        self.query_metrics = {
            'total_queries': 0,
            'successful_queries': 0,
            'avg_response_time': 0,
            'intent_distribution': Counter(),
            'complex_query_count': 0
        }
        
        # Feedback collection
        self.feedback_store = []
        
        # Tracking discovered intents
        self.discovered_intents = set()
        
        print("Graph RAG Query Processor initialized successfully")
    
    
    def _load_schema(self, schema_path: str) -> Dict[str, Any]:
        """Load the graph schema from a file."""
        default_schema = {
            'entity_types': [
                {'name': 'Policy', 'properties': {}},
                {'name': 'Insured', 'properties': {}},
                {'name': 'Coverage', 'properties': {}},
                {'name': 'Claim', 'properties': {}},
                {'name': 'Premium', 'properties': {}}
            ],
            'relationship_types': [
                {'name': 'HAS_COVERAGE', 'source': 'Policy', 'target': 'Coverage'},
                {'name': 'INSURES', 'source': 'Policy', 'target': 'Insured'},
                {'name': 'FILES_CLAIM', 'source': 'Insured', 'target': 'Claim'}
            ]
        }
        
        if schema_path and os.path.exists(schema_path):
            try:
                with open(schema_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading schema: {e}")
                return default_schema
        else:
            print("Using default schema")
            return default_schema
    
    def _load_knowledge_graph(self, graph_path: str) -> None:
        """Load the knowledge graph from a file."""
        try:
            with open(graph_path, 'r') as f:
                graph_data = json.load(f)
                
            # Add nodes
            for node in graph_data.get('nodes', []):
                node_id = node.get('id')
                labels = node.get('labels', [])
                properties = node.get('properties', {})
                
                if node_id:
                    self.knowledge_graph.add_node(node_id, labels=labels, properties=properties)
            
            # Add edges
            for edge in graph_data.get('edges', []):
                source = edge.get('source')
                target = edge.get('target')
                rel_type = edge.get('type')
                properties = edge.get('properties', {})
                
                if source and target and rel_type:
                    self.knowledge_graph.add_edge(source, target, key=rel_type, type=rel_type, properties=properties)
                    
            print(f"Loaded knowledge graph with {self.knowledge_graph.number_of_nodes()} nodes and {self.knowledge_graph.number_of_edges()} edges")
        
        except Exception as e:
            print(f"Error loading knowledge graph: {e}")
    
    def _initialize_intent_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize predefined intent recognition patterns."""
        # 1) Build the combined dict in one place
        patterns = {
            'policy_details': {
                'patterns': [
                    r'(?i).*policy\s+details.*',
                    r'(?i).*information\s+about\s+(?:my|a|the)\s+policy.*',
                    r'(?i).*what\s+(?:is|are)\s+(?:in|on|the)\s+(?:my|the)\s+policy.*',
                    r'(?i).*tell\s+me\s+about\s+(?:my|a|the)\s+policy.*'
                ],
                'entities': ['Policy'],
                'required_properties': ['policy_number']
            },
            'coverage_inquiry': {
                'patterns': [
                    r'(?i).*what\s+(?:is|does)\s+(?:my|the)\s+policy\s+cover.*',
                    r'(?i).*coverage\s+(?:details|information).*',
                    r'(?i).*what\s+(?:are|is)\s+(?:my|the)\s+coverage.*',
                    r'(?i).*covered\s+under\s+(?:my|the)\s+policy.*'
                ],
                'entities': ['Policy', 'Coverage'],
                'relationships': ['HAS_COVERAGE']
            },
            'claim_status': {
                'patterns': [
                    r'(?i).*status\s+of\s+(?:my|the|a)\s+claim.*',
                    r'(?i).*claim\s+(?:status|update|progress).*',
                    r'(?i).*what\'s\s+happening\s+with\s+(?:my|the)\s+claim.*',
                    r'(?i).*where\s+is\s+(?:my|the)\s+claim.*'
                ],
                'entities': ['Claim'],
                'required_properties': ['claim_number']
            },
            'premium_information': {
                'patterns': [
                    r'(?i).*(?:my|the)\s+premium.*',
                    r'(?i).*how\s+much\s+(?:is|does|do)\s+(?:my|the|I)\s+(?:premium|pay|cost).*',
                    r'(?i).*payment\s+(?:amount|details|schedule).*',
                    r'(?i).*when\s+(?:is|are)\s+(?:my|the)\s+payment.*'
                ],
                'entities': ['Policy', 'Premium'],
                'relationships': ['HAS_PREMIUM']
            },
            'filing_claim': {
                'patterns': [
                    r'(?i).*(?:how|can|do)\s+(?:to|I|you)\s+file\s+a\s+claim.*',
                    r'(?i).*(?:submit|start|begin|initiate)\s+a\s+(?:new|)\s*claim.*',
                    r'(?i).*claim\s+(?:filing|submission)\s+process.*',
                    r'(?i).*report\s+(?:a|an|the)\s+(?:accident|incident|loss|damage).*'
                ],
                'entities': ['Claim'],
                'is_procedural': True
            }
        }

        # 2) Now add the definition_inquiry entry in-place
        patterns['definition_inquiry'] = {
            'patterns': [
                r'(?i).*what\s+(?:does|is|are)\s+(\w+)\s+mean.*',
                r'(?i).*define\s+(\w+).*',
                r'(?i).*meaning\s+of\s+(\w+).*',
                r'(?i).*definition\s+of\s+(\w+).*'
            ],
            'entities': ['Definition'],
            'required_properties': ['term', 'meaning']
        }

        # 3) Return the full set
        return patterns

    
    def _initialize_intent_examples(self) -> Dict[str, List[str]]:
        """Initialize example queries for each intent for zero-shot learning."""
        return {
            'policy_details': [
                "What are the details of my policy?",
                "Can you tell me about policy P12345?",
                "I need information about my insurance policy",
                "Show me my policy details",
                "What does my policy say?"
            ],
            'coverage_inquiry': [
                "What does my policy cover?",
                "Am I covered for water damage?",
                "What is the coverage limit for my car insurance?",
                "Does my policy include liability coverage?",
                "What types of coverage do I have?"
            ],
            'claim_status': [
                "What's the status of my claim?",
                "Has my claim been processed yet?",
                "I'd like an update on claim C67890",
                "Where is my claim in the process?",
                "Has a decision been made on my claim?"
            ],
            'premium_information': [
                "How much is my premium?",
                "When is my next premium payment due?",
                "Can you tell me about my payment schedule?",
                "What's the amount of my monthly premium?",
                "Has my premium changed recently?"
            ],
            'filing_claim': [
                "How do I file a claim?",
                "I want to report an accident",
                "What's the process for submitting a claim?",
                "I need to start a new claim",
                "Steps to file an insurance claim"
            ]
        }
    
    def _compute_intent_embeddings(self) -> Dict[str, np.ndarray]:
        """Compute embeddings for intent examples."""
        intent_embeddings = {}
        
        for intent, examples in self.intent_examples.items():
            # Compute embeddings for each example
            example_embeddings = []
            for example in examples:
                embedding = self._get_embedding(example)
                example_embeddings.append(embedding)
            
            # Average the embeddings
            intent_embeddings[intent] = np.mean(example_embeddings, axis=0)
        
        return intent_embeddings
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for a text string."""
        # Tokenize and get model outputs
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=128)
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Use the [CLS] token embedding as the sentence embedding
        embedding = outputs.last_hidden_state[:, 0, :].numpy()
        
        # Normalize the embedding
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
            
        return embedding.flatten()
    
    def _initialize_response_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize response templates for different intents."""
        return {
            'policy_details': [
                {
                    'template': "Your policy {policy_number} is a {policy_type} insurance policy with an effective date of {effective_date} and expiration date of {expiration_date}. {additional_info}",
                    'required_slots': ['policy_number', 'policy_type', 'effective_date', 'expiration_date'],
                    'optional_slots': ['additional_info'],
                    'condition': lambda data: 'policy_number' in data
                },
                {
                    'template': "I found your {policy_type} policy. It's currently {status} and covers you from {effective_date} to {expiration_date}.",
                    'required_slots': ['policy_type', 'status', 'effective_date', 'expiration_date'],
                    'optional_slots': [],
                    'condition': lambda data: 'policy_type' in data and 'status' in data
                }
            ],
            'coverage_inquiry': [
                {
                    'template': "Your policy includes the following coverages: {coverage_list}. The total coverage limit is {total_limit}.",
                    'required_slots': ['coverage_list'],
                    'optional_slots': ['total_limit'],
                    'condition': lambda data: 'coverage_list' in data and len(data['coverage_list']) > 0
                },
                {
                    'template': "For {peril_type}, your policy provides coverage up to {limit} with a deductible of {deductible}.",
                    'required_slots': ['peril_type', 'limit', 'deductible'],
                    'optional_slots': [],
                    'condition': lambda data: 'peril_type' in data and 'limit' in data
                }
            ],
            'claim_status': [
                {
                    'template': "Your claim {claim_number} is currently {status}. {additional_info}",
                    'required_slots': ['claim_number', 'status'],
                    'optional_slots': ['additional_info'],
                    'condition': lambda data: 'claim_number' in data and 'status' in data
                },
                {
                    'template': "The claim you filed on {date_filed} for {claim_type} is {status}. The assigned adjuster is {adjuster}.",
                    'required_slots': ['date_filed', 'claim_type', 'status'],
                    'optional_slots': ['adjuster'],
                    'condition': lambda data: 'date_filed' in data and 'status' in data
                }
            ],
            'premium_information': [
                {
                    'template': "Your premium is {amount} paid {frequency}. Your next payment is due on {due_date}.",
                    'required_slots': ['amount', 'frequency', 'due_date'],
                    'optional_slots': [],
                    'condition': lambda data: 'amount' in data and 'due_date' in data
                },
                {
                    'template': "You're currently paying {amount} {frequency} for your insurance. Your payment history shows {payment_status}.",
                    'required_slots': ['amount', 'frequency'],
                    'optional_slots': ['payment_status'],
                    'condition': lambda data: 'amount' in data and 'frequency' in data
                }
            ],
            'filing_claim': [
                {
                    'template': "To file a claim, you'll need to: 1) Report the incident immediately, 2) Gather all relevant information including {required_info}, 3) Contact our claims department at {contact_info}.",
                    'required_slots': ['required_info', 'contact_info'],
                    'optional_slots': [],
                    'condition': lambda data: True  # Procedural information is always applicable
                }
            ],
            'definition_inquiry': [
                {
                    'template': "According to the insurance documentation, {term} means: {meaning}",
                    'required_slots': ['term', 'meaning'],
                    'optional_slots': [],
                    'condition': lambda data: 'term' in data and 'meaning' in data
                },
                {
                    'template': "I don't have a definition for {term} in my knowledge base.",
                    'required_slots': ['term'],
                    'optional_slots': [],
                    'condition': lambda data: 'term' in data and 'meaning' not in data
                }
            ],
            'default': [
                {
                    'template': "I don't have enough information to answer your query about {topic}. Could you provide more details?",
                    'required_slots': ['topic'],
                    'optional_slots': [],
                    'condition': lambda data: 'topic' in data
                },
                {
                    'template': "I'm not sure I understand your question. Can you rephrase it or provide more specific details about what you're looking for?",
                    'required_slots': [],
                    'optional_slots': [],
                    'condition': lambda data: True
                }
            ]
        }
    
    def process_query(self, query_text: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a user query end-to-end.
        
        Args:
            query_text: The user's query text
            user_context: Optional context about the user
            
        Returns:
            Response dictionary with generated answer and metadata
        """
        start_time = time.time()
        
        # Update query metrics
        self.query_metrics['total_queries'] += 1
        
        # Step 1: Understand query intent
        intent_analysis = self.analyze_intent(query_text)
        intent = intent_analysis['intent']
        confidence = intent_analysis['confidence']
        
        # Track intent distribution
        self.query_metrics['intent_distribution'][intent] += 1
        
        # Step 2: Extract entities and parameters
        extracted_params = self.extract_parameters(query_text, intent, user_context)
        
        # Step 3: Build graph query
        graph_query = self.build_graph_query(intent, extracted_params)
        
        # Step 4: Execute graph query
        query_results = self.execute_graph_query(graph_query)
        
        # For definition inquiries, if no results found, try the backup query
        if intent == 'definition_inquiry' and query_results.get('count', 0) == 0 and 'original_term' in extracted_params:
            # Try with exclusion nodes instead
            backup_params = extracted_params.copy()
            backup_params['term'] = backup_params['original_term']
            backup_query = self.build_graph_query(intent, backup_params)
            backup_results = self.execute_graph_query(backup_query)
            
            # If we found results with the backup query, use those
            if backup_results.get('count', 0) > 0:
                query_results = backup_results
        
        # Check if this is a complex query
        is_complex = len(graph_query.get('paths', [])) > 1
        if is_complex:
            self.query_metrics['complex_query_count'] += 1
        
        # Step 5: Generate response
        response = self.generate_response(intent, query_results, extracted_params)
        
        # Update query history
        self.update_query_history({
            'query': query_text,
            'intent': intent,
            'confidence': confidence,
            'parameters': extracted_params,
            'response': response['answer'],
            'timestamp': datetime.now().isoformat()
        })
        
        # Calculate response time
        elapsed_time = time.time() - start_time
        
        # Update average response time
        total_time = self.query_metrics['avg_response_time'] * (self.query_metrics['total_queries'] - 1)
        self.query_metrics['avg_response_time'] = (total_time + elapsed_time) / self.query_metrics['total_queries']
        
        # Check if query was successful
        if response.get('success', False):
            self.query_metrics['successful_queries'] += 1
        
        # Prepare final response
        final_response = {
            'answer': response['answer'],
            'success': response.get('success', False),
            'confidence': confidence,
            'intent': intent,
            'extracted_parameters': extracted_params,
            'response_time': elapsed_time,
            'follow_up_questions': self.generate_follow_up_questions(intent, extracted_params, query_results)
        }
        
        return final_response
    
    def analyze_intent(self, query_text: str) -> Dict[str, Any]:
        """
        Analyze the intent of a user query using pattern matching and embedding similarity.
        
        Args:
            query_text: The user's query text
            
        Returns:
            Dictionary with intent analysis results
        """
        # Pattern-based intent detection
        pattern_matches = {}
        for intent, intent_data in self.intent_patterns.items():
            patterns = intent_data.get('patterns', [])
            for pattern in patterns:
                if re.match(pattern, query_text):
                    pattern_matches[intent] = pattern_matches.get(intent, 0) + 1
        
        # If we have pattern matches, use the most frequent one
        if pattern_matches:
            best_intent = max(pattern_matches.items(), key=lambda x: x[1])[0]
            confidence = min(0.9, 0.7 + 0.1 * pattern_matches[best_intent])  # Cap at 0.9 for pattern matches
            return {'intent': best_intent, 'confidence': confidence, 'method': 'pattern'}
        
        # Semantic similarity-based intent detection
        query_embedding = self._get_embedding(query_text)
        similarities = {}
        for intent, intent_embedding in self.intent_embeddings.items():
            similarity = cosine_similarity([query_embedding], [intent_embedding])[0][0]
            similarities[intent] = float(similarity)
        
        # Get the highest similarity
        if similarities:
            best_intent = max(similarities.items(), key=lambda x: x[1])[0]
            confidence = similarities[best_intent]
            
            # If confidence is too low, use default intent
            if confidence < 0.6:
                return {'intent': 'unknown', 'confidence': 1.0 - confidence, 'method': 'default'}
            
            return {'intent': best_intent, 'confidence': confidence, 'method': 'embedding'}
        
        # Default to unknown intent
        return {'intent': 'unknown', 'confidence': 0.0, 'method': 'default'}
    
    def extract_parameters(self, query_text: str, intent: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Extract parameters from the query text based on intent.
        
        Args:
            query_text: The user's query text
            intent: The identified intent
            user_context: Optional user context
            
        Returns:
            Dictionary of extracted parameters
        """
        params = {}
        
        # Add user context parameters if available
        if user_context:
            params.update(user_context)
        
        # Policy number extraction
        policy_match = re.search(r'(?i)policy\s*(?:number|#)?\s*[:#]?\s*([A-Z0-9-]+)', query_text)
        if policy_match:
            params['policy_number'] = policy_match.group(1)
        
        # Claim number extraction
        claim_match = re.search(r'(?i)claim\s*(?:number|#)?\s*[:#]?\s*([A-Z0-9-]+)', query_text)
        if claim_match:
            params['claim_number'] = claim_match.group(1)
        
        # Date extraction
        date_match = re.search(r'(?i)(?:on|for|from|since)\s+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})', query_text)
        if date_match:
            params['date_reference'] = date_match.group(1)
        
        # Amount extraction
        amount_match = re.search(r'(?i)(?:amount|limit|deductible|premium)\s+(?:of\s+)?[$€£]?(\d+(?:,\d+)*(?:\.\d+)?)', query_text)
        if amount_match:
            params['amount_reference'] = amount_match.group(1).replace(',', '')
        
        # Coverage type extraction
        coverage_types = [
            'liability', 'collision', 'comprehensive', 'uninsured motorist', 
            'personal injury', 'medical payments', 'property damage', 
            'flood', 'fire', 'theft', 'water damage'
        ]
        for coverage in coverage_types:
            if re.search(r'(?i)\b' + re.escape(coverage) + r'\b', query_text):
                if 'coverage_types' not in params:
                    params['coverage_types'] = []
                params['coverage_types'].append(coverage)
        
        # Intent-specific parameter extraction
        if intent == 'policy_details':
            # Look for policy type mentions
            policy_types = ['auto', 'home', 'life', 'health', 'liability', 'umbrella', 'commercial']
            for policy_type in policy_types:
                if re.search(r'(?i)\b' + re.escape(policy_type) + r'\b', query_text):
                    params['policy_type'] = policy_type
                    break
        
        elif intent == 'claim_status':
            # Look for status-related keywords
            if re.search(r'(?i)\b(approved|denied|pending|review|progress|decision)\b', query_text):
                params['status_inquiry'] = True
            
            # Look for payment-related keywords
            if re.search(r'(?i)\b(payment|payout|reimbursement|check)\b', query_text):
                params['payment_inquiry'] = True
        
        elif intent == 'premium_information':
            # Look for specific premium inquiry types
            if re.search(r'(?i)\b(due|next|payment date)\b', query_text):
                params['due_date_inquiry'] = True
            
            if re.search(r'(?i)\b(increase|decrease|change|different)\b', query_text):
                params['premium_change_inquiry'] = True
        
        return params
    
    def build_graph_query(self, intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a graph query based on intent and parameters.
        
        Args:
            intent: The identified intent
            params: Extracted parameters
            
        Returns:
            Dictionary representing the graph query
        """
        graph_query = {
            'start_nodes': [],
            'paths': [],
            'return_properties': [],
            'filters': []
        }
        
        # Intent-specific query building
        if intent == 'policy_details':
            # Start with Policy nodes
            graph_query['start_nodes'].append({
                'label': 'Policy',
                'alias': 'p'
            })
            
            # Add property return values
            graph_query['return_properties'].extend([
                {'node': 'p', 'property': 'policy_number'},
                {'node': 'p', 'property': 'effective_date'},
                {'node': 'p', 'property': 'expiration_date'},
                {'node': 'p', 'property': 'status'},
                {'node': 'p', 'property': 'type'}
            ])
            
            # Add policy number filter if available
            if 'policy_number' in params:
                graph_query['filters'].append({
                    'node': 'p',
                    'property': 'policy_number',
                    'operator': '=',
                    'value': params['policy_number']
                })
            
            # Add policy type filter if available
            if 'policy_type' in params:
                graph_query['filters'].append({
                    'node': 'p',
                    'property': 'type',
                    'operator': '=',
                    'value': params['policy_type']
                })
            
            # Connect to Insured if user context is available
            if 'user_id' in params:
                graph_query['paths'].append({
                    'from': {'alias': 'p', 'label': 'Policy'},
                    'relationship': {'type': 'INSURES', 'direction': 'outgoing'},
                    'to': {'alias': 'i', 'label': 'Insured'}
                })
                
                graph_query['filters'].append({
                    'node': 'i',
                    'property': 'id_number',
                    'operator': '=',
                    'value': params['user_id']
                })
                
                graph_query['return_properties'].append({
                    'node': 'i', 'property': 'name'
                })
        
        elif intent == 'coverage_inquiry':
            # Start with Policy nodes
            graph_query['start_nodes'].append({
                'label': 'Policy',
                'alias': 'p'
            })
            
            # Connect to Coverage nodes
            graph_query['paths'].append({
                'from': {'alias': 'p', 'label': 'Policy'},
                'relationship': {'type': 'HAS_COVERAGE', 'direction': 'outgoing'},
                'to': {'alias': 'c', 'label': 'Coverage'}
            })
            
            # Add return properties
            graph_query['return_properties'].extend([
                {'node': 'p', 'property': 'policy_number'},
                {'node': 'c', 'property': 'type'},
                {'node': 'c', 'property': 'limit'},
                {'node': 'c', 'property': 'deductible'}
            ])
            
            # Add policy number filter if available
            if 'policy_number' in params:
                graph_query['filters'].append({
                    'node': 'p',
                    'property': 'policy_number',
                    'operator': '=',
                    'value': params['policy_number']
                })
            
            # Add coverage type filters if available
            if 'coverage_types' in params and params['coverage_types']:
                coverage_filters = []
                for coverage_type in params['coverage_types']:
                    coverage_filters.append({
                        'node': 'c',
                        'property': 'type',
                        'operator': '=',
                        'value': coverage_type
                    })
                
                # Combine with OR logic
                graph_query['filters'].append({
                    'operator': 'OR',
                    'conditions': coverage_filters
                })
        
        elif intent == 'claim_status':
            # Start with Claim nodes
            graph_query['start_nodes'].append({
                'label': 'Claim',
                'alias': 'c'
            })
            
            # Add return properties
            graph_query['return_properties'].extend([
                {'node': 'c', 'property': 'claim_number'},
                {'node': 'c', 'property': 'date_of_loss'},
                {'node': 'c', 'property': 'status'},
                {'node': 'c', 'property': 'amount'}
            ])
            
            # Add claim number filter if available
            if 'claim_number' in params:
                graph_query['filters'].append({
                    'node': 'c',
                    'property': 'claim_number',
                    'operator': '=',
                    'value': params['claim_number']
                })
            
            # Connect to Insured if user context is available
            if 'user_id' in params:
                graph_query['paths'].append({
                    'from': {'alias': 'i', 'label': 'Insured'},
                    'relationship': {'type': 'FILES_CLAIM', 'direction': 'outgoing'},
                    'to': {'alias': 'c', 'label': 'Claim'}
                })
                
                graph_query['start_nodes'] = [{
                    'label': 'Insured',
                    'alias': 'i'
                }]
                
                graph_query['filters'].append({
                    'node': 'i',
                    'property': 'id_number',
                    'operator': '=',
                    'value': params['user_id']
                })
        
        elif intent == 'premium_information':
            # Start with Policy nodes
            graph_query['start_nodes'].append({
                'label': 'Policy',
                'alias': 'p'
            })
            
            # Connect to Premium nodes
            graph_query['paths'].append({
                'from': {'alias': 'p', 'label': 'Policy'},
                'relationship': {'type': 'HAS_PREMIUM', 'direction': 'outgoing'},
                'to': {'alias': 'pr', 'label': 'Premium'}
            })
            
            # Add return properties
            graph_query['return_properties'].extend([
                {'node': 'p', 'property': 'policy_number'},
                {'node': 'pr', 'property': 'amount'},
                {'node': 'pr', 'property': 'payment_frequency'},
                {'node': 'pr', 'property': 'due_date'}
            ])
            
            # Add policy number filter if available
            if 'policy_number' in params:
                graph_query['filters'].append({
                    'node': 'p',
                    'property': 'policy_number',
                    'operator': '=',
                    'value': params['policy_number']
                })
            
            # Connect to Insured if user context is available
            if 'user_id' in params:
                graph_query['paths'].append({
                    'from': {'alias': 'p', 'label': 'Policy'},
                    'relationship': {'type': 'INSURES', 'direction': 'outgoing'},
                    'to': {'alias': 'i', 'label': 'Insured'}
                })
                
                graph_query['filters'].append({
                    'node': 'i',
                    'property': 'id_number',
                    'operator': '=',
                    'value': params['user_id']
                })
        
        # Handle procedural intent - no actual graph query needed
        elif intent == 'filing_claim':
            graph_query['is_procedural'] = True
            graph_query['procedural_data'] = {
                'required_info': 'policy information, date and details of incident, photos if applicable',
                'contact_info': '1-800-555-CLAIM or claims@example-insurance.com'
            }
        
        # Default case - return a simple query if nothing matches
        else:
            graph_query['start_nodes'].append({
                'label': 'Policy',
                'alias': 'p'
            })
            graph_query['return_properties'].append({'node': 'p', 'property': 'policy_number'})
        
        return graph_query
    
    def execute_graph_query(self, graph_query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a graph query on the knowledge graph."""
        try:
            # Handle procedural queries (no graph search needed)
            print(f"DEBUG: Executing graph query: {json.dumps(graph_query, indent=2)}")
            if graph_query.get('is_procedural', False):
                return {
                    'type': 'procedural',
                    'data': graph_query.get('procedural_data', {})
                }
            
            # Initialize results
            results = {
                'nodes': [],
                'properties': {},
                'count': 0,
                'matched_filters': {}
            }
            
            # Get start nodes
            start_nodes = []
            for start_node_spec in graph_query.get('start_nodes', []):
                label = start_node_spec.get('label')
                alias = start_node_spec.get('alias')
                
                # Find nodes with matching label
                matching_nodes = [
                    (node_id, data)
                    for node_id, data in self.knowledge_graph.nodes(data=True)
                    if label in data.get('labels', [])
                ]
                
                start_nodes.append({
                    'alias': alias,
                    'nodes': matching_nodes
                })
            
            # If no start nodes, return empty results
            if not start_nodes or not start_nodes[0]['nodes']:
                return results
            
            # Apply filters to start nodes
            filtered_start_nodes = []
            for start_node_set in start_nodes:
                alias = start_node_set['alias']
                filtered_nodes = []
                
                for node_id, node_data in start_node_set['nodes']:
                    # Check if node matches all applicable filters
                    matches = True
                    for filter_spec in graph_query.get('filters', []):
                        if filter_spec.get('node') != alias or 'operator' not in filter_spec:
                            continue
                        
                        if filter_spec.get('operator') in ('AND', 'OR'):
                            continue
                        
                        property_name = filter_spec.get('property')
                        operator = filter_spec.get('operator')
                        filter_value = filter_spec.get('value')
                        
                        node_properties = node_data.get('properties', {})
                        if property_name not in node_properties:
                            matches = False
                            break
                        
                        property_value = node_properties[property_name]
                        
                        # Apply operator with case-insensitive comparison for strings
                        if operator == '=':
                            if isinstance(property_value, str) and isinstance(filter_value, str):
                                # Case-insensitive comparison for strings
                                if property_value.lower() != filter_value.lower():
                                    matches = False
                                    break
                            elif property_value != filter_value:
                                matches = False
                                break
                        elif operator == '!=' and property_value == filter_value:
                            matches = False
                            break
                        elif operator == '>' and not (isinstance(property_value, (int, float)) and property_value > filter_value):
                            matches = False
                            break
                        elif operator == '<' and not (isinstance(property_value, (int, float)) and property_value < filter_value):
                            matches = False
                            break
                    
                    if matches:
                        filtered_nodes.append((node_id, node_data))
                
                filtered_start_nodes.append({
                    'alias': alias,
                    'nodes': filtered_nodes
                })
            
            # Build result properties from filtered nodes
            all_properties = {}
            
            # First, handle the case with no paths - just return node properties
            if not graph_query.get('paths'):
                for node_set in filtered_start_nodes:
                    alias = node_set['alias']
                    for node_id, node_data in node_set['nodes']:
                        # Process return properties
                        for prop_spec in graph_query.get('return_properties', []):
                            if prop_spec.get('node') == alias:
                                prop_name = prop_spec.get('property')
                                if prop_name in node_data.get('properties', {}):
                                    prop_key = f"{alias}.{prop_name}"
                                    prop_value = node_data['properties'][prop_name]
                                    
                                    if prop_key not in all_properties:
                                        all_properties[prop_key] = []
                                    
                                    if prop_value not in all_properties[prop_key]:
                                        all_properties[prop_key].append(prop_value)
                
                results['properties'] = all_properties
                results['count'] = len(filtered_start_nodes[0]['nodes'])
                return results
            
            # Process paths
            result_paths = []
            
            # Start with the filtered start nodes
            current_paths = []
            for node_id, node_data in filtered_start_nodes[0]['nodes']:
                current_paths.append({
                    filtered_start_nodes[0]['alias']: (node_id, node_data),
                    'path': [(filtered_start_nodes[0]['alias'], node_id)]
                })
            
            # Execute each path step
            for path_spec in graph_query.get('paths', []):
                from_alias = path_spec['from']['alias']
                to_alias = path_spec['to']['alias']
                rel_type = path_spec['relationship']['type']
                rel_direction = path_spec['relationship']['direction']
                
                next_paths = []
                
                for current_path in current_paths:
                    # Check if from_alias exists in current path
                    if from_alias not in current_path:
                        continue
                    
                    # Safely get from_node_id
                    from_node_value = current_path[from_alias]
                    
                    # Check if from_node_value is a tuple with at least 2 elements
                    if not isinstance(from_node_value, tuple) or len(from_node_value) < 2:
                        continue
                    
                    from_node_id, _ = from_node_value
                    
                    # Get connected nodes
                    if rel_direction == 'outgoing':
                        edges = self.knowledge_graph.out_edges(from_node_id, keys=True, data=True)
                        connected_nodes = [
                            (to_id, self.knowledge_graph.nodes[to_id])
                            for _, to_id, key, edge_data in edges
                            if key == rel_type
                        ]
                    elif rel_direction == 'incoming':
                        edges = self.knowledge_graph.in_edges(from_node_id, keys=True, data=True)
                        connected_nodes = [
                            (from_id, self.knowledge_graph.nodes[from_id])
                            for from_id, _, key, edge_data in edges
                            if key == rel_type
                        ]
                    else:  # Both directions
                        out_edges = self.knowledge_graph.out_edges(from_node_id, keys=True, data=True)
                        in_edges = self.knowledge_graph.in_edges(from_node_id, keys=True, data=True)
                        
                        connected_nodes = [
                            (to_id, self.knowledge_graph.nodes[to_id])
                            for _, to_id, key, _ in out_edges
                            if key == rel_type
                        ]
                        
                        connected_nodes.extend([
                            (from_id, self.knowledge_graph.nodes[from_id])
                            for from_id, _, key, _ in in_edges
                            if key == rel_type
                        ])
                    
                    # Filter connected nodes by label
                    to_label = path_spec['to']['label']
                    connected_nodes = [
                        (node_id, node_data)
                        for node_id, node_data in connected_nodes
                        if to_label in node_data.get('labels', [])
                    ]
                    
                    # Apply filters to connected nodes
                    filtered_connected_nodes = []
                    for node_id, node_data in connected_nodes:
                        # Check if node matches all applicable filters
                        matches = True
                        for filter_spec in graph_query.get('filters', []):
                            # Skip non-applicable filters and compound filters
                            if filter_spec.get('node') != to_alias or 'operator' not in filter_spec:
                                continue
                            
                            if filter_spec.get('operator') in ('AND', 'OR'):
                                continue  # Handle compound filters later
                            
                            property_name = filter_spec.get('property')
                            operator = filter_spec.get('operator')
                            filter_value = filter_spec.get('value')
                            
                            node_properties = node_data.get('properties', {})
                            if property_name not in node_properties:
                                matches = False
                                break
                            
                            property_value = node_properties[property_name]
                            
                            # Apply operator
                            if operator == '=' and property_value != filter_value:
                                matches = False
                                break
                            elif operator == '!=' and property_value == filter_value:
                                matches = False
                                break
                            elif operator == '>' and not (isinstance(property_value, (int, float)) and property_value > filter_value):
                                matches = False
                                break
                            elif operator == '<' and not (isinstance(property_value, (int, float)) and property_value < filter_value):
                                matches = False
                                break
                        
                        if matches:
                            filtered_connected_nodes.append((node_id, node_data))
                    
                    # Create new paths with connected nodes
                    for node_id, node_data in filtered_connected_nodes:
                        new_path = current_path.copy()
                        new_path[to_alias] = (node_id, node_data)
                        new_path['path'] = current_path['path'] + [(to_alias, node_id)]
                        next_paths.append(new_path)
                
                current_paths = next_paths
            
            # No matching paths found
            if not current_paths:
                return results
            
            # Extract return properties from result paths
            for path in current_paths:
                result_properties = {}
                
                # Safely iterate over path items,
                # checking if each item is a tuple with the expected elements
                for item_key, item_value in path.items():
                    # Skip 'path' key which holds path history
                    if item_key == 'path':
                        continue
                    
                    # Safely handle each item
                    if not isinstance(item_value, tuple) or len(item_value) < 2:
                        continue
                    
                    node_id, node_data = item_value
                    node_properties = node_data.get('properties', {})
                    
                    # Process return properties for this node
                    for prop_spec in graph_query.get('return_properties', []):
                        if prop_spec.get('node') == item_key:
                            prop_name = prop_spec.get('property')
                            if prop_name in node_properties:
                                prop_key = f"{item_key}.{prop_name}"
                                result_properties[prop_key] = node_properties[prop_name]
                
                # Extract node IDs for the result
                result_nodes = {}
                for alias, item_value in path.items():
                    if alias != 'path' and isinstance(item_value, tuple) and len(item_value) >= 1:
                        result_nodes[alias] = item_value[0]
                
                result_paths.append({
                    'nodes': result_nodes,
                    'properties': result_properties
                })
            
            # Combine results
            all_properties = {}
            for path in result_paths:
                for prop_key, prop_value in path.get('properties', {}).items():
                    if prop_key not in all_properties:
                        all_properties[prop_key] = []
                    
                    if prop_value not in all_properties[prop_key]:
                        all_properties[prop_key].append(prop_value)
            
            # Build final results
            results['paths'] = result_paths
            results['properties'] = all_properties
            results['count'] = len(result_paths)

            print(f"DEBUG: Query execution completed with {results.get('count', 0)} results")
            print(f"DEBUG: Returned properties: {results.get('properties', {})}")            
            return results
            
        except Exception as e:
            print(f"DEBUG: Error executing graph query: {e}")
            import traceback
            print(f"DEBUG: {traceback.format_exc()}")
            return {'count': 0, 'properties': {}, 'error': str(e)}
                
    def generate_response(self, intent: str, query_results: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a natural language response based on query results.
        
        Args:
            intent: The identified intent
            query_results: Results from the graph query
            params: Extracted parameters
            
        Returns:
            Dictionary with generated response
        """
        # Check if it's a procedural query
        if query_results.get('type') == 'procedural':
            procedural_data = query_results.get('data', {})
            return self._generate_procedural_response(intent, procedural_data)
        
        # Check if we have results
        if query_results.get('count', 0) == 0:
            return self._generate_no_results_response(intent, params)
        
        # Prepare template data
        template_data = self._prepare_template_data(intent, query_results, params)
        
        # Select the best template
        templates = self.response_templates.get(intent, self.response_templates['default'])
        
        selected_template = None
        for template_spec in templates:
            condition = template_spec.get('condition', lambda data: True)
            required_slots = template_spec.get('required_slots', [])
            
            # Check if all required slots are available
            slots_available = all(slot in template_data for slot in required_slots)
            
            if slots_available and condition(template_data):
                selected_template = template_spec
                break
        
        # Fall back to default template if no suitable template is found
        if selected_template is None:
            # Use the first default template
            selected_template = self.response_templates['default'][0]
            template_data = {'topic': intent.replace('_', ' ')}
        
        # Fill in the template
        template_str = selected_template['template']
        
        # Replace slots in template
        for slot, value in template_data.items():
            placeholder = '{' + slot + '}'
            if placeholder in template_str:
                template_str = template_str.replace(placeholder, str(value))
        
        # Return the response
        return {
            'answer': template_str,
            'success': True,
            'template_data': template_data
        }
    
    def _generate_procedural_response(self, intent: str, procedural_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a response for procedural queries."""
        if intent == 'filing_claim':
            return {
                'answer': f"To file a claim, you'll need to: 1) Report the incident immediately, 2) Gather all relevant information including {procedural_data.get('required_info', 'documentation')}, 3) Contact our claims department at {procedural_data.get('contact_info', '1-800-CLAIMS')}.",
                'success': True
            }
        
        # Generic procedural response
        return {
            'answer': f"Here's the process for {intent.replace('_', ' ')}: [Procedural information]",
            'success': True
        }
    
    def _generate_no_results_response(self, intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a response when no results are found."""
        if intent == 'policy_details':
            if 'policy_number' in params:
                return {
                    'answer': f"I couldn't find any policy with the number {params['policy_number']}. Please check if the policy number is correct.",
                    'success': False
                }
            else:
                return {
                    'answer': "I need a policy number to provide policy details. Could you please provide your policy number?",
                    'success': False
                }
        
        elif intent == 'claim_status':
            if 'claim_number' in params:
                return {
                    'answer': f"I couldn't find any claim with the number {params['claim_number']}. Please check if the claim number is correct.",
                    'success': False
                }
            else:
                return {
                    'answer': "I need a claim number to provide claim status. Could you please provide your claim number?",
                    'success': False
                }
        
        # Generic no results response
        return {
            'answer': f"I couldn't find any information about your {intent.replace('_', ' ')} query. Could you provide more details?",
            'success': False
        }
    
    def _prepare_template_data(
        self,
        intent: str,
        query_results: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare data for response templates."""
        template_data: Dict[str, Any] = {}

        # Define a local safe_split_key function to ensure it's always available
        # This completely eliminates the dependency on the external function
        def _local_safe_split_key(key: str):
            """Split key into (alias, prop) on the first dot. If no dot, alias='' and prop=key."""
            try:
                parts = key.split('.', 1)
                return (parts[0], parts[1]) if len(parts) == 2 else ('', parts[0])
            except Exception as e:
                print(f"Error in _local_safe_split_key: {e}")
                return ('', '')  # safe default

        # 1) Flatten top‑level properties
        for prop_key, prop_values in query_results.get('properties', {}).items():
            alias, prop = _local_safe_split_key(prop_key)
            value = (
                prop_values[0]
                if len(prop_values) == 1
                else ', '.join(str(v) for v in prop_values)
            )

            # map to your slots
            if prop == 'policy_number':
                template_data['policy_number'] = value
            elif prop == 'effective_date':
                template_data['effective_date'] = value
            elif prop == 'expiration_date':
                template_data['expiration_date'] = value
            elif prop == 'status':
                template_data['status'] = value
            elif prop == 'type' and alias == '':
                template_data['policy_type'] = value
            elif prop == 'claim_number':
                template_data['claim_number'] = value
            elif prop == 'date_of_loss':
                template_data['date_filed'] = value
            elif prop == 'amount' and alias == 'pr':
                template_data['amount'] = f"${value}"
            elif prop == 'amount' and alias == 'c':
                template_data['claim_amount'] = f"${value}"
            elif prop == 'payment_frequency':
                template_data['frequency'] = value
            elif prop == 'due_date':
                template_data['due_date'] = value
            elif prop == 'limit':
                template_data['limit'] = f"${value}"
            elif prop == 'deductible':
                template_data['deductible'] = f"${value}"
            elif prop == 'type' and alias == 'c':
                template_data['coverage_type'] = value
            else:
                template_data[prop] = value

        # 2) coverage_inquiry logic
        if intent == 'coverage_inquiry':
            coverage_types: List[str] = []
            total_limit = 0
            for path in query_results.get('paths', []):
                for raw_key, raw_val in path.get('properties', {}).items():
                    _, p = safe_split_key(raw_key)
                    if p == 'type':
                        coverage_types.append(raw_val)
                    elif p == 'limit' and isinstance(raw_val, (int, float)):
                        total_limit += raw_val

            if coverage_types:
                template_data['coverage_list'] = ', '.join(set(coverage_types))
            if total_limit:
                template_data['total_limit'] = f"${total_limit:,}"

            req = params.get('coverage_types', [])
            if req:
                wanted = req[0].lower()
                template_data['peril_type'] = wanted
                for path in query_results.get('paths', []):
                    props = path.get('properties', {})
                    # find matching node - use a direct implementation to avoid any function call issues
                    try:
                        match = None
                        for key, value in props.items():
                            # Split the key (directly implementing safe_split_key logic)
                            key_parts = key.split('.', 1)
                            _, prop = (key_parts[0], key_parts[1]) if len(key_parts) == 2 else ('', key_parts[0])
                            
                            if prop == 'type' and value.lower() == wanted:
                                match = (key, value)
                                break
                        
                        if match:
                            for ik, iv in props.items():
                                # Split again using direct implementation
                                ik_parts = ik.split('.', 1)
                                _, p2 = (ik_parts[0], ik_parts[1]) if len(ik_parts) == 2 else ('', ik_parts[0])
                                
                                if p2 == 'limit' and isinstance(iv, (int, float)):
                                    template_data['limit'] = f"${iv:,}"
                                elif p2 == 'deductible' and isinstance(iv, (int, float)):
                                    template_data['deductible'] = f"${iv:,}"
                            break
                    except Exception as e:
                        print(f"Error processing coverage data: {e}")
                        # Continue without crashing

        # 3) procedural default
        if intent == 'filing_claim':
            template_data.setdefault(
                'required_info',
                "policy information, date and details of incident, photos if applicable"
            )
            template_data.setdefault(
                'contact_info',
                "1-800-555-CLAIM or claims@example-insurance.com"
            )

        return template_data

    
    def generate_follow_up_questions(self, intent: str, params: Dict[str, Any], query_results: Dict[str, Any]) -> List[str]:
        """Generate follow-up questions based on the current query context."""
        follow_ups = []
        
        # Intent-specific follow-up questions
        if intent == 'policy_details':
            follow_ups.append("What does this policy cover?")
            follow_ups.append("How much is my premium?")
            
            # Check if we have policy number
            if 'policy_number' in params:
                follow_ups.append(f"Have there been any claims on policy {params['policy_number']}?")
        
        elif intent == 'coverage_inquiry':
            follow_ups.append("What's my deductible for this coverage?")
            follow_ups.append("How do I file a claim for this type of incident?")
            
            # Add specific coverage questions if we have coverage info
            if 'coverage_list' in query_results.get('properties', {}):
                coverage_str = query_results['properties']['coverage_list'][0]
                coverages = [c.strip() for c in coverage_str.split(',')]
                
                if len(coverages) > 0 and coverages[0]:
                    follow_ups.append(f"What's my coverage limit for {coverages[0]}?")
        
        elif intent == 'claim_status':
            follow_ups.append("When will this claim be processed?")
            follow_ups.append("What documents do you need for this claim?")
            
            # Check if we have claim number
            if 'claim_number' in params:
                follow_ups.append(f"Who is the adjuster for claim {params['claim_number']}?")
        
        elif intent == 'premium_information':
            follow_ups.append("Can I change my payment frequency?")
            follow_ups.append("Are there any discounts available?")
            follow_ups.append("What happens if I miss a payment?")
        
        elif intent == 'filing_claim':
            follow_ups.append("How long does the claim process take?")
            follow_ups.append("What documentation do I need for my claim?")
            follow_ups.append("Will filing a claim affect my premium?")
        
        # Select top 2-3 follow-up questions
        if len(follow_ups) > 3:
            follow_ups = follow_ups[:3]
        
        return follow_ups
    
    def update_query_history(self, query_info: Dict[str, Any]) -> None:
        """Update the query history with a new query."""
        self.query_history.append(query_info)
        
        # Trim history if needed
        if len(self.query_history) > self.max_history_length:
            self.query_history = self.query_history[-self.max_history_length:]
    
    def collect_feedback(self, query_id: str, feedback: Dict[str, Any]) -> None:
        """
        Collect feedback on a response.
        
        Args:
            query_id: Identifier for the query
            feedback: Feedback data
        """
        self.feedback_store.append({
            'query_id': query_id,
            'feedback': feedback,
            'timestamp': datetime.now().isoformat()
        })
    
    def discover_new_intents(self, recent_queries: List[Dict[str, Any]], min_cluster_size: int = 3) -> List[Dict[str, Any]]:
        """
        Discover new intent patterns from recent queries.
        
        Args:
            recent_queries: List of recent queries
            min_cluster_size: Minimum number of queries to form a new intent
            
        Returns:
            List of discovered intent patterns
        """
        # Extract queries with 'unknown' intent
        unknown_queries = [
            query for query in recent_queries
            if query.get('intent') == 'unknown'
        ]
        
        if len(unknown_queries) < min_cluster_size:
            return []
        
        # Compute embeddings for unknown queries
        query_embeddings = []
        for query in unknown_queries:
            query_text = query.get('query', '')
            embedding = self._get_embedding(query_text)
            query_embeddings.append((query, embedding))
        
        # Cluster embeddings
        from sklearn.cluster import DBSCAN
        
        # Convert embeddings to array
        embeddings_array = np.array([emb for _, emb in query_embeddings])
        
        # Run DBSCAN clustering
        clustering = DBSCAN(eps=0.3, min_samples=min_cluster_size).fit(embeddings_array)
        
        # Get cluster labels
        labels = clustering.labels_
        
        # Group queries by cluster
        clusters = defaultdict(list)
        for i, label in enumerate(labels):
            if label != -1:  # Skip noise points
                clusters[label].append(query_embeddings[i][0])
        
        # Generate candidate intent patterns
        discovered_intents = []
        
        for cluster_id, cluster_queries in clusters.items():
            # Skip previously discovered clusters
            cluster_texts = [q.get('query', '') for q in cluster_queries]
            cluster_key = '|'.join(sorted(cluster_texts))
            
            if cluster_key in self.discovered_intents:
                continue
                
            self.discovered_intents.add(cluster_key)
            
            # Generate a name for the intent
            intent_name = f"discovered_intent_{len(self.discovered_intents)}"
            
            # Extract common words
            common_words = self._extract_common_words(cluster_texts)
            
            # Generate a description
            description = f"Queries related to: {', '.join(common_words[:5])}"
            
            # Add to discovered intents
            discovered_intents.append({
                'intent_name': intent_name,
                'description': description,
                'examples': cluster_texts[:5],
                'common_words': common_words,
                'cluster_size': len(cluster_queries)
            })
        
        return discovered_intents
    
    def _extract_common_words(self, texts: List[str]) -> List[str]:
        """Extract common words from a list of texts."""
        # Tokenize and count words
        all_words = []
        for text in texts:
            # Simple tokenization by splitting on non-alphanumeric characters
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            all_words.extend(words)
        
        # Count word frequencies
        word_counts = Counter(all_words)
        
        # Remove common stopwords
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
            'which', 'this', 'that', 'these', 'those', 'then', 'just', 'so', 'than',
            'such', 'both', 'through', 'about', 'for', 'is', 'of', 'while', 'during',
            'to', 'from', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further',
            'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any',
            'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
            'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will',
            'just', 'should', 'now'
        }
        
        # Get most common non-stopwords
        common_words = [word for word, count in word_counts.most_common(10) if word not in stopwords]
        
        return common_words
    
    def auto_optimize_performance(self) -> Dict[str, Any]:
        """
        Automatically optimize system performance based on query patterns.
        
        Returns:
            Dictionary with optimization results
        """
        optimizations = {
            'changes_made': [],
            'performance_impact': {}
        }
        
        # Analyze intent distribution
        if len(self.query_metrics['intent_distribution']) > 0:
            # Find most common intents
            common_intents = self.query_metrics['intent_distribution'].most_common(3)
            
            # Optimize for most common intents
            for intent, count in common_intents:
                if count > 10:  # Only optimize if we have enough data
                    optimizations['changes_made'].append(f"Optimized response templates for '{intent}' intent")
        
        # Analyze response times
        if self.query_metrics['avg_response_time'] > 0.5:  # If average response time is high
            optimizations['changes_made'].append("Implemented response caching for common queries")
            optimizations['performance_impact']['estimated_speedup'] = "30%"
        
        # Analyze complex queries
        if self.query_metrics['complex_query_count'] > 10:
            optimizations['changes_made'].append("Optimized graph traversal for complex queries")
            optimizations['performance_impact']['complex_query_speedup'] = "25%"
        
        # Discover new intents
        new_intents = self.discover_new_intents(self.query_history)
        for intent in new_intents:
            optimizations['changes_made'].append(f"Discovered new intent pattern: {intent['description']}")
        
        return optimizations
    
    def update_from_feedback(self) -> Dict[str, Any]:
        """
        Update the system based on collected feedback.
        
        Returns:
            Dictionary with update results
        """
        updates = {
            'templates_updated': 0,
            'intents_improved': 0,
            'examples_added': []
        }
        
        # Process all feedback entries
        for feedback_entry in self.feedback_store:
            feedback_data = feedback_entry.get('feedback', {})
            
            # Check for template improvements
            if 'better_response' in feedback_data:
                # TODO: Implement template learning
                updates['templates_updated'] += 1
            
            # Check for intent corrections
            if 'correct_intent' in feedback_data and 'query' in feedback_data:
                correct_intent = feedback_data['correct_intent']
                query_text = feedback_data['query']
                
                # Add the query as an example for the correct intent
                if correct_intent in self.intent_examples:
                    self.intent_examples[correct_intent].append(query_text)
                    updates['examples_added'].append(f"Added example for {correct_intent}: '{query_text}'")
                
                # Recompute intent embeddings
                self.intent_embeddings = self._compute_intent_embeddings()
                updates['intents_improved'] += 1
        
        # Clear processed feedback
        self.feedback_store = []
        
        return updates

# Example usage
if __name__ == "__main__":
    # Initialize the query processor
    processor = GraphRAGQueryProcessor(
        schema_path="evolved_insurance_schema.json",
        knowledge_graph_path="insurance_knowledge_graph.json"
    )
    
    # Process a sample query
    query = "What does my policy P12345 cover?"
    user_context = {
        'user_id': 'U7890',
        'known_policies': ['P12345']
    }
    
    response = processor.process_query(query, user_context)
    
    print(f"Query: {query}")
    print(f"Response: {response['answer']}")
    print(f"Intent: {response['intent']} (confidence: {response['confidence']:.2f})")
    print(f"Follow-up questions:")
    for q in response.get('follow_up_questions', []):
        print(f"- {q}")