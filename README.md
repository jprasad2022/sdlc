# Insurance Graph RAG System

## Overview

This project implements a fully automated Graph Retrieval-Augmented Generation (RAG) system designed specifically for the insurance domain. The system leverages Generative AI throughout the software development lifecycle to automate every aspect of solution development, from document processing to knowledge graph construction, query handling, testing, and operation.

## Key Features

- **Zero-Shot Document Processing**: Automatically ingests and processes insurance documents without predefined templates, extracting structured information to build the knowledge graph.

- **Self-Evolving Graph Schema**: Continuously adapts the knowledge graph schema based on new data patterns without human intervention.

- **End-to-End Query Processing**: Handles the complete pipeline from understanding user queries to generating responses, with dynamic improvement capabilities.

- **Fully Automated Testing & QA**: Continuously verifies system performance, identifies issues, and implements fixes without human supervision.

- **Human-AI Collaboration Minimization**: Intelligently determines when responses can be provided without human review and handles exceptions automatically.

## System Architecture

The system consists of five main components:

1. **InsuranceDocumentProcessor**: Handles document crawling, analysis, and extraction of structured data to build and maintain the knowledge graph.

2. **SelfEvolvingGraphSchema**: Manages the knowledge graph schema, evolving it based on new data patterns. Can identify new entity types, properties, and relationships based on instance data analysis.

3. **GraphRAGQueryProcessor**: Processes user queries, extracts parameters, executes graph queries, and generates responses. Features intent recognition, parameter extraction, and template-based response generation.

4. **AutomatedQASystem**: Performs automated testing, diagnoses issues, and applies fixes. Continuously monitors performance, identifies error patterns, and proposes improvements.

5. **AutomationManager**: Minimizes human intervention by managing autonomous decision-making and exception handling. Learns from feedback to improve confidence thresholds and exception handlers.

These components are integrated by the **InsuranceGraphRAGSystem** that coordinates their interaction and provides a unified interface.

## GenAI Integration

The system demonstrates comprehensive use of GenAI techniques throughout the SDLC:

- **Prompt Engineering**: Custom-designed prompts for document processing, query analysis, and response generation
- **Chain-of-Thought Reasoning**: Structured reasoning for complex decisions and scenario analysis
- **Few-Shot Learning**: Examples for specialized extraction and classification tasks
- **Continuous Learning**: Self-improvement mechanisms based on observed patterns and feedback
- **Model Orchestration**: Dynamic selection and optimization of models for different tasks

## Installation

### Prerequisites

- Python 3.8+
- Required Python packages:
  - numpy
  - pandas
  - matplotlib
  - networkx
  - transformers
  - torch
  - sklearn
  - spacy
  - beautifulsoup4
  - PyPDF2
  - python-docx
  - openai (for LLM API calls)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/insurance-graph-rag.git
cd insurance-graph-rag
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Download spaCy model:
```bash
python -m spacy download en_core_web_lg
```

4. Set up environment variables:
```bash
# Create a .env file with your API keys
echo "OPENAI_API_KEY=your_openai_api_key" > .env
```

5. Prepare a data directory for your insurance documents:
```bash
mkdir -p data/insurance_documents
# Place your insurance documents in this directory
```

## Usage

### Basic Usage

```python
from src.insurance_graph_rag_system import InsuranceGraphRAGSystem

# Initialize the system
system = InsuranceGraphRAGSystem(config_path="config.json")

# Process documents and build knowledge graph
system.initialize_system(sources=["data/insurance_documents"])

# Process a query
response = system.process_query(
    "What does my policy P1001 cover?", 
    user_context={'user_id': 'U5001'}
)

print(response['answer'])
```

### Command Line Interface

The system can also be used from the command line:

```bash
# Run with interactive development mode
python main.py --mode develop

# Run automated development pipeline
python main.py --mode automate --requirements requirements.txt --output_dir genai_artifacts

# Run the system with interactive demo
python main.py --mode run --data_dir data/insurance_documents --interactive --improve
```

## Interactive Development Pipeline

The system includes an interactive development pipeline that guides you through each phase of development using GenAI:

1. **Requirements Analysis**: Generate structured requirements from business needs
2. **Architecture Design**: Design high-level system architecture
3. **Component Design**: Design detailed component structures
4. **Code Generation**: Generate production-ready code
5. **Test Generation**: Create comprehensive test suites
6. **Documentation Generation**: Create technical documentation

To use the pipeline:

```bash
python main.py --mode develop
```

## Configuration

The system configuration is stored in `config.json`:

```json
{
  "data_dir": "data/insurance_documents",
  "output_dir": "output",
  "logging": {
    "level": "INFO",
    "file": "insurance_rag_system.log"
  },
  "components": {
    "document_processor": {
      "model_name": "sentence-transformers/all-mpnet-base-v2"
    },
    "schema_manager": {
      "base_schema_path": null
    },
    "query_processor": {
      "model_name": "sentence-transformers/all-mpnet-base-v2"
    },
    "qa_system": {
      "llm_model_name": "gpt-4o-mini",
      "api_type": "openai",
      "test_count": 10
    },
    "automation_manager": {
      "default_threshold": 0.8
    }
  }
}
```

## Directory Structure

```
insurance-graph-rag/
│
├── main.py                              # Main entry point
├── config.json                          # Configuration file
├── requirements.txt                     # Dependencies
├── .env                                 # Environment variables
│
├── genai/                               # GenAI orchestration components
│   ├── __init__.py
│   ├── genai_architecture_controller.py # Controls the SDLC process
│   ├── model_interaction_manager.py     # Manages model interactions
│   ├── prompt_pipeline.py               # Handles prompt templates and pipelines
│   ├── genai_test_framework.py          # Test generation and analysis
│   └── interactive_development_pipeline.py  # Interactive development
│
├── prompts/                             # Prompt templates
│   ├── registry.json                    # Registry of prompt templates
│   ├── requirements_analysis.txt        # Requirements analysis template
│   ├── architecture_design.txt          # Architecture design template
│   └── ...                              # Other prompt templates
│
├── src/                                 # Core system implementation
│   ├── __init__.py
│   ├── insurance_graph_rag_system.py    # Main system class
│   ├── document_processor.py            # Document processing
│   ├── self_evolving_graph_schema.py    # Schema management
│   ├── graph_rag_query_processor.py     # Query processing
│   ├── enhanced_query_processor.py      # Enhanced query processing
│   ├── automation_manager.py            # Automation management
│   └── automated_qa_system.py           # Automated QA
│
├── data/                                # Data directories
│   ├── insurance_documents/             # Input documents
│   └── knowledge_graph/                 # Knowledge graph data
│
├── output/                              # Output artifacts
│   ├── genai_artifacts/                 # GenAI-generated artifacts
│   ├── schema/                          # Generated schemas
│   ├── visualizations/                  # Generated visualizations
│   └── test_results/                    # Test results
│
├── tests/                               # Test suite
│   ├── __init__.py
│   ├── test_document_processor.py       # Tests for document processor
│   ├── test_schema_manager.py           # Tests for schema manager
│   ├── test_query_processor.py          # Tests for query processor
│   └── test_automation.py               # Tests for automation
│
└── docs/                                # Documentation
    ├── requirements_analysis.md         # Requirements analysis
    ├── architecture.md                  # System architecture
    ├── genai_integration.md             # GenAI integration details
    ├── prompt_engineering.md            # Prompt engineering guide
    └── api_reference.md                 # API documentation
```

## Examples

### Document Processing Example

```python
from src.document_processor import InsuranceDocumentProcessor

# Initialize document processor
processor = InsuranceDocumentProcessor()

# Process a batch of documents
document_paths = ["data/insurance_documents/policy1.pdf", 
                  "data/insurance_documents/policy2.pdf"]
results = processor.process_document_batch(document_paths)

# Export to graph format
processor.export_to_graph_format("output/knowledge_graph.json")
```

### Query Processing Example

```python
from src.enhanced_query_processor import EnhancedGraphRAGQueryProcessor

# Initialize query processor
processor = EnhancedGraphRAGQueryProcessor(
    schema_path="output/schema/insurance_schema.json",
    knowledge_graph_path="output/knowledge_graph.json"
)

# Process a query
response = processor.process_query(
    "What is my deductible for collision coverage on policy P1001?",
    user_context={"user_id": "U5001"}
)

print(f"Intent: {response['intent']}")
print(f"Answer: {response['answer']}")
```

### Automated Testing Example

```python
from src.automated_qa_system import AutomatedQASystem

# Initialize QA system
qa_system = AutomatedQASystem(query_processor, schema_manager)

# Run test suite
test_results = qa_system.run_test_suite(suite_name="coverage_inquiry")

# Diagnose and fix issues
diagnostics = qa_system.diagnose_failures(test_results)
fix_results = qa_system.fix_common_issues(diagnostics)

# Generate performance report
report = qa_system.generate_performance_report()
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.