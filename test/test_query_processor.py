import unittest
import json
import networkx as nx
import sys
sys.path.append('../')  # Add parent directory to path

from src.graph_rag_query_processor import GraphRAGQueryProcessor
from src.enhanced_query_processor import EnhancedGraphRAGQueryProcessor

class TestGraphRAGQueryProcessor(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        # Create a simple in-memory graph for testing
        self.query_processor = GraphRAGQueryProcessor()
        
        # Add some test data to the knowledge graph
        self._setup_test_graph()
    
    def _setup_test_graph(self):
        """Set up a test knowledge graph with sample data."""
        # Create some test nodes
        policy_node = {
            'labels': ['Policy'],
            'properties': {
                'policy_number': 'P1001',
                'effective_date': '2023-01-01',
                'expiration_date': '2024-01-01',
                'status': 'active',
                'type': 'auto'
            }
        }
        
        insured_node = {
            'labels': ['Insured'],
            'properties': {
                'name': 'John Doe',
                'id_number': 'U5001',
                'date_of_birth': '1980-01-01'
            }
        }
        
        coverage_node = {
            'labels': ['Coverage'],
            'properties': {
                'type': 'liability',
                'limit': 500000,
                'deductible': 1000
            }
        }
        
        claim_node = {
            'labels': ['Claim'],
            'properties': {
                'claim_number': 'CL4001',
                'date_of_loss': '2023-06-15',
                'status': 'approved',
                'amount': 5000
            }
        }
        
        premium_node = {
            'labels': ['Premium'],
            'properties': {
                'amount': 1200,
                'payment_frequency': 'monthly',
                'due_date': '2023-07-01'
            }
        }
        
        # Add nodes to the graph
        self.query_processor.knowledge_graph.add_node('pol1', **policy_node)
        self.query_processor.knowledge_graph.add_node('ins1', **insured_node)
        self.query_processor.knowledge_graph.add_node('cov1', **coverage_node)
        self.query_processor.knowledge_graph.add_node('clm1', **claim_node)
        self.query_processor.knowledge_graph.add_node('prm1', **premium_node)
        
        # Add relationships
        self.query_processor.knowledge_graph.add_edge(
            'pol1', 'ins1', key='INSURES', type='INSURES', properties={}
        )
        self.query_processor.knowledge_graph.add_edge(
            'pol1', 'cov1', key='HAS_COVERAGE', type='HAS_COVERAGE', 
            properties={'added_date': '2023-01-01'}
        )
        self.query_processor.knowledge_graph.add_edge(
            'ins1', 'clm1', key='FILES_CLAIM', type='FILES_CLAIM',
            properties={'filing_date': '2023-06-16'}
        )
        self.query_processor.knowledge_graph.add_edge(
            'pol1', 'prm1', key='HAS_PREMIUM', type='HAS_PREMIUM',
            properties={}
        )
    
    def test_analyze_intent(self):
        """Test intent analysis."""
        # Test policy details intent
        result = self.query_processor.analyze_intent("What are the details of my policy P1001?")
        self.assertEqual(result['intent'], 'policy_details')
        self.assertGreater(result['confidence'], 0.5)
        
        # Test coverage inquiry intent
        result = self.query_processor.analyze_intent("What does my policy cover?")
        self.assertEqual(result['intent'], 'coverage_inquiry')
        self.assertGreater(result['confidence'], 0.5)
        
        # Test claim status intent
        result = self.query_processor.analyze_intent("What's the status of my claim CL4001?")
        self.assertEqual(result['intent'], 'claim_status')
        self.assertGreater(result['confidence'], 0.5)
        
        # Test unknown intent
        result = self.query_processor.analyze_intent("What's the weather like today?")
        self.assertEqual(result['intent'], 'unknown')
    
    def test_extract_parameters(self):
        """Test parameter extraction."""
        # Test policy number extraction
        params = self.query_processor.extract_parameters(
            "Tell me about policy P1001", 'policy_details'
        )
        self.assertEqual(params.get('policy_number'), 'P1001')
        
        # Test claim number extraction
        params = self.query_processor.extract_parameters(
            "What is the status of claim CL4001?", 'claim_status'
        )
        self.assertEqual(params.get('claim_number'), 'CL4001')
        
        # Test policy type extraction
        params = self.query_processor.extract_parameters(
            "What does my auto insurance cover?", 'coverage_inquiry'
        )
        self.assertEqual(params.get('policy_type'), 'auto')
        
        # Test coverage type extraction
        params = self.query_processor.extract_parameters(
            "Am I covered for liability damage?", 'coverage_inquiry'
        )
        self.assertIn('liability', params.get('coverage_types', []))
    
    def test_build_graph_query(self):
        """Test building graph queries."""
        # Test policy details query
        params = {'policy_number': 'P1001'}
        query = self.query_processor.build_graph_query('policy_details', params)
        
        self.assertEqual(query['start_nodes'][0]['label'], 'Policy')
        self.assertEqual(query['filters'][0]['property'], 'policy_number')
        self.assertEqual(query['filters'][0]['value'], 'P1001')
        
        # Test coverage inquiry query
        params = {'policy_number': 'P1001', 'coverage_types': ['liability']}
        query = self.query_processor.build_graph_query('coverage_inquiry', params)
        
        self.assertEqual(query['start_nodes'][0]['label'], 'Policy')
        self.assertEqual(query['paths'][0]['to']['label'], 'Coverage')
        self.assertEqual(query['paths'][0]['relationship']['type'], 'HAS_COVERAGE')
        
        # Test claim status query
        params = {'claim_number': 'CL4001'}
        query = self.query_processor.build_graph_query('claim_status', params)
        
        self.assertEqual(query['start_nodes'][0]['label'], 'Claim')
        self.assertEqual(query['filters'][0]['property'], 'claim_number')
        self.assertEqual(query['filters'][0]['value'], 'CL4001')
    
    def test_execute_graph_query(self):
        """Test executing graph queries."""
        # Test policy query
        query = {
            'start_nodes': [{'label': 'Policy', 'alias': 'p'}],
            'filters': [{
                'node': 'p', 
                'property': 'policy_number', 
                'operator': '=', 
                'value': 'P1001'
            }],
            'return_properties': [
                {'node': 'p', 'property': 'policy_number'},
                {'node': 'p', 'property': 'status'}
            ]
        }
        
        result = self.query_processor.execute_graph_query(query)
        
        self.assertGreater(result.get('count', 0), 0)
        self.assertIn('p.policy_number', result.get('properties', {}))
        self.assertEqual(result['properties']['p.policy_number'][0], 'P1001')
        
        # Test relationship query
        query = {
            'start_nodes': [{'label': 'Policy', 'alias': 'p'}],
            'paths': [{
                'from': {'alias': 'p', 'label': 'Policy'},
                'relationship': {'type': 'HAS_COVERAGE', 'direction': 'outgoing'},
                'to': {'alias': 'c', 'label': 'Coverage'}
            }],
            'filters': [{
                'node': 'p', 
                'property': 'policy_number', 
                'operator': '=', 
                'value': 'P1001'
            }],
            'return_properties': [
                {'node': 'p', 'property': 'policy_number'},
                {'node': 'c', 'property': 'type'},
                {'node': 'c', 'property': 'limit'}
            ]
        }
        
        result = self.query_processor.execute_graph_query(query)
        
        self.assertGreater(result.get('count', 0), 0)
        self.assertIn('c.type', result.get('properties', {}))
        self.assertEqual(result['properties']['c.type'][0], 'liability')
    
    def test_generate_response(self):
        """Test response generation."""
        # Test policy details response
        intent = 'policy_details'
        query_results = {
            'properties': {
                'p.policy_number': ['P1001'],
                'p.effective_date': ['2023-01-01'],
                'p.expiration_date': ['2024-01-01'],
                'p.status': ['active'],
                'p.type': ['auto']
            },
            'count': 1
        }
        params = {'policy_number': 'P1001'}
        
        response = self.query_processor.generate_response(intent, query_results, params)
        
        self.assertTrue(response.get('success', False))
        self.assertIn('P1001', response.get('answer', ''))
        self.assertIn('auto', response.get('answer', ''))
        
        # Test no results response
        query_results = {'count': 0}
        params = {'policy_number': 'NONEXISTENT'}
        
        response = self.query_processor.generate_response(intent, query_results, params)
        
        self.assertFalse(response.get('success', True))
        self.assertIn("couldn't find", response.get('answer', '').lower())
    
    def test_process_query(self):
        """Test end-to-end query processing."""
        # Test policy details query
        response = self.query_processor.process_query(
            "What are the details of policy P1001?", 
            {'user_id': 'U5001'}
        )
        
        self.assertEqual(response.get('intent'), 'policy_details')
        self.assertIn('P1001', response.get('answer', ''))
        
        # Test coverage inquiry
        response = self.query_processor.process_query(
            "What does my auto policy P1001 cover?", 
            {'user_id': 'U5001'}
        )
        
        self.assertEqual(response.get('intent'), 'coverage_inquiry')
        self.assertIn('liability', response.get('answer', '').lower())
        
        # Test unknown query
        response = self.query_processor.process_query(
            "Tell me a joke", 
            {'user_id': 'U5001'}
        )
        
        self.assertEqual(response.get('intent'), 'unknown')

class TestEnhancedQueryProcessor(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        # Create an enhanced query processor
        self.query_processor = EnhancedGraphRAGQueryProcessor()
        
        # Add some test data to the knowledge graph (simplified)
        self.query_processor.knowledge_graph.add_node('def1', 
            labels=['Definition'],
            properties={
                'term': 'Deductible',
                'meaning': 'The amount you pay out of pocket before insurance coverage kicks in.'
            }
        )
    
    def test_extract_definition_parameters(self):
        """Test extraction of definition parameters."""
        # Test simple definition query
        params = self.query_processor.extract_parameters(
            "What is a deductible?", 'definition_inquiry'
        )
        self.assertEqual(params.get('term'), 'deductible')
        
        # Test more complex definition query
        params = self.query_processor.extract_parameters(
            "Can you define comprehensive coverage for me?", 'definition_inquiry'
        )
        self.assertEqual(params.get('term'), 'comprehensive coverage')
    
    def test_build_definition_query(self):
        """Test building definition queries."""
        # Build definition query
        params = {'term': 'deductible'}
        query = self.query_processor.build_graph_query('definition_inquiry', params)
        
        self.assertEqual(query['start_nodes'][0]['label'], 'Definition')
        
        # Check that query includes filters for the term
        has_term_filter = False
        for filter_group in query['filters']:
            if filter_group.get('operator') == 'OR':
                for condition in filter_group.get('conditions', []):
                    if condition.get('property') == 'term' and condition.get('value') == 'deductible':
                        has_term_filter = True
                        break
        
        self.assertTrue(has_term_filter)

if __name__ == '__main__':
    unittest.main()