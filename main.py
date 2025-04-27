# main.py
import os
import asyncio
import argparse
from datetime import datetime
from dotenv import load_dotenv

from genai.genai_architecture_controller import GenAIArchitectureController
from genai.model_interaction_manager import ModelInteractionManager
from genai.prompt_pipeline import PromptRegistry
from genai.interactive_development_pipeline import interactive_development_session
from src.insurance_graph_rag_system import InsuranceGraphRAGSystem

async def run_complete_solution(args):
    """Run the complete Insurance Graph RAG solution with GenAI orchestration."""
    print("🚀 Insurance Graph RAG System with GenAI Orchestration")
    print("=" * 80)
    
    # Initialize components
    arch_controller = GenAIArchitectureController(config_path=args.config)
    model_manager = ModelInteractionManager()
    prompt_registry = PromptRegistry()
    
    if args.mode == "develop":
        # Run the interactive development session
        await interactive_development_session()
    
    elif args.mode == "automate":
        # Run automated development pipeline
        if args.requirements:
            try:
                with open(args.requirements, 'r') as f:
                    requirements = f.read()
                print(f"Requirements loaded from {args.requirements}")
            except Exception as e:
                print(f"Error loading requirements file: {e}")
                requirements = """
                Create an insurance domain knowledge graph RAG system that:
                1. Processes insurance policy documents to extract structured information
                2. Builds and maintains a self-evolving knowledge graph schema
                3. Processes natural language queries about policies, coverages, and claims
                4. Provides accurate, contextual responses based on the knowledge graph
                5. Learns and improves over time through automated testing and feedback
                """
                print("Using default requirements")
        else:
            requirements = """
            Create an insurance domain knowledge graph RAG system that:
            1. Processes insurance policy documents to extract structured information
            2. Builds and maintains a self-evolving knowledge graph schema
            3. Processes natural language queries about policies, coverages, and claims
            4. Provides accurate, contextual responses based on the knowledge graph
            5. Learns and improves over time through automated testing and feedback
            """
            print("Using default requirements")
        
        print(f"\n🧠 Running automated development pipeline based on requirements...")
        print(f"Requirements length: {len(requirements)} characters")
        print(f"First 200 chars: {requirements[:200]}...")
        
        # Run test first to verify OpenAI connection
        print("\nTesting OpenAI API connection...")
        try:
            test_response = model_manager.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Please respond with 'API connection successful.'"}
                ],
                max_tokens=20
            )
            print(f"API test response: {test_response.choices[0].message.content}")
        except Exception as e:
            print(f"❌ API test failed: {e}")
            print("Please check your OpenAI API configuration and try again.")
            return
        
        # Run the SDLC process
        results = await arch_controller.run_complete_sdlc(requirements)
        
        print(f"\n✅ Development pipeline complete with {len(results)} artifacts generated.")
        print(f"All artifacts saved to {args.output_dir}")
    
    elif args.mode == "run":
        # Initialize and run the actual system
        # [rest of the implementation unchanged]
        # Initialize and run the actual system
        print(f"\n🏃 Running the Insurance Graph RAG System...")
        
        # Initialize the system
        system = InsuranceGraphRAGSystem(config_path=args.config)
        
        # Process documents and build knowledge graph
        if args.data_dir:
            print(f"\n📚 Processing documents from {args.data_dir}...")
            system.initialize_system(sources=[args.data_dir])
        
        # Run interactive demo if requested
        if args.interactive:
            print(f"\n🤖 Starting interactive demo...")
            system.run_interactive_demo()
        
        # Run improvement cycle if requested
        if args.improve:
            print(f"\n🔄 Running system improvement cycle...")
            improvement_results = system.run_improvement_cycle()
            print(f"\nImprovement results: {improvement_results}")

def main():
    """Main entry point for the application."""
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Insurance Graph RAG System with GenAI Orchestration")
    parser.add_argument('--mode', choices=['develop', 'automate', 'run'], default='develop',
                        help='Mode to run: interactive development, automated pipeline, or run system')
    parser.add_argument('--config', type=str, default='config.json',
                        help='Path to configuration file')
    parser.add_argument('--requirements', type=str, 
                        help='Path to requirements file (for automate mode)')
    parser.add_argument('--data_dir', type=str, default='data',
                        help='Directory containing input data (for run mode)')
    parser.add_argument('--output_dir', type=str, default='output',
                        help='Directory for output artifacts')
    parser.add_argument('--interactive', action='store_true',
                        help='Run in interactive demo mode (for run mode)')
    parser.add_argument('--improve', action='store_true',
                        help='Run system improvement cycle (for run mode)')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Run the appropriate function based on arguments
    asyncio.run(run_complete_solution(args))

if __name__ == "__main__":
    main()