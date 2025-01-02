"""Execution engine for the order fulfillment system."""

from typing import Dict, List, Optional
import json
from openai import OpenAI
from utils import OutputManager, append_message
from registry import FunctionRegistry
from functions import BusinessFunctions
from context import Context, ContextConfig
from config import ModelConfig
from plans import Plan, PlanGenerator

class PolicyExecutor:
    """Handles the execution of fulfillment policies using AI."""
    
    def __init__(
        self, 
        api_key: str, 
        model_config: ModelConfig = ModelConfig,
        context_config: Optional[ContextConfig] = None
    ):
        """Initialize the executor with configurations."""
        self.client = OpenAI(api_key=api_key)
        self.model_config = model_config
        self.context = Context.create_context(context_config)
        self.business_functions = BusinessFunctions(self.context)
        self.function_mapping = self.business_functions.get_function_mapping()
        self.tools = FunctionRegistry.generate_tools_list(self.function_mapping)
        self.message_list = []
        self.plan_generator = PlanGenerator(api_key, model_config)

    def generate_plan(self, scenario: str) -> Plan:
        """Generate a new plan."""
        return self.plan_generator.generate_plan(scenario, self.function_mapping)

    def execute_plan(self, plan: Plan, output: OutputManager) -> List[Dict]:
        """Execute a pre-generated plan."""
        executor_config = self.model_config.get_executor_config()
        
        system_prompt = executor_config['prompt_template'].format(plan=plan.plan_text)
        
        messages = [
            {'role': 'system', 'content': system_prompt},
        ]

        append_message({
            'type': 'context',
            'message': f'Before the plan is executed, here is the current context:\n{json.dumps(self.context, indent=4)}'
        }, output, self.message_list)

        while True:
            response = self.client.chat.completions.create(
                model=executor_config['model'],
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            messages.append({"role": "assistant", "content": response_message.content})
            
            # Check if there's a function call
            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    
                    # Check if processing is complete
                    if function_name == 'processing_complete':
                        return self.message_list
                        
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Log the function call
                    append_message({
                        'type': 'function_call',
                        'function': function_name,
                        'args': function_args
                    }, output, self.message_list)
                    
                    # Execute the function
                    function_to_call = self.function_mapping[function_name]
                    function_response = function_to_call(**function_args)
                    
                    # Log the response
                    append_message({
                        'type': 'function_response',
                        'function': function_name,
                        'response': function_response
                    }, output, self.message_list)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps(function_response)
                    })
            else:
                # If no function call, we're done
                break
                
        return self.message_list

    def process_scenario(self, scenario: str, existing_plan: Optional[Plan] = None) -> List[Dict]:
        """Process a scenario with optional pre-generated plan."""
        with OutputManager() as output:
            if existing_plan is None:
                append_message({
                    'type': 'status', 
                    'message': 'Generating new plan...'
                }, output, self.message_list)
                
                plan = self.generate_plan(scenario)
                
                # Save the generated plan
                plan.save()
            else:
                plan = existing_plan
                append_message({
                    'type': 'status', 
                    'message': f'Using existing plan generated by {plan.model_used}'
                }, output, self.message_list)
            
            append_message({
                'type': 'plan', 
                'content': plan.plan_text
            }, output, self.message_list)
            
            append_message({
                'type': 'status', 
                'message': 'Executing plan...'
            }, output, self.message_list)
            
            messages = self.execute_plan(plan, output)
            
            append_message({
                'type': 'status', 
                'message': 'Processing complete.'
            }, output, self.message_list)
            
            return messages