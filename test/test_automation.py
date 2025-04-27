import unittest
from unittest.mock import patch, MagicMock
import sys
sys.path.append('../')  # Add parent directory to path

from src.automation_manager import AutomationManager

class TestAutomationManager(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        # Create mock dependencies
        self.mock_query_processor = MagicMock()
        self.mock_qa_system = MagicMock()
        
        # Initialize the automation manager with mocks
        self.automation_manager = AutomationManager(
            self.mock_query_processor,
            self.mock_qa_system
        )
    
    def test_confidence_thresholds_initialization(self):
        """Test that confidence thresholds are properly initialized."""
        thresholds = self.automation_manager.confidence_thresholds
        
        # Check that default thresholds exist
        self.assertIn('policy_details', thresholds)
        self.assertIn('coverage_inquiry', thresholds)
        self.assertIn('claim_status', thresholds)
        self.assertIn('premium_information', thresholds)
        self.assertIn('filing_claim', thresholds)
        self.assertIn('default', thresholds)
        
        # Check some specific values
        self.assertGreater(thresholds['claim_status'], thresholds['filing_claim'])
        self.assertEqual(thresholds['default'], 0.8)
    
    def test_check_if_needs_review_high_confidence(self):
        """Test that high confidence queries pass without review."""
        # Create a high confidence response
        query = "What are the details of my policy P1001?"
        response = {
            'intent': 'policy_details',
            'confidence': 0.95,
            'success': True,
            'answer': 'Your policy P1001 is an auto insurance policy...'
        }
        
        # Check if needs review
        needs_review, reason = self.automation_manager._check_if_needs_review(query, response)
        
        # Should not need review (confidence > threshold)
        self.assertFalse(needs_review)
        self.assertEqual(reason, "")
    
    def test_check_if_needs_review_low_confidence(self):
        """Test that low confidence queries get flagged for review."""
        # Create a low confidence response
        query = "What are the details of my policy P1001?"
        response = {
            'intent': 'policy_details',
            'confidence': 0.6,  # Below threshold
            'success': True,
            'answer': 'Your policy P1001 is an auto insurance policy...'
        }
        
        # Check if needs review
        needs_review, reason = self.automation_manager._check_if_needs_review(query, response)
        
        # Should need review (confidence < threshold)
        self.assertTrue(needs_review)
        self.assertIn("Confidence", reason)
        self.assertIn("below threshold", reason)
    
    def test_check_if_needs_review_sensitive_terms(self):
        """Test that queries with sensitive terms get flagged for review."""
        # Create a query with sensitive terms
        query = "I want to sue my insurance company because they denied my claim"
        response = {
            'intent': 'claim_status',
            'confidence': 0.9,
            'success': True,
            'answer': 'I understand your frustration...'
        }
        
        # Check if needs review
        needs_review, reason = self.automation_manager._check_if_needs_review(query, response)
        
        # Should need review (contains sensitive terms)
        self.assertTrue(needs_review)
        self.assertIn("sensitive terms", reason.lower())
    
    def test_process_query_with_automation_autonomous(self):
        """Test processing a query that can be handled autonomously."""
        # Set up mock query processor
        self.mock_query_processor.process_query.return_value = {
            'intent': 'policy_details',
            'confidence': 0.95,
            'success': True,
            'answer': 'Your policy P1001 is an auto insurance policy...'
        }
        
        # Process a query
        query = "What are the details of my policy P1001?"
        user_context = {'user_id': 'U5001'}
        
        response = self.automation_manager.process_query_with_automation(query, user_context)
        
        # Check that query processor was called
        self.mock_query_processor.process_query.assert_called_once_with(query, user_context)
        
        # Check response
        self.assertTrue(response.get('autonomous', False))
        self.assertFalse(response.get('requires_human_review', False))
        
        # Check metrics
        self.assertEqual(self.automation_manager.autonomous_metrics['autonomous_decisions'], 1)
        self.assertEqual(self.automation_manager.autonomous_metrics['escalations'], 0)
    
    def test_process_query_with_automation_escalation(self):
        """Test processing a query that requires human review."""
        # Set up mock query processor
        self.mock_query_processor.process_query.return_value = {
            'intent': 'policy_details',
            'confidence': 0.6,  # Below threshold
            'success': True,
            'answer': 'Your policy P1001 is an auto insurance policy...'
        }
        
        # Process a query
        query = "What are the details of my policy P1001?"
        user_context = {'user_id': 'U5001'}
        
        response = self.automation_manager.process_query_with_automation(query, user_context)
        
        # Check response
        self.assertTrue(response.get('requires_human_review', False))
        self.assertFalse(response.get('autonomous', False))
        self.assertIn('review_reason', response)
        
        # Check metrics
        self.assertEqual(self.automation_manager.autonomous_metrics['autonomous_decisions'], 0)
        self.assertEqual(self.automation_manager.autonomous_metrics['escalations'], 1)
    
    def test_handle_missing_policy_number(self):
        """Test handling a query missing a policy number."""
        # Set up query, response, and context with a single policy
        query = "What are the details of my policy?"
        response = {
            'intent': 'policy_details',
            'confidence': 0.9,
            'success': False,
            'answer': 'I need a policy number to provide policy details.'
        }
        user_context = {
            'user_id': 'U5001',
            'known_policies': ['P1001']  # Only one policy
        }
        
        # Set up mock for enhanced query
        enhanced_response = {
            'intent': 'policy_details',
            'confidence': 0.9,
            'success': True,
            'answer': 'Your policy P1001 is an auto insurance policy...'
        }
        self.mock_query_processor.process_query.return_value = enhanced_response
        
        # Handle the exception
        handled_response = self.automation_manager._handle_missing_policy_number(
            query, response, user_context
        )
        
        # Check that the handler was able to resolve the issue
        self.assertIsNotNone(handled_response)
        self.assertEqual(handled_response, enhanced_response)
        
        # Check that query processor was called with the enhanced query
        self.mock_query_processor.process_query.assert_called_once()
        args, _ = self.mock_query_processor.process_query.call_args
        self.assertIn('P1001', args[0])  # Policy number added to query
    
    def test_handle_missing_policy_number_multiple_policies(self):
        """Test handling a query missing a policy number with multiple policies."""
        # Set up query, response, and context with multiple policies
        query = "What are the details of my policy?"
        response = {
            'intent': 'policy_details',
            'confidence': 0.9,
            'success': False,
            'answer': 'I need a policy number to provide policy details.'
        }
        user_context = {
            'user_id': 'U5001',
            'known_policies': ['P1001', 'P1002']  # Multiple policies
        }
        
        # Handle the exception
        handled_response = self.automation_manager._handle_missing_policy_number(
            query, response, user_context
        )
        
        # Check that the handler couldn't resolve the issue (can't decide which policy)
        self.assertIsNone(handled_response)
    
    def test_adjust_confidence_thresholds(self):
        """Test adjusting confidence thresholds based on performance."""
        # Add some decision history with feedback
        self.automation_manager.decision_history.extend([
            {
                'query': 'What are the details of my policy P1001?',
                'response': {'intent': 'policy_details', 'confidence': 0.85},
                'feedback': {'was_correct': True}
            },
            {
                'query': 'What are the details of my policy P1002?',
                'response': {'intent': 'policy_details', 'confidence': 0.82},
                'feedback': {'was_correct': True}
            },
            {
                'query': 'What are the details of my policy P1003?',
                'response': {'intent': 'policy_details', 'confidence': 0.81},
                'feedback': {'was_correct': True}
            },
            {
                'query': 'What are the details of my policy P1004?',
                'response': {'intent': 'policy_details', 'confidence': 0.80},
                'feedback': {'was_correct': True}
            },
            {
                'query': 'What are the details of my policy P1005?',
                'response': {'intent': 'policy_details', 'confidence': 0.79},
                'feedback': {'was_correct': True}
            }
        ])
        
        # Store original threshold
        original_threshold = self.automation_manager.confidence_thresholds['policy_details']
        
        # Adjust thresholds
        adjustment_results = self.automation_manager.adjust_confidence_thresholds()
        
        # Check results
        self.assertIn('policy_details', adjustment_results['adjustments'])
        
        # Check that threshold was lowered due to good performance
        new_threshold = self.automation_manager.confidence_thresholds['policy_details']
        self.assertLess(new_threshold, original_threshold)
        
        # Add some negative feedback
        self.automation_manager.decision_history.extend([
            {
                'query': 'What does my policy cover?',
                'response': {'intent': 'coverage_inquiry', 'confidence': 0.75},
                'feedback': {'was_correct': False}
            },
            {
                'query': 'What coverages do I have?',
                'response': {'intent': 'coverage_inquiry', 'confidence': 0.73},
                'feedback': {'was_correct': False}
            },
            {
                'query': 'Am I covered for water damage?',
                'response': {'intent': 'coverage_inquiry', 'confidence': 0.72},
                'feedback': {'was_correct': False}
            }
        ])
        
        # Store original threshold
        original_threshold = self.automation_manager.confidence_thresholds['coverage_inquiry']
        
        # Adjust thresholds again
        adjustment_results = self.automation_manager.adjust_confidence_thresholds()
        
        # Check results
        self.assertIn('coverage_inquiry', adjustment_results['adjustments'])
        
        # Check that threshold was increased due to poor performance
        new_threshold = self.automation_manager.confidence_thresholds['coverage_inquiry']
        self.assertGreater(new_threshold, original_threshold)
    
    def test_learn_from_escalations(self):
        """Test learning from escalation history."""
        # Add some escalation history
        self.automation_manager.escalation_history.extend([
            {
                'query': 'What is my deductible?',
                'response': {'answer': 'I need to know which policy you are referring to.'},
                'reason': 'Confidence below threshold',
                'user_context': {'user_id': 'U5001'}
            },
            {
                'query': 'How much is my deductible?',
                'response': {'answer': 'I need to know which policy you are referring to.'},
                'reason': 'Confidence below threshold',
                'user_context': {'user_id': 'U5001'}
            },
            {
                'query': 'Tell me about my deductible',
                'response': {'answer': 'I need to know which policy you are referring to.'},
                'reason': 'Confidence below threshold',
                'user_context': {'user_id': 'U5001'}
            }
        ])
        
        # Learn from escalations
        learning_results = self.automation_manager.learn_from_escalations()
        
        # Check results
        self.assertGreater(len(learning_results['patterns_identified']), 0)
        
        # Check that a pattern involving 'deductible' was identified
        deductible_pattern = False
        for pattern in learning_results['patterns_identified']:
            if any('deductible' in term for term in pattern.get('common_terms', [])):
                deductible_pattern = True
                break
        
        self.assertTrue(deductible_pattern)
        
        # Check that there are improvement suggestions
        self.assertGreater(len(learning_results['improvements']), 0)

if __name__ == '__main__':
    unittest.main()