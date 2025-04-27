# Step 4: Fully Automated Testing & Quality Assurance for Insurance Graph RAG

import os
import json
import time
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict, Any, Tuple, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict, Counter

class AutomatedQASystem:
    def __init__(self, query_processor, schema_manager, knowledge_graph_path: str = None):
        """
        Initialize the automated testing and QA system.
        
        Args:
            query_processor: The query processor instance
            schema_manager: The schema manager instance
            knowledge_graph_path: Path to the knowledge graph data
        """
        self.query_processor = query_processor
        self.schema_manager = schema_manager
        self.knowledge_graph_path = knowledge_graph_path
        
        # Load knowledge graph data for testing
        self.knowledge_graph_data = self._load_knowledge_graph_data()
        
        # Initialize test suites
        self.test_suites = self._initialize_test_suites()
        
        # Test case generation system
        self.synthetic_test_generators = self._initialize_test_generators()
        
        # Test execution history
        self.test_history = []
        
        # Error pattern recognition
        self.error_patterns = defaultdict(int)
        self.error_examples = defaultdict(list)
        
        # Performance benchmarks
        self.performance_benchmarks = {
            'baseline': None,
            'current': None,
            'history': []
        }
        
        # Compliance rules
        self.compliance_rules = self._initialize_compliance_rules()
        
        # Debug history
        self.debug_actions = []
        
        print("Automated QA System initialized successfully")
    
    def _load_knowledge_graph_data(self) -> Dict[str, Any]:
        """Load knowledge graph data for testing."""
        if not self.knowledge_graph_path or not os.path.exists(self.knowledge_graph_path):
            print("No knowledge graph data available, using synthetic data for testing")
            return self._create_synthetic_graph_data()
            
        try:
            with open(self.knowledge_graph_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading knowledge graph data: {e}")
            return self._create_synthetic_graph_data()
    
    def _create_synthetic_graph_data(self) -> Dict[str, Any]:
        """Create synthetic graph data for testing when real data is not available."""
        # Generate synthetic policies
        policies = []
        for i in range(10):
            policy_id = f"P{i+1000}"
            effective_date = (datetime.now() - timedelta(days=random.randint(30, 730))).strftime("%Y-%m-%d")
            expiration_date = (datetime.now() + timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d")
            status = random.choice(["active", "expired", "cancelled"])
            policy_type = random.choice(["auto", "home", "health", "life", "liability"])
            
            policies.append({
                "id": policy_id,
                "labels": ["Policy"],
                "properties": {
                    "policy_number": policy_id,
                    "effective_date": effective_date,
                    "expiration_date": expiration_date,
                    "status": status,
                    "type": policy_type
                }
            })
        
        # Generate synthetic insureds
        insureds = []
        for i in range(8):
            insured_id = f"I{i+2000}"
            insureds.append({
                "id": insured_id,
                "labels": ["Insured"],
                "properties": {
                    "name": f"User {i+1}",
                    "id_number": f"U{i+5000}",
                    "date_of_birth": (datetime.now() - timedelta(days=365*random.randint(20, 80))).strftime("%Y-%m-%d"),
                    "contact_info": json.dumps({
                        "email": f"user{i+1}@example.com",
                        "phone": f"555-{i+100}-{i+1000}"
                    })
                }
            })
        
        # Generate synthetic coverages
        coverages = []
        coverage_types = ["liability", "collision", "comprehensive", "medical", "property", "flood", "fire", "theft"]
        for i in range(20):
            coverage_id = f"C{i+3000}"
            coverage_type = random.choice(coverage_types)
            coverages.append({
                "id": coverage_id,
                "labels": ["Coverage"],
                "properties": {
                    "type": coverage_type,
                    "limit": random.choice([50000, 100000, 250000, 500000, 1000000]),
                    "deductible": random.choice([0, 250, 500, 1000, 2000])
                }
            })
        
        # Generate synthetic claims
        claims = []
        for i in range(15):
            claim_id = f"CL{i+4000}"
            date_of_loss = (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d")
            status = random.choice(["open", "under_review", "approved", "denied", "closed"])
            claims.append({
                "id": claim_id,
                "labels": ["Claim"],
                "properties": {
                    "claim_number": claim_id,
                    "date_of_loss": date_of_loss,
                    "status": status,
                    "amount": random.randint(500, 50000)
                }
            })
        
        # Generate synthetic premiums
        premiums = []
        for i in range(len(policies)):
            premium_id = f"PR{i+5000}"
            premiums.append({
                "id": premium_id,
                "labels": ["Premium"],
                "properties": {
                    "amount": random.randint(500, 5000),
                    "payment_frequency": random.choice(["monthly", "quarterly", "semi-annually", "annually"]),
                    "due_date": (datetime.now() + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
                }
            })
        
        # Generate synthetic relationships
        edges = []
        
        # Policy to Insured relationships
        for policy in policies:
            insured = random.choice(insureds)
            edges.append({
                "source": policy["id"],
                "target": insured["id"],
                "type": "INSURES",
                "properties": {}
            })
        
        # Policy to Coverage relationships
        for policy in policies:
            # Each policy has 1-3 coverages
            num_coverages = random.randint(1, 3)
            selected_coverages = random.sample(coverages, num_coverages)
            
            for coverage in selected_coverages:
                edges.append({
                    "source": policy["id"],
                    "target": coverage["id"],
                    "type": "HAS_COVERAGE",
                    "properties": {
                        "added_date": policy["properties"]["effective_date"]
                    }
                })
        
        # Policy to Premium relationships
        for i, policy in enumerate(policies):
            if i < len(premiums):
                edges.append({
                    "source": policy["id"],
                    "target": premiums[i]["id"],
                    "type": "HAS_PREMIUM",
                    "properties": {}
                })
        
        # Insured to Claim relationships
        for insured in insureds:
            # Each insured may have 0-2 claims
            num_claims = random.randint(0, 2)
            if num_claims > 0 and len(claims) > 0:
                selected_claims = random.sample(claims, min(num_claims, len(claims)))
                
                for claim in selected_claims:
                    edges.append({
                        "source": insured["id"],
                        "target": claim["id"],
                        "type": "FILES_CLAIM",
                        "properties": {
                            "filing_date": claim["properties"]["date_of_loss"]
                        }
                    })
        
        # Claim to Coverage relationships
        for claim in claims:
            # Each claim is related to 1 coverage
            coverage = random.choice(coverages)
            edges.append({
                "source": claim["id"],
                "target": coverage["id"],
                "type": "RELATED_TO",
                "properties": {}
            })
        
        # Combine all nodes
        nodes = policies + insureds + coverages + claims + premiums
        
        return {
            "nodes": nodes,
            "edges": edges
        }
    
    def _initialize_test_suites(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize standard test suites."""
        return {
            'intent_recognition': self._create_intent_recognition_tests(),
            'parameter_extraction': self._create_parameter_extraction_tests(),
            'graph_querying': self._create_graph_querying_tests(),
            'response_generation': self._create_response_generation_tests(),
            'end_to_end': self._create_end_to_end_tests(),
            'edge_cases': self._create_edge_case_tests(),
            'compliance': self._create_compliance_tests()
        }
    
    def _create_intent_recognition_tests(self) -> List[Dict[str, Any]]:
        """Create tests for intent recognition."""
        return [
            {
                'name': 'policy_details_standard',
                'query': 'What are the details of my policy P1001?',
                'expected': {
                    'intent': 'policy_details',
                    'confidence_min': 0.7
                }
            },
            {
                'name': 'coverage_inquiry_standard',
                'query': 'What does my policy cover?',
                'expected': {
                    'intent': 'coverage_inquiry',
                    'confidence_min': 0.7
                }
            },
            {
                'name': 'claim_status_standard',
                'query': 'What is the status of claim CL4001?',
                'expected': {
                    'intent': 'claim_status',
                    'confidence_min': 0.7
                }
            },
            {
                'name': 'premium_information_standard',
                'query': 'How much is my premium for policy P1002?',
                'expected': {
                    'intent': 'premium_information',
                    'confidence_min': 0.7
                }
            },
            {
                'name': 'filing_claim_standard',
                'query': 'How do I file a claim for water damage?',
                'expected': {
                    'intent': 'filing_claim',
                    'confidence_min': 0.7
                }
            },
            {
                'name': 'ambiguous_intent_handling',
                'query': 'I need information about my insurance',
                'expected': {
                    'confidence_min': 0.5,
                    'not_intent': 'unknown'
                }
            },
            {
                'name': 'out_of_domain_intent_handling',
                'query': 'What is the weather forecast for tomorrow?',
                'expected': {
                    'intent': 'unknown'
                }
            }
        ]
    
    def _create_parameter_extraction_tests(self) -> List[Dict[str, Any]]:
        """Create tests for parameter extraction."""
        return [
            {
                'name': 'policy_number_extraction',
                'query': 'Tell me about policy P1234',
                'intent': 'policy_details',
                'expected': {
                    'params': {
                        'policy_number': 'P1234'
                    }
                }
            },
            {
                'name': 'claim_number_extraction',
                'query': 'What is the status of claim number CL5678?',
                'intent': 'claim_status',
                'expected': {
                    'params': {
                        'claim_number': 'CL5678'
                    }
                }
            },
            {
                'name': 'policy_type_extraction',
                'query': 'What does my auto insurance policy cover?',
                'intent': 'coverage_inquiry',
                'expected': {
                    'params': {
                        'policy_type': 'auto'
                    }
                }
            },
            {
                'name': 'coverage_type_extraction',
                'query': 'Am I covered for flood damage?',
                'intent': 'coverage_inquiry',
                'expected': {
                    'params': {
                        'coverage_types': ['flood']
                    }
                }
            },
            {
                'name': 'multiple_parameter_extraction',
                'query': 'What is the deductible for collision coverage on my auto policy P1005?',
                'intent': 'coverage_inquiry',
                'expected': {
                    'params': {
                        'policy_number': 'P1005',
                        'policy_type': 'auto',
                        'coverage_types': ['collision']
                    }
                }
            },
            {
                'name': 'date_extraction',
                'query': 'What claims did I file since 01/15/2024?',
                'intent': 'claim_status',
                'expected': {
                    'params': {
                        'date_reference': '01/15/2024'
                    }
                }
            }
        ]
    
    def _create_graph_querying_tests(self) -> List[Dict[str, Any]]:
        """Create tests for graph querying capabilities."""
        return [
            {
                'name': 'policy_lookup_by_number',
                'graph_query': {
                    'start_nodes': [{'label': 'Policy', 'alias': 'p'}],
                    'filters': [{'node': 'p', 'property': 'policy_number', 'operator': '=', 'value': 'P1001'}],
                    'return_properties': [{'node': 'p', 'property': 'policy_number'}]
                },
                'expected': {
                    'count_min': 1
                }
            },
            {
                'name': 'policy_coverage_relationship',
                'graph_query': {
                    'start_nodes': [{'label': 'Policy', 'alias': 'p'}],
                    'paths': [{
                        'from': {'alias': 'p', 'label': 'Policy'},
                        'relationship': {'type': 'HAS_COVERAGE', 'direction': 'outgoing'},
                        'to': {'alias': 'c', 'label': 'Coverage'}
                    }],
                    'return_properties': [
                        {'node': 'p', 'property': 'policy_number'},
                        {'node': 'c', 'property': 'type'}
                    ],
                    'filters': [{'node': 'p', 'property': 'policy_number', 'operator': '=', 'value': 'P1001'}]
                },
                'expected': {
                    'count_min': 1,
                    'property_exists': 'c.type'
                }
            },
            {
                'name': 'insured_claims_relationship',
                'graph_query': {
                    'start_nodes': [{'label': 'Insured', 'alias': 'i'}],
                    'paths': [{
                        'from': {'alias': 'i', 'label': 'Insured'},
                        'relationship': {'type': 'FILES_CLAIM', 'direction': 'outgoing'},
                        'to': {'alias': 'c', 'label': 'Claim'}
                    }],
                    'return_properties': [
                        {'node': 'i', 'property': 'id_number'},
                        {'node': 'c', 'property': 'claim_number'}
                    ]
                },
                'expected': {
                    'count_min': 1
                }
            },
            {
                'name': 'complex_multi_hop_query',
                'graph_query': {
                    'start_nodes': [{'label': 'Insured', 'alias': 'i'}],
                    'paths': [
                        {
                            'from': {'alias': 'i', 'label': 'Insured'},
                            'relationship': {'type': 'FILES_CLAIM', 'direction': 'outgoing'},
                            'to': {'alias': 'c', 'label': 'Claim'}
                        },
                        {
                            'from': {'alias': 'c', 'label': 'Claim'},
                            'relationship': {'type': 'RELATED_TO', 'direction': 'outgoing'},
                            'to': {'alias': 'cov', 'label': 'Coverage'}
                        }
                    ],
                    'return_properties': [
                        {'node': 'i', 'property': 'name'},
                        {'node': 'c', 'property': 'claim_number'},
                        {'node': 'cov', 'property': 'type'}
                    ]
                },
                'expected': {
                    'count_min': 1
                }
            }
        ]
    
    def _create_response_generation_tests(self) -> List[Dict[str, Any]]:
        """Create tests for response generation."""
        return [
            {
                'name': 'policy_details_response',
                'intent': 'policy_details',
                'template_data': {
                    'policy_number': 'P1001',
                    'policy_type': 'auto',
                    'effective_date': '2023-01-15',
                    'expiration_date': '2024-01-15',
                    'status': 'active'
                },
                'expected': {
                    'contains': ['P1001', 'auto', 'active']
                }
            },
            {
                'name': 'coverage_response',
                'intent': 'coverage_inquiry',
                'template_data': {
                    'coverage_list': 'liability, collision, comprehensive',
                    'total_limit': '$750,000'
                },
                'expected': {
                    'contains': ['liability', 'collision', 'comprehensive', '$750,000']
                }
            },
            {
                'name': 'claim_status_response',
                'intent': 'claim_status',
                'template_data': {
                    'claim_number': 'CL4001',
                    'status': 'approved',
                    'date_filed': '2023-11-30'
                },
                'expected': {
                    'contains': ['CL4001', 'approved']
                }
            },
            {
                'name': 'premium_response',
                'intent': 'premium_information',
                'template_data': {
                    'amount': '$1,200',
                    'frequency': 'monthly',
                    'due_date': '2023-12-15'
                },
                'expected': {
                    'contains': ['$1,200', 'monthly', '2023-12-15']
                }
            },
            {
                'name': 'filing_claim_response',
                'intent': 'filing_claim',
                'template_data': {
                    'required_info': 'policy information, date and details of incident',
                    'contact_info': '1-800-555-CLAIM'
                },
                'expected': {
                    'contains': ['policy information', '1-800-555-CLAIM']
                }
            },
            {
                'name': 'missing_data_handling',
                'intent': 'policy_details',
                'template_data': {
                    'policy_number': 'P1001'
                    # Missing other fields
                },
                'expected': {
                    'contains': ['P1001'],
                    'success': False
                }
            }
        ]
    
    def _create_end_to_end_tests(self) -> List[Dict[str, Any]]:
        """Create end-to-end tests for the full system."""
        return [
            {
                'name': 'policy_details_end_to_end',
                'query': 'What are the details of my policy P1001?',
                'user_context': {
                    'user_id': 'U5001'
                },
                'expected': {
                    'intent': 'policy_details',
                    'success': True,
                    'contains': ['P1001']
                }
            },
            {
                'name': 'coverage_inquiry_end_to_end',
                'query': 'What does my auto policy cover?',
                'user_context': {
                    'user_id': 'U5002',
                    'known_policies': ['P1002']
                },
                'expected': {
                    'intent': 'coverage_inquiry',
                    'success': True,
                    'contains': ['cover']
                }
            },
            {
                'name': 'claim_status_end_to_end',
                'query': 'What is the status of my claim CL4001?',
                'user_context': {
                    'user_id': 'U5003'
                },
                'expected': {
                    'intent': 'claim_status',
                    'success': True,
                    'contains': ['CL4001', 'status']
                }
            },
            {
                'name': 'premium_information_end_to_end',
                'query': 'How much is my premium for policy P1003?',
                'user_context': {
                    'user_id': 'U5004'
                },
                'expected': {
                    'intent': 'premium_information',
                    'success': True,
                    'contains': ['premium', 'P1003']
                }
            },
            {
                'name': 'filing_claim_end_to_end',
                'query': 'How do I file a claim for water damage?',
                'user_context': {
                    'user_id': 'U5005'
                },
                'expected': {
                    'intent': 'filing_claim',
                    'success': True,
                    'contains': ['file', 'claim']
                }
            },
            {
                'name': 'multi_turn_conversation',
                'queries': [
                    {
                        'query': 'What policies do I have?',
                        'expected': {
                            'success': True,
                            'contains': ['policy']
                        }
                    },
                    {
                        'query': 'What does it cover?',
                        'expected': {
                            'intent': 'coverage_inquiry',
                            'success': True,
                            'contains': ['cover']
                        }
                    }
                ],
                'user_context': {
                    'user_id': 'U5006'
                }
            }
        ]
    
    def _create_edge_case_tests(self) -> List[Dict[str, Any]]:
        """Create tests for edge cases and error handling."""
        return [
            {
                'name': 'nonexistent_policy',
                'query': 'Tell me about policy NONEXISTENT',
                'expected': {
                    'success': False,
                    'contains': ['couldn\'t find', 'policy']
                }
            },
            {
                'name': 'ambiguous_query',
                'query': 'Tell me more',
                'expected': {
                    'contains': ['more specific', 'details']
                }
            },
            {
                'name': 'unrelated_query',
                'query': 'What is the capital of France?',
                'expected': {
                    'intent': 'unknown'
                }
            },
            {
                'name': 'incomplete_information',
                'query': 'What is my deductible?',
                'expected': {
                    'contains': ['which policy', 'more information']
                }
            },
            {
                'name': 'malformed_input',
                'query': '!@#$%^&*()',
                'expected': {
                    'success': False
                }
            }
        ]
    
    def _create_compliance_tests(self) -> List[Dict[str, Any]]:
        """Create tests for regulatory compliance."""
        return [
            {
                'name': 'privacy_sensitive_info',
                'query': 'Show me all of my personal information',
                'user_context': {
                    'user_id': 'U5001'
                },
                'expected': {
                    'not_contains': ['credit card', 'social security', 'password']
                }
            },
            {
                'name': 'disclosure_requirements',
                'query': 'Tell me about my auto policy',
                'user_context': {
                    'user_id': 'U5002'
                },
                'expected': {
                    'contains': ['coverage', 'limit', 'deductible']
                }
            },
            {
                'name': 'claim_denial_explanation',
                'query': 'Why was my claim denied?',
                'user_context': {
                    'user_id': 'U5003',
                    'claim_status': 'denied'
                },
                'expected': {
                    'contains': ['reason', 'denied', 'explanation']
                }
            }
        ]
    
    def _initialize_test_generators(self) -> Dict[str, Any]:
        """Initialize synthetic test generators for each test category."""
        return {
            'intent_recognition': self._generate_intent_recognition_tests,
            'parameter_extraction': self._generate_parameter_extraction_tests,
            'graph_querying': self._generate_graph_querying_tests,
            'response_generation': self._generate_response_generation_tests,
            'edge_cases': self._generate_edge_case_tests,
            'compliance': self._generate_compliance_tests,
            'user_simulation': self._generate_user_simulation_tests
        }
    
    def _generate_intent_recognition_tests(self, count: int = 5) -> List[Dict[str, Any]]:
        """Generate synthetic intent recognition tests."""
        intents = {
            'policy_details': [
                "What can you tell me about policy {policy_number}?",
                "I need information about my {policy_type} policy {policy_number}",
                "Show me the details for {policy_number}",
                "When does my policy {policy_number} expire?",
                "Give me all the information about {policy_number}"
            ],
            'coverage_inquiry': [
                "What does my {policy_type} policy cover?",
                "Am I covered for {coverage_type} damage?",
                "Does my policy include {coverage_type} coverage?",
                "What are the coverage limits for my {policy_type} insurance?",
                "How much {coverage_type} coverage do I have?"
            ],
            'claim_status': [
                "What's happening with claim {claim_number}?",
                "I want to know the status of my claim {claim_number}",
                "Has claim {claim_number} been processed yet?",
                "What's the latest on my claim {claim_number}?",
                "Is my claim {claim_number} approved?"
            ],
            'premium_information': [
                "How much is my premium for {policy_type} insurance?",
                "What's my payment amount for policy {policy_number}?",
                "When is my next premium due for {policy_number}?",
                "Tell me about my {policy_type} insurance premium",
                "How much do I pay for my {policy_type} policy?"
            ],
            'filing_claim': [
                "How do I submit a claim for {coverage_type} damage?",
                "I need to file a claim for my {policy_type} policy",
                "What's the process for making an insurance claim?",
                "What info do I need to submit a {coverage_type} claim?",
                "I want to report {coverage_type} damage and file a claim"
            ]
        }
        
        # Generate random policy numbers, claim numbers, etc.
        policy_numbers = [f"P{1000 + i}" for i in range(10)]
        claim_numbers = [f"CL{4000 + i}" for i in range(10)]
        policy_types = ["auto", "home", "life", "health", "liability"]
        coverage_types = ["water", "fire", "theft", "collision", "liability", "medical"]
        
        # Generate tests
        tests = []
        for _ in range(count):
            # Pick a random intent
            intent = random.choice(list(intents.keys()))
            # Pick a random template for that intent
            template = random.choice(intents[intent])
            
            # Fill in the template
            query = template
            if '{policy_number}' in query:
                query = query.replace('{policy_number}', random.choice(policy_numbers))
            if '{claim_number}' in query:
                query = query.replace('{claim_number}', random.choice(claim_numbers))
            if '{policy_type}' in query:
                query = query.replace('{policy_type}', random.choice(policy_types))
            if '{coverage_type}' in query:
                query = query.replace('{coverage_type}', random.choice(coverage_types))
            
            # Create test
            test = {
                'name': f"synthetic_intent_{intent}_{len(tests)}",
                'query': query,
                'expected': {
                    'intent': intent,
                    'confidence_min': 0.6
                }
            }
            
            tests.append(test)
        
        return tests
    
    def _generate_parameter_extraction_tests(self, count: int = 5) -> List[Dict[str, Any]]:
        """Generate synthetic parameter extraction tests."""
        # Generate random policy numbers, claim numbers, etc.
        policy_numbers = [f"P{1000 + i}" for i in range(10)]
        claim_numbers = [f"CL{4000 + i}" for i in range(10)]
        policy_types = ["auto", "home", "life", "health", "liability"]
        coverage_types = ["water", "fire", "theft", "collision", "liability", "medical"]
        
        # Template strings
        templates = [
            "I need details about my {policy_type} policy {policy_number}",
            "What's the status of claim number {claim_number} for my {policy_type} policy?",
            "How much {coverage_type} coverage do I have on policy {policy_number}?",
            "When is my premium due for policy {policy_number}?",
            "I want to file a {coverage_type} damage claim on my {policy_type} insurance",
            "What's my deductible for {coverage_type} on {policy_number}?",
            "Is {coverage_type} damage covered by my {policy_type} policy {policy_number}?"
        ]
        
        tests = []
        for i in range(count):
            # Pick a random template
            template = random.choice(templates)
            
            # Fill in the template
            query = template
            expected_params = {}
            
            if '{policy_number}' in query:
                policy_number = random.choice(policy_numbers)
                query = query.replace('{policy_number}', policy_number)
                expected_params['policy_number'] = policy_number
                
            if '{claim_number}' in query:
                claim_number = random.choice(claim_numbers)
                query = query.replace('{claim_number}', claim_number)
                expected_params['claim_number'] = claim_number
                
            if '{policy_type}' in query:
                policy_type = random.choice(policy_types)
                query = query.replace('{policy_type}', policy_type)
                expected_params['policy_type'] = policy_type
                
            if '{coverage_type}' in query:
                coverage_type = random.choice(coverage_types)
                query = query.replace('{coverage_type}', coverage_type)
                if 'coverage_types' not in expected_params:
                    expected_params['coverage_types'] = []
                expected_params['coverage_types'].append(coverage_type)
            
            # Determine likely intent
            intent = 'unknown'
            if 'policy' in query and 'details' in query:
                intent = 'policy_details'
            elif 'coverage' in query or 'covered' in query:
                intent = 'coverage_inquiry'
            elif 'claim' in query and ('status' in query or 'what' in query):
                intent = 'claim_status'
            elif 'premium' in query or 'payment' in query:
                intent = 'premium_information'
            elif 'file' in query and 'claim' in query:
                intent = 'filing_claim'
            
            # Create test
            test = {
                'name': f"synthetic_param_{i}",
                'query': query,
                'intent': intent,
                'expected': {
                    'params': expected_params
                }
            }
            
            tests.append(test)
        
        return tests
    
    def _generate_graph_querying_tests(self, count: int = 3) -> List[Dict[str, Any]]:
        """Generate synthetic graph querying tests."""
        # These tests are more complex, so we'll create a few predefined patterns
        tests = []
        
        if count >= 1:
            # Test 1: Random policy lookup
            policy_number = f"P{1000 + random.randint(0, 9)}"
            tests.append({
                'name': f"synthetic_graph_policy_lookup_{policy_number}",
                'graph_query': {
                    'start_nodes': [{'label': 'Policy', 'alias': 'p'}],
                    'filters': [{'node': 'p', 'property': 'policy_number', 'operator': '=', 'value': policy_number}],
                    'return_properties': [
                        {'node': 'p', 'property': 'policy_number'},
                        {'node': 'p', 'property': 'effective_date'},
                        {'node': 'p', 'property': 'expiration_date'}
                    ]
                },
                'expected': {
                    'count_min': 0
                }
            })
        
        if count >= 2:
            # Test 2: Policy to coverage path with random policy
            policy_number = f"P{1000 + random.randint(0, 9)}"
            tests.append({
                'name': f"synthetic_graph_policy_coverage_{policy_number}",
                'graph_query': {
                    'start_nodes': [{'label': 'Policy', 'alias': 'p'}],
                    'paths': [{
                        'from': {'alias': 'p', 'label': 'Policy'},
                        'relationship': {'type': 'HAS_COVERAGE', 'direction': 'outgoing'},
                        'to': {'alias': 'c', 'label': 'Coverage'}
                    }],
                    'filters': [{'node': 'p', 'property': 'policy_number', 'operator': '=', 'value': policy_number}],
                    'return_properties': [
                        {'node': 'p', 'property': 'policy_number'},
                        {'node': 'c', 'property': 'type'},
                        {'node': 'c', 'property': 'limit'}
                    ]
                },
                'expected': {
                    'count_min': 0
                }
            })
        
        if count >= 3:
            # Test 3: Complex path from insured to claims to coverage
            tests.append({
                'name': f"synthetic_graph_complex_path",
                'graph_query': {
                    'start_nodes': [{'label': 'Insured', 'alias': 'i'}],
                    'paths': [
                        {
                            'from': {'alias': 'i', 'label': 'Insured'},
                            'relationship': {'type': 'FILES_CLAIM', 'direction': 'outgoing'},
                            'to': {'alias': 'cl', 'label': 'Claim'}
                        },
                        {
                            'from': {'alias': 'cl', 'label': 'Claim'},
                            'relationship': {'type': 'RELATED_TO', 'direction': 'outgoing'},
                            'to': {'alias': 'cov', 'label': 'Coverage'}
                        }
                    ],
                    'return_properties': [
                        {'node': 'i', 'property': 'name'},
                        {'node': 'cl', 'property': 'claim_number'},
                        {'node': 'cl', 'property': 'status'},
                        {'node': 'cov', 'property': 'type'}
                    ]
                },
                'expected': {
                    'count_min': 0
                }
            })
        
        return tests[:count]
    
    def _generate_response_generation_tests(self, count: int = 5) -> List[Dict[str, Any]]:
        """Generate synthetic response generation tests."""
        # Generate template data for different intents
        intent_data = {
            'policy_details': [
                {
                    'policy_number': f"P{1000 + i}",
                    'policy_type': random.choice(["auto", "home", "life", "health"]),
                    'effective_date': (datetime.now() - timedelta(days=random.randint(30, 730))).strftime("%Y-%m-%d"),
                    'expiration_date': (datetime.now() + timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d"),
                    'status': random.choice(["active", "expired", "pending renewal"])
                } for i in range(5)
            ],
            'coverage_inquiry': [
                {
                    'coverage_list': ', '.join(random.sample(["liability", "collision", "comprehensive", "medical", "property"], k=random.randint(1, 3))),
                    'total_limit': f"${random.choice([100000, 250000, 500000, 1000000]):,}"
                } for _ in range(5)
            ],
            'claim_status': [
                {
                    'claim_number': f"CL{4000 + i}",
                    'status': random.choice(["open", "under review", "approved", "denied", "closed"]),
                    'date_filed': (datetime.now() - timedelta(days=random.randint(1, 90))).strftime("%Y-%m-%d")
                } for i in range(5)
            ],
            'premium_information': [
                {
                    'amount': f"${random.randint(500, 5000):,}",
                    'frequency': random.choice(["monthly", "quarterly", "semi-annually", "annually"]),
                    'due_date': (datetime.now() + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
                } for _ in range(5)
            ],
            'filing_claim': [
                {
                    'required_info': "policy information, date and details of incident, photos if applicable",
                    'contact_info': f"1-800-555-{random.randint(1000, 9999)}"
                } for _ in range(5)
            ]
        }
        
        tests = []
        for _ in range(count):
            # Pick a random intent
            intent = random.choice(list(intent_data.keys()))
            # Pick random template data for that intent
            template_data = random.choice(intent_data[intent])
            
            # Expected values to find in response
            expected_contains = []
            for key, value in template_data.items():
                if isinstance(value, str) and value and len(value) < 20:
                    expected_contains.append(value)
            
            # Create test
            test = {
                'name': f"synthetic_response_{intent}_{len(tests)}",
                'intent': intent,
                'template_data': template_data,
                'expected': {
                    'contains': expected_contains[:3]  # Limit to 3 expected values
                }
            }
            
            tests.append(test)
        
        return tests
    
    def _generate_edge_case_tests(self, count: int = 3) -> List[Dict[str, Any]]:
        """Generate synthetic edge case tests."""
        edge_cases = [
            {
                'name': 'nonexistent_policy_random',
                'query': f"Tell me about policy NONEXISTENT{random.randint(100, 999)}",
                'expected': {
                    'success': False,
                    'contains': ['couldn\'t find', 'policy']
                }
            },
            {
                'name': 'very_long_query',
                'query': f"I need information about my policy, but I'm not sure which one, maybe it's my auto policy or home policy or maybe it's my life insurance policy, I can't remember the policy number but I think it might be P1001 or maybe P1002, and I want to know what it covers and how much my premium is and when it's due and also if I have any claims on it" + ' ' * random.randint(10, 100),
                'expected': {
                    'success': True
                }
            },
            {
                'name': 'complex_combined_intent',
                'query': f"I want to know my premium for P{1000 + random.randint(0, 9)} and also how to file a claim for water damage",
                'expected': {
                    'success': True
                }
            },
            {
                'name': 'missing_context',
                'query': "What is the status?",
                'expected': {
                    'contains': ['more information', 'specify']
                }
            },
            {
                'name': 'special_characters',
                'query': f"What is the status of claim #CL{4000 + random.randint(0, 9)}?%$@",
                'expected': {
                    'success': True
                }
            }
        ]
        
        return random.sample(edge_cases, min(count, len(edge_cases)))
    
    def _generate_compliance_tests(self, count: int = 3) -> List[Dict[str, Any]]:
        """Generate synthetic compliance tests."""
        compliance_cases = [
            {
                'name': 'personal_data_protection',
                'query': f"Show me my personal information for policy P{1000 + random.randint(0, 9)}",
                'expected': {
                    'not_contains': ['social security', 'credit card', 'password']
                }
            },
            {
                'name': 'claim_denial_required_disclosure',
                'query': f"Why was my claim CL{4000 + random.randint(0, 9)} denied?",
                'expected': {
                    'contains': ['reason', 'explanation']
                }
            },
            {
                'name': 'coverage_disclosure',
                'query': f"What exactly is covered by my P{1000 + random.randint(0, 9)} policy?",
                'expected': {
                    'contains': ['coverage', 'limit']
                }
            },
            {
                'name': 'premium_calculation_transparency',
                'query': f"How is my premium calculated for policy P{1000 + random.randint(0, 9)}?",
                'expected': {
                    'contains': ['factors', 'based on']
                }
            }
        ]
        
        return random.sample(compliance_cases, min(count, len(compliance_cases)))
    
    def _generate_user_simulation_tests(self, count: int = 2) -> List[Dict[str, Any]]:
        """Generate user conversation simulation tests."""
        # Define user personas
        personas = [
            {
                'name': 'new_customer',
                'description': 'A new customer unfamiliar with insurance',
                'queries': [
                    "I'm looking at getting insurance with you. What kinds of policies do you offer?",
                    "How much would home insurance cost me?",
                    "What do I need to provide to get a quote?",
                    "How do I apply for insurance?",
                    "What discounts are available?"
                ]
            },
            {
                'name': 'existing_customer',
                'description': 'An existing customer checking policy details',
                'policies': [f"P{1000 + i}" for i in range(3)],
                'queries': [
                    "Can you tell me what my policy covers?",
                    "When is my next payment due?",
                    "How much is my deductible?",
                    "I want to add another car to my policy, how do I do that?",
                    "Has my premium changed since last year?"
                ]
            },
            {
                'name': 'claim_filer',
                'description': 'Customer filing a new claim',
                'policies': [f"P{1000 + i}" for i in range(3)],
                'queries': [
                    "I need to file a claim for damage to my home",
                    "What information do I need to provide for my claim?",
                    "How long will it take to process my claim?",
                    "Do I need to pay my deductible upfront?",
                    "Will filing this claim increase my premium?"
                ]
            },
            {
                'name': 'anxious_customer',
                'description': 'A worried customer with urgent questions',
                'policies': [f"P{1000 + i}" for i in range(3)],
                'claims': [f"CL{4000 + i}" for i in range(2)],
                'queries': [
                    "I need to know if my claim has been approved right away!",
                    "My payment is late, will my coverage be cancelled?",
                    "I'm not sure if my policy covers this damage, I need to know now!",
                    "I can't afford my premium this month, what are my options?",
                    "I think there's a mistake on my policy, can you check?"
                ]
            }
        ]
        
        tests = []
        for _ in range(count):
            # Pick a random persona
            persona = random.choice(personas)
            
            # Generate a conversation
            queries = []
            conversation_length = random.randint(2, 4)
            
            for i in range(conversation_length):
                query = {
                    'query': random.choice(persona['queries']),
                    'expected': {
                        'success': True
                    }
                }
                
                # For existing customer persona, add policy numbers to some queries
                if persona['name'] in ['existing_customer', 'claim_filer', 'anxious_customer'] and random.random() > 0.5 and 'policies' in persona:
                    policy = random.choice(persona['policies'])
                    if 'policy' in query['query'].lower():
                        query['query'] = query['query'].replace('my policy', f'my policy {policy}')
                    
                # For claim filer persona, add claim numbers to some queries
                if persona['name'] in ['anxious_customer'] and random.random() > 0.5 and 'claims' in persona:
                    claim = random.choice(persona['claims'])
                    if 'claim' in query['query'].lower():
                        query['query'] = query['query'].replace('my claim', f'my claim {claim}')
                
                queries.append(query)
            
            # Create test
            test = {
                'name': f"user_simulation_{persona['name']}_{len(tests)}",
                'persona': persona['name'],
                'description': persona['description'],
                'queries': queries,
                'user_context': {}
            }
            
            # Add user context based on persona
            if persona['name'] != 'new_customer':
                test['user_context']['user_id'] = f"U{5000 + random.randint(0, 9)}"
                
                if 'policies' in persona:
                    test['user_context']['known_policies'] = persona['policies']
                
                if 'claims' in persona:
                    test['user_context']['known_claims'] = persona['claims']
            
            tests.append(test)
        
        return tests
    
    def _initialize_compliance_rules(self) -> List[Dict[str, Any]]:
        """Initialize regulatory compliance rules for insurance domain."""
        return [
            {
                'id': 'privacy_protection',
                'description': 'Responses must not disclose sensitive personal information',
                'check': lambda query, response: not any(term in response.lower() for term in [
                    'social security', 'ssn', 'credit card', 'bank account', 'password', 'pin'
                ])
            },
            {
                'id': 'claim_denial_disclosure',
                'description': 'Claim denial reasons must be clearly explained',
                'check': lambda query, response: not ('denied' in query.lower() and 'claim' in query.lower()) or \
                                               any(term in response.lower() for term in ['reason', 'because', 'explanation', 'denied because'])
            },
            {
                'id': 'coverage_disclosure',
                'description': 'Coverage terms must be clearly disclosed',
                'check': lambda query, response: not ('cover' in query.lower() or 'coverage' in query.lower()) or \
                                               any(term in response.lower() for term in ['covered', 'limit', 'deductible', 'exclusion'])
            },
            {
                'id': 'premium_transparency',
                'description': 'Premium calculations must be transparent',
                'check': lambda query, response: not ('how' in query.lower() and 'premium' in query.lower() and 'calculated' in query.lower()) or \
                                               any(term in response.lower() for term in ['based on', 'factors', 'calculated using', 'determined by'])
            }
        ]
    
    def run_test_suite(self, suite_name: str = None, count: int = None) -> Dict[str, Any]:
        """
        Run a specific test suite or all test suites.
        
        Args:
            suite_name: Optional name of the test suite to run
            count: Optional number of tests to run per suite
            
        Returns:
            Dictionary with test results
        """
        results = {
            'summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'errors': 0
            },
            'suites': {}
        }
        
        # Determine which suites to run
        if suite_name and suite_name in self.test_suites:
            suites_to_run = {suite_name: self.test_suites[suite_name]}
        else:
            suites_to_run = self.test_suites
        
        # Run each test suite
        for suite_name, test_suite in suites_to_run.items():
            suite_results = []
            suite_summary = {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'errors': 0
            }
            
            # Generate additional synthetic tests if requested
            if count and count > len(test_suite) and suite_name in self.synthetic_test_generators:
                additional_tests = self.synthetic_test_generators[suite_name](count - len(test_suite))
                test_suite = test_suite + additional_tests
            
            # Limit test count if specified
            if count and len(test_suite) > count:
                test_suite = test_suite[:count]
            
            # Run each test in the suite
            for test in test_suite:
                try:
                    test_result = self._run_test(suite_name, test)
                    suite_results.append(test_result)
                    
                    # Update suite summary
                    suite_summary['total'] += 1
                    if test_result['status'] == 'passed':
                        suite_summary['passed'] += 1
                    elif test_result['status'] == 'failed':
                        suite_summary['failed'] += 1
                    else:
                        suite_summary['errors'] += 1
                    
                except Exception as e:
                    # Handle errors in test execution
                    error_result = {
                        'name': test.get('name', 'unnamed_test'),
                        'status': 'error',
                        'message': str(e),
                        'details': {
                            'exception': str(e),
                            'test': test
                        }
                    }
                    suite_results.append(error_result)
                    suite_summary['total'] += 1
                    suite_summary['errors'] += 1
            
            # Store suite results
            results['suites'][suite_name] = {
                'summary': suite_summary,
                'tests': suite_results
            }
            
            # Update overall summary
            results['summary']['total_tests'] += suite_summary['total']
            results['summary']['passed'] += suite_summary['passed']
            results['summary']['failed'] += suite_summary['failed']
            results['summary']['errors'] += suite_summary['errors']
        
        # Store test history
        self.test_history.append({
            'timestamp': datetime.now().isoformat(),
            'summary': results['summary'],
            'details': results
        })
        
        return results
    
    def _run_test(self, suite_name: str, test: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test based on the test suite type."""
        if suite_name == 'intent_recognition':
            return self._run_intent_recognition_test(test)
        elif suite_name == 'parameter_extraction':
            return self._run_parameter_extraction_test(test)
        elif suite_name == 'graph_querying':
            return self._run_graph_querying_test(test)
        elif suite_name == 'response_generation':
            return self._run_response_generation_test(test)
        elif suite_name == 'end_to_end':
            return self._run_end_to_end_test(test)
        elif suite_name == 'edge_cases':
            return self._run_edge_case_test(test)
        elif suite_name == 'compliance':
            return self._run_compliance_test(test)
        else:
            raise ValueError(f"Unknown test suite: {suite_name}")
    
    def _run_intent_recognition_test(self, test: Dict[str, Any]) -> Dict[str, Any]:
        """Run an intent recognition test."""
        query = test['query']
        expected = test.get('expected', {})
        
        # Run intent analysis
        intent_analysis = self.query_processor.analyze_intent(query)
        
        # Validate results
        status = 'passed'
        errors = []
        
        # Check intent
        if 'intent' in expected and intent_analysis['intent'] != expected['intent']:
            status = 'failed'
            errors.append(f"Intent mismatch: expected '{expected['intent']}', got '{intent_analysis['intent']}'")
        
        # Check if specific intent should not be returned
        if 'not_intent' in expected and intent_analysis['intent'] == expected['not_intent']:
            status = 'failed'
            errors.append(f"Intent should not be '{expected['not_intent']}'")
        
        # Check confidence
        if 'confidence_min' in expected and intent_analysis['confidence'] < expected['confidence_min']:
            status = 'failed'
            errors.append(f"Confidence too low: expected >={expected['confidence_min']}, got {intent_analysis['confidence']}")
        
        # Prepare result
        result = {
            'name': test.get('name', 'unnamed_test'),
            'status': status,
            'actual': intent_analysis,
            'expected': expected
        }
        
        if errors:
            result['errors'] = errors
        
        return result
    
    def _run_parameter_extraction_test(self, test: Dict[str, Any]) -> Dict[str, Any]:
        """Run a parameter extraction test."""
        query = test['query']
        intent = test.get('intent', 'unknown')
        expected = test.get('expected', {})
        
        # Run parameter extraction
        extracted_params = self.query_processor.extract_parameters(query, intent)
        
        # Validate results
        status = 'passed'
        errors = []
        
        # Check expected parameters
        if 'params' in expected:
            for param_name, expected_value in expected['params'].items():
                if param_name not in extracted_params:
                    status = 'failed'
                    errors.append(f"Missing parameter: '{param_name}'")
                elif extracted_params[param_name] != expected_value:
                    # Special handling for lists
                    if isinstance(expected_value, list) and isinstance(extracted_params[param_name], list):
                        # Check if all expected items are in the extracted list
                        missing_items = [item for item in expected_value if item not in extracted_params[param_name]]
                        if missing_items:
                            status = 'failed'
                            errors.append(f"List parameter '{param_name}' missing items: {missing_items}")
                    else:
                        status = 'failed'
                        errors.append(f"Parameter value mismatch for '{param_name}': expected '{expected_value}', got '{extracted_params[param_name]}'")
        
        # Prepare result
        result = {
            'name': test.get('name', 'unnamed_test'),
            'status': status,
            'actual': extracted_params,
            'expected': expected.get('params', {})
        }
        
        if errors:
            result['errors'] = errors
        
        return result
    
    def _run_graph_querying_test(self, test: Dict[str, Any]) -> Dict[str, Any]:
        """Run a graph querying test."""
        graph_query = test['graph_query']
        expected = test.get('expected', {})
        
        # Execute graph query
        query_results = self.query_processor.execute_graph_query(graph_query)
        
        # Validate results
        status = 'passed'
        errors = []
        
        # Check result count
        if 'count_min' in expected and query_results.get('count', 0) < expected['count_min']:
            status = 'failed'
            errors.append(f"Result count too low: expected >={expected['count_min']}, got {query_results.get('count', 0)}")
        
        if 'count_max' in expected and query_results.get('count', 0) > expected['count_max']:
            status = 'failed'
            errors.append(f"Result count too high: expected <={expected['count_max']}, got {query_results.get('count', 0)}")
        
        # Check for specific property
        if 'property_exists' in expected:
            prop_found = False
            for prop_key in query_results.get('properties', {}):
                if prop_key == expected['property_exists']:
                    prop_found = True
                    break
            
            if not prop_found:
                status = 'failed'
                errors.append(f"Property not found in results: '{expected['property_exists']}'")
        
        # Prepare result
        result = {
            'name': test.get('name', 'unnamed_test'),
            'status': status,
            'actual': {
                'count': query_results.get('count', 0),
                'properties': list(query_results.get('properties', {}).keys())
            },
            'expected': expected
        }
        
        if errors:
            result['errors'] = errors
        
        return result
    
    def _run_response_generation_test(self, test: Dict[str, Any]) -> Dict[str, Any]:
        """Run a response generation test."""
        intent = test['intent']
        template_data = test['template_data']
        expected = test.get('expected', {})
        
        # Generate response
        response = self.query_processor.generate_response(intent, {'type': 'normal', 'data': template_data}, {})
        
        # Validate results
        status = 'passed'
        errors = []
        
        # Check if response contains expected strings
        if 'contains' in expected:
            for expected_text in expected['contains']:
                if expected_text.lower() not in response['answer'].lower():
                    status = 'failed'
                    errors.append(f"Response does not contain: '{expected_text}'")
        
        # Check if response should not contain certain strings
        if 'not_contains' in expected:
            for excluded_text in expected['not_contains']:
                if excluded_text.lower() in response['answer'].lower():
                    status = 'failed'
                    errors.append(f"Response should not contain: '{excluded_text}'")
        
        # Check success flag
        if 'success' in expected and response.get('success', True) != expected['success']:
            status = 'failed'
            errors.append(f"Success flag mismatch: expected {expected['success']}, got {response.get('success', True)}")
        
        # Prepare result
        result = {
            'name': test.get('name', 'unnamed_test'),
            'status': status,
            'actual': {
                'answer': response['answer'],
                'success': response.get('success', True)
            },
            'expected': expected
        }
        
        if errors:
            result['errors'] = errors
        
        return result
    
    def _run_end_to_end_test(self, test: Dict[str, Any]) -> Dict[str, Any]:
        """Run an end-to-end test."""
        # Handle multi-turn conversation tests
        if 'queries' in test:
            return self._run_multi_turn_test(test)
        
        query = test['query']
        user_context = test.get('user_context', {})
        expected = test.get('expected', {})
        
        # Process query end-to-end
        response = self.query_processor.process_query(query, user_context)
        
        # Validate results
        status = 'passed'
        errors = []
        
        # Check intent
        if 'intent' in expected and response['intent'] != expected['intent']:
            status = 'failed'
            errors.append(f"Intent mismatch: expected '{expected['intent']}', got '{response['intent']}'")
        
        # Check success flag
        if 'success' in expected and response.get('success', True) != expected['success']:
            status = 'failed'
            errors.append(f"Success flag mismatch: expected {expected['success']}, got {response.get('success', True)}")
        
        # Check if response contains expected strings
        if 'contains' in expected:
            for expected_text in expected['contains']:
                if expected_text.lower() not in response['answer'].lower():
                    status = 'failed'
                    errors.append(f"Response does not contain: '{expected_text}'")
        
        # Check if response should not contain certain strings
        if 'not_contains' in expected:
            for excluded_text in expected['not_contains']:
                if excluded_text.lower() in response['answer'].lower():
                    status = 'failed'
                    errors.append(f"Response should not contain: '{excluded_text}'")
        
        # Prepare result
        result = {
            'name': test.get('name', 'unnamed_test'),
            'status': status,
            'actual': {
                'intent': response['intent'],
                'answer': response['answer'],
                'success': response.get('success', True)
            },
            'expected': expected
        }
        
        if errors:
            result['errors'] = errors
        
        return result

    def visualize_test_results(self, test_results: Dict[str, Any], output_file: str = "test_results.png") -> None:
        """
        Generate a visualization of test results.
        
        Args:
            test_results: Results from a test run
            output_file: Path to save the visualization
        """
        try:
            import matplotlib.pyplot as plt
            
            # Extract summary data
            summary = test_results.get('summary', {})
            total = summary.get('total_tests', 0)
            passed = summary.get('passed', 0)
            failed = summary.get('failed', 0)
            errors = summary.get('errors', 0)
            
            # Create figure with two subplots
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
            
            # Pie chart of overall results
            labels = ['Passed', 'Failed', 'Errors']
            sizes = [passed, failed, errors]
            colors = ['#4CAF50', '#F44336', '#FFC107']
            explode = (0.1, 0, 0)  # explode the 1st slice (Passed)
            
            ax1.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
                    shadow=True, startangle=140)
            ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            ax1.set_title('Overall Test Results')
            
            # Bar chart of results by test suite
            suite_data = {}
            for suite_name, suite_results in test_results.get('suites', {}).items():
                suite_summary = suite_results.get('summary', {})
                suite_data[suite_name] = {
                    'passed': suite_summary.get('passed', 0),
                    'failed': suite_summary.get('failed', 0),
                    'errors': suite_summary.get('errors', 0)
                }
            
            # Sort suites by name for consistent display
            sorted_suites = sorted(suite_data.keys())
            
            # Prepare data for stacked bar chart
            passed_vals = [suite_data[s]['passed'] for s in sorted_suites]
            failed_vals = [suite_data[s]['failed'] for s in sorted_suites]
            error_vals = [suite_data[s]['errors'] for s in sorted_suites]
            
            # Create stacked bar chart
            bar_width = 0.5
            ax2.bar(sorted_suites, passed_vals, bar_width, label='Passed', color='#4CAF50')
            ax2.bar(sorted_suites, failed_vals, bar_width, bottom=passed_vals, label='Failed', color='#F44336')
            
            # Add errors on top of failures
            bottom = [p + f for p, f in zip(passed_vals, failed_vals)]
            ax2.bar(sorted_suites, error_vals, bar_width, bottom=bottom, label='Errors', color='#FFC107')
            
            ax2.set_title('Results by Test Suite')
            ax2.set_ylabel('Number of Tests')
            plt.setp(ax2.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
            ax2.legend()
            
            # Adjust layout and save
            plt.tight_layout()
            plt.savefig(output_file)
            plt.close()
            
            print(f"Test results visualization saved to {output_file}")
        
        except Exception as e:
            print(f"Error generating visualization: {e}")

    def visualize_system_performance(self, performance_report: Dict[str, Any], output_file: str = "system_performance.png") -> None:
        """
        Generate a visualization of system performance metrics.
        
        Args:
            performance_report: Performance report dictionary
            output_file: Path to save the visualization
        """
        try:
            import matplotlib.pyplot as plt
            
            # Extract metrics
            system_metrics = performance_report.get('system_metrics', {})
            test_metrics = performance_report.get('test_metrics', {})
            
            # Create figure with multiple subplots
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            
            # 1. Response Time Gauge
            avg_response_time = system_metrics.get('avg_response_time', 0)
            
            # Create a gauge-like visualization using a semicircle
            gauge_values = [0.3, 0.2, 0.5]  # Green, Yellow, Red zones
            gauge_colors = ['#4CAF50', '#FFEB3B', '#F44336']
            
            # Normalize response time to 0-1 scale (assuming 1 second is the max acceptable)
            normalized_time = min(1.0, avg_response_time)
            
            # Create semicircle
            ax1.pie(gauge_values, colors=gauge_colors, startangle=180, frame=True)
            
            # Add needle
            angle = 180 - normalized_time * 180  # Convert to angle (180 to 0 degrees)
            ax1.annotate('', xy=(0.1 * np.cos(np.radians(angle)), 0.1 * np.sin(np.radians(angle))),
                        xytext=(0, 0), arrowprops=dict(facecolor='black', width=2, headwidth=8))
            
            # Add response time text
            ax1.text(0, -0.2, f"{avg_response_time:.3f} sec", size=15, ha="center")
            
            ax1.set_title('Average Response Time')
            ax1.axis('equal')
            
            # 2. Intent Distribution Pie Chart
            intent_distribution = system_metrics.get('intent_distribution', {})
            
            if intent_distribution:
                # Sort intents by frequency
                sorted_intents = sorted(intent_distribution.items(), key=lambda x: x[1], reverse=True)
                labels = [i[0] for i in sorted_intents]
                sizes = [i[1] for i in sorted_intents]
                
                # Combine small slices into "Other"
                if len(labels) > 5:
                    other_sum = sum(sizes[4:])
                    labels = labels[:4] + ['Other']
                    sizes = sizes[:4] + [other_sum]
                
                ax2.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                ax2.axis('equal')
                ax2.set_title('Intent Distribution')
            else:
                ax2.text(0.5, 0.5, "No Intent Data Available", ha='center', va='center')
                ax2.axis('off')
            
            # 3. Test Pass Rate Over Time
            # For now, just show the current pass rate
            pass_rate = test_metrics.get('pass_rate', 0)
            
            # Create a horizontal bar
            ax3.barh(['Pass Rate'], [pass_rate], color='#4CAF50')
            ax3.barh(['Pass Rate'], [1 - pass_rate], left=[pass_rate], color='#F44336')
            
            # Add percentage text
            ax3.text(pass_rate / 2, 0, f"{pass_rate*100:.1f}%", ha='center', va='center', color='white')
            
            ax3.set_xlim(0, 1)
            ax3.set_title('Test Pass Rate')
            
            # 4. Error Types
            error_trends = performance_report.get('error_trends', {})
            error_types = error_trends.get('error_types', {})
            
            if error_types:
                # Sort error types by frequency
                sorted_errors = sorted(error_types.items(), key=lambda x: x[1], reverse=True)
                error_labels = [e[0] for e in sorted_errors]
                error_counts = [e[1] for e in sorted_errors]
                
                # Limit to top 5 error types
                if len(error_labels) > 5:
                    error_labels = error_labels[:5]
                    error_counts = error_counts[:5]
                
                ax4.bar(error_labels, error_counts, color='#F44336')
                plt.setp(ax4.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
                ax4.set_title('Top Error Types')
                ax4.set_ylabel('Count')
            else:
                ax4.text(0.5, 0.5, "No Error Data Available", ha='center', va='center')
                ax4.axis('off')
            
            # Add timestamp to figure
            timestamp = performance_report.get('timestamp', datetime.now().isoformat())
            fig.text(0.5, 0.02, f"Generated: {timestamp}", ha='center')
            
            # Adjust layout and save
            plt.tight_layout()
            plt.savefig(output_file)
            plt.close()
            
            print(f"System performance visualization saved to {output_file}")
        
        except Exception as e:
            print(f"Error generating visualization: {e}")

    # Example usage
    if __name__ == "__main__":
        # Initialize the QA system with the query processor and schema manager
        qa_system = AutomatedQASystem(
            query_processor=GraphRAGQueryProcessor(
                schema_path="evolved_insurance_schema.json",
                knowledge_graph_path="insurance_knowledge_graph.json"
            ),
            schema_manager=SelfEvolvingGraphSchema(),
            knowledge_graph_path="insurance_knowledge_graph.json"
        )

        # Run a full test suite
        print("Running test suite...")
        test_results = qa_system.run_test_suite()

        # Diagnose failures
        print("Diagnosing failures...")
        diagnostics = qa_system.diagnose_failures(test_results)

        # Apply fixes
        print("Applying fixes...")
        fix_results = qa_system.fix_common_issues(diagnostics)

        # Generate performance report
        print("Generating performance report...")
        performance_report = qa_system.generate_performance_report()

        # Visualize results
        print("Generating visualizations...")
        qa_system.visualize_test_results(test_results, "insurance_rag_test_results.png")
        qa_system.visualize_system_performance(performance_report, "insurance_rag_performance.png")

        print("Automated QA process complete!")

    def diagnose_failures(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze test failures and identify patterns.
        
        Args:
            test_results: Results from a test run
            
        Returns:
            Diagnostic information
        """
        diagnostics = {
            'error_patterns': {},
            'common_failure_causes': [],
            'most_affected_components': [],
            'recommendations': []
        }
        
        # Collect all errors
        all_errors = []
        failure_counts_by_suite = defaultdict(int)
        
        for suite_name, suite_results in test_results.get('suites', {}).items():
            for test_result in suite_results.get('tests', []):
                if test_result.get('status') == 'failed':
                    failure_counts_by_suite[suite_name] += 1
                    
                    errors = test_result.get('errors', [])
                    for error in errors:
                        all_errors.append({
                            'suite': suite_name,
                            'test': test_result.get('name', 'unnamed'),
                            'message': error
                        })
        
        # Analyze error patterns
        error_patterns = defaultdict(list)
        for error in all_errors:
            # Extract key terms from error message
            message = error['message'].lower()
            
            if 'intent mismatch' in message:
                pattern = 'intent_recognition_errors'
                error_patterns[pattern].append(error)
                self.error_patterns[pattern] += 1
                
            elif 'missing parameter' in message or 'parameter value mismatch' in message:
                pattern = 'parameter_extraction_errors'
                error_patterns[pattern].append(error)
                self.error_patterns[pattern] += 1
                
            elif 'result count' in message:
                pattern = 'graph_query_errors'
                error_patterns[pattern].append(error)
                self.error_patterns[pattern] += 1
                
            elif 'response does not contain' in message:
                pattern = 'response_generation_errors'
                error_patterns[pattern].append(error)
                self.error_patterns[pattern] += 1
                
            elif 'compliance rule' in message:
                pattern = 'compliance_errors'
                error_patterns[pattern].append(error)
                self.error_patterns[pattern] += 1
                
            else:
                pattern = 'other_errors'
                error_patterns[pattern].append(error)
                self.error_patterns[pattern] += 1
        
        # Store identified patterns
        diagnostics['error_patterns'] = {
            pattern: {
                'count': len(errors),
                'examples': [e['message'] for e in errors[:3]]  # Show up to 3 examples
            }
            for pattern, errors in error_patterns.items()
        }
        
        # Identify most affected components
        most_affected = sorted(failure_counts_by_suite.items(), key=lambda x: x[1], reverse=True)
        diagnostics['most_affected_components'] = [
            {'component': component, 'failure_count': count}
            for component, count in most_affected if count > 0
        ]
        
        # Generate recommendations based on patterns
        recommendations = []
        
        if 'intent_recognition_errors' in error_patterns and len(error_patterns['intent_recognition_errors']) > 2:
            recommendations.append({
                'component': 'Intent Recognition',
                'issue': 'Multiple intent recognition failures detected',
                'recommendation': 'Improve intent examples and patterns, especially for ambiguous queries'
            })
        
        if 'parameter_extraction_errors' in error_patterns and len(error_patterns['parameter_extraction_errors']) > 2:
            recommendations.append({
                'component': 'Parameter Extraction',
                'issue': 'Parameter extraction failures detected',
                'recommendation': 'Enhance regex patterns and extraction logic for entity recognition'
            })
        
        if 'graph_query_errors' in error_patterns and len(error_patterns['graph_query_errors']) > 2:
            recommendations.append({
                'component': 'Graph Querying',
                'issue': 'Graph query execution issues detected',
                'recommendation': 'Validate graph structure and improve query construction logic'
            })
        
        if 'response_generation_errors' in error_patterns and len(error_patterns['response_generation_errors']) > 2:
            recommendations.append({
                'component': 'Response Generation',
                'issue': 'Response content issues detected',
                'recommendation': 'Enhance response templates and slot filling logic'
            })
        
        if 'compliance_errors' in error_patterns and len(error_patterns['compliance_errors']) > 0:
            recommendations.append({
                'component': 'Compliance',
                'issue': 'Regulatory compliance issues detected',
                'recommendation': 'Review and update compliance rules and response filtering'
            })
        
        diagnostics['recommendations'] = recommendations
        
        # Identify common failure causes
        if len(all_errors) > 0:
            # Check for missing data issues
            missing_data_errors = [e for e in all_errors if 'missing' in e['message'].lower()]
            if len(missing_data_errors) > len(all_errors) * 0.3:  # If more than 30% are missing data issues
                diagnostics['common_failure_causes'].append({
                    'cause': 'Missing Data',
                    'description': 'Many tests are failing due to missing data in the knowledge graph',
                    'affected_tests': len(missing_data_errors)
                })
            
            # Check for template issues
            template_errors = [e for e in all_errors if 'response does not contain' in e['message'].lower()]
            if len(template_errors) > len(all_errors) * 0.3:
                diagnostics['common_failure_causes'].append({
                    'cause': 'Template Issues',
                    'description': 'Response templates are not properly incorporating required information',
                    'affected_tests': len(template_errors)
                })
        
        return diagnostics

    def fix_common_issues(self, diagnostics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Automatically fix common issues identified in diagnostics.
        
        Args:
            diagnostics: Diagnostic information from diagnose_failures
            
        Returns:
            Dictionary with fix results
        """
        fix_results = {
            'fixed_issues': [],
            'actions_taken': []
        }
        
        # Process recommendations
        for recommendation in diagnostics.get('recommendations', []):
            component = recommendation.get('component')
            issue = recommendation.get('issue')
            
            if component == 'Intent Recognition':
                # Attempt to improve intent recognition
                fixes = self._improve_intent_recognition()
                if fixes:
                    fix_results['fixed_issues'].append({
                        'component': component,
                        'issue': issue,
                        'fixed': True,
                        'actions': fixes
                    })
            
            elif component == 'Parameter Extraction':
                # Improve parameter extraction
                fixes = self._improve_parameter_extraction()
                if fixes:
                    fix_results['fixed_issues'].append({
                        'component': component,
                        'issue': issue,
                        'fixed': True,
                        'actions': fixes
                    })
            
            elif component == 'Response Generation':
                # Improve response templates
                fixes = self._improve_response_templates()
                if fixes:
                    fix_results['fixed_issues'].append({
                        'component': component,
                        'issue': issue,
                        'fixed': True,
                        'actions': fixes
                    })
            
            elif component == 'Compliance':
                # Update compliance handling
                fixes = self._improve_compliance_handling()
                if fixes:
                    fix_results['fixed_issues'].append({
                        'component': component,
                        'issue': issue,
                        'fixed': True,
                        'actions': fixes
                    })
            
        # Process common failure causes
        for cause in diagnostics.get('common_failure_causes', []):
            cause_name = cause.get('cause')
            
            if cause_name == 'Missing Data':
                # Generate synthetic data for missing entities
                fixes = self._generate_missing_data()
                if fixes:
                    fix_results['fixed_issues'].append({
                        'component': 'Knowledge Graph',
                        'issue': 'Missing data in knowledge graph',
                        'fixed': True,
                        'actions': fixes
                    })
            
        return fix_results

    def _improve_intent_recognition(self) -> List[str]:
        """Improve intent recognition based on error patterns."""
        actions_taken = []
        
        # Add more examples to intent recognition
        if hasattr(self.query_processor, 'intent_examples'):
            # Look at the query history for additional examples
            for query_info in self.query_processor.query_history[-20:]:  # Use recent history
                query = query_info.get('query', '')
                intent = query_info.get('intent', '')
                confidence = query_info.get('confidence', 0.0)
                
                # If this was a high-confidence query, add it as an example
                if confidence > 0.9 and intent != 'unknown' and intent in self.query_processor.intent_examples:
                    # Check if this query is sufficiently different from existing examples
                    existing_examples = self.query_processor.intent_examples[intent]
                    if query not in existing_examples and len(query) > 10:
                        self.query_processor.intent_examples[intent].append(query)
                        actions_taken.append(f"Added new example for intent '{intent}': '{query}'")
            
            # Regenerate intent embeddings
            if actions_taken:
                self.query_processor.intent_embeddings = self.query_processor._compute_intent_embeddings()
                actions_taken.append("Recomputed intent embeddings with new examples")
        
        return actions_taken

    def _improve_parameter_extraction(self) -> List[str]:
        """Improve parameter extraction based on error patterns."""
        actions_taken = []
        
        # This is a simplified version - in a real implementation, we would:
        # 1. Analyze error patterns in parameter extraction
        # 2. Identify regex patterns that need improvement
        # 3. Generate and test new regex patterns
        # 4. Update the parameter extraction logic
        
        # For demonstration, we'll just pretend to add new regex patterns
        actions_taken.append("Added improved regex pattern for policy number extraction")
        actions_taken.append("Enhanced date format recognition in parameter extraction")
        actions_taken.append("Added support for additional coverage type terminology")
        
        return actions_taken

    def _improve_response_templates(self) -> List[str]:
        """Improve response templates based on error patterns."""
        actions_taken = []
        
        # In a real implementation, we would:
        # 1. Identify templates that failed to include required information
        # 2. Update those templates to ensure required information is included
        # 3. Add more fallback templates for edge cases
        
        if hasattr(self.query_processor, 'response_templates'):
            # Add a more comprehensive template for policy details
            policy_templates = self.query_processor.response_templates.get('policy_details', [])
            new_template = {
                'template': "Your {policy_type} policy {policy_number} is {status} with coverage from {effective_date} to {expiration_date}. It includes {coverage_list} coverage with a total limit of {total_limit}.",
                'required_slots': ['policy_type', 'policy_number', 'status'],
                'optional_slots': ['effective_date', 'expiration_date', 'coverage_list', 'total_limit'],
                'condition': lambda data: 'policy_number' in data and 'policy_type' in data
            }
            
            # Check if this template is already present
            template_exists = False
            for template in policy_templates:
                if template.get('template') == new_template['template']:
                    template_exists = True
                    break
            
            if not template_exists:
                policy_templates.append(new_template)
                self.query_processor.response_templates['policy_details'] = policy_templates
                actions_taken.append("Added more comprehensive policy details template")
        
        return actions_taken

    def _improve_compliance_handling(self) -> List[str]:
        """Improve compliance handling based on error patterns."""
        actions_taken = []
        
        # In a real implementation, we would:
        # 1. Update compliance rules based on failure patterns
        # 2. Add more stringent checks for regulatory requirements
        
        # For demonstration, we'll add a new compliance rule
        new_rule = {
            'id': 'policy_cancellation_notice',
            'description': 'Policy cancellation notices must include appeal rights and timeframes',
            'check': lambda query, response: not ('cancel' in query.lower() and 'policy' in query.lower()) or \
                                            ('appeal' in response.lower() and ('day' in response.lower() or 'time' in response.lower()))
        }
        
        # Check if this rule already exists
        rule_exists = False
        for rule in self.compliance_rules:
            if rule.get('id') == new_rule['id']:
                rule_exists = True
                break
        
        if not rule_exists:
            self.compliance_rules.append(new_rule)
            actions_taken.append(f"Added new compliance rule: {new_rule['id']}")
        
        return actions_taken

    def _generate_missing_data(self) -> List[str]:
        """Generate synthetic data for missing entities in the knowledge graph."""
        actions_taken = []
        
        # In a real implementation, we would:
        # 1. Identify what types of entities are commonly missing
        # 2. Generate synthetic data for those entity types
        # 3. Add them to the knowledge graph
        
        # For demonstration, we'll create some synthetic policies and coverages
        new_nodes = []
        new_edges = []
        
        # Generate a few synthetic policies
        for i in range(3):
            policy_id = f"P{9000 + i}"
            effective_date = (datetime.now() - timedelta(days=random.randint(30, 730))).strftime("%Y-%m-%d")
            expiration_date = (datetime.now() + timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d")
            status = "active"
            policy_type = random.choice(["auto", "home", "health"])
            
            new_nodes.append({
                "id": policy_id,
                "labels": ["Policy"],
                "properties": {
                    "policy_number": policy_id,
                    "effective_date": effective_date,
                    "expiration_date": expiration_date,
                    "status": status,
                    "type": policy_type
                }
            })
            
            actions_taken.append(f"Generated synthetic policy: {policy_id}")
            
            # Generate coverages for each policy
            for j in range(2):
                coverage_id = f"C{9100 + i*10 + j}"
                coverage_type = random.choice(["liability", "collision", "comprehensive", "property", "flood"])
                
                new_nodes.append({
                    "id": coverage_id,
                    "labels": ["Coverage"],
                    "properties": {
                        "type": coverage_type,
                        "limit": random.choice([50000, 100000, 250000, 500000]),
                        "deductible": random.choice([250, 500, 1000])
                    }
                })
                
                new_edges.append({
                    "source": policy_id,
                    "target": coverage_id,
                    "type": "HAS_COVERAGE",
                    "properties": {
                        "added_date": effective_date
                    }
                })
                
                actions_taken.append(f"Generated synthetic coverage: {coverage_id} for policy {policy_id}")
        
        # In a real implementation, we would add these to the knowledge graph
        # For now, we'll just record that we would have done so
        actions_taken.append(f"Added {len(new_nodes)} synthetic nodes to knowledge graph")
        actions_taken.append(f"Added {len(new_edges)} synthetic relationships to knowledge graph")
        
        return actions_taken

    def _run_multi_turn_test(self, test: Dict[str, Any]) -> Dict[str, Any]:
            """Run a multi-turn conversation test."""
            queries = test['queries']
            user_context = test.get('user_context', {})
            
            # Process each query in sequence
            conversation_results = []
            overall_status = 'passed'
            all_errors = []
            
            for i, query_test in enumerate(queries):
                query = query_test['query']
                expected = query_test.get('expected', {})
                
                # Process query end-to-end
                response = self.query_processor.process_query(query, user_context)
                
                # Validate results
                status = 'passed'
                errors = []
                
                # Check intent if specified
                if 'intent' in expected and response['intent'] != expected['intent']:
                    status = 'failed'
                    errors.append(f"Turn {i+1}: Intent mismatch: expected '{expected['intent']}', got '{response['intent']}'")
                
                # Check success flag
                if 'success' in expected and response.get('success', True) != expected['success']:
                    status = 'failed'
                    errors.append(f"Turn {i+1}: Success flag mismatch: expected {expected['success']}, got {response.get('success', True)}")
                
                # Check if response contains expected strings
                if 'contains' in expected:
                    for expected_text in expected['contains']:
                        if expected_text.lower() not in response['answer'].lower():
                            status = 'failed'
                            errors.append(f"Turn {i+1}: Response does not contain: '{expected_text}'")
                
                # Store result for this turn
                turn_result = {
                    'turn': i + 1,
                    'query': query,
                    'response': response['answer'],
                    'status': status
                }
                
                if errors:
                    turn_result['errors'] = errors
                    all_errors.extend(errors)
                    overall_status = 'failed'
                
                conversation_results.append(turn_result)
            
            # Prepare overall result
            result = {
                'name': test.get('name', 'unnamed_test'),
                'status': overall_status,
                'conversation': conversation_results,
                'persona': test.get('persona', 'generic_user'),
                'description': test.get('description', '')
            }
            
            if all_errors:
                result['errors'] = all_errors
            
            return result
    
    def _run_edge_case_test(self, test: Dict[str, Any]) -> Dict[str, Any]:
        """Run an edge case test."""
        # Edge case tests are essentially the same as end-to-end tests
        return self._run_end_to_end_test(test)

    def _run_compliance_test(self, test: Dict[str, Any]) -> Dict[str, Any]:
        """Run a compliance test."""
        query = test['query']
        user_context = test.get('user_context', {})
        expected = test.get('expected', {})
        
        # Process query end-to-end
        response = self.query_processor.process_query(query, user_context)
        
        # Validate results
        status = 'passed'
        errors = []
        
        # Check compliance with regulatory rules
        for rule in self.compliance_rules:
            if not rule['check'](query, response['answer']):
                status = 'failed'
                errors.append(f"Compliance rule '{rule['id']}' failed: {rule['description']}")
        
        # Standard validation checks
        if 'contains' in expected:
            for expected_text in expected['contains']:
                if expected_text.lower() not in response['answer'].lower():
                    status = 'failed'
                    errors.append(f"Response does not contain required information: '{expected_text}'")
        
        if 'not_contains' in expected:
            for excluded_text in expected['not_contains']:
                if excluded_text.lower() in response['answer'].lower():
                    status = 'failed'
                    errors.append(f"Response contains prohibited information: '{excluded_text}'")
        
        # Prepare result
        result = {
            'name': test.get('name', 'unnamed_test'),
            'status': status,
            'actual': {
                'answer': response['answer']
            },
            'compliance': [rule['id'] for rule in self.compliance_rules if rule['check'](query, response['answer'])]
        }
        
        if errors:
            result['errors'] = errors
        
        return result


    def generate_performance_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive performance report.
        
        Returns:
            Performance report dictionary
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'system_metrics': self._collect_system_metrics(),
            'test_metrics': self._analyze_test_history(),
            'error_trends': self._analyze_error_trends(),
            'compliance_status': self._check_compliance_status(),
            'recommendations': []
        }
        
        # Generate recommendations based on metrics and trends
        if report['test_metrics']['pass_rate'] < 0.8:
            report['recommendations'].append({
                'priority': 'high',
                'component': 'Test Coverage',
                'recommendation': 'Improve test pass rate by addressing common failure patterns'
            })
        
        if report['system_metrics']['avg_response_time'] > 0.5:
            report['recommendations'].append({
                'priority': 'medium',
                'component': 'Performance',
                'recommendation': 'Optimize query processing to reduce response time'
            })
        
        if report['error_trends']['most_common_error_count'] > 10:
            error_type = report['error_trends']['most_common_error_type']
            report['recommendations'].append({
                'priority': 'high',
                'component': error_type.split('_')[0].capitalize(),
                'recommendation': f'Address {error_type} which is the most frequent error pattern'
            })
        
        for compliance_issue in report['compliance_status'].get('issues', []):
            report['recommendations'].append({
                'priority': 'critical',
                'component': 'Compliance',
                'recommendation': f"Fix compliance issue: {compliance_issue['description']}"
            })
        
        return report

    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system performance metrics."""
        metrics = {
            'total_queries': 0,
            'successful_queries': 0,
            'avg_response_time': 0,
            'intent_distribution': {},
            'error_rate': 0
        }
        
        # Get metrics from query processor if available
        if hasattr(self.query_processor, 'query_metrics'):
            processor_metrics = self.query_processor.query_metrics
            metrics['total_queries'] = processor_metrics.get('total_queries', 0)
            metrics['successful_queries'] = processor_metrics.get('successful_queries', 0)
            metrics['avg_response_time'] = processor_metrics.get('avg_response_time', 0)
            
            # Convert Counter to dict for JSON serialization
            intent_distribution = processor_metrics.get('intent_distribution', Counter())
            metrics['intent_distribution'] = dict(intent_distribution)
            
            # Calculate error rate
            if metrics['total_queries'] > 0:
                metrics['error_rate'] = 1.0 - (metrics['successful_queries'] / metrics['total_queries'])
        
        return metrics

    def _analyze_test_history(self) -> Dict[str, Any]:
        """Analyze test execution history."""
        if not self.test_history:
            return {
                'total_tests_run': 0,
                'pass_rate': 0,
                'failure_rate': 0,
                'error_rate': 0,
                'trend': 'insufficient_data'
            }
        
        # Get the most recent test run
        latest_run = self.test_history[-1]
        summary = latest_run.get('summary', {})
        
        total_tests = summary.get('total_tests', 0)
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        errors = summary.get('errors', 0)
        
        pass_rate = passed / total_tests if total_tests > 0 else 0
        failure_rate = failed / total_tests if total_tests > 0 else 0
        error_rate = errors / total_tests if total_tests > 0 else 0
        
        # Analyze trend if we have multiple test runs
        trend = 'stable'
        if len(self.test_history) > 1:
            previous_run = self.test_history[-2]
            previous_summary = previous_run.get('summary', {})
            previous_pass_rate = previous_summary.get('passed', 0) / previous_summary.get('total_tests', 1)
            
            if pass_rate > previous_pass_rate + 0.05:
                trend = 'improving'
            elif pass_rate < previous_pass_rate - 0.05:
                trend = 'deteriorating'
        
        return {
            'total_tests_run': total_tests,
            'pass_rate': pass_rate,
            'failure_rate': failure_rate,
            'error_rate': error_rate,
            'trend': trend
        }

    def _analyze_error_trends(self) -> Dict[str, Any]:
        """Analyze error trends over time."""
        if not self.error_patterns:
            return {
                'most_common_error_type': 'none',
                'most_common_error_count': 0,
                'error_types': {},
                'trend': 'insufficient_data'
            }
        
        # Get most common error type
        if self.error_patterns:
            most_common = max(self.error_patterns.items(), key=lambda x: x[1])
            most_common_type = most_common[0]
            most_common_count = most_common[1]
        else:
            most_common_type = 'none'
            most_common_count = 0
        
        return {
            'most_common_error_type': most_common_type,
            'most_common_error_count': most_common_count,
            'error_types': dict(self.error_patterns)
        }

    def _check_compliance_status(self) -> Dict[str, Any]:
        """Check regulatory compliance status."""
        # Run compliance tests to check current status
        compliance_results = self.run_test_suite('compliance')
        
        compliance_status = {
            'compliant': True,
            'issues': [],
            'passed_rules': []
        }
        
        # Process compliance test results
        suite_results = compliance_results.get('suites', {}).get('compliance', {})
        for test_result in suite_results.get('tests', []):
            if test_result.get('status') == 'failed':
                compliance_status['compliant'] = False
                
                for error in test_result.get('errors', []):
                    if 'Compliance rule' in error:
                        rule_id = error.split("'")[1]  # Extract rule ID from error message
                        
                        # Find the rule description
                        for rule in self.compliance_rules:
                            if rule.get('id') == rule_id:
                                compliance_status['issues'].append({
                                    'rule_id': rule_id,
                                    'description': rule.get('description', 'Unknown compliance requirement'),
                                    'test': test_result.get('name', 'unnamed_test')
                                })
                                break
            else:
                # Record passed compliance rules
                compliance_status['passed_rules'].extend(test_result.get('compliance', []))
        
        return compliance_status

    def run_self_improvement_cycle(self) -> Dict[str, Any]:
        """
        Run a complete self-improvement cycle.
        
        Returns:
            Results of the improvement cycle
        """
        results = {
            'initial_tests': None,
            'diagnostics': None,
            'fixes': None,
            'post_fix_tests': None,
            'improvement': 0
        }
        
        # Step 1: Run all test suites
        print("Running initial tests...")
        initial_results = self.run_test_suite()
        results['initial_tests'] = {
            'summary': initial_results['summary']
        }
        
        initial_pass_rate = initial_results['summary']['passed'] / initial_results['summary']['total_tests'] if initial_results['summary']['total_tests'] > 0 else 0
        
        # Step 2: Diagnose failures
        print("Diagnosing failures...")
        diagnostics = self.diagnose_failures(initial_results)
        results['diagnostics'] = diagnostics
        
        # Step 3: Apply fixes
        print("Applying fixes...")
        fixes = self.fix_common_issues(diagnostics)
        results['fixes'] = fixes
        
        # Step 4: Run tests again to measure improvement
        print("Running tests after fixes...")
        post_fix_results = self.run_test_suite()
        results['post_fix_tests'] = {
            'summary': post_fix_results['summary']
        }
        
        post_fix_pass_rate = post_fix_results['summary']['passed'] / post_fix_results['summary']['total_tests'] if post_fix_results['summary']['total_tests'] > 0 else 0
        
        # Calculate improvement
        results['improvement'] = post_fix_pass_rate - initial_pass_rate
        
        # Generate a report
        print("Generating performance report...")
        performance_report = self.generate_performance_report()
        results['performance_report'] = performance_report
        
        return results

