# genai_test_framework.py
import os
import json
import time
import random
from typing import Dict, Any, List, Callable, Optional
import unittest
import textwrap
import inspect
import asyncio
from datetime import datetime
import openai
from dotenv import load_dotenv

class TestGenerator:
    def __init__(self, model_client, model_name: str = "gpt-4o"):
        """Initialize the test generator."""
        self.model_client = model_client
        self.model_name = model_name
        self.test_history = []
    
    async def generate_unit_tests(self, 
                           code_snippet: str, 
                           module_name: str = None,
                           num_tests: int = 5,
                           focus_areas: List[str] = None) -> str:
        """Generate unit tests for a code snippet."""
        module_desc = f"module '{module_name}'" if module_name else "code"
        focus_desc = ""
        
        if focus_areas:
            focus_desc = f"\nFocus on testing these specific areas:\n" + "\n".join([f"- {area}" for area in focus_areas])
        
        prompt = f"""
        Generate {num_tests} comprehensive unit tests for the following {module_desc}.

        CODE:
        ```python
        {code_snippet}
        ```
        
        Requirements for the tests:
        1. Use the unittest framework
        2. Include proper setup and teardown methods if needed
        3. Use mocking when appropriate for external dependencies
        4. Include edge cases and error conditions
        5. Add clear docstrings explaining test purpose{focus_desc}
        
        Return ONLY valid Python code for the unit tests that can be directly executed.
        """
        
        response = await self.model_client.run_completion(
            prompt=prompt,
            model=self.model_name,
            temperature=0.2,
            max_tokens=4000
        )
        
        if not response.get("success", False):
            return f"Error generating tests: {response.get('error', 'Unknown error')}"
        
        test_code = response.get("text", "")
        
        # Strip markdown code blocks if present
        if "```python" in test_code and "```" in test_code:
            test_code = test_code.split("```python")[1].split("```")[0].strip()
        elif "```" in test_code:
            test_code = test_code.split("```")[1].split("```")[0].strip()
        
        # Record in history
        self.test_history.append({
            "timestamp": datetime.now().isoformat(),
            "module_name": module_name,
            "code_snippet_length": len(code_snippet),
            "generated_tests_length": len(test_code),
            "focus_areas": focus_areas
        })
        
        return test_code
    
    async def generate_integration_tests(self,
                                  component_definitions: List[Dict[str, str]],
                                  focus_scenario: str = None,
                                  num_tests: int = 3) -> str:
        """Generate integration tests for components."""
        components_text = ""
        for i, comp in enumerate(component_definitions):
            components_text += f"\nComponent {i+1}: {comp['name']}\n"
            components_text += f"Description: {comp['description']}\n"
            if 'interface' in comp:
                components_text += f"Interface:\n```python\n{comp['interface']}\n```\n"
        
        scenario_text = f"\nSpecific scenario to test: {focus_scenario}" if focus_scenario else ""
        
        prompt = f"""
        Generate {num_tests} comprehensive integration tests for the following components that interact with each other.
        
        {components_text}
        {scenario_text}
        
        Requirements for the tests:
        1. Use the unittest framework
        2. Focus on testing the interaction between components
        3. Include proper setup of mock dependencies
        4. Test error handling and edge cases in component interactions
        5. Add clear docstrings explaining the integration scenario being tested
        
        Return ONLY valid Python code for the integration tests that can be directly executed.
        """
        
        response = await self.model_client.run_completion(
            prompt=prompt,
            model=self.model_name,
            temperature=0.3,
            max_tokens=4000
        )
        
        if not response.get("success", False):
            return f"Error generating tests: {response.get('error', 'Unknown error')}"
        
        test_code = response.get("text", "")
        
        # Strip markdown code blocks if present
        if "```python" in test_code and "```" in test_code:
            test_code = test_code.split("```python")[1].split("```")[0].strip()
        elif "```" in test_code:
            test_code = test_code.split("```")[1].split("```")[0].strip()
        
        # Record in history
        self.test_history.append({
            "timestamp": datetime.now().isoformat(),
            "components": [c["name"] for c in component_definitions],
            "focus_scenario": focus_scenario,
            "generated_tests_length": len(test_code)
        })
        
        return test_code
    
    async def analyze_test_coverage(self, code_snippet: str, test_code: str) -> Dict[str, Any]:
        """Analyze the coverage of tests against the code."""
        prompt = f"""
        Analyze the test coverage of the following code and its test suite.
        
        IMPLEMENTATION CODE:
        ```python
        {code_snippet}
        ```
        
        TEST CODE:
        ```python
        {test_code}
        ```
        
        Perform a detailed analysis answering these questions:
        1. What percentage of functions/methods are covered by tests?
        2. What are the key edge cases that are tested?
        3. What edge cases or error conditions are NOT covered?
        4. Are there any critical bugs or issues the tests might miss?
        5. Rate the overall test quality from 1-10 and explain why.
        
        Provide the analysis in a structured JSON format with these fields: 
        - functions_covered_percent
        - covered_edge_cases
        - missing_edge_cases
        - potential_issues
        - quality_score
        - recommendations
        """
        
        response = await self.model_client.run_completion(
            prompt=prompt,
            model=self.model_name,
            temperature=0.1,
            max_tokens=3000
        )
        
        if not response.get("success", False):
            return {"error": response.get("error", "Unknown error")}
        
        # Extract JSON from response
        analysis_text = response.get("text", "")
        
        try:
            # Try to find and parse JSON in the response
            import re
            json_match = re.search(r'\{[\s\S]*\}', analysis_text)
            
            if json_match:
                json_str = json_match.group(0)
                analysis = json.loads(json_str)
            else:
                # Fallback - create structured response
                analysis = {
                    "functions_covered_percent": 0,
                    "covered_edge_cases": [],
                    "missing_edge_cases": [],
                    "potential_issues": [],
                    "quality_score": 0,
                    "recommendations": [],
                    "raw_analysis": analysis_text
                }
        except Exception as e:
            analysis = {
                "error": f"Failed to parse analysis: {str(e)}",
                "raw_analysis": analysis_text
            }
        
        return analysis
    
    async def improve_tests(self, test_code: str, analysis: Dict[str, Any]) -> str:
        """Improve test code based on analysis."""
        # Extract relevant information from analysis
        missing_edge_cases = analysis.get("missing_edge_cases", [])
        potential_issues = analysis.get("potential_issues", [])
        recommendations = analysis.get("recommendations", [])
        
        issues_text = ""
        if missing_edge_cases:
            issues_text += "Missing edge cases:\n" + "\n".join([f"- {case}" for case in missing_edge_cases]) + "\n\n"
        
        if potential_issues:
            issues_text += "Potential issues:\n" + "\n".join([f"- {issue}" for issue in potential_issues]) + "\n\n"
        
        if recommendations:
            issues_text += "Recommendations:\n" + "\n".join([f"- {rec}" for rec in recommendations]) + "\n\n"
        
        prompt = f"""
        Improve the following test code to address these issues:
        
        {issues_text}
        
        CURRENT TEST CODE:
        ```python
        {test_code}
        ```
        
        Please enhance this test code to address all the issues mentioned above.
        Return the improved test code only, as valid Python code that can be executed directly.
        """
        
        response = await self.model_client.run_completion(
            prompt=prompt,
            model=self.model_name,
            temperature=0.2,
            max_tokens=4000
        )
        
        if not response.get("success", False):
            return f"Error improving tests: {response.get('error', 'Unknown error')}"
        
        improved_test_code = response.get("text", "")
        
        # Strip markdown code blocks if present
        if "```python" in improved_test_code and "```" in improved_test_code:
            improved_test_code = improved_test_code.split("```python")[1].split("```")[0].strip()
        elif "```" in improved_test_code:
            improved_test_code = improved_test_code.split("```")[1].split("```")[0].strip()
        
        return improved_test_code

class GenAITestRunner:
    def __init__(self, test_generator: TestGenerator):
        """Initialize the test runner."""
        self.test_generator = test_generator
        self.test_results = []
    
    async def run_generated_tests(self, code_to_test: str, test_code: str) -> Dict[str, Any]:
        """Run generated tests against the code to test."""
        # Create temporary files
        test_filename = f"temp_test_{int(time.time())}.py"
        module_filename = f"temp_module_{int(time.time())}.py"
        
        try:
            # Write module code to file
            with open(module_filename, 'w') as f:
                f.write(code_to_test)
            
            # Adjust import in test code if needed
            adjusted_test_code = test_code.replace(
                "import unittest", 
                f"import unittest\nimport importlib.util\nspec = importlib.util.spec_from_file_location('module_under_test', '{module_filename}')\nmodule_under_test = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(module_under_test)"
            )
            adjusted_test_code = adjusted_test_code.replace(
                "from module_name import", 
                "from module_under_test import"
            )
            
            # Write test code to file
            with open(test_filename, 'w') as f:
                f.write(adjusted_test_code)
            
            # Run tests and capture output
            import subprocess
            result = subprocess.run(
                ['python', '-m', 'unittest', test_filename],
                capture_output=True,
                text=True
            )
            
            # Process results
            success = result.returncode == 0
            output = result.stdout + result.stderr
            
            test_result = {
                "success": success,
                "output": output,
                "timestamp": datetime.now().isoformat()
            }
            
            self.test_results.append(test_result)
            
            return test_result
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.test_results.append(error_result)
            return error_result
            
        finally:
            # Clean up temporary files
            for filename in [test_filename, module_filename]:
                if os.path.exists(filename):
                    os.remove(filename)
    
    async def complete_test_cycle(self, code_snippet: str, module_name: str = None) -> Dict[str, Any]:
        """Run a complete test cycle: generate, analyze, improve, and run tests."""
        results = {}
        
        # Step 1: Generate initial tests
        print("📝 Generating tests...")
        initial_tests = await self.test_generator.generate_unit_tests(
            code_snippet=code_snippet,
            module_name=module_name
        )
        results["initial_tests"] = initial_tests
        
        # Step 2: Analyze test coverage
        print("🔍 Analyzing test coverage...")
        analysis = await self.test_generator.analyze_test_coverage(
            code_snippet=code_snippet,
            test_code=initial_tests
        )
        results["analysis"] = analysis
        
        # Step 3: Improve tests based on analysis
        print("🔧 Improving tests...")
        improved_tests = await self.test_generator.improve_tests(
            test_code=initial_tests,
            analysis=analysis
        )
        results["improved_tests"] = improved_tests
        
        # Step 4: Run the improved tests
        print("🧪 Running tests...")
        test_results = await self.run_generated_tests(
            code_to_test=code_snippet,
            test_code=improved_tests
        )
        results["test_results"] = test_results
        
        # Step 5: Generate final report
        quality_score = analysis.get("quality_score", 0)
        passing = test_results.get("success", False)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "module_name": module_name,
            "tests_passing": passing,
            "quality_score": quality_score,
            "recommendations": analysis.get("recommendations", []),
            "next_steps": []
        }
        
        if not passing:
            report["next_steps"].append("Fix failing tests")
        
        if quality_score < 7:
            report["next_steps"].append("Further improve test coverage")
        
        results["report"] = report
        
        return results