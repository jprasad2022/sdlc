# API Reference: Insurance Graph RAG System

## Overview

This document provides a comprehensive reference for the APIs available in the Insurance Graph RAG System. The system is organized into multiple components, each with its own set of classes and methods.

## Document Processor API

The document processor handles the ingestion and processing of insurance documents.

### InsuranceDocumentProcessor

Main class for processing insurance documents and extracting structured data.

#### Constructor

```python
def __init__(self, schema_path: str = None, model_name: str = "sentence-transformers/all-mpnet-base-v2")
```

- **schema_path**: Path to the schema file (optional)
- **model_name**: Name of the model to use for embeddings

#### Methods

```python
def crawl_documents(self, sources: List[str]) -> List[str]
```
- **Description**: Crawls and identifies insurance documents from sources
- **Parameters**:
  - `sources`: List of URLs, directories, or APIs to crawl
- **Returns**: List of file paths to discovered documents

```python
def process_document(self, file_path: str) -> dict
```
- **Description**: Processes a document to extract structured information
- **Parameters**:
  - `file_path`: Path to the document file
- **Returns**: Dictionary containing extracted entities and relationships

```python
def process_document_batch(self, file_paths: List[str]) -> Dict[str, Any]
```
- **Description**: Processes multiple documents and merges their extracted information
- **Parameters**:
  - `file_paths`: List of paths to document files
- **Returns**: Dictionary with combined entities and relationships

```python
def export_to_graph_format(self, output_file: str) -> None
```
- **Description**: Exports processed data to a format suitable for graph database import
- **Parameters**:
  - `output_file`: Path to save the output file
- **Returns**: None

## Schema Manager API

The schema manager handles the evolution and management of the knowledge graph schema.

### SelfEvolvingGraphSchema

Main class for schema management and evolution.

#### Constructor

```python
def __init__(self, base_schema_path=None)
```

- **base_schema_path**: Optional path to a base schema file to start with

#### Methods

```python
def add_entity_type(self, name: str, properties: Dict[str, Any] = None, constraints: Dict[str, Any] = None) -> bool
```
- **Description**: Adds a new entity type to the schema
- **Parameters**:
  - `name`: Name of the entity type
  - `properties`: Dictionary of property definitions (optional)
  - `constraints`: Dictionary of constraints (optional)
- **Returns**: Boolean indicating success

```python
def add_relationship_type(self, name: str, source_type: str, target_type: str, properties: Dict[str, Any] = None, constraints: Dict[str, Any] = None) -> bool
```
- **Description**: Adds a new relationship type to the schema
- **Parameters**:
  - `name`: Name of the relationship type
  - `source_type`: Source entity type name
  - `target_type`: Target entity type name
  - `properties`: Dictionary of property definitions (optional)
  - `constraints`: Dictionary of constraints (optional)
- **Returns**: Boolean indicating success

```python
def get_entity_types(self) -> List[str]
```
- **Description**: Gets all entity type names in the schema
- **Returns**: List of entity type names

```python
def get_relationship_types(self) -> List[Dict[str, Any]]
```
- **Description**: Gets all relationship types in the schema
- **Returns**: List of relationship type dictionaries

```python
def analyze_instance_data(self, instance_data: Dict[str, Any]) -> Dict[str, Any]
```
- **Description**: Analyzes instance data to identify potential schema improvements
- **Parameters**:
  - `instance_data`: Dictionary containing nodes and edges from processed documents
- **Returns**: Dictionary of recommended schema changes

```python
def evolve_schema(self, instance_data: Dict[str, Any], threshold: float = 0.7) -> Dict[str, Any]
```
- **Description**: Automatically evolves the schema based on instance data
- **Parameters**:
  - `instance_data`: Dictionary containing nodes and edges from processed documents
  - `threshold`: Confidence threshold for automatic changes (0.0-1.0)
- **Returns**: Dictionary of applied changes

```python
def export_schema(self, output_file: str) -> None
```
- **Description**: Exports the current schema to a file
- **Parameters**:
  - `output_file`: Path to save the schema
- **Returns**: None

```python
def generate_visualization(self, output_file: str) -> None
```
- **Description**: Generates a visualization of the schema graph
- **Parameters**:
  - `output_file`: Path to save the visualization
- **Returns**: None

## Query Processor API

The query processor handles understanding and responding to user queries.

### GraphRAGQueryProcessor

Main class for processing queries against the knowledge graph.

#### Constructor

```python
def __init__(self, schema_path: str = None, knowledge_graph_path: str = None, model_name: str = "sentence-transformers/all-mpnet-base-v2")
```

- **schema_path**: Path to the schema file
- **knowledge_graph_path**: Path to the knowledge graph data
- **model_name**: Name of the model to use for embeddings

#### Methods

```python
def process_query(self, query_text: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]
```
- **Description**: Processes a user query end-to-end
- **Parameters**:
  - `query_text`: The user's query text
  - `user_context`: Optional context about the user
- **Returns**: Response dictionary with generated answer and metadata

```python
def analyze_intent(self, query_text: str) -> Dict[str, Any]
```
- **Description**: Analyzes the intent of a user query
- **Parameters**:
  - `query_text`: The user's query text
- **Returns**: Dictionary with intent analysis results

```python
def extract_parameters(self, query_text: str, intent: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]
```
- **Description**: Extracts parameters from the query text based on intent
- **Parameters**:
  - `query_text`: The user's query text
  - `intent`: The identified intent
  - `user_context`: Optional user context
- **Returns**: Dictionary of extracted parameters

```python
def build_graph_query(self, intent: str, params: Dict[str, Any]) -> Dict[str, Any]
```
- **Description**: Builds a graph query based on intent and parameters
- **Parameters**:
  - `intent`: The identified intent
  - `params`: Extracted parameters
- **Returns**: Dictionary representing the graph query

```python
def execute_graph_query(self, graph_query: Dict[str, Any]) -> Dict[str, Any]
```
- **Description**: Executes a graph query on the knowledge graph
- **Parameters**:
  - `graph_query`: Dictionary representing the graph query
- **Returns**: Query results

```python
def generate_response(self, intent: str, query_results: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]
```
- **Description**: Generates a natural language response based on query results
- **Parameters**:
  - `intent`: The identified intent
  - `query_results`: Results from the graph query
  - `params`: Extracted parameters
- **Returns**: Dictionary with generated response

### EnhancedGraphRAGQueryProcessor

Extended class with improved query processing capabilities.

#### Constructor

```python
def __init__(self, *args, **kwargs)
```

- Inherits constructor parameters from GraphRAGQueryProcessor

#### Methods

Inherits all methods from GraphRAGQueryProcessor with enhancements to these methods:

```python
def extract_parameters(self, query_text: str, intent: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]
```
- Enhanced version with better parameter extraction, especially for definition inquiries

```python
def build_graph_query(self, intent: str, params: Dict[str, Any]) -> Dict[str, Any]
```
- Enhanced version with better query building, especially for definition and term lookup

## Automation Manager API

The automation manager minimizes the need for human intervention.

### AutomationManager

Main class for managing autonomous decisions and human review.

#### Constructor

```python
def __init__(self, query_processor, qa_system)
```

- **query_processor**: The query processor instance
- **qa_system**: The automated QA system instance

#### Methods

```python
def process_query_with_automation(self, query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]
```
- **Description**: Processes a user query with automation to minimize human intervention
- **Parameters**:
  - `query`: The user's query text
  - `user_context`: Optional context about the user
- **Returns**: Response with automation metadata

```python
def record_feedback(self, query_id: str, was_correct: bool, feedback: str = None) -> None
```
- **Description**: Records feedback on an autonomous decision
- **Parameters**:
  - `query_id`: ID of the query
  - `was_correct`: Whether the autonomous decision was correct
  - `feedback`: Optional feedback text
- **Returns**: None

```python
def adjust_confidence_thresholds(self) -> Dict[str, Any]
```
- **Description**: Automatically adjusts confidence thresholds based on performance
- **Returns**: Dictionary with adjustment results

```python
def extend_exception_handlers(self) -> Dict[str, Any]
```
- **Description**: Automatically extends exception handlers based on escalation patterns
- **Returns**: Dictionary with extension results

```python
def learn_from_escalations(self) -> Dict[str, Any]
```
- **Description**: Learns from escalation history to improve future automation
- **Returns**: Dictionary with learning results

```python
def generate_self_improvement_report(self) -> Dict[str, Any]
```
- **Description**: Generates a comprehensive report on system self-improvement
- **Returns**: Self-improvement report dictionary

```python
def visualize_autonomy_metrics(self, output_file: str = "autonomy_metrics.png") -> None
```
- **Description**: Generates a visualization of autonomy metrics
- **Parameters**:
  - `output_file`: Path to save the visualization
- **Returns**: None

```python
def run_continuous_improvement_cycle(self, cycles: int = 1) -> Dict[str, Any]
```
- **Description**: Runs a continuous self-improvement cycle to maximize autonomy
- **Parameters**:
  - `cycles`: Number of improvement cycles to run
- **Returns**: Results of the improvement cycles

## Automated QA System API

The automated QA system handles testing and quality assurance.

### AutomatedQASystem

Main class for automated testing and quality assurance.

#### Constructor

```python
def __init__(self, query_processor, schema_manager, knowledge_graph_path: str = None)
```

- **query_processor**: The query processor instance
- **schema_manager**: The schema manager instance
- **knowledge_graph_path**: Path to the knowledge graph data

#### Methods

```python
def run_test_suite(self, suite_name: str = None, count: int = None) -> Dict[str, Any]
```
- **Description**: Runs a specific test suite or all test suites
- **Parameters**:
  - `suite_name`: Optional name of the test suite to run
  - `count`: Optional number of tests to run per suite
- **Returns**: Dictionary with test results

```python
def diagnose_failures(self, test_results: Dict[str, Any]) -> Dict[str, Any]
```
- **Description**: Analyzes test failures and identifies patterns
- **Parameters**:
  - `test_results`: Results from a test run
- **Returns**: Diagnostic information

```python
def fix_common_issues(self, diagnostics: Dict[str, Any]) -> Dict[str, Any]
```
- **Description**: Automatically fixes common issues identified in diagnostics
- **Parameters**:
  - `diagnostics`: Diagnostic information from diagnose_failures
- **Returns**: Dictionary with fix results

```python
def generate_performance_report(self) -> Dict[str, Any]
```
- **Description**: Generates a comprehensive performance report
- **Returns**: Performance report dictionary

```python
def visualize_test_results(self, test_results: Dict[str, Any], output_file: str = "test_results.png") -> None
```
- **Description**: Generates a visualization of test results
- **Parameters**:
  - `test_results`: Results from a test run
  - `output_file`: Path to save the visualization
- **Returns**: None

```python
def visualize_system_performance(self, performance_report: Dict[str, Any], output_file: str = "system_performance.png") -> None
```
- **Description**: Generates a visualization of system performance metrics
- **Parameters**:
  - `performance_report`: Performance report dictionary
  - `output_file`: Path to save the visualization
- **Returns**: None

```python
def run_self_improvement_cycle(self) -> Dict[str, Any]
```
- **Description**: Runs a complete self-improvement cycle
- **Returns**: Results of the improvement cycle

## System Integration API

The main system class integrates all components.

### InsuranceGraphRAGSystem

Main class for the integrated system.

#### Constructor

```python
def __init__(self, config_path: str = None)
```

- **config_path**: Path to configuration file

#### Methods

```python
def initialize_system(self, sources: List[str] = None) -> Dict[str, Any]
```
- **Description**: Initializes the system with document sources
- **Parameters**:
  - `sources`: List of document source paths
- **Returns**: Initialization results

```python
def process_query(self, query: str, user_context: Dict[str, Any] = None, autonomous: bool = True) -> Dict[str, Any]
```
- **Description**: Processes a user query through the system
- **Parameters**:
  - `query`: The user's query text
  - `user_context`: Optional user context information
  - `autonomous`: Whether to use the automation manager
- **Returns**: Response dictionary

```python
def run_improvement_cycle(self) -> Dict[str, Any]
```
- **Description**: Runs a complete improvement cycle for the system
- **Returns**: Dictionary with improvement results

```python
def generate_system_report(self) -> Dict[str, Any]
```
- **Description**: Generates a comprehensive system report
- **Returns**: System report dictionary

```python
def save_system_state(self, path: str = None) -> str
```
- **Description**: Saves current system state to a file
- **Parameters**:
  - `path`: Optional path to save state
- **Returns**: Path to saved state file

```python
def load_system_state(self, path: str) -> bool
```
- **Description**: Loads system state from a file
- **Parameters**:
  - `path`: Path to state file
- **Returns**: Boolean indicating success

```python
def run_interactive_demo(self) -> None
```
- **Description**: Runs an interactive demo of the system
- **Returns**: None