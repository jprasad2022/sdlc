# Step 1: Zero-Shot Document Processing Pipeline for Insurance Graph RAG

import os
import openai
import re
import json
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

# Import necessary libraries
import requests
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import PyPDF2
import pdfplumber
from docx import Document
import spacy
from transformers import AutoTokenizer, AutoModel, pipeline
from openai import OpenAI

load_dotenv()

class InsuranceDocumentProcessor:
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        llm_model_name: str = "gpt-4o-mini",
    ):
        """
        Initialize the document processor.
        
        Args:
            model_name: HuggingFace repository for sentence embeddings.
            llm_model_name: OpenAI model identifier for extraction.
        """
        # 1) spaCy for NLP utilities
        try:
            self.nlp = spacy.load("en_core_web_lg")
        except OSError:
            print("Downloading spaCy model...")
            os.system("python -m spacy download en_core_web_lg")
            self.nlp = spacy.load("en_core_web_lg")

        # 2) Sentence-Transformer for embeddings
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.embed_model = AutoModel.from_pretrained(model_name)

        # 3) OpenAI for zero-shot extraction
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Please set OPENAI_API_KEY in your environment.")
        self.openai_client = OpenAI()
        self.llm_model = llm_model_name

        # 4) In-memory stores & tracking
        self.document_store = {}
        self.entity_cache = {}
        self.used_ids = set()  # Track used IDs to prevent duplicates
        
        # 5) Domain-specific entities
        self.insurance_entities = [
            "Policy", "Claim", "Coverage", "Exclusion", "Premium",
            "Deductible", "Insured", "Insurer", "Beneficiary", "Term",
            "Endorsement", "Rider", "Underwriting", "Risk", "Peril",
            "Definition", "Limit", "Condition", "Property", "Liability",
            "Additional_Coverage"
        ]
        
        # 6) Section patterns for better structure
        self.section_patterns = {
            'definitions': r'DEFINITIONS\s*(.*?)(?=SECTION|\Z)',
            'section_i_coverages': r'SECTION I PROPERTY COVERAGES\s*(.*?)(?=SECTION|\Z)',
            'section_i_exclusions': r'SECTION I EXCLUSIONS\s*(.*?)(?=SECTION|\Z)',
            'section_ii_coverages': r'SECTION II LIABILITY COVERAGES\s*(.*?)(?=SECTION|\Z)',
            'section_ii_exclusions': r'SECTION II EXCLUSIONS\s*(.*?)(?=SECTION|\Z)',
            'perils': r'PERILS INSURED AGAINST\s*(.*?)(?=SECTION|\Z)',
            'conditions': r'CONDITIONS\s*(.*?)(?=SECTION|\Z)'
        }

    def _extract_definitions_from_text(self, text: str) -> list:
        """Extract definitions using pattern matching."""
        definitions = []
        
        # Pattern 1: "X" means: ...
        pattern1 = r'"([^"]+)"\s+means:\s*([^\.]+).'
        matches1 = re.finditer(pattern1, text)
        
        for match in matches1:
            term = match.group(1)
            definition = match.group(2).strip()
            definitions.append({
                'term': term,
                'definition': definition,
                'type': 'direct_match'
            })
        
        # Pattern 2: X is defined as ...
        pattern2 = r'(\w+)\s+is defined as\s+([^\.]+).'
        matches2 = re.finditer(pattern2, text)
        
        for match in matches2:
            term = match.group(1)
            definition = match.group(2).strip()
            definitions.append({
                'term': term,
                'definition': definition,
                'type': 'is_defined_as'
            })
        
        return definitions
    
    def _extract_with_llm(self, prompt: str) -> str:
        """Use LLM to extract structured information from document text."""
        try:
            response = self.openai_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": """You are an expert at extracting structured information from insurance documents. 
                    Output ONLY valid JSON without any additional text, markdown formatting, or explanation.
                    Generate UNIQUE IDs for each entity - do not reuse IDs across different chunks."""},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=3000,
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            raw_content = response.choices[0].message.content
            
            # Ensure valid JSON
            try:
                parsed_json = json.loads(raw_content)
                return json.dumps(parsed_json)
            except json.JSONDecodeError:
                print(f"Failed to parse JSON, returning empty structure")
                return json.dumps({"entities": [], "relationships": []})
                
        except Exception as e:
            print(f"Error calling LLM API: {e}")
            return json.dumps({"entities": [], "relationships": []})

    def crawl_documents(self, sources: List[str]) -> List[str]:
        """
        Autonomously crawl and identify insurance documents from various sources.
        
        Args:
            sources: List of URLs, directories, or APIs to crawl
            
        Returns:
            List of file paths to discovered documents
        """
        # Add these debug lines
        import os
        print(f"Current working directory: {os.getcwd()}")
        for source in sources:
            print(f"Looking for documents in: {os.path.abspath(source)}")
        
        discovered_documents = []
        
        for source in sources:
            if source.startswith(('http://', 'https://')):
                # Web crawling logic
                web_docs = self._crawl_web_source(source)
                discovered_documents.extend(web_docs)
            elif os.path.isdir(source):
                # Local directory scanning
                local_docs = self._scan_directory(source)
                discovered_documents.extend(local_docs)
            else:
                print(f"Unsupported source type: {source}")
                
        print(f"Discovered {len(discovered_documents)} insurance documents")
        return discovered_documents
    
    def _crawl_web_source(self, url: str) -> List[str]:
        """Crawl a website for insurance documents."""
        # This would be expanded with proper web crawling logic
        docs = []
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for PDF, DOCX links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.endswith(('.pdf', '.docx', '.doc')):
                    if self._is_insurance_document(href):
                        # Download logic would go here
                        local_path = f"downloaded/{os.path.basename(href)}"
                        docs.append(local_path)
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            
        return docs
    
    def _scan_directory(self, directory: str) -> List[str]:
        """Scan a local directory for insurance documents."""
        docs = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.pdf', '.docx', '.doc', '.txt')):
                    file_path = os.path.join(root, file)
                    # Check if it's an insurance document
                    if self._is_insurance_document(file_path):
                        docs.append(file_path)
        return docs
    
    def _is_insurance_document(self, file_path: str) -> bool:
        """Determine if a document is insurance-related using zero-shot classification."""
        # In a real implementation, this would use the model to classify
        # For now, we'll use a basic keyword approach
        
        insurance_keywords = [
            "policy", "insurance", "coverage", "claim", "premium",
            "deductible", "insured", "underwriting", "risk", "peril"
        ]
        print(f"Checking if {file_path} is an insurance document")    

        try:
            text = self._extract_text_sample(file_path)
            text_lower = text.lower()

            print(f"Extracted text sample from {file_path} (first 100 chars): {text[:100]}")
            
            # Count insurance keywords
            keyword_count = 0
            found_keywords = []
            for keyword in insurance_keywords:
                if keyword in text_lower:
                    keyword_count += 1
                    found_keywords.append(keyword)
            
            print(f"Found {keyword_count} insurance keywords: {found_keywords}")
            
            # If more than 3 keywords are present, consider it an insurance document
            is_insurance = keyword_count > 3
            print(f"Is insurance document: {is_insurance} (threshold: > 3 keywords)")
            return is_insurance
        except Exception as e:
            print(f"Error checking if {file_path} is an insurance document: {e}")
            return False

    
    def _extract_text_sample(self, file_path: str, max_chars: int = 5000) -> str:
        """Extract a text sample from a document for classification."""
        print(f"Extracting text sample from {file_path}")
        sample_text = ""
        
        try:
            if file_path.endswith('.pdf'):
                print(f"Processing PDF file: {file_path}")
                # Logic for PDF extraction
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as file:
                        print(f"Successfully opened PDF file")
                        reader = PyPDF2.PdfReader(file)
                        print(f"PDF has {len(reader.pages)} pages")
                        
                        # Extract text from first few pages
                        for page_num in range(min(3, len(reader.pages))):
                            page_text = reader.pages[page_num].extract_text()
                            sample_text += page_text[:1000]  # Take up to 1000 chars per page
                            
                        print(f"Extracted {len(sample_text)} characters of text from PDF")
                except Exception as pdf_error:
                    print(f"Error extracting PDF text: {pdf_error}")
                    sample_text = "Sample PDF text with insurance policy details..."
                    
            elif file_path.endswith(('.docx', '.doc')):
                print(f"Processing Word file: {file_path}")
                # Logic for Word docs
                sample_text = "Sample DOCX text with coverage and premium information..."
            else:
                print(f"Processing generic text file: {file_path}")
                # Default text handling
                with open(file_path, 'r', encoding='utf-8') as file:
                    sample_text = file.read(max_chars)
                    
            return sample_text[:max_chars]
        except Exception as e:
            print(f"Error in _extract_text_sample: {e}")
            return "Error extracting text sample"
    
    def process_document(self, file_path: str) -> dict:
        """Process a document by chunks with better extraction."""
        print(f"\n=== Processing document: {file_path} ===")
        
        all_entities = []
        all_relationships = []
        
        try:
            # Extract full document text
            document_text = self._extract_full_text(file_path)
            print(f"Document text length: {len(document_text)} characters")
            
            # Extract definitions using pattern matching
            pattern_definitions = self._extract_definitions_from_text(document_text)
            
            # Extract document sections
            sections = self._extract_document_sections(document_text)
            
            # Process each section
            for section_name, section_text in sections.items():
                if not section_text:
                    continue
                    
                print(f"\nProcessing section: {section_name}")
                
                # Break section into chunks if needed
                chunk_size = 3000
                chunks = [section_text[i:i+chunk_size] for i in range(0, len(section_text), chunk_size)]
                
                for i, chunk in enumerate(chunks):
                    print(f"  Processing chunk {i+1}/{len(chunks)}...")
                    
                    # Generate specialized prompt for this section
                    extraction_prompt = self._generate_extraction_prompt(chunk, section_name)
                    
                    # Extract information
                    extracted_info = self._extract_with_llm(extraction_prompt)
                    processed_data = self._process_extraction_result(extracted_info)
                    
                    # Ensure unique IDs across all chunks
                    processed_data = self._ensure_unique_ids(processed_data, section_name, i)
                    
                    all_entities.extend(processed_data.get('entities', []))
                    all_relationships.extend(processed_data.get('relationships', []))
            
            # Add pattern-matched definitions as entities
            for i, def_data in enumerate(pattern_definitions):
                def_entity = {
                    'id': f'def_pattern_{i+1}',
                    'type': 'Definition',
                    'name': def_data['term'],
                    'attributes': {
                        'term': def_data['term'],
                        'meaning': def_data['definition'],
                        'extraction_type': def_data['type'],
                        'source': 'pattern_matching'
                    }
                }
                
                # Avoid duplicates
                if not any(e['name'].lower() == def_entity['name'].lower() and e['type'] == 'Definition' 
                         for e in all_entities):
                    all_entities.append(def_entity)
                    
                    # Add relationship to document entity if present
                    doc_entities = [e for e in all_entities if e['type'] == 'Document']
                    if doc_entities:
                        all_relationships.append({
                            'source': doc_entities[0]['id'],
                            'target': def_entity['id'],
                            'type': 'defines'
                        })
            
            # Post-process to deduplicate and enrich
            final_entities = self._deduplicate_entities(all_entities)
            final_relationships = self._update_relationships(all_relationships, final_entities)
            
            # Add additional relationships based on insurance domain knowledge
            final_relationships.extend(self._infer_relationships(final_entities))
            
            result = {
                'entities': final_entities,
                'relationships': final_relationships
            }
            
            # Store in document store
            doc_id = os.path.basename(file_path)
            self.document_store[doc_id] = {
                'file_path': file_path,
                'processed_data': result,
                'extraction_date': pd.Timestamp.now().isoformat()
            }
            
            print(f"\nFinal results: {len(final_entities)} entities, {len(final_relationships)} relationships")
            
            return result
        
        except Exception as e:
            print(f"Error processing document: {e}")
            import traceback
            print(traceback.format_exc())
            return {'entities': [], 'relationships': []}
    
    def _extract_document_sections(self, document_text: str) -> Dict[str, str]:
        """Extract major sections from the document for targeted processing."""
        sections = {}
        
        for section_name, pattern in self.section_patterns.items():
            matches = re.findall(pattern, document_text, re.DOTALL | re.IGNORECASE)
            if matches:
                sections[section_name] = matches[0].strip()
            else:
                sections[section_name] = ""
        
        # Also extract the full document as a section for anything missed
        sections['full_document'] = document_text
        
        return sections

    def _ensure_unique_ids(self, data: Dict[str, Any], section_name: str, chunk_num: int) -> Dict[str, Any]:
        """Ensure all entity IDs are unique across the document."""
        updated_entities = []
        id_mapping = {}
        
        for entity in data.get('entities', []):
            old_id = entity['id']
            
            # Generate a unique ID based on section, chunk, and entity type
            entity_type = entity['type'].lower().replace(' ', '_')
            
            # For Definition entities, use 'term' as the identifier, otherwise use 'name'
            if entity['type'] == 'Definition':
                identifier = entity.get('attributes', {}).get('term', '')
                if not identifier:
                    # Fallback to name if term is not available
                    identifier = entity.get('name', '')
            else:
                identifier = entity.get('name', '')
            
            # If still no identifier, use the original id
            if not identifier:
                identifier = old_id
                
            # Clean up identifier for use in ID
            identifier = identifier[:10].lower().replace(' ', '_')
            
            base_id = f"{entity_type}_{section_name[:3]}_{chunk_num}_{identifier}"
            
            # Ensure uniqueness
            unique_id = base_id
            counter = 1
            while unique_id in self.used_ids:
                unique_id = f"{base_id}_{counter}"
                counter += 1
            
            self.used_ids.add(unique_id)
            id_mapping[old_id] = unique_id
            
            entity['id'] = unique_id
            updated_entities.append(entity)
        
        # Update relationships with new IDs
        updated_relationships = []
        for rel in data.get('relationships', []):
            if rel['source'] in id_mapping and rel['target'] in id_mapping:
                rel['source'] = id_mapping[rel['source']]
                rel['target'] = id_mapping[rel['target']]
                updated_relationships.append(rel)
        
        return {
            'entities': updated_entities,
            'relationships': updated_relationships
        }

    def _infer_relationships(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Infer additional relationships based on insurance domain knowledge."""
        inferred_relationships = []
        
        # Create entity lookups
        definitions = [e for e in entities if e['type'] == 'Definition']
        coverages = [e for e in entities if e['type'] == 'Coverage']
        exclusions = [e for e in entities if e['type'] == 'Exclusion']
        
        # Link definitions to coverages that reference them
        for coverage in coverages:
            coverage_text = json.dumps(coverage['attributes']).lower()
            for definition in definitions:
                term = definition.get('attributes', {}).get('term', '').lower()
                if term and term in coverage_text:
                    inferred_relationships.append({
                        'source': definition['id'],
                        'target': coverage['id'],
                        'type': 'referenced_by'
                    })
        
        # Link exclusions to coverages they apply to
        for exclusion in exclusions:
            exclusion_text = json.dumps(exclusion['attributes']).lower()
            for coverage in coverages:
                coverage_name = coverage['name'].lower()
                if coverage_name in exclusion_text:
                    inferred_relationships.append({
                        'source': exclusion['id'],
                        'target': coverage['id'],
                        'type': 'excludes'
                    })
        
        return inferred_relationships

    def _extract_full_text(self, file_path: str) -> str:
        """Extract full text content from a document."""
        text = ""
        
        try:
            if file_path.endswith('.pdf'):
                import pdfplumber
                
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() + "\n\n"
                    
                print(f"Extracted text from {len(pdf.pages)} PDF pages using PDFplumber")
            
            elif file_path.endswith('.docx'):
                doc = Document(file_path)
                text = "\n".join([para.text for para in doc.paragraphs])
                
            elif file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
            
        return text
    

    def _generate_extraction_prompt(self, document_text: str, section_name: str = None) -> str:
        """Generate an optimal prompt for the LLM to extract insurance entities."""
        
        # Customize prompt based on section
        section_specific_instructions = ""
        if section_name == "definitions":
            section_specific_instructions = """
            Focus on extracting DEFINITIONS. Look for patterns like:
            - '"Term" means: [definition]'
            - 'Term: definition of term'
            - Numbers followed by definitions (e.g., '1. "Term" means...')
            
            For Definition entities, create structured JSON with:
            {
                "id": "unique_id",
                "type": "Definition",
                "attributes": {
                    "term": "the word or phrase being defined",
                    "meaning": "the definition text",
                    "section": "definitions"
                }
            }
            DO NOT include "name" for Definition entities!
            """
        elif section_name == "section_i_coverages":
            section_specific_instructions = """
            Focus on extracting PROPERTY COVERAGES. Look for:
            - Coverage A, B, C, D, etc.
            - Specific limits, deductibles, and conditions
            - Special limits for certain property types
            Use "name" and "description" for these entities.
            """
        elif section_name == "section_i_exclusions":
            section_specific_instructions = """
            Focus on extracting PROPERTY EXCLUSIONS. Look for:
            - What is NOT covered
            - Specific circumstances that void coverage
            - Exceptions to exclusions
            Use "name" and "description" for these entities.
            """
        elif section_name == "section_ii_coverages":
            section_specific_instructions = """
            Focus on extracting LIABILITY COVERAGES. Look for:
            - Coverage E (Personal Liability)
            - Coverage F (Medical Payments)
            - Limits and conditions for liability coverage
            Use "name" and "description" for these entities.
            """
        elif section_name == "section_ii_exclusions":
            section_specific_instructions = """
            Focus on extracting LIABILITY EXCLUSIONS. Look for:
            - Motor vehicle liability exclusions
            - Watercraft liability exclusions
            - Business-related exclusions
            Use "name" and "description" for these entities.
            """
        elif section_name == "perils":
            section_specific_instructions = """
            Focus on extracting PERILS INSURED AGAINST. Look for:
            - Fire, lightning, windstorm, etc.
            - Specific conditions for each peril
            - Exclusions within perils
            Use "name" and "description" for these entities.
            """
        
        prompt = f"""Extract insurance entities and relationships from the following document section.

        Section: {section_name if section_name else 'General'}
        
        {section_specific_instructions}

        Entity types to identify:
        {', '.join(self.insurance_entities)}

        Return ONLY valid JSON with this exact structure:
        {{
            "entities": [
                {{
                    "id": "unique_id",
                    "type": "entity_type",
                    "name": "entity_name",  // Use for Coverage, Exclusion, Policy etc. DO NOT USE FOR Definition!
                    "attributes": {{
                        "term": "term_being_defined",    // ONLY FOR Definition entities
                        "meaning": "definition_text",    // ONLY FOR Definition entities
                        "description": "detailed description",  // For non-Definition entities
                        "section": "{section_name if section_name else 'general'}",
                        "limit": numeric_value_or_null,
                        "deductible": numeric_value_or_null,
                        "conditions": ["condition 1", "condition 2"],
                        "additional_key": "value"
                    }}
                }}
            ],
            "relationships": [
                {{
                    "source": "source_entity_id",
                    "target": "target_entity_id",
                    "type": "relationship_type",
                    "properties": {{}}
                }}
            ]
        }}

        IMPORTANT INSTRUCTIONS:
        1. For Definition entities:
            - Do NOT include "name" field
            - Use "term" and "meaning" in attributes
            - For ID generation, use the term
        2. For all other entities:
            - USE "name" field
            - Use "description" in attributes
        3. Generate UNIQUE IDs for all entities
        4. Extract limits and deductibles as numeric values when possible
        5. Identify relationships between coverages and exclusions
        6. Include section context in attributes

        Document text:
        {document_text[:3000]}
        """
        return prompt
    
  
    def _process_extraction_result(self, extraction_result: str) -> Dict[str, Any]:
        """Process and validate the extraction results."""
        # Parse the JSON response
        try:
            data = json.loads(extraction_result)
            
            # Validate entities and relationships
            valid_entities = []
            for entity in data.get('entities', []):
                if self._validate_entity(entity):
                    valid_entities.append(entity)
                    
            valid_relationships = []
            for rel in data.get('relationships', []):
                if self._validate_relationship(rel, valid_entities):
                    valid_relationships.append(rel)
                    
            return {
                'entities': valid_entities,
                'relationships': valid_relationships
            }
            
        except json.JSONDecodeError:
            print("Failed to parse extraction result as JSON")
            return {'entities': [], 'relationships': []}
    
    def _validate_entity(self, entity: Dict[str, Any]) -> bool:
        """Validate and convert entity to proper format if needed."""
        required_fields = ['id', 'type']
        
        if not all(field in entity for field in required_fields):
            print(f"Entity missing required fields: {entity}")
            return False
        
        if entity['type'] not in self.insurance_entities:
            print(f"Unknown entity type: {entity['type']}")
            return False
        
        if not entity['id'] or len(entity['id'].strip()) == 0:
            print(f"Invalid entity ID: {entity}")
            return False
        
        if 'attributes' not in entity:
            entity['attributes'] = {}
        
        # Special handling for Definition entities
        if entity['type'] == 'Definition':
            # Convert name/description to term/meaning if needed
            if 'term' not in entity['attributes'] or 'meaning' not in entity['attributes']:
                # If name exists, use it as term
                if 'name' in entity and 'description' in entity['attributes']:
                    entity['attributes']['term'] = entity['name']
                    entity['attributes']['meaning'] = entity['attributes']['description']
                    # Remove the original description to avoid confusion
                    if 'description' in entity['attributes']:
                        del entity['attributes']['description']
                    print(f"Converted Definition entity format: {entity['id']}")
                else:
                    print(f"Definition missing term or meaning: {entity}")
                    return False
        else:
            # For non-Definition entities, ensure name exists
            if 'name' not in entity:
                print(f"Non-Definition entity missing name: {entity}")
                return False
        
        return True
    
    def _validate_relationship(self, relationship: Dict[str, Any], entities: List[Dict[str, Any]]) -> bool:
        """Validate that a relationship references valid entities and has a valid type."""
        required_fields = ['source', 'target', 'type']
        
        if not all(field in relationship for field in required_fields):
            return False
            
        # Check if source and target entities exist
        entity_ids = [entity['id'] for entity in entities]
        if relationship['source'] not in entity_ids or relationship['target'] not in entity_ids:
            return False
            
        valid_relationship_types = ['covers', 'excludes', 'has', 'applies_to', 'pays_to']
        if relationship['type'] not in valid_relationship_types:
            return False
            
        return True
    
    def process_document_batch(self, file_paths: List[str]) -> Dict[str, Any]:
        """Process a batch of documents and merge their extracted information."""
        all_entities = []
        all_relationships = []
        
        for file_path in file_paths:
            result = self.process_document(file_path)
            all_entities.extend(result.get('entities', []))
            all_relationships.extend(result.get('relationships', []))
        
        # Deduplicate entities
        unique_entities = self._deduplicate_entities(all_entities)
        
        # Update relationships to use canonical entity IDs
        updated_relationships = self._update_relationships(all_relationships, unique_entities)
        
        return {
            'entities': unique_entities,
            'relationships': updated_relationships
        }
    
    def _deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate entities based on their properties."""
        entity_map = {}
        
        for entity in entities:
            # Create a key based on type and normalized name
            entity_type = entity['type']
            
            # For definitions, use the term as identifier
            if entity_type == 'Definition' and 'attributes' in entity and 'term' in entity['attributes']:
                key = f"{entity_type}:{entity['attributes']['term'].lower()}"
                # Ensure entity has a name field for consistent handling
                if 'name' not in entity:
                    entity['name'] = entity['attributes']['term']
            else:
                # For other entities, use name if available
                if 'name' not in entity:
                    # Skip entities without a name or identifier
                    continue
                normalized_name = entity['name'].lower().strip()
                key = f"{entity_type}:{normalized_name}"
            
            if key not in entity_map:
                entity_map[key] = entity
            else:
                # Merge attributes if entity already exists
                existing_entity = entity_map[key]
                existing_attrs = existing_entity.get('attributes', {})
                new_attrs = entity.get('attributes', {})
                
                # Merge attributes, preferring non-empty values
                merged_attrs = existing_attrs.copy()
                for k, v in new_attrs.items():
                    if v and (k not in merged_attrs or not merged_attrs[k]):
                        merged_attrs[k] = v
                    elif k in merged_attrs and isinstance(merged_attrs[k], list) and isinstance(v, list):
                        # Merge lists without duplicates
                        merged_attrs[k] = list(set(merged_attrs[k] + v))
                
                entity_map[key]['attributes'] = merged_attrs
                
                # Preserve the more specific ID (longer or more descriptive)
                if len(entity['id']) > len(existing_entity['id']):
                    entity_map[key]['id'] = entity['id']
        
        return list(entity_map.values())
    
    def _update_relationships(self, relationships: List[Dict[str, Any]], unique_entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Update relationship references to use canonical entity IDs."""
        # Create lookup for entity IDs
        entity_id_lookup = {entity['id']: entity for entity in unique_entities}
        
        # Also create lookups by name for fallback
        entity_name_lookup = {}
        for entity in unique_entities:
            key = f"{entity['type']}:{entity['name'].lower()}"
            entity_name_lookup[key] = entity['id']
        
        updated_rels = []
        for rel in relationships:
            source_found = rel['source'] in entity_id_lookup
            target_found = rel['target'] in entity_id_lookup
            
            # Try to find entities if IDs don't match
            if not source_found:
                # Try to find by name
                for entity in unique_entities:
                    if entity['id'].startswith(rel['source'].split('_')[0]):  # Match by prefix
                        rel['source'] = entity['id']
                        source_found = True
                        break
            
            if not target_found:
                for entity in unique_entities:
                    if entity['id'].startswith(rel['target'].split('_')[0]):  # Match by prefix
                        rel['target'] = entity['id']
                        target_found = True
                        break
            
            if source_found and target_found:
                updated_rels.append(rel)
            else:
                print(f"Dropping relationship due to missing entities: {rel}")
        
        return updated_rels
    
    def export_to_graph_format(self, output_file: str) -> None:
        """Export all processed data to a format suitable for graph database import."""
        # Collect all processed data
        all_entities = []
        all_relationships = []
        
        for doc_data in self.document_store.values():
            processed_data = doc_data['processed_data']
            all_entities.extend(processed_data.get('entities', []))
            all_relationships.extend(processed_data.get('relationships', []))
        
        # Deduplicate entities and update relationships
        unique_entities = self._deduplicate_entities(all_entities)
        updated_relationships = self._update_relationships(all_relationships, unique_entities)
        
        # Add additional inferred relationships
        updated_relationships.extend(self._infer_relationships(unique_entities))
        
        # Remove duplicate relationships
        unique_relationships = self._deduplicate_relationships(updated_relationships)
        
        # Create export data
        export_data = {
            'nodes': [self._format_node_for_export(entity) for entity in unique_entities],
            'edges': [self._format_edge_for_export(rel) for rel in unique_relationships]
        }
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"Exported {len(export_data['nodes'])} nodes and {len(export_data['edges'])} edges to {output_file}")

    def _deduplicate_relationships(self, relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate relationships based on source, target, and type."""
        seen = set()
        unique_relationships = []
        
        for rel in relationships:
            key = (rel['source'], rel['target'], rel['type'])
            if key not in seen:
                seen.add(key)
                unique_relationships.append(rel)
        
        return unique_relationships
    
    def _enhance_relationships(self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance relationships with more specific types and properties."""
        enhanced_relationships = []
        
        # Create lookups for quick access
        entity_lookup = {e['id']: e for e in entities}
        
        for rel in relationships:
            source_entity = entity_lookup.get(rel['source'])
            target_entity = entity_lookup.get(rel['target'])
            
            if not source_entity or not target_entity:
                continue
            
            # Determine more specific relationship type based on entity types
            if source_entity['labels'][0] == 'Term':
                if target_entity['labels'][0] == 'Coverage':
                    rel['type'] = 'defines_concept_in'
            elif source_entity['labels'][0] == 'Exclusion':
                if target_entity['labels'][0] == 'Coverage':
                    rel['type'] = 'excludes_from'
            elif source_entity['labels'][0] == 'Limit':
                if target_entity['labels'][0] == 'Coverage':
                    rel['type'] = 'limits_amount_for'
            elif source_entity['labels'][0] == 'Condition':
                if target_entity['labels'][0] == 'Coverage':
                    rel['type'] = 'modifies_coverage'
            
            # Add relationship metadata
            rel['properties'] = {
                'source_type': source_entity['labels'][0],
                'target_type': target_entity['labels'][0],
                'source_section': source_entity['properties'].get('section', ''),
                'target_section': target_entity['properties'].get('section', '')
            }
            
            enhanced_relationships.append(rel)
        
        return enhanced_relationships
    def _format_node_for_export(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Format an entity as a node for graph database import."""
        return {
            'id': entity['id'],
            'labels': [entity['type']],
            'properties': {
                'name': entity['name'],
                **entity.get('attributes', {})
            }
        }
    
    def _format_edge_for_export(self, relationship: Dict[str, Any]) -> Dict[str, Any]:
        """Format a relationship as an edge for graph database import."""
        return {
            'source': relationship['source'],
            'target': relationship['target'],
            'type': relationship['type'],
            'properties': {}
        }

    def debug_extracted_data(self, file_path: str) -> None:
        """Debug method to see what's being extracted from a document."""
        try:
            print(f"\n=== Debugging extraction for {file_path} ===")
            
            # Extract text from document
            document_text = self._extract_full_text(file_path)
            print(f"Document text length: {len(document_text)} characters")
            
            # Extract sections
            sections = self._extract_document_sections(document_text)
            print("\nSections found:")
            for section_name, section_text in sections.items():
                if section_text:
                    print(f"  - {section_name}: {len(section_text)} characters")
            
            # Debug extraction for each section
            for section_name, section_text in sections.items():
                if not section_text:
                    continue
                
                print(f"\n=== Debugging section: {section_name} ===")
                
                # Generate extraction prompt
                extraction_prompt = self._generate_extraction_prompt(section_text[:1000], section_name)
                print(f"Extraction prompt preview: {extraction_prompt[:200]}...")
                
                # Extract information
                extracted_info = self._extract_with_llm(extraction_prompt)
                processed_data = self._process_extraction_result(extracted_info)
                
                print(f"Extracted: {len(processed_data.get('entities', []))} entities, {len(processed_data.get('relationships', []))} relationships")
                
                # Show sample entities
                if processed_data.get('entities'):
                    print("\nSample entities:")
                    for entity in processed_data['entities'][:3]:
                        print(f"  - {entity['type']}: {entity['name']} (ID: {entity['id']})")
            
            return processed_data
        
        except Exception as e:
            print(f"Error in debug_extracted_data: {e}")
            import traceback
            print(traceback.format_exc())
            return None

# Example usage
if __name__ == "__main__":
    # Initialize the processor
    processor = InsuranceDocumentProcessor()
    
    # Crawl for documents
    sources = [
        "https://example-insurance.com/policies",
        "/path/to/local/insurance/documents"
    ]
    document_paths = processor.crawl_documents(sources)
    
    # Process documents
    processing_results = processor.process_document_batch(document_paths)
    
    # Export to graph format
    processor.export_to_graph_format("insurance_knowledge_graph.json")
    
    print("Document processing complete!")