# interactive_development_pipeline.py
import os
import json
import asyncio
from typing import Dict, Any, List
import argparse
from datetime import datetime
import re
from dotenv import load_dotenv

from genai.genai_architecture_controller import GenAIArchitectureController
from genai.prompt_pipeline import PromptRegistry, PromptTemplate, PromptPipeline
from genai.model_interaction_manager import ModelInteractionManager
from genai.genai_test_framework import TestGenerator, GenAITestRunner

async def interactive_development_session():
    """Run an interactive development session."""
    load_dotenv()
    
    print("🚀 Starting Interactive GenAI-Driven Development Session")
    print("=" * 80)
    
    # Initialize components
    print("\n🔧 Initializing components...")
    model_manager = ModelInteractionManager()
    arch_controller = GenAIArchitectureController()
    prompt_registry = PromptRegistry()
    
    # Initialize test framework
    test_generator = TestGenerator(model_manager)
    test_runner = GenAITestRunner(test_generator)
    
    # Track completed steps
    completed_steps = set()
    
    # Main menu loop
    while True:
        print("\n" + "=" * 40)
        print("🧠 GenAI Development Pipeline")
        print("=" * 40)
        print("1. 📋 Requirements Analysis")
        
        # Gray out or highlight items based on availability
        if 1 in completed_steps:
            print("2. 🏗️ Architecture Design")
        else:
            print("2. 🏗️ Architecture Design (requires step 1)")
        
        if 2 in completed_steps:
            print("3. 🧩 Component Design")
        else:
            print("3. 🧩 Component Design (requires step 2)")
        
        if 3 in completed_steps:
            print("4. 💻 Code Generation")
        else:
            print("4. 💻 Code Generation (requires step 3)")
        
        if 4 in completed_steps:
            print("5. 🧪 Test Generation & Analysis")
        else:
            print("5. 🧪 Test Generation & Analysis (requires step 4)")
        
        if 5 in completed_steps:
            print("6. 📊 Document Generation")
        else:
            print("6. 📊 Document Generation (requires step 5)")
        
        print("7. 🔄 Full SDLC Pipeline")
        print("8. 📁 View Artifacts")
        print("9. ⚙️ Configure Pipeline")
        print("0. 🚪 Exit")
        
        choice = input("\nSelect an option (0-9): ")
        
        if choice == "0":
            print("\nThank you for using the GenAI Development Pipeline!")
            break
        
        elif choice == "1":
            result = await requirements_analysis_workflow(arch_controller, model_manager)
            if result:
                completed_steps.add(1)
        
        elif choice == "2":
            if 1 in completed_steps:
                result = await architecture_design_workflow(arch_controller, model_manager)
                if result:
                    completed_steps.add(2)
            else:
                print("\n⚠️ Please complete Requirements Analysis (Step 1) first.")
        
        elif choice == "3":
            if 2 in completed_steps:
                result = await component_design_workflow(arch_controller, model_manager)
                if result:
                    completed_steps.add(3)
            else:
                print("\n⚠️ Please complete Architecture Design (Step 2) first.")
        
        elif choice == "4":
            if 3 in completed_steps:
                result = await code_generation_workflow(arch_controller, model_manager)
                if result:
                    completed_steps.add(4)
            else:
                print("\n⚠️ Please complete Component Design (Step 3) first.")
        
        elif choice == "5":
            if 4 in completed_steps:
                result = await test_generation_workflow(test_generator, test_runner, model_manager)
                if result:
                    completed_steps.add(5)
            else:
                print("\n⚠️ Please complete Code Generation (Step 4) first.")
        
        elif choice == "6":
            if 5 in completed_steps:
                result = await documentation_workflow(arch_controller, model_manager)
                if result:
                    completed_steps.add(6)
            else:
                print("\n⚠️ Please complete Test Generation (Step 5) first.")
        
        elif choice == "7":
            await full_sdlc_workflow(arch_controller)
            # Mark all steps as completed after full SDLC
            completed_steps.update({1, 2, 3, 4, 5, 6})
        
        elif choice == "8":
            view_artifacts()
        
        elif choice == "9":
            configure_pipeline(prompt_registry)
        
        else:
            print("Invalid option. Please select 0-9.")

async def requirements_analysis_workflow(arch_controller, model_manager):
    """Run the requirements analysis workflow."""
    print("\n📋 Requirements Analysis Workflow")
    print("-" * 40)
    
    # Get user input
    print("\nPlease provide the business requirements for your insurance RAG system:")
    requirements = input_multiline()
    
    print("\n🧠 Analyzing requirements...")
    results = await arch_controller.generate_with_prompt("requirements_analysis", {
        "business_requirements": requirements
    })
    
    print("\n✅ Requirements analysis complete! Results saved to output directory.")
    print("\nSummary of requirements:")
    print("-" * 40)
    print(results[:500] + "..." if len(results) > 500 else results)
    
    return True

async def architecture_design_workflow(arch_controller, model_manager):
    """Run the architecture design workflow with automatic requirements loading."""
    print("\n🏗️ Architecture Design Workflow")
    print("-" * 40)
    
    # Find the latest requirements file in the output directory
    requirements_dir = arch_controller.config["output_dir"]
    latest_req_file = None
    latest_timestamp = 0
    
    print("\nAutomatically loading latest requirements analysis...")
    try:
        for filename in os.listdir(requirements_dir):
            if filename.startswith("requirements_analysis_") and (filename.endswith(".md") or filename.endswith(".txt")):
                file_path = os.path.join(requirements_dir, filename)
                file_timestamp = os.path.getmtime(file_path)
                if file_timestamp > latest_timestamp:
                    latest_timestamp = file_timestamp
                    latest_req_file = file_path
        
        if not latest_req_file:
            print("\n⚠️ No requirements analysis file found. Please run Step 1 first.")
            return False
        
        print(f"\nFound latest requirements file: {latest_req_file}")
        
        # Read the requirements from the file
        with open(latest_req_file, 'r') as f:
            file_content = f.read()
        
        # Simplified extraction approach - keep only the core sections
        # Find the "Generated Result" section if it exists
        if "## Generated Result" in file_content:
            generated_content = file_content.split("## Generated Result", 1)[1].strip()
            
            # Keep only the core requirements sections 
            # Create a clean summary with just the necessary information
            requirements_sections = []
            
            # Get Core User Stories
            if "## 1. Core User Stories" in generated_content:
                user_stories_section = generated_content.split("## 1. Core User Stories", 1)[1]
                if "##" in user_stories_section:
                    user_stories_section = user_stories_section.split("##", 1)[0].strip()
                else:
                    user_stories_section = user_stories_section.strip()
                requirements_sections.append("## Core User Stories\n\n" + user_stories_section)
            
            # Get Data Requirements
            if "## 4. Data Requirements" in generated_content:
                data_requirements_section = generated_content.split("## 4. Data Requirements", 1)[1]
                if "##" in data_requirements_section:
                    data_requirements_section = data_requirements_section.split("##", 1)[0].strip()
                else:
                    data_requirements_section = data_requirements_section.strip()
                requirements_sections.append("## Data Requirements\n\n" + data_requirements_section)
            
            # Get Technical Constraints
            if "## 5. Technical Constraints" in generated_content:
                tech_constraints_section = generated_content.split("## 5. Technical Constraints", 1)[1]
                if "##" in tech_constraints_section:
                    tech_constraints_section = tech_constraints_section.split("##", 1)[0].strip()
                else:
                    tech_constraints_section = tech_constraints_section.strip()
                requirements_sections.append("## Technical Constraints\n\n" + tech_constraints_section)
            
            # Create a condensed summary of the functional requirements without tables
            if "## 2. Functional Requirements" in generated_content:
                func_req_section = "## Key Functional Requirements\n\n"
                func_req_section += "- Document processing and entity extraction\n"
                func_req_section += "- Self-evolving knowledge graph schema\n"
                func_req_section += "- Natural language query processing\n"
                func_req_section += "- Response generation with citations\n"
                func_req_section += "- Continuous learning and improvement\n"
                requirements_sections.append(func_req_section)
            
            # Combine all parts into a clean, focused requirements document
            requirements = "# Requirements Summary for Insurance Graph RAG System\n\n" + "\n\n".join(requirements_sections)
        else:
            # Fall back to using the full content if we can't find the Generated Result section
            requirements = file_content
            
        print(f"Extracted focused requirements ({len(requirements)} chars)")
    except Exception as e:
        print(f"\nError accessing requirements files: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False
    
    print("\n🧠 Designing architecture based on requirements...")
    
    # Force a system prompt that will keep the output focused on architecture
    custom_system_prompt = """
    You are an expert software architect specializing in graph-based RAG systems. 
    Your task is to design a comprehensive, detailed architecture for an Insurance Graph RAG system.
    
    Important instructions:
    1. Focus ONLY on architecture design, not requirements analysis
    2. Structure your response with clear component definitions, relationships, and diagrams
    3. Include technical justifications for your design decisions
    4. Ensure the architecture addresses all the requirements provided
    5. DO NOT repeat or restate the requirements in your response
    
    Your architecture design should include:
    - High-level system architecture
    - Component breakdown with responsibilities
    - Data flow diagrams
    - Technical justifications for technology choices
    - Integration patterns
    """
    
    # Check if the _generate_with_custom_prompt method exists
    if hasattr(arch_controller, '_generate_with_custom_prompt'):
        # Use the custom prompt method if available
        results = await arch_controller._generate_with_custom_prompt(
            template_name="architecture_design",
            variables={"requirements": requirements},
            system_prompt=custom_system_prompt
        )
    else:
        # Fall back to the regular method with a note
        print("Note: Using standard prompt method. For better results, add the _generate_with_custom_prompt method.")
        results = await arch_controller.generate_with_prompt("architecture_design", {
            "requirements": requirements
        })
    
    print("\n✅ Architecture design complete! Results saved to output directory.")
    print("\nSummary of architecture:")
    print("-" * 40)
    print(results[:500] + "..." if len(results) > 500 else results)
    
    return True

async def component_design_workflow(arch_controller, model_manager):
    """Run the component design workflow with component selection."""
    print("\n🧩 Component Design Workflow")
    print("-" * 40)
    
    # Find the latest architecture design file in the output directory
    arch_design_file = None
    latest_timestamp = 0
    output_dir = arch_controller.config["output_dir"]
    
    print("\nAutomatically loading architecture design...")
    try:
        for filename in os.listdir(output_dir):
            if filename.startswith("architecture_design_") and (filename.endswith(".md") or filename.endswith(".txt")):
                file_path = os.path.join(output_dir, filename)
                file_timestamp = os.path.getmtime(file_path)
                if file_timestamp > latest_timestamp:
                    latest_timestamp = file_timestamp
                    arch_design_file = file_path
        
        if not arch_design_file:
            print("\n⚠️ No architecture design file found. Please run Step 2 first.")
            return False
        
        print(f"\nFound architecture design file: {arch_design_file}")
        
        # Read the architecture design file
        with open(arch_design_file, 'r') as f:
            arch_content = f.read()
        
        # Extract component sections
        component_sections = []
        
        # Look for "### X. Component Name" patterns
        component_pattern = r'### \d+\.\s+(.+?)(?=\n)'
        component_matches = re.findall(component_pattern, arch_content)
        
        if not component_matches:
            # Try alternate pattern without numbers
            component_pattern = r'### ([^#\n]+)(?=\n)'
            component_matches = re.findall(component_pattern, arch_content)
        
        if component_matches:
            print("\nFound the following components in the architecture:")
            for i, component in enumerate(component_matches):
                print(f"{i+1}. {component.strip()}")
            
            # Ask which component(s) to design
            print("\nSelect component(s) to design (comma-separated numbers, or 'all' for all components):")
            component_selection = input()
            
            components_to_design = []
            if component_selection.lower() == 'all':
                components_to_design = component_matches
            else:
                try:
                    indices = [int(idx.strip()) - 1 for idx in component_selection.split(',')]
                    for idx in indices:
                        if 0 <= idx < len(component_matches):
                            components_to_design.append(component_matches[idx])
                        else:
                            print(f"Invalid selection: {idx+1}")
                except ValueError:
                    print("Invalid input. Please enter numbers separated by commas.")
                    return False
            
            # Process each selected component
            all_results = []
            for component_name in components_to_design:
                component_name = component_name.strip()
                print(f"\n🔹 Designing {component_name}...")
                
                # Extract requirements for this component
                component_section_pattern = f"### [^\n]*{re.escape(component_name)}"
                component_section = ""
                
                section_match = re.search(component_section_pattern, arch_content)
                if section_match:
                    section_start = section_match.start()
                    
                    # Find the end of this component's section
                    next_component_pattern = "### "
                    next_match = re.search(next_component_pattern, arch_content[section_start + len(section_match.group(0)):])
                    
                    if next_match:
                        section_end = section_start + len(section_match.group(0)) + next_match.start()
                    else:
                        next_section_pattern = "## "
                        next_match = re.search(next_section_pattern, arch_content[section_start + len(section_match.group(0)):])
                        if next_match:
                            section_end = section_start + len(section_match.group(0)) + next_match.start()
                        else:
                            section_end = len(arch_content)
                    
                    component_section = arch_content[section_start:section_end].strip()
                
                # Also extract general architecture context
                architecture_overview = ""
                if "## High-Level System Architecture" in arch_content:
                    overview_start = arch_content.find("## High-Level System Architecture")
                    overview_end = arch_content.find("##", overview_start + len("## High-Level System Architecture"))
                    if overview_end != -1:
                        architecture_overview = arch_content[overview_start:overview_end].strip()
                    else:
                        architecture_overview = arch_content[overview_start:].strip()
                
                # Also grab data flow information which is relevant to all components
                data_flow = ""
                if "## Data Flow Diagrams" in arch_content:
                    flow_start = arch_content.find("## Data Flow Diagrams")
                    flow_end = arch_content.find("##", flow_start + len("## Data Flow Diagrams"))
                    if flow_end != -1:
                        data_flow = arch_content[flow_start:flow_end].strip()
                    else:
                        data_flow = arch_content[flow_start:].strip()
                
                # Combine everything into comprehensive requirements
                component_requirements = f"""
                # Requirements for {component_name}
                
                ## Component Description from Architecture
                {component_section}
                
                ## Architectural Context
                {architecture_overview}
                
                ## Relevant Data Flows
                {data_flow}
                
                ## Additional Requirements
                - The component should follow the modular design pattern of the overall system
                - It should have well-defined interfaces with other components
                - It should implement proper error handling and logging
                - It should be scalable and maintainable
                """
                
                # Generate design for this component
                result = await arch_controller.generate_with_prompt("component_design", {
                    "component_name": component_name,
                    "component_requirements": component_requirements
                })
                
                print(f"\n✅ {component_name} design complete!")
                print("\nSummary:")
                print("-" * 40)
                print(result[:300] + "..." if len(result) > 300 else result)
                
                all_results.append({
                    "component_name": component_name,
                    "design": result
                })
            
            # If at least one component was designed successfully
            return len(all_results) > 0
        else:
            print("\n⚠️ No components found in the architecture design.")
            return False
            
    except Exception as e:
        print(f"\nError processing architecture file: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

async def code_generation_workflow(arch_controller, model_manager):
    """Run the code generation workflow with component selection."""
    print("\n💻 Code Generation Workflow")
    print("-" * 40)
    
    # Find the latest component design files
    output_dir = arch_controller.config["output_dir"]
    component_files = []
    
    print("\nAutomatically loading component designs...")
    try:
        for filename in os.listdir(output_dir):
            if filename.startswith("component_design_") and (filename.endswith(".md") or filename.endswith(".txt")):
                file_path = os.path.join(output_dir, filename)
                component_files.append((filename, file_path, os.path.getmtime(file_path)))
        
        # Sort by timestamp (newest first)
        component_files.sort(key=lambda x: x[2], reverse=True)
        
        if not component_files:
            print("\n⚠️ No component design files found. Please run Step 3 first.")
            return False
        
        # Extract component names from filenames
        component_names = []
        for filename, file_path, _ in component_files:
            # Try to extract component name from filename
            name_match = re.search(r'component_design_([^_]+)_\d+', filename)
            if name_match:
                component_name = name_match.group(1).replace('_', ' ')
            else:
                # Try to extract from content
                with open(file_path, 'r') as f:
                    content = f.read()
                    match = re.search(r'# Component Design for (.+?)[\n\r]', content)
                    component_name = match.group(1) if match else f"Component from {filename}"
            
            component_names.append((component_name, file_path))
        
        print("\nAvailable components:")
        for i, (component_name, _) in enumerate(component_names):
            print(f"{i+1}. {component_name}")
        
        # Ask which component(s) to implement
        print("\nSelect component(s) to implement (comma-separated numbers, or 'all' for all components):")
        component_selection = input()
        
        files_to_process = []
        if component_selection.lower() == 'all':
            files_to_process = component_names
        else:
            try:
                indices = [int(idx.strip()) - 1 for idx in component_selection.split(',')]
                for idx in indices:
                    if 0 <= idx < len(component_names):
                        files_to_process.append(component_names[idx])
                    else:
                        print(f"Invalid selection: {idx+1}")
            except ValueError:
                print("Invalid input. Please enter numbers separated by commas.")
                return False
        
        # Process each selected component
        all_results = []
        for component_name, file_path in files_to_process:
            print(f"\n🔹 Implementing {component_name}...")
            
            # Read component design
            with open(file_path, 'r') as f:
                design = f.read()
            
            # Generate code for this component
            result = await arch_controller.generate_with_prompt("code_generation", {
                "module_name": component_name,
                "module_design": design
            })
            
            # Extract code from results
            if "```python" in result:
                code = result.split("```python")[1].split("```")[0].strip()
            elif "```" in result:
                code = result.split("```")[1].split("```")[0].strip()
            else:
                code = result
            
            print(f"\n✅ {component_name} implementation complete!")
            print("\nPreview:")
            print("-" * 40)
            print(code[:300] + "..." if len(code) > 300 else code)
            
            # Auto-save to file
            safe_name = component_name.lower().replace(' ', '_').replace('-', '_')
            filename = f"{safe_name}.py"
            with open(filename, 'w') as f:
                f.write(code)
            
            print(f"Code saved to {filename}")
            
            all_results.append({
                "component_name": component_name,
                "code": code,
                "filename": filename
            })
        
        # If at least one component was implemented successfully
        return len(all_results) > 0
            
    except Exception as e:
        print(f"\nError generating code: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

async def test_generation_workflow(test_generator, test_runner, model_manager):
    """Run an improved test generation and analysis workflow for implemented components."""
    print("\n🧪 Improved Test Generation & Analysis Workflow")
    print("-" * 40)
    
    # Find Python files in the working directory (from code generation)
    python_files = []
    
    print("\nLooking for implemented components...")
    try:
        for filename in os.listdir('.'):
            if filename.endswith('.py') and not filename.startswith('test_') and not filename == "run_tests.py":
                python_files.append(filename)
        
        if not python_files:
            print("\n⚠️ No Python implementations found. Please run Step 4 first.")
            return False
        
        print("\nAvailable implementations:")
        for i, filename in enumerate(python_files):
            print(f"{i+1}. {filename}")
        
        # Ask which component(s) to test
        print("\nSelect implementation(s) to test (comma-separated numbers, or 'all' for all implementations):")
        component_selection = input()
        
        files_to_test = []
        if component_selection.lower() == 'all':
            files_to_test = python_files
        else:
            try:
                indices = [int(idx.strip()) - 1 for idx in component_selection.split(',')]
                for idx in indices:
                    if 0 <= idx < len(python_files):
                        files_to_test.append(python_files[idx])
                    else:
                        print(f"Invalid selection: {idx+1}")
            except ValueError:
                print("Invalid input. Please enter numbers separated by commas.")
                return False
        
        # Process each selected implementation
        all_results = []
        for filename in files_to_test:
            module_name = os.path.splitext(filename)[0]
            print(f"\n🔹 Testing {module_name}...")
            
            # Read implementation with proper encoding handling
            try:
                # Try UTF-8 first
                with open(filename, 'r', encoding='utf-8') as f:
                    code = f.read()
            except UnicodeDecodeError:
                try:
                    # Fall back to another encoding if UTF-8 fails
                    with open(filename, 'r', encoding='latin-1') as f:
                        code = f.read()
                except Exception as e:
                    print(f"Error reading file {filename}: {e}")
                    continue
            
            # Generate tests with proper sanitization
            print(f"\nGenerating tests for {module_name}...")
            
            # Use a safer template for test generation that avoids problematic Unicode
            # and adds proper environment setup
            sanitized_tests = await test_generator.generate_unit_tests(
                code_snippet=code,
                module_name=module_name,
                focus_areas=["Avoid Unicode characters", "Proper environment setup"]
            )
            
            # Ensure tests have proper environment setup
            setup_code = """
# Add proper environment setup
import os
import sys
from unittest import mock

# Handle potential dependencies
required_modules = {
    'dotenv': 'python-dotenv',
    'openai': 'openai',
    'numpy': 'numpy',
    'pandas': 'pandas'
}

# Mock modules that might be missing
for module_name, package_name in required_modules.items():
    try:
        __import__(module_name)
    except ImportError:
        # Create a mock for this module
        sys.modules[module_name] = mock.MagicMock()
        print(f"Created mock for {module_name}")
"""
            
            # Insert setup code at the beginning of the tests
            if "import unittest" in sanitized_tests:
                sanitized_tests = sanitized_tests.replace(
                    "import unittest", 
                    "import unittest\n" + setup_code
                )
            else:
                sanitized_tests = setup_code + "\nimport unittest\n" + sanitized_tests
            
            # Replace problematic Unicode characters
            sanitized_tests = sanitized_tests.replace("Café", "Cafe")
            sanitized_tests = sanitized_tests.replace("Münchner", "Munchner")
            
            # Save the sanitized tests
            test_filename = f"test_{module_name}.py"
            with open(test_filename, 'w', encoding='utf-8') as f:
                f.write(sanitized_tests)
            
            print(f"Tests saved to {test_filename}")
            
            # Run the tests with proper environment
            print(f"Running tests for {module_name}...")
            try:
                import subprocess
                result = subprocess.run(
                    [sys.executable, '-m', 'unittest', test_filename],
                    capture_output=True,
                    text=True,
                    env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
                )
                
                if result.returncode == 0:
                    print(f"\n✓ All tests for {module_name} passed successfully!")
                else:
                    print(f"\n✗ Some tests for {module_name} failed. Details:")
                    print(result.stdout)
                    print(result.stderr)
            except Exception as e:
                print(f"Error running tests: {e}")
            
            all_results.append({
                "module_name": module_name,
                "test_filename": test_filename
            })
        
        # If at least one implementation was tested successfully
        return len(all_results) > 0
            
    except Exception as e:
        print(f"\nError in test generation workflow: {e}")
        import traceback
        print(traceback.format_exc())
        return False

async def documentation_workflow(arch_controller, model_manager):
    """Run the documentation generation workflow for implemented components."""
    print("\n📊 Documentation Generation Workflow")
    print("-" * 40)
    
    # Find Python implementations and their test files
    component_files = []
    
    print("\nLooking for implemented components...")
    try:
        # Collect regular Python files
        python_files = [f for f in os.listdir('.') if f.endswith('.py') and not f.startswith('test_')]
        
        # Match each with its test file if available
        for filename in python_files:
            module_name = os.path.splitext(filename)[0]
            test_filename = f"test_{module_name}.py"
            
            if os.path.exists(test_filename):
                component_files.append((module_name, filename, test_filename))
            else:
                component_files.append((module_name, filename, None))
        
        if not component_files:
            print("\n⚠️ No Python implementations found. Please run Step 4 first.")
            return False
        
        print("\nAvailable components:")
        for i, (module_name, _, _) in enumerate(component_files):
            print(f"{i+1}. {module_name}")
        
        # Ask which component(s) to document
        print("\nSelect component(s) to document (comma-separated numbers, or 'all' for all components):")
        component_selection = input()
        
        components_to_document = []
        if component_selection.lower() == 'all':
            components_to_document = component_files
        else:
            try:
                indices = [int(idx.strip()) - 1 for idx in component_selection.split(',')]
                for idx in indices:
                    if 0 <= idx < len(component_files):
                        components_to_document.append(component_files[idx])
                    else:
                        print(f"Invalid selection: {idx+1}")
            except ValueError:
                print("Invalid input. Please enter numbers separated by commas.")
                return False
        
        # Process each selected component
        all_results = []
        for module_name, filename, test_filename in components_to_document:
            print(f"\n🔹 Documenting {module_name}...")
            
            # Read implementation
            with open(filename, 'r') as f:
                implementation = f.read()
            
            # Append test code if available
            if test_filename and os.path.exists(test_filename):
                with open(test_filename, 'r') as f:
                    test_code = f.read()
                implementation += f"\n\n# Test code\n{test_code}"
            
            # Generate documentation for this component
            result = await arch_controller.generate_with_prompt("documentation_generation", {
                "component_name": module_name,
                "component_implementation": implementation
            })
            
            print(f"\n✅ {module_name} documentation complete!")
            print("\nPreview:")
            print("-" * 40)
            print(result[:300] + "..." if len(result) > 300 else result)
            
            # Auto-save to file
            doc_filename = f"{module_name}_documentation.md"
            with open(doc_filename, 'w') as f:
                f.write(result)
            
            print(f"Documentation saved to {doc_filename}")
            
            all_results.append({
                "module_name": module_name,
                "documentation": result,
                "doc_filename": doc_filename
            })
        
        # If at least one component was documented successfully
        return len(all_results) > 0
            
    except Exception as e:
        print(f"\nError generating documentation: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

async def full_sdlc_workflow(arch_controller):
    """Run the full SDLC pipeline."""
    print("\n🔄 Full SDLC Pipeline")
    print("-" * 40)
    
    # Get project requirements
    print("\nPlease provide the project requirements:")
    requirements = input_multiline()
    
    print("\n🚀 Running complete SDLC pipeline...")
    print("This may take some time...")
    
    results = await arch_controller.run_complete_sdlc(requirements)
    
    print("\n✅ SDLC pipeline complete! All artifacts saved to output directory.")
    print("\nSummary of generated artifacts:")
    print("-" * 40)
    
    for key in results:
        if key == 'final_report':
            continue
        print(f"- {key.replace('_', ' ').title()}")
    
    print("\nFinal Report Preview:")
    print("-" * 40)
    report = results.get('final_report', 'No report available')
    print(report[:500] + "..." if len(report) > 500 else report)
    
    return True

def view_artifacts():
    """View available artifacts."""
    print("\n📁 Available Artifacts")
    print("-" * 40)
    
    # Check standard output directories
    directories = ["genai_artifacts", "output", "prompts", "."]
    artifacts = []
    
    for directory in directories:
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                if os.path.isfile(os.path.join(directory, filename)):
                    # Only include relevant file types
                    if filename.endswith(('.py', '.md', '.txt', '.json')):
                        artifacts.append((filename, directory))
    
    if not artifacts:
        print("No artifacts found.")
        return
    
    # Display artifacts
    for i, (filename, directory) in enumerate(artifacts):
        print(f"{i+1}. {filename} (in {directory})")
    
    # Ask if user wants to view an artifact
    try:
        choice = input("\nEnter artifact number to view (0 to cancel): ")
        if choice == "0":
            return
        
        choice = int(choice) - 1
        if 0 <= choice < len(artifacts):
            filename, directory = artifacts[choice]
            file_path = os.path.join(directory, filename)
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            print(f"\n📄 Content of {filename}:")
            print("-" * 40)
            
            # For large files, only show the beginning
            if len(content) > 1000:
                print(content[:1000] + "...\n(Content truncated, file is too large to display fully)")
            else:
                print(content)
        else:
            print("Invalid selection.")
    except ValueError:
        print("Please enter a number.")
    except Exception as e:
        print(f"Error: {e}")

def configure_pipeline(prompt_registry):
    """Configure the development pipeline."""
    print("\n⚙️ Pipeline Configuration")
    print("-" * 40)
    
    print("\nConfiguration Options:")
    print("1. View/Edit Prompt Templates")
    print("2. Create New Prompt Pipeline")
    print("3. Back to Main Menu")
    
    choice = input("\nSelect an option (1-3): ")
    
    if choice == "1":
        # View/Edit Prompt Templates
        templates = prompt_registry.templates
        
        if not templates:
            print("No templates available.")
            return
        
        # Display templates
        print("\nAvailable Templates:")
        for i, (name, template) in enumerate(templates.items()):
            print(f"{i+1}. {name}")
        
        # Ask if user wants to edit a template
        try:
            template_choice = input("\nEnter template number to edit (0 to cancel): ")
            if template_choice == "0":
                return
            
            template_choice = int(template_choice) - 1
            if 0 <= template_choice < len(templates):
                template_name = list(templates.keys())[template_choice]
                template = templates[template_name]
                
                print(f"\nCurrent Template: {template_name}")
                print(f"Template Content:\n{template.template[:200]}...")
                
                edit = input("\nEdit this template? (y/n): ").lower()
                if edit == 'y':
                    print("\nEnter new template content (Ctrl+D or Ctrl+Z+Enter to finish):")
                    new_content = input_multiline()
                    
                    metadata = template.metadata or {}
                    new_template = PromptTemplate(new_content, metadata)
                    prompt_registry.register_template(template_name, new_template)
                    print(f"Template '{template_name}' updated!")
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a number.")
        except Exception as e:
            print(f"Error: {e}")
            
    elif choice == "2":
        # Create New Prompt Pipeline
        pipeline_name = input("\nEnter the name for the new pipeline: ")
        
        templates = prompt_registry.templates
        if not templates:
            print("No templates available to create a pipeline.")
            return
        
        # Display templates
        print("\nAvailable Templates:")
        for i, name in enumerate(templates.keys()):
            print(f"{i+1}. {name}")
        
        # Ask for templates to include
        print("\nEnter template numbers to include in the pipeline (comma-separated):")
        template_choices = input()
        
        try:
            template_indices = [int(idx.strip()) - 1 for idx in template_choices.split(',')]
            template_names = []
            
            for idx in template_indices:
                if 0 <= idx < len(templates):
                    template_names.append(list(templates.keys())[idx])
                else:
                    print(f"Invalid template index: {idx+1}")
            
            if template_names:
                pipeline = prompt_registry.create_pipeline(pipeline_name, template_names)
                print(f"Pipeline '{pipeline_name}' created with templates: {', '.join(template_names)}")
            else:
                print("No valid templates selected.")
        except ValueError:
            print("Please enter valid numbers.")
        except Exception as e:
            print(f"Error: {e}")
    
    elif choice == "3":
        return
    
    else:
        print("Invalid option.")

def input_multiline():
    """Get multiline input from the user."""
    print("Enter text (press Enter twice to finish):")
    lines = []
    
    while True:
        line = input()
        if not line and (not lines or not lines[-1]):
            break
        lines.append(line)
    
    return '\n'.join(lines)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interactive GenAI Development Pipeline")
    parser.add_argument('--noninteractive', action='store_true', help='Run in non-interactive mode')
    parser.add_argument('--requirements', type=str, help='Path to requirements file')
    parser.add_argument('--output', type=str, default='output', help='Output directory')
    
    args = parser.parse_args()
    
    if args.noninteractive and args.requirements:
        # Non-interactive mode with requirements file
        with open(args.requirements, 'r') as f:
            requirements = f.read()
        
        async def run_noninteractive():
            arch_controller = GenAIArchitectureController()
            results = await arch_controller.run_complete_sdlc(requirements)
            print(f"SDLC pipeline complete! {len(results)} artifacts generated.")
        
        asyncio.run(run_noninteractive())
    else:
        # Interactive mode
        asyncio.run(interactive_development_session())