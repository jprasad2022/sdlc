# Step 2: Self-Evolving Graph Schema for Insurance Knowledge Graph

import os
import json
import time
from typing import List, Dict, Any, Set, Tuple
import networkx as nx
from datetime import datetime
import random

class SelfEvolvingGraphSchema:
    def __init__(self, base_schema_path=None):
        """
        Initialize the self‑evolving graph schema system.
        
        Args:
            base_schema_path: Optional path to a base schema file to start with
        """
        import os, networkx as nx
        from datetime import datetime

        # 1) Schema graph
        self.schema_graph = nx.DiGraph()

        # 2) Prepare version & metrics *before* any schema mutations
        self.schema_versions = []
        self.schema_metrics = {
            'entity_counts':       {},
            'relationship_counts': {},
            'schema_changes':      []
        }
        self.quality_scores = {
            'coverage':     0.0,
            'consistency':  0.0,
            'connectivity': 0.0
        }

        # 3) Load base schema or initialize default
        if base_schema_path and os.path.exists(base_schema_path):
            self._load_base_schema(base_schema_path)
        else:
            self._initialize_default_schema()

        # 4) Record the very first schema version
        self._record_schema_version("Initial schema creation")

    
    def _load_base_schema(self, schema_path: str) -> None:
        """Load a base schema from a file."""
        try:
            with open(schema_path, 'r') as f:
                schema_data = json.load(f)
            
            # Add entity types to schema graph
            for entity_type in schema_data.get('entity_types', []):
                self.add_entity_type(
                    entity_type['name'],
                    entity_type.get('properties', {}),
                    entity_type.get('constraints', {})
                )
            
            # Add relationship types to schema graph
            for rel_type in schema_data.get('relationship_types', []):
                self.add_relationship_type(
                    rel_type['name'],
                    rel_type['source'],
                    rel_type['target'],
                    rel_type.get('properties', {}),
                    rel_type.get('constraints', {})
                )
                
            print(f"Loaded base schema with {len(schema_data.get('entity_types', []))} entity types and {len(schema_data.get('relationship_types', []))} relationship types")
        
        except Exception as e:
            print(f"Error loading base schema: {e}")
            # Fall back to default schema
            self._initialize_default_schema()
    
    def _initialize_default_schema(self) -> None:
        """Initialize a default insurance domain schema."""
        # Core insurance entity types
        entity_types = [
            {
                "name": "Policy",
                "properties": {
                    "policy_number": {"type": "string", "required": True},
                    "effective_date": {"type": "date", "required": True},
                    "expiration_date": {"type": "date", "required": True},
                    "status": {"type": "string", "enum": ["active", "expired", "cancelled"]}
                }
            },
            {
                "name": "Insured",
                "properties": {
                    "name": {"type": "string", "required": True},
                    "id_number": {"type": "string", "required": True},
                    "date_of_birth": {"type": "date"},
                    "contact_info": {"type": "object"}
                }
            },
            {
                "name": "Coverage",
                "properties": {
                    "type": {"type": "string", "required": True},
                    "limit": {"type": "number"},
                    "deductible": {"type": "number"}
                }
            },
            {
                "name": "Claim",
                "properties": {
                    "claim_number": {"type": "string", "required": True},
                    "date_of_loss": {"type": "date", "required": True},
                    "status": {"type": "string", "enum": ["open", "under_review", "approved", "denied", "closed"]},
                    "amount": {"type": "number"}
                }
            },
            {
                "name": "Premium",
                "properties": {
                    "amount": {"type": "number", "required": True},
                    "payment_frequency": {"type": "string", "enum": ["monthly", "quarterly", "annually"]},
                    "due_date": {"type": "date"}
                }
            },
            {
                "name": "Definition",
                "properties": {
                    "term": {"type": "string", "required": True},
                    "meaning": {"type": "string", "required": True},
                    "aliases": {"type": "array"}
                }
            }            
        ]
        
        # Core relationship types
        relationship_types = [
            {
                "name": "HAS_COVERAGE",
                "source": "Policy",
                "target": "Coverage",
                "properties": {
                    "added_date": {"type": "date"}
                },
                "constraints": {
                    "cardinality": "one_to_many"
                }
            },
            {
                "name": "INSURES",
                "source": "Policy",
                "target": "Insured",
                "properties": {},
                "constraints": {
                    "cardinality": "many_to_many"
                }
            },
            {
                "name": "HAS_PREMIUM",
                "source": "Policy",
                "target": "Premium",
                "properties": {},
                "constraints": {
                    "cardinality": "one_to_one"
                }
            },
            {
                "name": "FILES_CLAIM",
                "source": "Insured",
                "target": "Claim",
                "properties": {
                    "filing_date": {"type": "date"}
                },
                "constraints": {
                    "cardinality": "one_to_many"
                }
            },
            {
                "name": "RELATED_TO",
                "source": "Claim",
                "target": "Coverage",
                "properties": {},
                "constraints": {
                    "cardinality": "many_to_many"
                }
            }
        ]
        
        # Add entity types to schema graph
        for entity_type in entity_types:
            self.add_entity_type(
                entity_type['name'],
                entity_type.get('properties', {}),
                entity_type.get('constraints', {})
            )
        
        # Add relationship types to schema graph
        for rel_type in relationship_types:
            self.add_relationship_type(
                rel_type['name'],
                rel_type['source'],
                rel_type['target'],
                rel_type.get('properties', {}),
                rel_type.get('constraints', {})
            )
            
        print(f"Initialized default insurance schema with {len(entity_types)} entity types and {len(relationship_types)} relationship types")
    
    def add_entity_type(self, name: str, properties: Dict[str, Any] = None, constraints: Dict[str, Any] = None) -> bool:
        """Add a new entity type to the schema."""
        if properties is None:
            properties = {}
        if constraints is None:
            constraints = {}
            
        # Check if entity type already exists
        if name in self.get_entity_types():
            print(f"Entity type '{name}' already exists in schema")
            return False
            
        # Add node to schema graph
        self.schema_graph.add_node(
            name,
            type='entity_type',
            properties=properties,
            constraints=constraints
        )
        
        # Update schema metrics
        self._update_schema_metrics()
        
        # Record schema change
        self._record_schema_version(f"Added entity type: {name}")
        
        return True
    
    def add_relationship_type(self, name: str, source_type: str, target_type: str, 
                             properties: Dict[str, Any] = None, constraints: Dict[str, Any] = None) -> bool:
        """
        Add a new relationship type to the schema.
        
        Args:
            name: Name of the relationship type
            source_type: Source entity type name
            target_type: Target entity type name
            properties: Dictionary of property definitions
            constraints: Dictionary of constraints
            
        Returns:
            Boolean indicating success
        """
        if properties is None:
            properties = {}
        if constraints is None:
            constraints = {}
            
        # Check if source and target entity types exist
        entity_types = self.get_entity_types()
        if source_type not in entity_types:
            print(f"Source entity type '{source_type}' does not exist in schema")
            return False
        if target_type not in entity_types:
            print(f"Target entity type '{target_type}' does not exist in schema")
            return False
            
        # Check if this relationship already exists
        for rel in self.schema_graph.edges(data=True):
            if (rel[0] == source_type and rel[1] == target_type and 
                rel[2].get('name') == name):
                print(f"Relationship type '{name}' already exists between '{source_type}' and '{target_type}'")
                return False
                
        # Add edge to schema graph
        self.schema_graph.add_edge(
            source_type,
            target_type,
            name=name,
            type='relationship_type',
            properties=properties,
            constraints=constraints
        )
        
        # Update schema metrics
        self._update_schema_metrics()
        
        # Record schema change
        self._record_schema_version(f"Added relationship type: {name} ({source_type} -> {target_type})")
        
        return True
    
    def get_entity_types(self) -> List[str]:
        """Get all entity type names in the schema."""
        return [node for node, data in self.schema_graph.nodes(data=True) 
                if data.get('type') == 'entity_type']
    
    def get_relationship_types(self) -> List[Dict[str, Any]]:
        """Get all relationship types in the schema."""
        relationships = []
        for source, target, data in self.schema_graph.edges(data=True):
            if data.get('type') == 'relationship_type':
                relationships.append({
                    'name': data.get('name'),
                    'source': source,
                    'target': target,
                    'properties': data.get('properties', {}),
                    'constraints': data.get('constraints', {})
                })
        return relationships
    
    def _update_schema_metrics(self) -> None:
        """Update schema metrics based on current state."""
        # Update entity counts
        entity_types = self.get_entity_types()
        self.schema_metrics['entity_counts'] = {
            'total': len(entity_types),
            'by_type': {entity: 1 for entity in entity_types}
        }
        
        # Update relationship counts
        relationships = self.get_relationship_types()
        rel_counts = {}
        for rel in relationships:
            rel_name = rel['name']
            if rel_name in rel_counts:
                rel_counts[rel_name] += 1
            else:
                rel_counts[rel_name] = 1
                
        self.schema_metrics['relationship_counts'] = {
            'total': len(relationships),
            'by_type': rel_counts
        }
        
        # Update quality scores
        self._calculate_quality_scores()
    
    def _calculate_quality_scores(self) -> None:
        """Calculate quality metrics for the current schema."""
        # Coverage score - based on number of entity and relationship types
        entity_count = len(self.get_entity_types())
        relationship_count = len(self.get_relationship_types())
        
        # Baseline expectations for a comprehensive insurance schema
        expected_entities = 15
        expected_relationships = 25
        
        coverage = min(1.0, (entity_count / expected_entities + relationship_count / expected_relationships) / 2)
        
        # Connectivity score - based on graph connectivity
        if entity_count > 0:
            connectivity = nx.density(self.schema_graph)
        else:
            connectivity = 0.0
            
        # Consistency score - based on property completeness
        property_completeness = []
        for _, data in self.schema_graph.nodes(data=True):
            if data.get('type') == 'entity_type':
                props = data.get('properties', {})
                required_props = sum(1 for p in props.values() if p.get('required', False))
                if len(props) > 0:
                    property_completeness.append(required_props / len(props))
                else:
                    property_completeness.append(0.0)
                    
        consistency = sum(property_completeness) / max(1, len(property_completeness))
        
        # Update quality scores
        self.quality_scores = {
            'coverage': coverage,
            'consistency': consistency,
            'connectivity': connectivity,
            'overall': (coverage + consistency + connectivity) / 3
        }
    
    def _record_schema_version(self, change_description: str) -> None:
        """Record a new version of the schema with change description."""
        version = {
            'version': len(self.schema_versions) + 1,
            'timestamp': datetime.now().isoformat(),
            'description': change_description,
            'entity_count': len(self.get_entity_types()),
            'relationship_count': len(self.get_relationship_types())
        }
        
        self.schema_versions.append(version)
        self.schema_metrics['schema_changes'].append(version)
    
    def analyze_instance_data(self, instance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze instance data to identify potential schema improvements.
        
        Args:
            instance_data: Dictionary containing nodes and edges from processed documents
            
        Returns:
            Dictionary of recommended schema changes
        """
        recommendations = {
            'new_entity_types': [],
            'new_property_types': {},
            'new_relationship_types': [],
            'confidence_scores': {}
        }
        
        # Extract existing entity and relationship types
        existing_entity_types = set(self.get_entity_types())
        existing_rel_types = {r['name']: (r['source'], r['target']) 
                             for r in self.get_relationship_types()}
        
        # Analyze nodes for new entity types and properties
        nodes = instance_data.get('nodes', [])
        all_labels = set()
        label_counts = {}
        property_sets = {}
        
        for node in nodes:
            labels = node.get('labels', [])
            for label in labels:
                all_labels.add(label)
                label_counts[label] = label_counts.get(label, 0) + 1
                
                # Track properties for each entity type
                if label not in property_sets:
                    property_sets[label] = {}
                    
                properties = node.get('properties', {})
                for prop_name, prop_value in properties.items():
                    if prop_name not in property_sets[label]:
                        property_sets[label][prop_name] = {
                            'count': 0,
                            'types': set(),
                            'values': set()
                        }
                    
                    prop_data = property_sets[label][prop_name]
                    prop_data['count'] += 1
                    
                    # Determine property type
                    prop_type = self._infer_property_type(prop_value)
                    prop_data['types'].add(prop_type)
                    
                    # Store sample values (up to 10)
                    if len(prop_data['values']) < 10:
                        prop_data['values'].add(str(prop_value))
        
        # Identify new entity types
        for label in all_labels:
            if label not in existing_entity_types:
                # Calculate confidence based on frequency
                confidence = min(1.0, label_counts[label] / 10.0)
                
                # Property analysis
                props = property_sets.get(label, {})
                common_props = {
                    name: self._analyze_property(name, data)
                    for name, data in props.items()
                    if data['count'] >= 3  # Only consider properties that appear multiple times
                }
                
                recommendations['new_entity_types'].append({
                    'name': label,
                    'frequency': label_counts[label],
                    'proposed_properties': common_props
                })
                
                recommendations['confidence_scores'][f'entity_type:{label}'] = confidence
        
        # Analyze edges for new relationship types
        edges = instance_data.get('edges', [])
        rel_patterns = {}
        
        for edge in edges:
            source_label = self._get_node_label(edge.get('source'), nodes)
            target_label = self._get_node_label(edge.get('target'), nodes)
            rel_type = edge.get('type')
            
            if not (source_label and target_label and rel_type):
                continue
                
            rel_key = f"{rel_type}:{source_label}:{target_label}"
            
            if rel_key not in rel_patterns:
                rel_patterns[rel_key] = {
                    'count': 0,
                    'properties': {}
                }
                
            rel_patterns[rel_key]['count'] += 1
            
            # Analyze relationship properties
            properties = edge.get('properties', {})
            for prop_name, prop_value in properties.items():
                if prop_name not in rel_patterns[rel_key]['properties']:
                    rel_patterns[rel_key]['properties'][prop_name] = {
                        'count': 0,
                        'types': set(),
                        'values': set()
                    }
                    
                prop_data = rel_patterns[rel_key]['properties'][prop_name]
                prop_data['count'] += 1
                
                # Determine property type
                prop_type = self._infer_property_type(prop_value)
                prop_data['types'].add(prop_type)
                
                # Store sample values (up to 5)
                if len(prop_data['values']) < 5:
                    prop_data['values'].add(str(prop_value))
        
        # Identify new relationship types
        for rel_key, data in rel_patterns.items():
            rel_type, source_label, target_label = rel_key.split(':')
            
            # Check if relationship type already exists
            existing_source_target = existing_rel_types.get(rel_type)
            
            if not existing_source_target or (existing_source_target != (source_label, target_label)):
                # Calculate confidence based on frequency
                confidence = min(1.0, data['count'] / 5.0)
                
                # Property analysis
                props = data.get('properties', {})
                common_props = {
                    name: self._analyze_property(name, prop_data)
                    for name, prop_data in props.items()
                    if prop_data['count'] >= 2  # Only consider properties that appear multiple times
                }
                
                recommendations['new_relationship_types'].append({
                    'name': rel_type,
                    'source': source_label,
                    'target': target_label,
                    'frequency': data['count'],
                    'proposed_properties': common_props
                })
                
                recommendations['confidence_scores'][f'relationship_type:{rel_key}'] = confidence
        
        # Identify new properties for existing entity types
        for entity_type in existing_entity_types:
            if entity_type in property_sets:
                # Get current properties for this entity type
                current_props = set()
                node_data = self.schema_graph.nodes.get(entity_type, {})
                if 'properties' in node_data:
                    current_props = set(node_data['properties'].keys())
                
                # Find new properties
                new_props = {}
                for prop_name, prop_data in property_sets[entity_type].items():
                    if prop_name not in current_props and prop_data['count'] >= 3:
                        new_props[prop_name] = self._analyze_property(prop_name, prop_data)
                        
                        # Calculate confidence based on frequency
                        confidence = min(1.0, prop_data['count'] / 10.0)
                        recommendations['confidence_scores'][f'property:{entity_type}.{prop_name}'] = confidence
                
                if new_props:
                    recommendations['new_property_types'][entity_type] = new_props
        
        return recommendations
    
    def _get_node_label(self, node_id: str, nodes: List[Dict[str, Any]]) -> str:
        """Get the primary label for a node by ID."""
        for node in nodes:
            if node.get('id') == node_id:
                labels = node.get('labels', [])
                return labels[0] if labels else None
        return None
    
    def _infer_property_type(self, value: Any) -> str:
        """Infer the data type of a property value."""
        if value is None:
            return 'null'
        
        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'number'
        elif isinstance(value, dict):
            return 'object'
        elif isinstance(value, list):
            return 'array'
        else:
            # Try to parse as date
            str_value = str(value)
            date_patterns = [
                r'\d{4}-\d{2}-\d{2}',  # ISO date
                r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
                r'\d{2}-\d{2}-\d{4}'   # MM-DD-YYYY
            ]
            
            import re
            for pattern in date_patterns:
                if re.fullmatch(pattern, str_value):
                    return 'date'
            
            # Default to string
            return 'string'
    
    def _analyze_property(self, name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze property data to determine type and constraints."""
        result = {
            'type': None,
            'required': data['count'] > 5,  # Heuristic for required fields
            'sample_values': list(data['values'])
        }
        
        # Determine most likely type
        types = data['types']
        if len(types) == 1:
            result['type'] = next(iter(types))
        elif 'string' in types and len(types) > 1:
            # If mixed types including string, prefer string
            result['type'] = 'string'
        elif 'number' in types and 'integer' in types:
            # If both number and integer, prefer number
            result['type'] = 'number'
        else:
            # Otherwise use most common or first type
            result['type'] = next(iter(types))
        
        # Additional constraints based on name and values
        lower_name = name.lower()
        if 'date' in lower_name and result['type'] == 'string':
            result['type'] = 'date'
        
        if 'id' in lower_name or 'number' in lower_name:
            result['required'] = True
        
        # Enum constraint for limited set of values
        if len(data['values']) <= 5 and data['count'] >= 5:
            result['enum'] = list(data['values'])
        
        return result
    
    def evolve_schema(self, instance_data: Dict[str, Any], threshold: float = 0.7) -> Dict[str, Any]:
        """
        Automatically evolve the schema based on instance data.
        
        Args:
            instance_data: Dictionary containing nodes and edges from processed documents
            threshold: Confidence threshold for automatic changes (0.0-1.0)
            
        Returns:
            Dictionary of applied changes
        """
        # Analyze instance data for recommendations
        recommendations = self.analyze_instance_data(instance_data)
        
        applied_changes = {
            'new_entity_types': [],
            'new_property_types': {},
            'new_relationship_types': []
        }
        
        # Apply entity type changes
        for entity_rec in recommendations['new_entity_types']:
            entity_name = entity_rec['name']
            confidence = recommendations['confidence_scores'].get(f'entity_type:{entity_name}', 0.0)
            
            if confidence >= threshold:
                # Create properties dictionary
                properties = {}
                for prop_name, prop_data in entity_rec['proposed_properties'].items():
                    properties[prop_name] = {
                        'type': prop_data['type'],
                        'required': prop_data.get('required', False)
                    }
                    
                    if 'enum' in prop_data:
                        properties[prop_name]['enum'] = prop_data['enum']
                
                # Add entity type to schema
                success = self.add_entity_type(entity_name, properties)
                
                if success:
                    applied_changes['new_entity_types'].append({
                        'name': entity_name,
                        'properties': properties,
                        'confidence': confidence
                    })
        
        # Apply property changes
        for entity_type, new_props in recommendations['new_property_types'].items():
            applied_props = {}
            
            for prop_name, prop_data in new_props.items():
                confidence = recommendations['confidence_scores'].get(f'property:{entity_type}.{prop_name}', 0.0)
                
                if confidence >= threshold:
                    # Add property to entity type
                    node_data = self.schema_graph.nodes.get(entity_type, {})
                    
                    if 'properties' not in node_data:
                        node_data['properties'] = {}
                        
                    prop_def = {
                        'type': prop_data['type'],
                        'required': prop_data.get('required', False)
                    }
                    
                    if 'enum' in prop_data:
                        prop_def['enum'] = prop_data['enum']
                        
                    node_data['properties'][prop_name] = prop_def
                    self.schema_graph.nodes[entity_type].update(node_data)
                    
                    applied_props[prop_name] = {
                        'definition': prop_def,
                        'confidence': confidence
                    }
            
            if applied_props:
                applied_changes['new_property_types'][entity_type] = applied_props
                self._record_schema_version(f"Added new properties to {entity_type}: {', '.join(applied_props.keys())}")
        
        # Apply relationship type changes
        for rel_rec in recommendations['new_relationship_types']:
            rel_name = rel_rec['name']
            source = rel_rec['source']
            target = rel_rec['target']
            rel_key = f"{rel_name}:{source}:{target}"
            confidence = recommendations['confidence_scores'].get(f'relationship_type:{rel_key}', 0.0)
            
            if confidence >= threshold:
                # Create properties dictionary
                properties = {}
                for prop_name, prop_data in rel_rec.get('proposed_properties', {}).items():
                    properties[prop_name] = {
                        'type': prop_data['type'],
                        'required': prop_data.get('required', False)
                    }
                    
                    if 'enum' in prop_data:
                        properties[prop_name]['enum'] = prop_data['enum']
                
                # Add relationship type to schema
                success = self.add_relationship_type(rel_name, source, target, properties)
                
                if success:
                    applied_changes['new_relationship_types'].append({
                        'name': rel_name,
                        'source': source,
                        'target': target,
                        'properties': properties,
                        'confidence': confidence
                    })
        
        # Update schema metrics
        self._update_schema_metrics()
        
        return applied_changes
    
    def export_schema(self, output_file: str) -> None:
        """Export the current schema to a file."""
        schema_data = {
            'entity_types': [],
            'relationship_types': [],
            'metadata': {
                'version': len(self.schema_versions),
                'timestamp': datetime.now().isoformat(),
                'quality_scores': self.quality_scores
            }
        }
        
        # Export entity types
        for node, data in self.schema_graph.nodes(data=True):
            if data.get('type') == 'entity_type':
                schema_data['entity_types'].append({
                    'name': node,
                    'properties': data.get('properties', {}),
                    'constraints': data.get('constraints', {})
                })
        
        # Export relationship types
        for source, target, data in self.schema_graph.edges(data=True):
            if data.get('type') == 'relationship_type':
                schema_data['relationship_types'].append({
                    'name': data.get('name'),
                    'source': source,
                    'target': target,
                    'properties': data.get('properties', {}),
                    'constraints': data.get('constraints', {})
                })
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(schema_data, f, indent=2)
            
        print(f"Exported schema with {len(schema_data['entity_types'])} entity types and {len(schema_data['relationship_types'])} relationship types to {output_file}")
    
    def generate_visualization(self, output_file: str) -> None:
        """Generate a visualization of the schema graph."""
        import matplotlib.pyplot as plt
        
        # Create a copy of the graph for visualization
        vis_graph = nx.DiGraph()
        
        # Add nodes with labels
        for node, data in self.schema_graph.nodes(data=True):
            if data.get('type') == 'entity_type':
                # Count properties
                prop_count = len(data.get('properties', {}))
                vis_graph.add_node(node, label=f"{node}\n({prop_count} props)")
        
        # Add edges with labels
        for source, target, data in self.schema_graph.edges(data=True):
            if data.get('type') == 'relationship_type':
                vis_graph.add_edge(source, target, label=data.get('name', 'RELATED_TO'))
        
        # Set up the plot
        plt.figure(figsize=(12, 10))
        pos = nx.spring_layout(vis_graph, seed=42)
        
        # Draw nodes
        nx.draw_networkx_nodes(vis_graph, pos, node_size=2000, node_color='lightblue')
        
        # Draw edges
        nx.draw_networkx_edges(vis_graph, pos, width=1.5, arrowsize=20)
        
        # Draw labels
        nx.draw_networkx_labels(vis_graph, pos, font_size=10, font_weight='bold')
        
        # Draw edge labels
        edge_labels = {(u, v): d.get('label', '') for u, v, d in vis_graph.edges(data=True)}
        nx.draw_networkx_edge_labels(vis_graph, pos, edge_labels=edge_labels, font_size=8)
        
        # Save the figure
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Schema visualization saved to {output_file}")

# Example usage
if __name__ == "__main__":
    # Initialize the self-evolving schema
    schema_manager = SelfEvolvingGraphSchema()
    
    # Load some sample data (this would come from the document processor)
    sample_data = {
        'nodes': [
            {'id': 'pol1', 'labels': ['Policy'], 'properties': {'policy_number': 'P12345', 'effective_date': '2023-01-01'}},
            {'id': 'ins1', 'labels': ['Insured'], 'properties': {'name': 'John Doe', 'id_number': 'ID-123'}},
            {'id': 'cov1', 'labels': ['Coverage'], 'properties': {'type': 'Liability', 'limit': 1000000}},
            {'id': 'clm1', 'labels': ['Claim'], 'properties': {'claim_number': 'C789', 'date_of_loss': '2023-03-15'}},
            {'id': 'doc1', 'labels': ['Document'], 'properties': {'type': 'Policy Form', 'version': '2.1'}}
        ],
        'edges': [
            {'source': 'pol1', 'target': 'ins1', 'type': 'INSURES', 'properties': {}},
            {'source': 'pol1', 'target': 'cov1', 'type': 'HAS_COVERAGE', 'properties': {'added_date': '2023-01-01'}},
            {'source': 'ins1', 'target': 'clm1', 'type': 'FILES_CLAIM', 'properties': {'filing_date': '2023-03-16'}},
            {'source': 'clm1', 'target': 'doc1', 'type': 'HAS_DOCUMENT', 'properties': {'upload_date': '2023-03-17'}}
        ]
    }
    
    # Evolve the schema based on the sample data
    changes = schema_manager.evolve_schema(sample_data, threshold=0.6)
    
    # Export the evolved schema
    schema_manager.export_schema("evolved_insurance_schema.json")
    
    # Generate a visualization
    schema_manager.generate_visualization("insurance_schema_visualization.png")
    
    print("Schema evolution complete!")