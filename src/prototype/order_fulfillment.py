# Warning control
import warnings
warnings.filterwarnings('ignore')

# Import OpenAI key
from helper import get_openai_api_key
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, get_type_hints, Callable
import inspect
import json

openai_api_key = get_openai_api_key()

import copy
from openai import OpenAI

class FunctionRegistry:
    """Registry for functions with their metadata and parameter specifications."""
    
    @staticmethod
    def get_param_type(param: inspect.Parameter) -> Dict:
        """Convert a parameter's type annotation to JSON schema type."""
        type_map = {
            str: {"type": "string"},
            int: {"type": "integer"},
            float: {"type": "number"},
            bool: {"type": "boolean"},
            dict: {"type": "object"},
            list: {"type": "array"},
        }
        
        param_type = param.annotation
        if param_type == inspect.Parameter.empty:
            return {"type": "string"}  # default to string if no type hint
        return type_map.get(param_type, {"type": "string"})

    @classmethod
    def extract_function_metadata(cls, func: Callable) -> Dict:
        """Extract function metadata including description and parameters."""
        sig = inspect.signature(func)
        doc = inspect.getdoc(func) or ""
        
        properties = {}
        required = []
        
        for name, param in sig.parameters.items():
            if name == 'self':
                continue
                
            param_schema = cls.get_param_type(param)
            if param.default == inspect.Parameter.empty:
                required.append(name)
            
            # Add description from docstring if available
            param_desc = ""
            for line in doc.split('\n'):
                if f":param {name}:" in line:
                    param_desc = line.split(f":param {name}:")[1].strip()
                    break
            
            properties[name] = {
                **param_schema,
                "description": param_desc or f"The {name.replace('_', ' ')}."
            }
            
            # Add enum values if specified in docstring
            if ":enum:" in doc:
                enum_line = [line for line in doc.split('\n') if f":enum {name}:" in line]
                if enum_line:
                    enum_values = enum_line[0].split(f":enum {name}:")[1].strip().split(',')
                    properties[name]["enum"] = [v.strip() for v in enum_values]
        
        return {
            "description": doc.split('\n')[0],  # First line of docstring
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            }
        }

    @classmethod
    def generate_tools_list(cls, functions: Dict[str, Callable]) -> List[Dict]:
        """Generate the TOOLS list for OpenAI function calling."""
        tools = []
        for name, func in functions.items():
            metadata = cls.extract_function_metadata(func)
            tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    **metadata
                }
            })
        return tools

    @classmethod
    def generate_functions_description(cls, functions: Dict[str, Callable]) -> str:
        """Generate the functions description for the prompt."""
        descriptions = []
        for name, func in functions.items():
            doc = inspect.getdoc(func)
            if doc:
                first_line = doc.split('\n')[0]
                descriptions.append(f"    - {name}(): {first_line}")
        return '\n'.join(descriptions)

class MessageFormatter:
    """Handles message formatting and output for different message types."""
    
    @staticmethod
    def format_message(message_type: str, message: Dict[str, Any]) -> str:
        """Format a message based on its type."""
        formatters = {
            'status': lambda m: f"\n[Status] {m['message']}\n",
            'plan': lambda m: f"\n[Plan]\n{'-' * 80}\n{m['content']}\n{'-' * 80}",
            'assistant': lambda m: f"\n[Assistant]\n{'-' * 80}\n{m['content']}\n{'-' * 80}",
            'tool_call': lambda m: f"\n[Function Call] {m['function_name']}\nArguments: {m['arguments']}",
            'tool_response': lambda m: f"\n[Function Response] {m['function_name']}\nResult: {m['response']}",
            'context': lambda m: f"\n[Context]\n{'-' * 80}\n{m['message']}\n{'-' * 80}",
            'default': lambda m: f"\n{m.get('content', '')}" if m.get('content') else ""
        }
        
        formatter = formatters.get(message_type, formatters['default'])
        return formatter(message)

class OutputManager:
    """Manages output to both console and file."""
    
    def __init__(self):
        """Initialize the output manager."""
        self.file = None
        self.formatter = MessageFormatter()
        self.setup_output_file()
    
    def setup_output_file(self):
        """Set up the output file in the run_results directory."""
        base_dir = Path("run_results/fulfillment_runs")
        base_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = base_dir / f"fulfillment_run_{timestamp}.log"
        
        self.file = open(output_path, 'w', encoding='utf-8')
        print(f"Logging output to: {output_path}")
    
    def write(self, message: Dict[str, Any]):
        """Write a formatted message to both console and file."""
        formatted_text = self.formatter.format_message(message.get('type', ''), message)
        print(formatted_text)
        if self.file:
            self.file.write(formatted_text + "\n")
            self.file.flush()
    
    def close(self):
        """Close the output file."""
        if self.file:
            self.file.close()
            self.file = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

# Initialize the message list
message_list = []

# Define the initial context for the application
context = {
    'inventory': {
        'SKU001': 100,  # Current inventory of Product SKU001
        'SKU002': 75,   # Current inventory of Product SKU002
        'SKU003': 50    # Current inventory of Product SKU003
    },
    'orders': [
        {
            'order_id': 'ORD001',
            'items': [
                {'sku': 'SKU001', 'quantity': 30},
                {'sku': 'SKU002', 'quantity': 20}
            ],
            'customer_id': 'CUST001',
            'shipping_address': 'New York, NY',
            'priority': 'Standard'
        },
        {
            'order_id': 'ORD002',
            'items': [
                {'sku': 'SKU002', 'quantity': 50}
            ],
            'customer_id': 'CUST002',
            'shipping_address': 'Los Angeles, CA',
            'priority': 'Express'
        }
    ],
    'suppliers': {
        'SUP001': {
            'name': 'Primary Supplier',
            'lead_time_days': 5,
            'items': {
                'SKU001': {'unit_cost': 10.00, 'min_order': 50},
                'SKU002': {'unit_cost': 15.00, 'min_order': 30}
            }
        },
        'SUP002': {
            'name': 'Secondary Supplier',
            'lead_time_days': 7,
            'items': {
                'SKU002': {'unit_cost': 16.00, 'min_order': 25},
                'SKU003': {'unit_cost': 20.00, 'min_order': 40}
            }
        }
    },
    'warehouse_capacity': {
        'processing': 200,  # Orders we can process per day
        'shipping': 150     # Orders we can ship per day
    }
}

# Store the initial state of context
initial_context = copy.deepcopy(context)

# Function Definitions
def check_inventory(sku: str) -> Dict:
    """Check current inventory level for a product.
    :param sku: The stock keeping unit identifier
    :enum sku: SKU001,SKU002,SKU003
    """
    quantity = context['inventory'].get(sku, 0)
    return {'sku': sku, 'quantity': quantity}

def get_pending_orders():
    """Get list of pending orders."""
    return context['orders']

def allocate_inventory(order_id: str, sku: str, quantity: int) -> Dict:
    """Allocate inventory for an order.
    :param order_id: The order identifier
    :param sku: The stock keeping unit identifier
    :param quantity: The quantity to allocate
    """
    available = context['inventory'].get(sku, 0)
    if available >= quantity:
        context['inventory'][sku] -= quantity
        return {'order_id': order_id, 'allocated': quantity}
    return {'order_id': order_id, 'allocated': 0, 'error': 'Insufficient inventory'}

def list_suppliers() -> Dict:
    """Get list of available suppliers."""
    return {'suppliers': list(context['suppliers'].keys())}

def get_supplier_catalog(supplier_id: str) -> Dict:
    """Get supplier's available items and pricing.
    :param supplier_id: The supplier identifier
    """
    supplier = context['suppliers'].get(supplier_id)
    return supplier if supplier else {'error': f"Supplier {supplier_id} not found"}

def create_purchase_order(supplier_id: str, sku: str, quantity: int) -> Dict:
    """Create a purchase order for items.
    :param supplier_id: The supplier identifier
    :param sku: The stock keeping unit to order
    :param quantity: The quantity to order
    """
    supplier = context['suppliers'].get(supplier_id)
    if not supplier:
        return {'error': f"Supplier {supplier_id} not found"}
    
    item = supplier['items'].get(sku)
    if not item:
        return {'error': f"SKU {sku} not available from supplier {supplier_id}"}
    
    if quantity < item['min_order']:
        return {'error': f"Quantity below minimum order of {item['min_order']}"}
    
    po_number = f"PO_{supplier_id}_{sku}"
    # Add purchase order to context
    context['purchase_orders'] = context.get('purchase_orders', {})
    context['purchase_orders'][po_number] = {
        'supplier_id': supplier_id,
        'sku': sku,
        'quantity': quantity,
        'expected_delivery': supplier['lead_time_days'],
        'lead_time_days': supplier['lead_time_days']
    }
    return {'po_number': po_number, 'expected_delivery': supplier['lead_time_days']}

def check_processing_capacity(time_frame: str) -> Dict:
    """Check available order processing capacity.
    :param time_frame: The time frame to check
    :enum time_frame: today,tomorrow,next_week
    """
    capacity = context['warehouse_capacity']['processing']
    return {'time_frame': time_frame, 'available_capacity': capacity}

def schedule_processing(order_id: str, priority: str) -> Dict:
    """Schedule order processing.
    :param order_id: The order identifier
    :param priority: The processing priority level
    :enum priority: Standard,Express,Rush
    """
    if context['warehouse_capacity']['processing'] > 0:
        context['warehouse_capacity']['processing'] -= 1
        # Record the scheduled processing
        context['scheduled_processing'] = context.get('scheduled_processing', {})
        context['scheduled_processing'][order_id] = {
            'priority': priority,
            'status': 'Scheduled',
            'scheduled_at': datetime.now().isoformat()
        }
        return {'order_id': order_id, 'status': 'Scheduled', 'priority': priority}
    return {'error': 'No processing capacity available'}

def notify_customer(customer_id: str, order_id: str, message: str) -> Dict:
    """Send notification to customer.
    :param customer_id: The customer identifier
    :param order_id: The order identifier
    :param message: The message to send
    """
    # Record the notification in context
    context['customer_notifications'] = context.get('customer_notifications', {})
    context['customer_notifications'][order_id] = {
        'customer_id': customer_id,
        'message': message,
        'sent_at': datetime.now().isoformat()
    }
    return {'customer_id': customer_id, 'order_id': order_id, 'notification_sent': True}

def instructions_complete():
    """Indicate that the instructions are complete."""
    return {'status': 'Instructions complete'}

# Create function mapping
function_mapping = {
    'check_inventory': check_inventory,
    'get_pending_orders': get_pending_orders,
    'allocate_inventory': allocate_inventory,
    'list_suppliers': list_suppliers,
    'get_supplier_catalog': get_supplier_catalog,
    'create_purchase_order': create_purchase_order,
    'check_processing_capacity': check_processing_capacity,
    'schedule_processing': schedule_processing,
    'notify_customer': notify_customer,
    'instructions_complete': instructions_complete,
}

# Generate TOOLS list using reflection
TOOLS = FunctionRegistry.generate_tools_list(function_mapping)

def process_scenario(scenario: str) -> List[Dict]:
    """Process a fulfillment scenario through planning and execution phases."""
    with OutputManager() as output:
        append_message({'type': 'status', 'message': 'Generating plan...'}, output)
        
        plan = generate_plan(scenario)
        append_message({'type': 'plan', 'content': plan}, output)
        
        append_message({'type': 'status', 'message': 'Executing plan...'}, output)
        messages = execute_plan(plan, output)
        
        append_message({'type': 'status', 'message': 'Processing complete.'}, output)
        return messages

def append_message(message: Dict[str, Any], output: OutputManager):
    """Append a message to the list and output it."""
    message_list.append(message)
    output.write(message)

def generate_plan(scenario: str) -> str:
    """Generate a plan using the O1 model."""
    client = OpenAI(api_key=openai_api_key)
    O1_MODEL = 'o1-mini'
    
    # Generate functions description dynamically
    functions_description = FunctionRegistry.generate_functions_description(function_mapping)
    
    prompt = f"""
You are an order fulfillment assistant. Your task is to create a detailed plan for processing orders,
managing inventory, and coordinating with suppliers.

The available functions and their descriptions are:
{functions_description}

Please create a detailed plan for the following scenario:
{scenario}

Format your plan with numbered steps and lettered sub-steps. 
*** Ensure that 'instructions_complete' is the last step. Don't run indefinitely, even if an error occurs. ***

"""

    response = client.chat.completions.create(
        model=O1_MODEL,
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response.choices[0].message.content

def execute_plan(plan: str, output: OutputManager) -> List[Dict]:
    """Execute the plan using GPT-4."""
    client = OpenAI(api_key=openai_api_key)
    GPT_MODEL = 'gpt-4o-mini'
    
    system_prompt = """
You are a policy execution assistant responsible for implementing the given plan. Do not analyze the plan, just execute it.
Follow each step carefully, calling the appropriate provided functions to complete the tasks.
Explain and justify each step you take.

PLAN:
{plan}
"""
    
    messages = [
        {'role': 'system', 'content': system_prompt.replace("{plan}", plan)},
    ]

    append_message({
        'type': 'context',
        'message': f'Before the plan is executed, here is the current context:\n{json.dumps(context, indent=4)}'
    }, output)

    while True:
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=messages,
            tools=TOOLS,
            parallel_tool_calls=False
        )

        assistant_message = response.choices[0].message.to_dict()
        messages.append(assistant_message)

        append_message({'type': 'assistant', 'content': assistant_message.get('content', '')}, output)

        if not response.choices[0].message.tool_calls:
            continue

        tool_calls = assistant_message.get('tool_calls', [])
        if not tool_calls:
            continue

        for tool in response.choices[0].message.tool_calls:
            tool_id = tool.id
            function_name = tool.function.name
            if function_name == 'instructions_complete':
                append_message({
                    'type': 'context',
                    'message': f'After the plan is executed, here is the current context:\n{json.dumps(context, indent=4)}'
                }, output)

                return messages

        for tool in response.choices[0].message.tool_calls:
            tool_id = tool.id
            function_name = tool.function.name
            input_arguments_str = tool.function.arguments

            append_message({
                'type': 'tool_call',
                'function_name': function_name,
                'arguments': input_arguments_str
            }, output)

            try:
                input_arguments = json.loads(input_arguments_str)
            except (ValueError, json.JSONDecodeError):
                continue

            if function_name in function_mapping:
                try:
                    function_response = function_mapping[function_name](**input_arguments)
                except Exception as e:
                    function_response = {'error': str(e)}
            else:
                function_response = {'error': f"Function '{function_name}' not implemented."}

            try:
                serialized_output = json.dumps(function_response)
            except (TypeError, ValueError):
                serialized_output = str(function_response)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "content": serialized_output
            })

            append_message({
                'type': 'tool_response',
                'function_name': function_name,
                'response': serialized_output
            }, output)

    return messages

if __name__ == "__main__":
    scenario_text = ("We need to process our latest batch of incoming orders. Review all pending orders "
                    "and develop a fulfillment strategy. Start by assessing our current inventory and "
                    "identify any components we need to source from our suppliers. Look at our production "
                    "capacity and schedule manufacturing accordingly. For any items we're short on, place "
                    "orders with our suppliers right away. Once products are ready, coordinate shipping "
                    "to the customer, and make sure to keep customers informed throughout the "
                    "process. The key priority is to ship whatever we can immediately while setting up "
                    "the pipeline for any backordered items.")
        
    messages = process_scenario(scenario_text) 