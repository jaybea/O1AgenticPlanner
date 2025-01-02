"""Function registry and metadata management for the order fulfillment system."""

import inspect
from typing import Dict, List, Callable

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
            
            param_desc = ""
            for line in doc.split('\n'):
                if f":param {name}:" in line:
                    param_desc = line.split(f":param {name}:")[1].strip()
                    break
            
            properties[name] = {
                **param_schema,
                "description": param_desc or f"The {name.replace('_', ' ')}."
            }
            
            if ":enum:" in doc:
                enum_line = [line for line in doc.split('\n') if f":enum {name}:" in line]
                if enum_line:
                    enum_values = enum_line[0].split(f":enum {name}:")[1].strip().split(',')
                    properties[name]["enum"] = [v.strip() for v in enum_values]
        
        return {
            "description": doc.split('\n')[0],
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