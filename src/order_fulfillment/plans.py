"""Plan management for the order fulfillment system."""

from dataclasses import dataclass
from typing import Optional
import json
from pathlib import Path
from datetime import datetime
from openai import OpenAI
from registry import FunctionRegistry
from config import ModelConfig

@dataclass
class Plan:
    """Represents a fulfillment plan."""
    scenario: str
    plan_text: str
    model_used: str
    created_at: str = datetime.now().isoformat()

    def save(self, filename: Optional[str] = None):
        """Save the plan to a file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"plan_{timestamp}.json"
        
        path = Path("run_results/plans") / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(self.__dict__, f, indent=2)
        
        return path

    @classmethod
    def load(cls, filename: str) -> 'Plan':
        """Load a plan from a file."""
        path = Path("run_results/plans") / filename
        with open(path) as f:
            data = json.load(f)
        return cls(**data)

class PlanGenerator:
    """Generates fulfillment plans using AI."""
    
    def __init__(self, api_key: str, model_config: ModelConfig = ModelConfig):
        """Initialize the plan generator."""
        self.client = OpenAI(api_key=api_key)
        self.model_config = model_config

    def generate_plan(self, scenario: str, function_mapping: dict) -> Plan:
        """Generate a plan for the given scenario."""
        planner_config = self.model_config.get_planner_config()
        functions_description = FunctionRegistry.generate_functions_description(function_mapping)
        
        prompt = planner_config['prompt_template'].format(
            functions_description=functions_description,
            scenario=scenario
        )

        response = self.client.chat.completions.create(
            model=planner_config['model'],
            messages=[{'role': 'user', 'content': prompt}]
        )
        
        return Plan(
            scenario=scenario,
            plan_text=response.choices[0].message.content,
            model_used=planner_config['model']
        )