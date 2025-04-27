import unittest
import os
import json
import networkx as nx
import sys
sys.path.append('../')  # Add parent directory to path

from src.self_evolving_graph_schema import SelfEvolvingGraphSchema

class TestSelfEvolvingGraphSchema(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        # Initialize schema manager with no base schema
        self.schema_manager = SelfEvolvingGraphSchema()
        
        # Create a temporary schema file for testing
        self.test_schema_path = "test_schema.json"
        with open(self.test_schema_path, 'w') as f:
            json.dump({
                "entity_types": [
                    {
                        "name": "TestEntity",
                        "properties": {
                            "test_prop": {"type": "string", "required": True}
                        }
                    }
                ],
                "relationship_types": []
            }, f)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove test schema file
        if os.path.exists(self.test_schema_path):
            os.remove(self.test_schema_path)
        
        # Remove test output file if it exists
        if os.path.exists("test_output_schema.json"):
            os.remove("test_output_schema.json")
        
        if os.path.exists("test_visualization.png"):
            os.remove("test_visualization.png")
    
    def test_init_with_base_schema(self):
        """Test initialization with base schema."""
        schema = SelfEvolvingGraphSchema(base_schema_path=self.test_schema_path)
        
        # Check that TestEntity was loaded
        entity_types = schema.get_entity_types()
        self.assertIn("TestEntity", entity_types)
    
    def test_add_entity_type(self):
        """Test adding an entity type."""
        # Add a new entity type
        properties = {
            "name": {"type": "string", "required": True},
            "age": {"type": "integer", "required": False}
        }
        success = self.schema_manager.add_entity_type("Person", properties)
        
        # Check result
        self.assertTrue(success)
        
        # Check that entity was added
        entity_types = self.schema_manager.get_entity_types()
        self.assertIn("Person", entity_types)
        
        # Try adding the same entity again
        success = self.schema_manager.add_entity_type("Person", properties)
        self.assertFalse(success)  # Should fail since entity already exists
    
    def test_add_relationship_type(self):
        """Test adding a relationship type."""
        # First add entity types
        self.schema_manager.add_entity_type("Person", {})
        self.schema_manager.add_entity_type("Policy", {})
        
        # Add relationship
        success = self.schema_manager.add_relationship_type(
            "OWNS", "Person", "Policy", {"purchase_date": {"type": "date"}}
        )
        
        # Check result
        self.assertTrue(success)
        
        # Check that relationship was added
        relationships = self.schema_manager.get_relationship_types()
        relationship_names = [r['name'] for r in relationships]
        self.assertIn("OWNS", relationship_names)
        
        # Try adding with non-existent source
        success = self.schema_manager.add_relationship_type(
            "INVALID", "NonExistentEntity", "Policy"
        )
        self.assertFalse(success)
    
    def test_export_schema(self):
        """Test exporting schema to file."""
        # Add some entities and relationships
        self.schema_manager.add_entity_type("Person", {"name": {"type": "string"}})
        self.schema_manager.add_entity_type("Policy", {"number": {"type": "string"}})
        self.schema_manager.add_relationship_type("OWNS", "Person", "Policy")
        
        # Export schema
        self.schema_manager.export_schema("test_output_schema.json")
        
        # Check that file was created
        self.assertTrue(os.path.exists("test_output_schema.json"))
        
        # Load and check content
        with open("test_output_schema.json", 'r') as f:
            schema_data = json.load(f)
        
        # Check entities
        entity_names = [e['name'] for e in schema_data['entity_types']]
        self.assertIn("Person", entity_names)
        self.assertIn("Policy", entity_names)
        
        # Check relationships
        relationship_names = [r['name'] for r in schema_data['relationship_types']]
        self.assertIn("OWNS", relationship_names)
    
    def test_analyze_instance_data(self):
        """Test analysis of instance data."""
        # Add some base entities
        self.schema_manager.add_entity_type("Person", {"name": {"type": "string"}})
        
        # Create instance data with new entity types and properties
        instance_data = {
            "nodes": [
                {
                    "id": "p1",
                    "labels": ["Person"],
                    "properties": {
                        "name": "John Doe",
                        "email": "john@example.com"  # New property
                    }
                },
                {
                    "id": "c1",
                    "labels": ["Car"],  # New entity type
                    "properties": {
                        "make": "Toyota",
                        "model": "Camry",
                        "year": 2020
                    }
                }
            ],
            "edges": [
                {
                    "source": "p1",
                    "target": "c1",
                    "type": "OWNS",
                    "properties": {
                        "since": "2020-01-01"
                    }
                }
            ]
        }
        
        # Analyze instance data
        recommendations = self.schema_manager.analyze_instance_data(instance_data)
        
        # Check recommendations for new entity types
        new_entity_names = [e['name'] for e in recommendations['new_entity_types']]
        self.assertIn("Car", new_entity_names)
        
        # Check recommendations for new properties
        self.assertIn("Person", recommendations['new_property_types'])
        person_props = recommendations['new_property_types']['Person']
        self.assertIn("email", person_props)
        
        # Check recommendations for new relationships
        new_rel_names = [r['name'] for r in recommendations['new_relationship_types']]
        self.assertIn("OWNS", new_rel_names)
    
    def test_evolve_schema(self):
        """Test schema evolution based on instance data."""
        # Add some base entities
        self.schema_manager.add_entity_type("Person", {"name": {"type": "string"}})
        
        # Create instance data with new entity types and properties
        instance_data = {
            "nodes": [
                {
                    "id": "p1",
                    "labels": ["Person"],
                    "properties": {
                        "name": "John Doe",
                        "email": "john@example.com"  # New property
                    }
                },
                {
                    "id": "c1",
                    "labels": ["Car"],  # New entity type
                    "properties": {
                        "make": "Toyota",
                        "model": "Camry",
                        "year": 2020
                    }
                }
            ],
            "edges": [
                {
                    "source": "p1",
                    "target": "c1",
                    "type": "OWNS",
                    "properties": {
                        "since": "2020-01-01"
                    }
                }
            ]
        }
        
        # Evolve schema with a low threshold to ensure changes are applied
        changes = self.schema_manager.evolve_schema(instance_data, threshold=0.1)
        
        # Check that changes were applied
        entity_types = self.schema_manager.get_entity_types()
        self.assertIn("Car", entity_types)  # New entity should be added
        
        # Check that the new relationship was added
        relationships = self.schema_manager.get_relationship_types()
        relationship_names = [r['name'] for r in relationships]
        self.assertIn("OWNS", relationship_names)
        
        # Check the changes report
        self.assertIn("Car", [e['name'] for e in changes['new_entity_types']])
        self.assertIn("OWNS", [r['name'] for r in changes['new_relationship_types']])
    
    def test_generate_visualization(self):
        """Test generation of schema visualization."""
        # Add some entities and relationships
        self.schema_manager.add_entity_type("Person", {"name": {"type": "string"}})
        self.schema_manager.add_entity_type("Policy", {"number": {"type": "string"}})
        self.schema_manager.add_relationship_type("OWNS", "Person", "Policy")
        
        # Only run this test if matplotlib is available
        try:
            import matplotlib
            self.schema_manager.generate_visualization("test_visualization.png")
            
            # Check that file was created
            self.assertTrue(os.path.exists("test_visualization.png"))
        except ImportError:
            print("Matplotlib not available, skipping visualization test")

if __name__ == '__main__':
    unittest.main()