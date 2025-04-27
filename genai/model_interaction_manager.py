# model_interaction_manager.py
import os
import json
import time
from typing import Dict, Any, List, Optional, Union, Callable
import openai
import tiktoken
import logging
from openai import OpenAI
from dotenv import load_dotenv

class ModelEvaluation:
    def __init__(self, model_name: str, prompt: str, response: str, metrics: Dict[str, Any]):
        """Initialize model evaluation results."""
        self.model_name = model_name
        self.prompt = prompt
        self.response = response
        self.metrics = metrics
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert evaluation to dictionary representation."""
        return {
            "model_name": self.model_name,
            "prompt": self.prompt,
            "response": self.response,
            "metrics": self.metrics,
            "timestamp": self.timestamp
        }

class ModelInteractionManager:
    def __init__(self, config_path: str = "model_config.json"):
        """Initialize the model interaction manager."""
        load_dotenv()
        self.config = self._load_config(config_path)
        self.clients = self._initialize_clients()
        self.history = []
        self.evaluation_results = []
        self.logger = self._setup_logging()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
            "openai": {
                "models": ["gpt-4o", "gpt-3.5-turbo"],
                "default_model": "gpt-4o",
                "api_key_env": "OPENAI_API_KEY"
            },
            "logging": {
                "level": "INFO",
                "file": "model_interactions.log"
            }
        }
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
            
            # Merge with defaults
            for provider, settings in loaded_config.items():
                if provider in default_config:
                    default_config[provider].update(settings)
                else:
                    default_config[provider] = settings
        
        return default_config
    
    def _initialize_clients(self) -> Dict[str, Any]:
        """Initialize API clients for different providers."""
        clients = {}
        
        # Initialize OpenAI client if configured
        if "openai" in self.config:
            openai_config = self.config["openai"]
            api_key = os.getenv(openai_config.get("api_key_env", "OPENAI_API_KEY"))
            
            if api_key:
                clients["openai"] = OpenAI()
        
        return clients
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging."""
        logger = logging.getLogger("ModelInteractionManager")
        
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        
        logger.setLevel(log_level)
        
        # File handler
        if "file" in log_config:
            file_handler = logging.FileHandler(log_config["file"])
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def get_token_count(self, text: str, model: str = "gpt-4o") -> int:
        """Get the token count for a text string."""
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except Exception as e:
            self.logger.warning(f"Error counting tokens: {e}")
            # Approximate token count (rough estimate: 4 chars per token)
            return len(text) // 4
    
    async def run_completion(self, 
                      prompt: str, 
                      model: str = None, 
                      provider: str = "openai",
                      temperature: float = 0.7,
                      max_tokens: int = 2000,
                      system_prompt: str = None) -> Dict[str, Any]:
        """Run a completion with the specified model and parameters."""
        start_time = time.time()
        
        # Default model selection
        if model is None:
            if provider == "openai":
                model = self.config["openai"].get("default_model", "gpt-4o")
        
        if provider not in self.clients:
            raise ValueError(f"Provider '{provider}' not initialized")
        
        client = self.clients[provider]
        result = {"success": False, "error": None}
        
        try:
            # Count tokens
            prompt_tokens = self.get_token_count(prompt, model)
            
            # Default system prompt
            if system_prompt is None:
                system_prompt = "You are a helpful AI assistant specialized in software development and architecture."
            
            # Run completion
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Extract response
            response_text = response.choices[0].message.content
            
            # Count response tokens
            response_tokens = self.get_token_count(response_text, model)
            
            # Calculate metrics
            elapsed_time = time.time() - start_time
            tokens_per_second = (prompt_tokens + response_tokens) / elapsed_time if elapsed_time > 0 else 0
            
            # Build result
            result = {
                "success": True,
                "text": response_text,
                "metrics": {
                    "prompt_tokens": prompt_tokens,
                    "response_tokens": response_tokens,
                    "total_tokens": prompt_tokens + response_tokens,
                    "elapsed_time": elapsed_time,
                    "tokens_per_second": tokens_per_second
                }
            }
            
            # Log interaction
            self.logger.info(f"Completion successful: model={model}, tokens={prompt_tokens+response_tokens}, time={elapsed_time:.2f}s")
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_msg = str(e)
            
            self.logger.error(f"Completion error: model={model}, error={error_msg}")
            
            result["error"] = error_msg
            result["metrics"] = {
                "elapsed_time": elapsed_time
            }
        
        # Record in history
        entry = {
            "timestamp": time.time(),
            "provider": provider,
            "model": model,
            "prompt": prompt,
            "result": result
        }
        self.history.append(entry)
        
        return result
    
    async def evaluate_model(self, 
                      prompt: str,
                      model: str = None,
                      provider: str = "openai",
                      evaluator: Callable[[str, str], Dict[str, Any]] = None) -> ModelEvaluation:
        """Evaluate model performance on a prompt."""
        # Run completion
        result = await self.run_completion(prompt, model, provider)
        
        # Basic metrics
        metrics = result.get("metrics", {})
        
        # Custom evaluation if provided
        if evaluator and result["success"]:
            try:
                custom_metrics = evaluator(prompt, result["text"])
                metrics.update(custom_metrics)
            except Exception as e:
                self.logger.error(f"Evaluation error: {e}")
        
        # Create evaluation
        evaluation = ModelEvaluation(
            model_name=model,
            prompt=prompt,
            response=result.get("text", ""),
            metrics=metrics
        )
        
        # Store evaluation
        self.evaluation_results.append(evaluation)
        
        return evaluation
    
    async def compare_models(self, 
                      prompt: str,
                      models: List[str] = None,
                      provider: str = "openai",
                      evaluator: Callable[[str, str], Dict[str, Any]] = None) -> List[ModelEvaluation]:
        """Compare multiple models on the same prompt."""
        if models is None:
            if provider == "openai":
                models = self.config["openai"].get("models", ["gpt-4o"])
        
        evaluations = []
        
        for model in models:
            evaluation = await self.evaluate_model(prompt, model, provider, evaluator)
            evaluations.append(evaluation)
        
        return evaluations
    
    def export_history(self, output_path: str) -> None:
        """Export interaction history to a file."""
        with open(output_path, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def export_evaluations(self, output_path: str) -> None:
        """Export evaluation results to a file."""
        evaluations = [e.to_dict() for e in self.evaluation_results]
        with open(output_path, 'w') as f:
            json.dump(evaluations, f, indent=2)