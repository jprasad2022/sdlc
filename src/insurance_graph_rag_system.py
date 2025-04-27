# Step 6: System Integration and Demo for Fully Automated Insurance Graph RAG

import os
import json
import time
import random
import argparse
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from pathlib import Path

# Import all components
from src.insurance_document_processor import InsuranceDocumentProcessor
from src.self_evolving_graph_schema import SelfEvolvingGraphSchema
from src.enhanced_query_processor import EnhancedGraphRAGQueryProcessor
from src.automated_qa_system import AutomatedQASystem
from src.automation_manager import AutomationManager

class InsuranceGraphRAGSystem:
    def __init__(self, config_path: str = None):
        """
        Initialize the complete Insurance Graph RAG System.
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Setup logging
        self._setup_logging()
        
        # Initialize components
        self.document_processor = self._init_document_processor()
        self.schema_manager = self._init_schema_manager()
        self.query_processor = self._init_query_processor()
        self.qa_system = self._init_qa_system()
        self.automation_manager = self._init_automation_manager()
        
        # System state
        self.is_initialized = False
        self.system_metrics = {
            'documents_processed': 0,
            'schema_updates': 0,
            'queries_processed': 0,
            'tests_executed': 0,
            'autonomous_decisions': 0
        }
        
        self.logger.info("Insurance Graph RAG System initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load system configuration."""
        default_config = {
            'data_dir': 'data',
            'output_dir': 'output',
            'logging': {
                'level': 'INFO',
                'file': 'insurance_rag_system.log'
            },
            'components': {
                'document_processor': {
                    'model_name': 'sentence-transformers/all-mpnet-base-v2'
                },
                'schema_manager': {
                    'base_schema_path': None
                },
                'query_processor': {
                    'model_name': 'sentence-transformers/all-mpnet-base-v2'
                },
                'qa_system': {
                    'test_count': 10
                },
                'automation_manager': {
                    'default_threshold': 0.8
                }
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    
                # Merge with default config
                for section, settings in loaded_config.items():
                    if section in default_config and isinstance(default_config[section], dict):
                        default_config[section].update(settings)
                    else:
                        default_config[section] = settings
                
                print(f"Configuration loaded from {config_path}")
                
            except Exception as e:
                print(f"Error loading configuration: {e}")
                print("Using default configuration")
        else:
            print("Using default configuration")
        
        # Create required directories
        os.makedirs(default_config['data_dir'], exist_ok=True)
        os.makedirs(default_config['output_dir'], exist_ok=True)
        
        return default_config
    
    def _setup_logging(self) -> None:
        """Setup system logging."""
        import logging
        
        log_config = self.config['logging']
        log_level = getattr(logging, log_config['level'])
        log_file = os.path.join(self.config['output_dir'], log_config['file'])
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('InsuranceGraphRAG')
        self.logger.info("Logging initialized")
    
    def _init_document_processor(self) -> InsuranceDocumentProcessor:
        """Initialize the document processor component."""
        config = self.config['components']['document_processor']
        
        document_processor = InsuranceDocumentProcessor(
            model_name=config.get('model_name', 'gpt-4o-mini')
        )
        
        self.logger.info("Document processor initialized")
        return document_processor
    
    def _init_schema_manager(self) -> SelfEvolvingGraphSchema:
        """Initialize the schema manager component."""
        config = self.config['components']['schema_manager']
        base_schema_path = config.get('base_schema_path')
        
        schema_manager = SelfEvolvingGraphSchema(
            base_schema_path=base_schema_path
        )
        
        self.logger.info("Schema manager initialized")
        return schema_manager
    
    def _init_query_processor(self) -> EnhancedGraphRAGQueryProcessor:
        """Initialize the query processor component."""
        config = self.config['components']['query_processor']
        
        # Paths for schema and knowledge graph
        schema_path = os.path.join(self.config['output_dir'], 'insurance_schema.json')
        knowledge_graph_path = os.path.join(self.config['output_dir'], 'insurance_knowledge_graph.json')
        
        # Check if files exist
        if not os.path.exists(schema_path):
            schema_path = None
        
        if not os.path.exists(knowledge_graph_path):
            knowledge_graph_path = None
        
        query_processor = EnhancedGraphRAGQueryProcessor(
            schema_path=schema_path,
            knowledge_graph_path=knowledge_graph_path,
            model_name=config.get('model_name', 'sentence-transformers/all-mpnet-base-v2')
        )
        
        self.logger.info("Query processor initialized")
        return query_processor
    
    def _init_qa_system(self) -> AutomatedQASystem:
        """Initialize the QA system component."""
        qa_system = AutomatedQASystem(
            query_processor=self.query_processor,
            schema_manager=self.schema_manager,
            knowledge_graph_path=os.path.join(self.config['output_dir'], 'insurance_knowledge_graph.json')
        )
        
        self.logger.info("QA system initialized")
        return qa_system
    
    def _init_automation_manager(self) -> AutomationManager:
        """Initialize the automation manager component."""
        config = self.config['components']['automation_manager']
        
        automation_manager = AutomationManager(
            query_processor=self.query_processor,
            qa_system=self.qa_system
        )
        
        # Update default threshold if configured
        if 'default_threshold' in config:
            automation_manager.confidence_thresholds['default'] = config['default_threshold']
        
        self.logger.info("Automation manager initialized")
        return automation_manager
    
    def _evolve_schema(self, kg_path: Path, threshold: float = 0.6) -> bool:
        """Load the graph, evolve schema, export JSON + visualization."""
        self.logger.info("Evolving schema...")
        if not kg_path.exists():
            self.logger.warning(f"Knowledge graph not found at {kg_path}")
            return False

        with kg_path.open('r', encoding='utf-8') as f:
            instance_data = json.load(f)

        # Evolve & export
        changes = self.schema_manager.evolve_schema(instance_data, threshold=threshold)
        schema_path = Path(self.config['output_dir']) / 'insurance_schema.json'
        vis_path    = Path(self.config['output_dir']) / 'schema_visualization.png'

        self.schema_manager.export_schema(str(schema_path))
        self.schema_manager.generate_visualization(str(vis_path))

        self.logger.info(f"Schema evolved and saved to {schema_path}")
        self.system_metrics['schema_updates'] += 1
        return True

    def initialize_system(self, sources: List[str] = None) -> Dict[str, Any]:
        start_time = time.time()
        results = {
            'success': False,
            'documents_processed': 0,
            'schema_updated': False,
            'knowledge_graph_created': False,
            'elapsed_time': 0
        }

        try:
            self.logger.info("Starting system initialization")

            # ── Step 1: Crawl & process documents ─────────────────────────────
            data_dir = Path(self.config['data_dir'])
            sources = sources or [str(data_dir)]
            self.logger.info(f"Using source directories: {sources}")

            self.logger.info("Step 1: Processing documents…")
            doc_paths = self.document_processor.crawl_documents(sources)

            kg_path = Path(self.config['output_dir']) / 'insurance_knowledge_graph.json'
            if doc_paths:
                _ = self.document_processor.process_document_batch(doc_paths)
                results['documents_processed'] = len(doc_paths)
                self.system_metrics['documents_processed'] = len(doc_paths)

                self.document_processor.export_to_graph_format(str(kg_path))
                self.logger.info(f"Knowledge graph exported to {kg_path}")
                results['knowledge_graph_created'] = True
            else:
                self.logger.warning("No documents found or processed")

            # ── Step 2: Schema evolution ───────────────────────────────────────
            results['schema_updated'] = self._evolve_schema(kg_path)

            # ── Step 3: Reinitialize query processor with updated schema ─────
            self.logger.info("Step 3: Reinitializing query processor…")
            self.query_processor = self._init_query_processor()

            # ── Step 4: Initial QA tests ─────────────────────────────────────
            self.logger.info("Step 4: Running initial QA tests…")
            test_count = self.config['components']['qa_system'].get('test_count', 10)
            test_results = self.qa_system.run_test_suite(count=test_count)

            # Persist & visualize QA results
            out_dir = Path(self.config['output_dir'])
            (out_dir / 'initial_test_results.json').write_text(
                json.dumps(test_results, indent=2), encoding='utf-8'
            )
            self.qa_system.visualize_test_results(
                test_results, str(out_dir / 'initial_test_results.png')
            )

            passed = test_results['summary']['passed']
            failed = test_results['summary']['failed']
            total  = test_results['summary']['total_tests']
            self.logger.info(f"Initial QA: {passed} passed, {failed} failed out of {total}")

            self.system_metrics['tests_executed'] += total

            # ── Finalize ────────────────────────────────────────────────────────
            self.is_initialized = True
            results['success']       = True
            results['elapsed_time']  = time.time() - start_time

            self.logger.info(f"System initialization completed in {results['elapsed_time']:.2f}s")

        except Exception as e:
            self.logger.error(f"System initialization failed: {e}", exc_info=True)
            results['error'] = str(e)

        return results
    
    def process_query(self, query: str, user_context: Dict[str, Any] = None, autonomous: bool = True) -> Dict[str, Any]:
        """
        Process a user query through the system.
        
        Args:
            query: The user's query text
            user_context: Optional user context information
            autonomous: Whether to use the automation manager
            
        Returns:
            Response dictionary
        """
        if not self.is_initialized:
            self.logger.warning("System not initialized, attempting to initialize with default settings")
            self.initialize_system()
        
        try:
            self.logger.info(f"Processing query: {query}")
            
            # Use automation manager if autonomous mode is enabled
            if autonomous:
                try:
                    response = self.automation_manager.process_query_with_automation(query, user_context)
                    self.system_metrics['autonomous_decisions'] += 1
                except Exception as e:
                    self.logger.error(f"Error in automation manager: {e}")
                    import traceback
                    self.logger.error(f"Traceback: {traceback.format_exc()}")
                    # Fall back to direct query processing
                    self.logger.info("Falling back to direct query processing...")
                    response = self.query_processor.process_query(query, user_context)
            else:
                response = self.query_processor.process_query(query, user_context)
            
            self.system_metrics['queries_processed'] += 1
            self.logger.info(f"Query processed successfully")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'answer': f"I'm sorry, there was an error processing your query. Please try again.",
                'success': False,
                'error': str(e)
            }
    
    def run_improvement_cycle(self) -> Dict[str, Any]:
        """
        Run a complete improvement cycle for the system.
        
        Returns:
            Dictionary with improvement results
        """
        if not self.is_initialized:
            self.logger.warning("System not initialized, attempting to initialize with default settings")
            self.initialize_system()
        
        try:
            self.logger.info("Starting system improvement cycle")
            
            # Step 1: Run QA tests
            self.logger.info("Step 1: Running QA tests...")
            test_results = self.qa_system.run_test_suite()
            
            # Step 2: Diagnose failures
            self.logger.info("Step 2: Diagnosing failures...")
            diagnostics = self.qa_system.diagnose_failures(test_results)
            
            # Step 3: Apply fixes
            self.logger.info("Step 3: Applying fixes...")
            fix_results = self.qa_system.fix_common_issues(diagnostics)
            
            # Step 4: Improve automation
            self.logger.info("Step 4: Improving automation...")
            automation_results = self.automation_manager.run_continuous_improvement_cycle(cycles=1)
            
            # Step 5: Run QA tests again
            self.logger.info("Step 5: Running follow-up QA tests...")
            post_fix_results = self.qa_system.run_test_suite()
            
            # Calculate improvement
            initial_pass_rate = test_results['summary']['passed'] / test_results['summary']['total_tests'] if test_results['summary']['total_tests'] > 0 else 0
            final_pass_rate = post_fix_results['summary']['passed'] / post_fix_results['summary']['total_tests'] if post_fix_results['summary']['total_tests'] > 0 else 0
            improvement = final_pass_rate - initial_pass_rate
            
            self.logger.info(f"Improvement cycle completed with {improvement:.2%} improvement in pass rate")
            
            # Generate reports
            qa_report = self.qa_system.generate_performance_report()
            automation_report = self.automation_manager.generate_self_improvement_report()
            
            # Save reports
            reports_path = os.path.join(self.config['output_dir'], 'improvement_reports')
            os.makedirs(reports_path, exist_ok=True)
            
            with open(os.path.join(reports_path, 'qa_report.json'), 'w') as f:
                json.dump(qa_report, f, indent=2)
                
            with open(os.path.join(reports_path, 'automation_report.json'), 'w') as f:
                json.dump(automation_report, f, indent=2)
            
            # Generate visualizations
            self.qa_system.visualize_test_results(
                post_fix_results, 
                os.path.join(reports_path, 'post_fix_test_results.png')
            )
            
            self.qa_system.visualize_system_performance(
                qa_report,
                os.path.join(reports_path, 'qa_performance.png')
            )
            
            self.automation_manager.visualize_autonomy_metrics(
                os.path.join(reports_path, 'autonomy_metrics.png')
            )
            
            # Update system metrics
            self.system_metrics['tests_executed'] += test_results['summary']['total_tests'] + post_fix_results['summary']['total_tests']
            
            # Return improvement results
            return {
                'initial_tests': test_results['summary'],
                'post_fix_tests': post_fix_results['summary'],
                'improvement': improvement,
                'fixes_applied': len(fix_results.get('fixed_issues', [])),
                'automation_improvement': automation_results.get('overall_improvement', {}).get('improvement', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error during improvement cycle: {e}")
            return {
                'error': str(e),
                'success': False
            }
    
    def generate_system_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive system report.
        
        Returns:
            System report dictionary
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'system_metrics': self.system_metrics,
            'components': {
                'document_processor': {
                    'documents_processed': self.system_metrics['documents_processed']
                },
                'schema_manager': {
                    'updates': self.system_metrics['schema_updates'],
                    'entity_types': len(self.schema_manager.get_entity_types()),
                    'relationship_types': len(self.schema_manager.get_relationship_types()),
                    'quality_scores': self.schema_manager.quality_scores
                },
                'query_processor': {
                    'queries_processed': self.system_metrics['queries_processed'],
                    'avg_response_time': getattr(self.query_processor, 'query_metrics', {}).get('avg_response_time', 0),
                    'intent_distribution': dict(getattr(self.query_processor, 'query_metrics', {}).get('intent_distribution', {}))
                },
                'qa_system': {
                    'tests_executed': self.system_metrics['tests_executed'],
                    'error_patterns': dict(self.qa_system.error_patterns)
                },
                'automation_manager': {
                    'autonomous_decisions': self.system_metrics['autonomous_decisions'],
                    'autonomy_rate': self.automation_manager.autonomous_metrics.get('autonomous_success_rate', 0),
                    'escalations': self.automation_manager.autonomous_metrics.get('escalations', 0)
                }
            },
            'recommendations': []
        }
        
        # Generate recommendations
        if self.system_metrics['documents_processed'] < 10:
            report['recommendations'].append({
                'component': 'Document Processing',
                'recommendation': 'Process more documents to improve knowledge graph coverage'
            })
        
        if self.schema_manager.quality_scores.get('coverage', 0) < 0.7:
            report['recommendations'].append({
                'component': 'Schema Manager',
                'recommendation': 'Expand schema coverage with more entity and relationship types'
            })
        
        qa_pass_rate = getattr(self.qa_system, 'test_metrics', {}).get('pass_rate', 0)
        if qa_pass_rate < 0.8:
            report['recommendations'].append({
                'component': 'QA System',
                'recommendation': 'Improve system performance to increase test pass rate'
            })
        
        autonomy_rate = self.automation_manager.autonomous_metrics.get('autonomous_success_rate', 0)
        if autonomy_rate < 0.7:
            report['recommendations'].append({
                'component': 'Automation Manager',
                'recommendation': 'Enhance exception handling to reduce human intervention'
            })
        
        return report
    
    def save_system_state(self, path: str = None) -> str:
        """
        Save current system state to a file.
        
        Args:
            path: Optional path to save state
            
        Returns:
            Path to saved state file
        """
        if not path:
            path = os.path.join(self.config['output_dir'], f"system_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        state = {
            'timestamp': datetime.now().isoformat(),
            'system_metrics': self.system_metrics,
            'is_initialized': self.is_initialized,
            'config': self.config,
            'component_states': {
                'schema_manager': {
                    'quality_scores': self.schema_manager.quality_scores,
                    'entity_count': len(self.schema_manager.get_entity_types()),
                    'relationship_count': len(self.schema_manager.get_relationship_types())
                },
                'query_processor': {
                    'query_metrics': getattr(self.query_processor, 'query_metrics', {})
                },
                'qa_system': {
                    'error_patterns': dict(self.qa_system.error_patterns)
                },
                'automation_manager': {
                    'autonomous_metrics': self.automation_manager.autonomous_metrics,
                    'confidence_thresholds': dict(self.automation_manager.confidence_thresholds)
                }
            }
        }
        
        with open(path, 'w') as f:
            json.dump(state, f, indent=2)
            
        self.logger.info(f"System state saved to {path}")
        return path
    
    def load_system_state(self, path: str) -> bool:
        """
        Load system state from a file.
        
        Args:
            path: Path to state file
            
        Returns:
            Boolean indicating success
        """
        if not os.path.exists(path):
            self.logger.error(f"State file not found: {path}")
            return False
        
        try:
            with open(path, 'r') as f:
                state = json.load(f)
            
            # Restore system metrics
            self.system_metrics = state.get('system_metrics', self.system_metrics)
            self.is_initialized = state.get('is_initialized', self.is_initialized)
            
            # Restore component states where applicable
            component_states = state.get('component_states', {})
            
            # Update confidence thresholds in automation manager
            if 'automation_manager' in component_states:
                auto_state = component_states['automation_manager']
                if 'confidence_thresholds' in auto_state:
                    self.automation_manager.confidence_thresholds.update(auto_state['confidence_thresholds'])
            
            self.logger.info(f"System state loaded from {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading system state: {e}")
            return False
    
    def run_interactive_demo(self) -> None:
        """Run an interactive demo of the system."""
        print("\n" + "=" * 80)
        print("   Insurance Graph RAG System - Interactive Demo")
        print("=" * 80)
        
        # Initialize if needed
        if not self.is_initialized:
            print("\nInitializing system...")
            init_result = self.initialize_system()
            
            if init_result['success']:
                print(f"System initialized successfully!")
                print(f"- Documents processed: {init_result['documents_processed']}")
                print(f"- Schema updated: {init_result['schema_updated']}")
                print(f"- Knowledge graph created: {init_result['knowledge_graph_created']}")
                print(f"- Elapsed time: {init_result['elapsed_time']:.2f} seconds")
            else:
                print(f"System initialization failed: {init_result.get('error', 'Unknown error')}")
                return
        
        # Create a simulated user
        user_context = {
            'user_id': 'U5001',
            'known_policies': ['P1001', 'P1002'],
            'known_claims': ['CL4001']
        }
        
        print("\nDemo User Context:")
        print(f"- User ID: {user_context['user_id']}")
        print(f"- Policies: {', '.join(user_context['known_policies'])}")
        print(f"- Claims: {', '.join(user_context['known_claims'])}")
        
        print("\nType your insurance-related questions (or 'exit' to quit):")
        
        while True:
            print("\n> ", end='')
            query = input().strip()
            
            if query.lower() in ('exit', 'quit', 'bye'):
                break
            
            if not query:
                continue
                
            start_time = time.time()
            response = self.process_query(query, user_context)
            elapsed_time = time.time() - start_time
            
            print(f"\nAnswer: {response['answer']}")
            print(f"Intent: {response.get('intent', 'unknown')} (confidence: {response.get('confidence', 0):.2f})")
            print(f"Response time: {elapsed_time:.2f}s")
            
            # Show automation info if available
            if 'autonomous' in response:
                if response.get('autonomous', False):
                    print("Decision: Autonomous")
                else:
                    print(f"Decision: Escalated - {response.get('review_reason', 'Unknown reason')}")
            
            # Show follow-up questions if available
            if 'follow_up_questions' in response and response['follow_up_questions']:
                print("\nYou might also want to ask:")
                for i, question in enumerate(response['follow_up_questions']):
                    print(f"  {i+1}. {question}")
        
        print("\nThank you for using the Insurance Graph RAG System!")

# Run the system when executed directly
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Insurance Graph RAG System')
    parser.add_argument('--config', '-c', type=str, help='Path to configuration file')
    parser.add_argument('--init', '-i', action='store_true', help='Initialize system on startup')
    parser.add_argument('--demo', '-d', action='store_true', help='Run interactive demo')
    parser.add_argument('--improve', '-m', action='store_true', help='Run improvement cycle')
    parser.add_argument('--query', '-q', type=str, help='Process a single query')
    parser.add_argument('--report', '-r', action='store_true', help='Generate system report')
    
    args = parser.parse_args()
    
    # Initialize system
    system = InsuranceGraphRAGSystem(config_path=args.config)
    
    if args.init or args.demo:
        system.initialize_system()
    
    if args.improve:
        print("Running improvement cycle...")
        improvement_results = system.run_improvement_cycle()
        print(f"Improvement results: {json.dumps(improvement_results, indent=2)}")
    
    if args.query:
        print(f"Processing query: {args.query}")
        response = system.process_query(args.query)
        print(f"Response: {response['answer']}")
    
    if args.report:
        print("Generating system report...")
        report = system.generate_system_report()
        report_path = os.path.join(system.config['output_dir'], 'system_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to {report_path}")
    
    if args.demo:
        system.run_interactive_demo()