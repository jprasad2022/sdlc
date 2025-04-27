# prompt_pipeline.py
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from string import Template

class PromptTemplate:
    def __init__(self, template: str, metadata: Dict[str, Any] = None):
        """Initialize a prompt template with metadata."""
        self.template = template
        self.metadata = metadata or {}
    
    def format(self, **kwargs) -> str:
        """Format the template with the provided variables."""
        template = Template(self.template)
        return template.safe_substitute(**kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary representation."""
        return {
            "template": self.template,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptTemplate':
        """Create template from dictionary representation."""
        return cls(data["template"], data.get("metadata"))

class PromptPipeline:
    def __init__(self, name: str, templates: List[PromptTemplate] = None):
        """Initialize a pipeline of prompts."""
        self.name = name
        self.templates = templates or []
    
    def add_template(self, template: PromptTemplate) -> None:
        """Add a template to the pipeline."""
        self.templates.append(template)
    
    def execute(self, variables: Dict[str, Any], llm_client: Any) -> List[str]:
        """Execute the pipeline of templates with the provided variables."""
        results = []
        
        for i, template in enumerate(self.templates):
            # Format the template
            prompt = template.format(**variables)
            
            # Update variables with results from previous steps
            for j, result in enumerate(results):
                variables[f"result_{j}"] = result
            
            # Execute the prompt with the LLM
            response = llm_client.chat.completions.create(
                model=template.metadata.get("model", "gpt-4o"),
                messages=[
                    {"role": "system", "content": template.metadata.get("system_prompt", "You are a helpful assistant.")},
                    {"role": "user", "content": prompt}
                ],
                temperature=template.metadata.get("temperature", 0.7)
            )
            
            result = response.choices[0].message.content
            results.append(result)
        
        return results
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pipeline to dictionary representation."""
        return {
            "name": self.name,
            "templates": [t.to_dict() for t in self.templates]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptPipeline':
        """Create pipeline from dictionary representation."""
        templates = [PromptTemplate.from_dict(t) for t in data.get("templates", [])]
        return cls(data["name"], templates)

class PromptRegistry:
    def __init__(self, registry_path: str = "prompts/registry.json"):
        """Initialize the prompt registry."""
        self.registry_path = registry_path
        self.templates: Dict[str, PromptTemplate] = {}
        self.pipelines: Dict[str, PromptPipeline] = {}
        
        # Load registry if it exists
        self._load_registry()
    
    def _load_registry(self) -> None:
        """Load registry from file if it exists."""
        if os.path.exists(self.registry_path):
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # DEBUG:
            print(f"Loaded registry from {self.registry_path}, templates:", list(data.get("templates", {}).keys()))  
                      
            # Load templates
            templates_data = data.get("templates", {})
            for name, template_data in templates_data.items():
                self.templates[name] = PromptTemplate.from_dict(template_data)
            
            # Load pipelines
            pipelines_data = data.get("pipelines", {})
            for name, pipeline_data in pipelines_data.items():
                self.pipelines[name] = PromptPipeline.from_dict(pipeline_data)
    
    def save_registry(self) -> None:
        """Save registry to file."""
        registry_dir = os.path.dirname(self.registry_path)
        os.makedirs(registry_dir, exist_ok=True)
        
        data = {
            "templates": {name: template.to_dict() for name, template in self.templates.items()},
            "pipelines": {name: pipeline.to_dict() for name, pipeline in self.pipelines.items()}
        }
        
        with open(self.registry_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def register_template(self, name: str, template: PromptTemplate) -> None:
        """Register a new template."""
        self.templates[name] = template
        self.save_registry()
    
    def register_pipeline(self, pipeline: PromptPipeline) -> None:
        """Register a new pipeline."""
        self.pipelines[pipeline.name] = pipeline
        self.save_registry()
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get a template by name."""
        return self.templates.get(name)
    
    def get_pipeline(self, name: str) -> Optional[PromptPipeline]:
        """Get a pipeline by name."""
        return self.pipelines.get(name)
    
    def create_pipeline(self, name: str, template_names: List[str]) -> PromptPipeline:
        """Create a pipeline from existing templates."""
        templates = []
        for template_name in template_names:
            template = self.get_template(template_name)
            if template:
                templates.append(template)
            else:
                raise ValueError(f"Template '{template_name}' not found")
        
        pipeline = PromptPipeline(name, templates)
        self.register_pipeline(pipeline)
        return pipeline