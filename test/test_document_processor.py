import unittest
import os
import json
from unittest.mock import patch, MagicMock
import sys
sys.path.append('../')  # Add parent directory to path

from src.document_processor import InsuranceDocumentProcessor

class TestInsuranceDocumentProcessor(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures, if any."""
        self.processor = InsuranceDocumentProcessor(model_name="test-model")
        # Create a test directory
        os.makedirs("test_docs", exist_ok=True)
        # Create a sample document
        with open("test_docs/sample_policy.txt", "w") as f:
            f.write("This is a sample insurance policy with coverage limits of $500,000 and a deductible of $1,000.")
    
    def tearDown(self):
        """Tear down test fixtures, if any."""
        # Remove test files
        if os.path.exists("test_docs/sample_policy.txt"):
            os.remove("test_docs/sample_policy.txt")
        if os.path.exists("test_docs"):
            os.rmdir("test_docs")
    
    @patch('src.document_processor.requests')
    def test_crawl_web_source(self, mock_requests):
        """Test crawling a web source for insurance documents."""
        # Mock the requests response
        mock_response = MagicMock()
        mock_response.text = '<html><a href="policy.pdf">Policy PDF</a></html>'
        mock_requests.get.return_value = mock_response
        
        # Call the method
        docs = self.processor._crawl_web_source("https://example.com")
        
        # Check that requests.get was called with the correct URL
        mock_requests.get.assert_called_once_with("https://example.com")
        
        # Assertions would depend on implementation details
        # This is just a placeholder assertion
        self.assertEqual(isinstance(docs, list), True)
    
    def test_is_insurance_document(self):
        """Test identification of insurance documents."""
        # Test a document with insurance terms
        result = self.processor._is_insurance_document("test_docs/sample_policy.txt")
        self.assertTrue(result)
        
        # Create a non-insurance document
        with open("test_docs/non_insurance.txt", "w") as f:
            f.write("This is a random document with no insurance terms.")
        
        try:
            # Test a document without insurance terms
            result = self.processor._is_insurance_document("test_docs/non_insurance.txt")
            self.assertFalse(result)
        finally:
            # Clean up
            if os.path.exists("test_docs/non_insurance.txt"):
                os.remove("test_docs/non_insurance.txt")
    
    @patch('src.document_processor.OpenAI')
    def test_extract_with_llm(self, mock_openai):
        """Test extraction using LLM."""
        # Mock the OpenAI client and response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '{"entities": [], "relationships": []}'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Set the mock client
        self.processor.openai_client = mock_client
        
        # Call the method
        result = self.processor._extract_with_llm("Test prompt")
        
        # Verify the client was called correctly
        mock_client.chat.completions.create.assert_called_once()
        
        # Check the result
        self.assertEqual(result, '{"entities": [], "relationships": []}')
    
    def test_extract_definitions_from_text(self):
        """Test extraction of definitions from text."""
        text = '"Policyholder" means: The individual or entity that owns the insurance policy. "Premium" means: The amount paid for insurance coverage.'
        
        definitions = self.processor._extract_definitions_from_text(text)
        
        self.assertEqual(len(definitions), 2)
        self.assertEqual(definitions[0]['term'], 'Policyholder')
        self.assertEqual(definitions[0]['definition'], 'The individual or entity that owns the insurance policy')
        self.assertEqual(definitions[1]['term'], 'Premium')
        self.assertEqual(definitions[1]['definition'], 'The amount paid for insurance coverage')
    
    @patch('src.document_processor.InsuranceDocumentProcessor._extract_with_llm')
    @patch('src.document_processor.InsuranceDocumentProcessor._extract_full_text')
    def test_process_document(self, mock_extract_text, mock_extract_llm):
        """Test document processing."""
        # Mock text extraction
        mock_extract_text.return_value = "Sample policy text with coverage details"
        
        # Mock LLM extraction
        mock_extract_llm.return_value = json.dumps({
            "entities": [
                {
                    "id": "policy1",
                    "type": "Policy",
                    "name": "Sample Policy",
                    "attributes": {
                        "policy_number": "P12345",
                        "effective_date": "2023-01-01"
                    }
                }
            ],
            "relationships": []
        })
        
        # Process a document
        result = self.processor.process_document("test_docs/sample_policy.txt")
        
        # Check that extraction methods were called
        mock_extract_text.assert_called_once()
        
        # Check the result contains expected data
        self.assertIn('entities', result)
        self.assertIn('relationships', result)
        self.assertEqual(len(result['entities']), 1)
        self.assertEqual(result['entities'][0]['type'], 'Policy')

if __name__ == '__main__':
    unittest.main()