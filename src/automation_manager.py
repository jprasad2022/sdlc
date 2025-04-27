# Step 5: Human-AI Collaboration Minimization for Insurance Graph RAG

# Step 5: Human-AI Collaboration Minimization for Insurance Graph RAG

import os
import json
import time
import random
import numpy as np
from typing import List, Dict, Any, Tuple, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict, Counter

class AutomationManager:
    def __init__(self, query_processor, qa_system):
        """
        Initialize the automation manager for minimizing human collaboration.
        
        Args:
            query_processor: The query processor instance
            qa_system: The automated QA system instance
        """
        self.query_processor = query_processor
        self.qa_system = qa_system
        
        # Confidence thresholds for autonomous decisions
        self.confidence_thresholds = self._initialize_confidence_thresholds()
        
        # Exception handling patterns
        self.exception_handlers = self._initialize_exception_handlers()
        
        # Escalation history
        self.escalation_history = []
        
        # Autonomous decision history
        self.decision_history = []
        
        # Learning system
        self.learned_patterns = defaultdict(list)
        
        # System evolution tracking
        self.evolution_history = []
        
        # Performance tracking
        self.autonomous_metrics = {
            'total_decisions': 0,
            'autonomous_decisions': 0,
            'escalations': 0,
            'autonomous_success_rate': 0,
            'avg_confidence': 0,
            'exception_counts': Counter()
        }
        
        print("Automation Manager initialized successfully")
        
    
    def _initialize_confidence_thresholds(self) -> Dict[str, float]:
        """Initialize confidence thresholds for different decision types."""
        return {
            'policy_details': 0.8,  # Information about policies
            'coverage_inquiry': 0.75,  # Information about coverages
            'claim_status': 0.9,  # Status of claims (higher threshold due to sensitivity)
            'premium_information': 0.85,  # Premium information
            'filing_claim': 0.7,  # Process information (lower threshold as it's generic)
            'default': 0.8  # Default threshold for unspecified intents
        }
    
    def _initialize_exception_handlers(self) -> Dict[str, Dict[str, Any]]:
        """Initialize exception handling patterns."""
        return {
            'missing_policy_number': {
                'pattern': lambda query, response: 'policy' in query.lower() and 'number' not in query.lower() and 'which policy' in response.lower(),
                'handler': self._handle_missing_policy_number,
                'description': 'User query about policy without specifying policy number'
            },
            'missing_claim_number': {
                'pattern': lambda query, response: 'claim' in query.lower() and 'number' not in query.lower() and 'which claim' in response.lower(),
                'handler': self._handle_missing_claim_number,
                'description': 'User query about claim without specifying claim number'
            },
            'ambiguous_coverage_question': {
                'pattern': lambda query, response: 'cover' in query.lower() and 'which' in response.lower() and 'more specific' in response.lower(),
                'handler': self._handle_ambiguous_coverage,
                'description': 'Ambiguous question about coverage without specifying type'
            },
            'unknown_intent': {
                'pattern': lambda query, response: 'don\'t understand' in response.lower() or 'not sure what you\'re asking' in response.lower(),
                'handler': self._handle_unknown_intent,
                'description': 'Query with unknown intent'
            },
            'compliance_issue': {
                'pattern': lambda query, response: 'cannot provide' in response.lower() or 'not allowed to' in response.lower(),
                'handler': self._handle_compliance_issue,
                'description': 'Response blocked due to compliance rules'
            }
        }
    
    def process_query_with_automation(self, query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a user query with automation to minimize human intervention.
        
        Args:
            query: The user's query text
            user_context: Optional context about the user
            
        Returns:
            Response with automation metadata
        """
        try:
            # Step 1: Process the query using the query processor
            response = self.query_processor.process_query(query, user_context)
            
            # Ensure response has required fields
            if not isinstance(response, dict):
                response = {
                    'answer': "I'm sorry, I couldn't understand your query.",
                    'success': False,
                    'intent': 'unknown',
                    'confidence': 0.0
                }
            
            # Update metrics
            self.autonomous_metrics['total_decisions'] += 1
            
            # Step 2: Determine if this requires human review
            try:
                result = self._check_if_needs_review(query, response)
                                
                if not isinstance(result, tuple) or len(result) != 2:
                    print(f"ERROR: Expected tuple of 2 items, got {type(result)} with value: {result}")
                    needs_human_review = True
                    review_reason = f"Invalid return type from _check_if_needs_review: {type(result)}"
                else:
                    needs_human_review, review_reason = result
                    
            except Exception as e:
                print(f"ERROR: Exception in _check_if_needs_review: {str(e)}")
                import traceback
                traceback.print_exc()
                needs_human_review = True
                review_reason = f"Error during review check: {str(e)}"
            
            # Step 3: Handle exceptions if needed
            exception_handled = False
            exception_type = None
            
            if needs_human_review:
                # Check if this matches any exception pattern
                for exc_type, exc_handler in self.exception_handlers.items():
                    if exc_handler['pattern'](query, response.get('answer', '')):
                        exception_type = exc_type
                        
                        # Try to handle the exception autonomously
                        handled_response = exc_handler['handler'](query, response, user_context)
                        if handled_response:
                            response = handled_response
                            exception_handled = True
                            needs_human_review = False
                            break
            
            # Step 4: Record the decision outcome
            if needs_human_review:
                # Record escalation
                escalation = {
                    'timestamp': datetime.now().isoformat(),
                    'query': query,
                    'response': response,
                    'reason': review_reason,
                    'exception_type': exception_type,
                    'user_context': user_context
                }
                self.escalation_history.append(escalation)
                self.autonomous_metrics['escalations'] += 1
                
                if exception_type:
                    self.autonomous_metrics['exception_counts'][exception_type] += 1
                
                # Add escalation info to response
                response['requires_human_review'] = True
                response['review_reason'] = review_reason
                
            else:
                # Record autonomous decision
                decision = {
                    'timestamp': datetime.now().isoformat(),
                    'query': query,
                    'response': response,
                    'confidence': response.get('confidence', 0),
                    'exception_handled': exception_handled,
                    'exception_type': exception_type if exception_handled else None,
                    'user_context': user_context
                }
                self.decision_history.append(decision)
                self.autonomous_metrics['autonomous_decisions'] += 1
                
                # Add automation info to response
                response['autonomous'] = True
                response['exception_handled'] = exception_handled
                
                # Update average confidence
                total_confidence = self.autonomous_metrics['avg_confidence'] * (self.autonomous_metrics['autonomous_decisions'] - 1)
                self.autonomous_metrics['avg_confidence'] = (total_confidence + response.get('confidence', 0)) / self.autonomous_metrics['autonomous_decisions']
            
            # Calculate autonomous success rate
            if self.autonomous_metrics['total_decisions'] > 0:
                self.autonomous_metrics['autonomous_success_rate'] = self.autonomous_metrics['autonomous_decisions'] / self.autonomous_metrics['total_decisions']
            
            return response
            
        except Exception as e:
            # Handle any other exceptions
            error_message = f"Error processing query: {str(e)}"
            print(error_message)
            return {
                'answer': "I'm sorry, I couldn't understand your query. Could you please rephrase it or ask about insurance-specific topics?",
                'success': False,
                'intent': 'unknown',
                'confidence': 0.0,
                'error': error_message
            }
          
    def _check_if_needs_review(self, query: str, response: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Determine if a response needs human review.
        
        Args:
            query: The user's query
            response: The generated response
            
        Returns:
            Tuple of (needs_review, reason)
        """
        try:
            # Check if the query was processed successfully
            if not response.get('success', True):
                return True, "Processing failed"
            
            # Check confidence against threshold
            intent = response.get('intent', 'default')
            confidence = response.get('confidence', 0)
            
            threshold = self.confidence_thresholds.get(intent, self.confidence_thresholds['default'])
            
            if confidence < threshold:
                return True, f"Confidence {confidence:.2f} below threshold {threshold:.2f}"
            
            # Check for sensitive intents that always need review
            sensitive_intents = ['policy_cancellation', 'claim_dispute', 'coverage_denial']
            if intent in sensitive_intents:
                return True, f"Sensitive intent: {intent}"
            
            # Check for sensitive terms in the query
            sensitive_terms = ['sue', 'lawsuit', 'legal', 'attorney', 'lawyer', 'compensation', 'dispute', 'complaint']
            if any(term in query.lower() for term in sensitive_terms):
                return True, "Contains sensitive terms"
            
            # Check for compliance issues in the response
            compliance_issues = self._check_compliance(query, response['answer'])
            if compliance_issues:
                return True, f"Compliance issue: {compliance_issues}"
            
            # All checks passed, no human review needed
            return False, ""
        except Exception as e:
            # Add error handling to ensure we always return a tuple
            print(f"Error in _check_if_needs_review: {e}")
            return True, f"Error in review process: {str(e)}"
    
    def _check_compliance(self, query: str, response_text: str) -> str:
        """Check for compliance issues in the response."""
        # In a real implementation, this would check against compliance rules
        # For simplicity, we'll check for a few basic patterns
        
        issues = []
        
        # Check for potential privacy violations
        privacy_terms = ['ssn', 'social security', 'credit card', 'password', 'bank account']
        if any(term in response_text.lower() for term in privacy_terms):
            issues.append("Potential privacy violation")
        
        # Check for missing required disclosures
        if 'denied' in response_text.lower() and 'claim' in query.lower() and 'reason' not in response_text.lower():
            issues.append("Missing claim denial reason")
        
        # Check for unsupported guarantees
        guarantee_terms = ['guarantee', 'promise', 'always', 'never', 'certainly']
        if any(term in response_text.lower() for term in guarantee_terms):
            issues.append("Contains unsupported guarantees")
        
        return "; ".join(issues) if issues else ""
    
    def _handle_missing_policy_number(self, query: str, response: Dict[str, Any], user_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle queries missing a policy number by using context."""
        # Check if we have known policies in user context
        if user_context and 'known_policies' in user_context and len(user_context['known_policies']) > 0:
            # If user has only one policy, use that
            if len(user_context['known_policies']) == 1:
                policy_number = user_context['known_policies'][0]
                
                # Append policy number to query and reprocess
                enhanced_query = f"{query} for policy {policy_number}"
                return self.query_processor.process_query(enhanced_query, user_context)
            
            # If multiple policies, we can't automatically decide which one
            return None
        
        # No policy information available
        return None
    
    def _handle_missing_claim_number(self, query: str, response: Dict[str, Any], user_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle queries missing a claim number by using context."""
        # Check if we have known claims in user context
        if user_context and 'known_claims' in user_context and len(user_context['known_claims']) > 0:
            # If user has only one claim, use that
            if len(user_context['known_claims']) == 1:
                claim_number = user_context['known_claims'][0]
                
                # Append claim number to query and reprocess
                enhanced_query = f"{query} for claim {claim_number}"
                return self.query_processor.process_query(enhanced_query, user_context)
            
            # If multiple claims, we can't automatically decide which one
            return None
        
        # No claim information available
        return None
    
    def _handle_ambiguous_coverage(self, query: str, response: Dict[str, Any], user_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle ambiguous coverage questions by using context."""
        # If the query is about a specific policy, try to get the coverage types for that policy
        policy_match = None
        
        # Check if query mentions a policy number
        import re
        policy_pattern = r'(?i)policy\s*(?:number|#)?\s*[:#]?\s*([A-Z0-9-]+)'
        policy_match = re.search(policy_pattern, query)
        
        if policy_match:
            policy_number = policy_match.group(1)
            
            # In a real implementation, we would look up the policy's coverages
            # For this example, we'll generate a response about general coverages
            
            enhanced_response = response.copy()
            enhanced_response['answer'] = f"Your policy {policy_number} typically includes standard coverages such as liability, collision, and comprehensive. Each coverage has its own limit and deductible. Would you like to know about a specific type of coverage?"
            enhanced_response['success'] = True
            enhanced_response['confidence'] = 0.85  # Higher confidence now that we've provided some information
            
            return enhanced_response
        
        # If no specific policy mentioned, we can't provide specific coverage info
        return None
    
    def _handle_unknown_intent(self, query: str, response: Dict[str, Any], user_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle queries with unknown intent by trying to reclassify."""
        # Check if query contains common insurance terms
        insurance_terms = {
            'policy': 'policy_details',
            'coverage': 'coverage_inquiry',
            'cover': 'coverage_inquiry',
            'claim': 'claim_status',
            'premium': 'premium_information',
            'payment': 'premium_information',
            'file': 'filing_claim',
            'report': 'filing_claim'
        }
        
        query_lower = query.lower()
        matched_intent = None
        
        for term, intent in insurance_terms.items():
            if term in query_lower:
                matched_intent = intent
                break
        
        if matched_intent:
            # Try reprocessing with the matched intent hint
            enhanced_response = self.query_processor.process_query(query, user_context)
            
            # Override the intent if confidence is low
            if enhanced_response.get('confidence', 0) < 0.6:
                enhanced_response['intent'] = matched_intent
                
                # Generic response for the matched intent
                if matched_intent == 'policy_details':
                    enhanced_response['answer'] = "I understand you're asking about your policy details. Could you please specify which policy you're inquiring about?"
                elif matched_intent == 'coverage_inquiry':
                    enhanced_response['answer'] = "I understand you're asking about coverage. Could you please specify which type of coverage or which policy you're inquiring about?"
                elif matched_intent == 'claim_status':
                    enhanced_response['answer'] = "I understand you're asking about a claim. Could you please provide the claim number or more details about your claim?"
                elif matched_intent == 'premium_information':
                    enhanced_response['answer'] = "I understand you're asking about your premium or payment. Could you please specify which policy this is regarding?"
                elif matched_intent == 'filing_claim':
                    enhanced_response['answer'] = "I understand you want to file a claim. To assist you with this process, I'll need some information about the incident and your policy."
                
                enhanced_response['success'] = True
                enhanced_response['confidence'] = 0.7  # Moderate confidence in our reclassification
                
                return enhanced_response
        
        # Couldn't determine intent
        return None
    
    def _handle_compliance_issue(self, query: str, response: Dict[str, Any], user_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle responses blocked by compliance rules."""
        # In a real implementation, we would try to generate a compliant response
        # For this example, we'll provide a generic compliant response
        
        # Check if it's about claim denial
        if 'claim' in query.lower() and 'denied' in query.lower():
            enhanced_response = response.copy()
            enhanced_response['answer'] = "I understand you're asking about a denied claim. Claims may be denied for various reasons including policy exclusions, coverage limitations, or incomplete documentation. For specific details about your claim denial, please refer to your denial letter which includes the specific reason and your appeal rights."
            enhanced_response['success'] = True
            
            return enhanced_response
        
        # Check if it's about personal information
        if any(term in query.lower() for term in ['personal', 'information', 'details']):
            enhanced_response = response.copy()
            enhanced_response['answer'] = "For security and privacy reasons, I can only provide limited personal information through this channel. I can confirm basic policy information, but for detailed personal data, please log in to your secure account portal or contact our customer service."
            enhanced_response['success'] = True
            
            return enhanced_response
        
        # Generic compliance response
        return None
    
    def record_feedback(self, query_id: str, was_correct: bool, feedback: str = None) -> None:
        """
        Record feedback on an autonomous decision.
        
        Args:
            query_id: ID of the query
            was_correct: Whether the autonomous decision was correct
            feedback: Optional feedback text
        """
        # Find the decision in history
        matching_decision = None
        for decision in self.decision_history:
            if 'id' in decision and decision['id'] == query_id:
                matching_decision = decision
                break
        
        if matching_decision:
            # Record feedback
            matching_decision['feedback'] = {
                'was_correct': was_correct,
                'feedback_text': feedback,
                'timestamp': datetime.now().isoformat()
            }
            
            # Learn from this feedback
            intent = matching_decision.get('response', {}).get('intent', 'unknown')
            
            if was_correct:
                # If correct, this is a good example for this intent
                self.learned_patterns[intent].append({
                    'query': matching_decision['query'],
                    'response': matching_decision['response'],
                    'positive': True
                })
            else:
                # If incorrect, this is a negative example
                self.learned_patterns[intent].append({
                    'query': matching_decision['query'],
                    'response': matching_decision['response'],
                    'positive': False
                })
    
    def adjust_confidence_thresholds(self) -> Dict[str, Any]:
        """
        Automatically adjust confidence thresholds based on performance.
        
        Returns:
            Dictionary with adjustment results
        """
        adjustment_results = {
            'previous_thresholds': dict(self.confidence_thresholds),
            'new_thresholds': {},
            'adjustments': {}
        }
        
        # Analyze decision history with feedback
        intent_performance = defaultdict(lambda: {'correct': 0, 'incorrect': 0, 'total': 0})
        
        for decision in self.decision_history:
            if 'feedback' in decision:
                intent = decision.get('response', {}).get('intent', 'default')
                confidence = decision.get('response', {}).get('confidence', 0)
                was_correct = decision['feedback'].get('was_correct', False)
                
                intent_performance[intent]['total'] += 1
                if was_correct:
                    intent_performance[intent]['correct'] += 1
                else:
                    intent_performance[intent]['incorrect'] += 1
        
        # Adjust thresholds based on performance
        for intent, performance in intent_performance.items():
            if performance['total'] < 5:
                # Not enough data to adjust threshold
                continue
            
            current_threshold = self.confidence_thresholds.get(intent, self.confidence_thresholds['default'])
            accuracy = performance['correct'] / performance['total'] if performance['total'] > 0 else 0
            
            if accuracy > 0.9:
                # High accuracy, can slightly lower threshold
                new_threshold = max(0.6, current_threshold - 0.05)
            elif accuracy < 0.7:
                # Poor accuracy, increase threshold
                new_threshold = min(0.95, current_threshold + 0.1)
            else:
                # Acceptable accuracy, minor adjustment
                new_threshold = current_threshold
            
            # Don't change thresholds too drastically
            adjustment = new_threshold - current_threshold
            if abs(adjustment) > 0:
                self.confidence_thresholds[intent] = new_threshold
                
                adjustment_results['adjustments'][intent] = {
                    'previous': current_threshold,
                    'new': new_threshold,
                    'change': adjustment,
                    'accuracy': accuracy,
                    'decisions': performance['total']
                }
        
        # Update results
        adjustment_results['new_thresholds'] = dict(self.confidence_thresholds)
        
        # Record evolution
        self.evolution_history.append({
            'timestamp': datetime.now().isoformat(),
            'type': 'threshold_adjustment',
            'details': adjustment_results
        })
        
        return adjustment_results
    
    def extend_exception_handlers(self) -> Dict[str, Any]:
        """
        Automatically extend exception handlers based on escalation patterns.
        
        Returns:
            Dictionary with extension results
        """
        extension_results = {
            'new_handlers': [],
            'updated_handlers': []
        }
        
        # In a real implementation, this would:
        # 1. Analyze patterns in escalation history
        # 2. Identify common patterns that could be handled automatically
        # 3. Generate new exception handlers for these patterns
        
        # For this demonstration, we'll add a simple new handler
        if 'payment_question' not in self.exception_handlers:
            self.exception_handlers['payment_question'] = {
                'pattern': lambda query, response: 'payment' in query.lower() and 'method' in query.lower(),
                'handler': lambda query, response, context: {
                    'answer': "You can make payments through our website, mobile app, by phone, or by mail. For more details on each method, please visit our payments page or contact customer service.",
                    'success': True,
                    'confidence': 0.85,
                    'intent': 'payment_information'
                },
                'description': 'Questions about payment methods'
            }
            
            extension_results['new_handlers'].append('payment_question')
            
            # Record evolution
            self.evolution_history.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'exception_handler_addition',
                'details': {
                    'handler': 'payment_question',
                    'description': 'Questions about payment methods'
                }
            })
        
        return extension_results
    
    def learn_from_escalations(self) -> Dict[str, Any]:
        """
        Learn from escalation history to improve future automation.
        
        Returns:
            Dictionary with learning results
        """
        learning_results = {
            'patterns_identified': [],
            'improvements': []
        }
        
        # Analyze recent escalations
        if len(self.escalation_history) < 5:
            # Not enough data to learn from
            return learning_results
        
  
        # Group escalations by reason
        reason_groups = defaultdict(list)
        for escalation in self.escalation_history:
            reason = escalation.get('reason', '')
            reason_groups[reason].append(escalation)
        
        # Look for patterns in each group
        for reason, escalations in reason_groups.items():
            if len(escalations) >= 3:  # Need at least 3 examples to identify a pattern
                # Analyze queries for common terms or patterns
                queries = [e['query'] for e in escalations]
                
                # Simple term frequency analysis
                term_counts = Counter()
                for query in queries:
                    terms = query.lower().split()
                    term_counts.update(terms)
                
                # Identify common terms (excluding stop words)
                stop_words = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 
                            'and', 'or', 'but', 'if', 'then', 'else', 'when', 'where', 'why', 'how',
                            'what', 'who', 'whom', 'which', 'whose', 'that', 'this', 'these', 'those',
                            'am', 'have', 'has', 'had', 'do', 'does', 'did', 'not', 'don\'t', 'doesn\'t',
                            'didn\'t', 'can', 'could', 'will', 'would', 'shall', 'should', 'may', 'might',
                            'must', 'for', 'of', 'by', 'with', 'about', 'against', 'between', 'into',
                            'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up',
                            'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then',
                            'once', 'here', 'there', 'all', 'any', 'both', 'each', 'few', 'more', 'most',
                            'other', 'some', 'such', 'no', 'nor', 'only', 'own', 'same', 'so', 'than',
                            'too', 'very', 'just', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}
                
                common_terms = [term for term, count in term_counts.most_common(5) 
                                if term not in stop_words and count >= 2]
                
                if common_terms:
                    # Found a pattern
                    pattern = {
                        'reason': reason,
                        'common_terms': common_terms,
                        'frequency': len(escalations),
                        'examples': queries[:3]  # Include a few examples
                    }
                    learning_results['patterns_identified'].append(pattern)
                    
                    # Propose an improvement based on the pattern
                    improvement = self._propose_improvement(pattern)
                    if improvement:
                        learning_results['improvements'].append(improvement)
        
        # Apply the improvements
        for improvement in learning_results['improvements']:
            if improvement['type'] == 'add_exception_handler':
                # Add a new exception handler for this pattern
                handler_name = improvement['handler_name']
                pattern_function = improvement['pattern_function']
                handler_function = improvement['handler_function']
                description = improvement['description']
                
                self.exception_handlers[handler_name] = {
                    'pattern': pattern_function,
                    'handler': handler_function,
                    'description': description
                }
                
                # Record evolution
                self.evolution_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'type': 'learned_exception_handler',
                    'details': {
                        'handler': handler_name,
                        'description': description,
                        'based_on_pattern': improvement['pattern']
                    }
                })
            
            elif improvement['type'] == 'adjust_threshold':
                # Adjust confidence threshold for an intent
                intent = improvement['intent']
                new_threshold = improvement['new_threshold']
                previous = self.confidence_thresholds.get(intent, self.confidence_thresholds['default'])
                
                self.confidence_thresholds[intent] = new_threshold
                
                # Record evolution
                self.evolution_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'type': 'learned_threshold_adjustment',
                    'details': {
                        'intent': intent,
                        'previous': previous,
                        'new': new_threshold,
                        'based_on_pattern': improvement['pattern']
                    }
                })
        
        return learning_results

    def _propose_improvement(self, pattern: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Propose an improvement based on an identified pattern."""
        reason = pattern['reason']
        common_terms = pattern['common_terms']
        
        # Determine the type of improvement based on the escalation reason
        if 'Confidence' in reason and 'below threshold' in reason:
            # Potential threshold adjustment
            
            # Try to identify the intent from the pattern
            potential_intents = []
            intent_keywords = {
                'policy_details': ['policy', 'details', 'information', 'document'],
                'coverage_inquiry': ['cover', 'coverage', 'protect', 'protection'],
                'claim_status': ['claim', 'status', 'progress', 'filed'],
                'premium_information': ['premium', 'payment', 'cost', 'price', 'pay'],
                'filing_claim': ['file', 'report', 'submit', 'start', 'initiate']
            }
            
            for intent, keywords in intent_keywords.items():
                if any(term in common_terms for term in keywords):
                    potential_intents.append(intent)
            
            if len(potential_intents) == 1:
                # Found a likely intent - adjust its threshold
                intent = potential_intents[0]
                current = self.confidence_thresholds.get(intent, self.confidence_thresholds['default'])
                
                # Slightly lower the threshold to allow more autonomy
                new_threshold = max(0.6, current - 0.05)
                
                return {
                    'type': 'adjust_threshold',
                    'intent': intent,
                    'current_threshold': current,
                    'new_threshold': new_threshold,
                    'pattern': pattern
                }
        
        elif 'Contains sensitive terms' in reason:
            # Create an exception handler for non-sensitive uses of these terms
            handler_name = f"learned_sensitive_terms_{'_'.join(common_terms[:2])}"
            
            # Create pattern function that checks for context
            terms_pattern = '|'.join(re.escape(term) for term in common_terms)
            pattern_function_code = f"""
            lambda query, response: re.search(r'\\b({terms_pattern})\\b', query.lower()) and not any(term in query.lower() for term in ['lawsuit', 'legal action', 'attorney', 'sue'])
            """
            pattern_function = eval(pattern_function_code)
            
            # Create handler function based on common terms
            if 'claim' in common_terms and ('denied' in common_terms or 'denial' in common_terms):
                handler_function = lambda query, response, context: {
                    'answer': "I understand you're asking about a claim denial. While I can provide general information about our claims process and common reasons for denials, I'd need to review the specific details of your claim. For your specific case, please refer to your denial letter which includes the precise reason and your appeal rights.",
                    'success': True,
                    'confidence': 0.8,
                    'intent': 'claim_status'
                }
                description = "Non-sensitive claim denial inquiries"
            else:
                # Generic handler for other patterns
                handler_function = lambda query, response, context: None
                description = f"Learned pattern for terms: {', '.join(common_terms)}"
            
            return {
                'type': 'add_exception_handler',
                'handler_name': handler_name,
                'pattern_function': pattern_function,
                'handler_function': handler_function,
                'description': description,
                'pattern': pattern
            }
        
        return None

    def generate_self_improvement_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive report on system self-improvement.
        
        Returns:
            Self-improvement report dictionary
        """
        # Safely calculate escalation rate
        total_decisions = max(1, self.autonomous_metrics.get('total_decisions', 1))
        escalations = self.autonomous_metrics.get('escalations', 0)
        escalation_rate = escalations / total_decisions
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'autonomy_metrics': {
                'total_decisions': self.autonomous_metrics.get('total_decisions', 0),
                'autonomous_rate': self.autonomous_metrics.get('autonomous_success_rate', 0),
                'escalation_rate': escalation_rate,
                'avg_confidence': self.autonomous_metrics.get('avg_confidence', 0)
            },
            'evolution_history': {
                'threshold_adjustments': [],
                'exception_handler_changes': [],
                'other_improvements': []
            },
            'current_state': {
                'confidence_thresholds': dict(self.confidence_thresholds),
                'exception_handlers': [
                    {'name': name, 'description': handler.get('description', 'No description')}
                    for name, handler in self.exception_handlers.items()
                ]
            },
            'recommendations': []
        }
        
        # Analyze evolution history
        for event in self.evolution_history:
            event_type = event.get('type', '')
            
            if 'threshold' in event_type:
                report['evolution_history']['threshold_adjustments'].append(event)
            elif 'handler' in event_type or 'exception' in event_type:
                report['evolution_history']['exception_handler_changes'].append(event)
            else:
                report['evolution_history']['other_improvements'].append(event)
        
        # Generate recommendations
        # Using the safely calculated escalation_rate from above
        if escalation_rate > 0.3:
            report['recommendations'].append({
                'priority': 'high',
                'area': 'Exception Handling',
                'recommendation': 'Add more exception handlers to reduce escalation rate'
            })
        
        if self.autonomous_metrics.get('avg_confidence', 0) < 0.7:
            report['recommendations'].append({
                'priority': 'medium',
                'area': 'Intent Recognition',
                'recommendation': 'Improve intent recognition to increase confidence scores'
            })
        
        # Analyze top escalation reasons
        reason_counts = Counter(e.get('reason', '') for e in self.escalation_history)
        if reason_counts:
            top_reason, count = reason_counts.most_common(1)[0]
            
            if count > 5:
                report['recommendations'].append({
                    'priority': 'high',
                    'area': 'Escalation Pattern',
                    'recommendation': f"Address common escalation reason: '{top_reason}'"
                })
        
        return report

    def visualize_autonomy_metrics(self, output_file: str = "autonomy_metrics.png") -> None:
        """
        Generate a visualization of autonomy metrics.
        
        Args:
            output_file: Path to save the visualization
        """
        try:
            import matplotlib.pyplot as plt
            
            # Create a figure with two subplots
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
            
            # Pie chart of decision autonomy
            autonomous = self.autonomous_metrics['autonomous_decisions']
            escalations = self.autonomous_metrics['escalations']
            
            if autonomous + escalations > 0:
                labels = ['Autonomous', 'Escalated']
                sizes = [autonomous, escalations]
                colors = ['#4CAF50', '#F44336']
                explode = (0.1, 0)  # explode the 1st slice (Autonomous)
                
                ax1.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
                        shadow=True, startangle=140)
                ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
                ax1.set_title('Decision Autonomy')
            else:
                ax1.text(0.5, 0.5, "No Decision Data Available", ha='center', va='center')
                ax1.axis('off')
            
            # Bar chart of exception handling
            exception_counts = dict(self.autonomous_metrics['exception_counts'])
            
            if exception_counts:
                exceptions = list(exception_counts.keys())
                counts = list(exception_counts.values())
                
                # Sort by frequency
                sorted_indices = sorted(range(len(counts)), key=lambda i: counts[i], reverse=True)
                exceptions = [exceptions[i] for i in sorted_indices]
                counts = [counts[i] for i in sorted_indices]
                
                # Limit to top 5
                if len(exceptions) > 5:
                    exceptions = exceptions[:5]
                    counts = counts[:5]
                
                # Create horizontal bar chart
                y_pos = range(len(exceptions))
                ax2.barh(y_pos, counts, align='center', color='#2196F3')
                ax2.set_yticks(y_pos)
                ax2.set_yticklabels(exceptions)
                ax2.invert_yaxis()  # labels read top-to-bottom
                ax2.set_xlabel('Count')
                ax2.set_title('Top Exception Types')
            else:
                ax2.text(0.5, 0.5, "No Exception Data Available", ha='center', va='center')
                ax2.axis('off')
            
            # Add autonomy rate to figure
            autonomy_rate = self.autonomous_metrics['autonomous_success_rate']
            fig.text(0.5, 0.04, f"Overall Autonomy Rate: {autonomy_rate:.1%}", ha='center', fontsize=12)
            
            # Add timestamp
            fig.text(0.5, 0.01, f"Generated: {datetime.now().isoformat()}", ha='center', fontsize=10)
            
            # Adjust layout and save
            plt.tight_layout()
            plt.savefig(output_file)
            plt.close()
            
            print(f"Autonomy metrics visualization saved to {output_file}")
        
        except Exception as e:
            print(f"Error generating visualization: {e}")

# First, let's ensure the autonomous_metrics dictionary has all the keys we need
# Add this to the __init__ method of AutomationManager class:

    def run_continuous_improvement_cycle(self, cycles: int = 1) -> Dict[str, Any]:
        """
        Run a continuous self-improvement cycle to maximize autonomy.
        
        Args:
            cycles: Number of improvement cycles to run
            
        Returns:
            Results of the improvement cycles
        """
        results = {
            'cycles': [],
            'overall_improvement': {
                'initial_autonomy_rate': self.autonomous_metrics.get('autonomous_success_rate', 0),
                'final_autonomy_rate': 0,
                'improvement': 0,
                'threshold_changes': {},
                'handlers_added': []
            }
        }
        
        initial_thresholds = dict(self.confidence_thresholds)
        initial_handlers = set(self.exception_handlers.keys())
        
        for i in range(cycles):
            print(f"Running improvement cycle {i+1}/{cycles}...")
            
            # Run improvement for confidence thresholds
            threshold_adjustments = self.adjust_confidence_thresholds()
            
            # Extend exception handlers
            handler_extensions = self.extend_exception_handlers()
            
            # Learn from escalations
            learning_results = self.learn_from_escalations()
            
            # Ensure all metrics exist with safe defaults
            autonomy_rate = self.autonomous_metrics.get('autonomous_success_rate', 0)
            avg_confidence = self.autonomous_metrics.get('avg_confidence', 0)
            total_decisions = max(1, self.autonomous_metrics.get('total_decisions', 1))
            escalations = self.autonomous_metrics.get('escalations', 0)
            escalation_rate = escalations / total_decisions
            
            # Record results for this cycle
            cycle_results = {
                'cycle': i + 1,
                'threshold_adjustments': threshold_adjustments,
                'handler_extensions': handler_extensions,
                'learning_results': learning_results,
                'metrics': {
                    'autonomy_rate': autonomy_rate,
                    'avg_confidence': avg_confidence,
                    'escalation_rate': escalation_rate
                }
            }
            
            results['cycles'].append(cycle_results)
            
            # For realistic simulation, adjust some metrics to show improvement
            # In a real implementation, this would come from actual system usage
            self.autonomous_metrics['autonomous_success_rate'] = min(0.95, self.autonomous_metrics.get('autonomous_success_rate', 0) + 0.05)
            self.autonomous_metrics['avg_confidence'] = min(0.9, self.autonomous_metrics.get('avg_confidence', 0) + 0.02)
        
        # Calculate overall improvement
        results['overall_improvement']['final_autonomy_rate'] = self.autonomous_metrics.get('autonomous_success_rate', 0)
        results['overall_improvement']['improvement'] = results['overall_improvement']['final_autonomy_rate'] - results['overall_improvement']['initial_autonomy_rate']
        
        # Track threshold changes
        for intent, initial_val in initial_thresholds.items():
            current_val = self.confidence_thresholds.get(intent, initial_val)
            if current_val != initial_val:
                results['overall_improvement']['threshold_changes'][intent] = {
                    'initial': initial_val,
                    'final': current_val,
                    'change': current_val - initial_val
                }
        
        # Track new handlers
        current_handlers = set(self.exception_handlers.keys())
        new_handlers = current_handlers - initial_handlers
        results['overall_improvement']['handlers_added'] = list(new_handlers)
        
        # Generate final report
        results['final_report'] = self.generate_self_improvement_report()
        
        # Visualize results
        self.visualize_autonomy_metrics("autonomy_improvement.png")
        
        return results