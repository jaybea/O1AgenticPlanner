"""Configuration management for the order fulfillment system."""

from typing import Dict, Any

class ModelConfig:
    """Configuration for AI models and prompts."""
    
    PLANNER_MODEL = 'o1-mini'
    EXECUTOR_MODEL = 'gpt-4o-mini'
    
    PLANNER_PROMPT = """
You are an order fulfillment assistant. Your task is to create a detailed plan for processing orders,
managing inventory, and coordinating with suppliers.

The available functions and their descriptions are:
{functions_description}

Please create a detailed plan for the following scenario:
{scenario}

Format your plan with numbered steps and lettered sub-steps. 
*** Ensure that 'instructions_complete' is the last step. Don't run indefinitely, even if an error occurs. ***
"""

    EXECUTOR_PROMPT = """
You are a policy execution assistant responsible for implementing the given plan. Do not analyze the plan, just execute it.
Follow each step carefully, calling the appropriate provided functions to complete the tasks.
Explain and justify each step you take.

PLAN:
{plan}
"""

    @classmethod
    def get_planner_config(cls) -> Dict[str, Any]:
        """Get configuration for the planner model."""
        return {
            'model': cls.PLANNER_MODEL,
            'prompt_template': cls.PLANNER_PROMPT,
        }
    
    @classmethod
    def get_executor_config(cls) -> Dict[str, Any]:
        """Get configuration for the executor model."""
        return {
            'model': cls.EXECUTOR_MODEL,
            'prompt_template': cls.EXECUTOR_PROMPT,
        }