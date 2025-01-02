"""Utility functions and classes for the order fulfillment system."""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import json

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
        base_dir = Path("run_results/order_fulfillment")
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

def append_message(message: Dict[str, Any], output: OutputManager, message_list: list):
    """Append a message to the list and output it."""
    message_list.append(message)
    output.write(message) 