"""Main entry point for the order fulfillment system."""

from helper import get_openai_api_key
from executor import PolicyExecutor
from scenarios import Scenarios
from config import ModelConfig
from context import ContextConfig, InventoryConfig, WarehouseConfig
from plans import Plan
from typing import List, Dict
from pathlib import Path

def generate_plans(api_key: str, scenario_names: List[str]) -> Dict[str, Plan]:
    """Generate plans for multiple scenarios using O1-mini."""
    class PlannerConfig(ModelConfig):
        PLANNER_MODEL = 'o1-mini'
    
    planner = PolicyExecutor(api_key, model_config=PlannerConfig)
    plans = {}
    
    for scenario_name in scenario_names:
        print(f"\nGenerating plan for scenario: {scenario_name}")
        scenario = Scenarios.get_scenario(scenario_name)
        plan = planner.generate_plan(scenario)
        plan.save(f"{scenario_name}_plan.json")
        plans[scenario_name] = plan
        
    return plans

def get_test_contexts() -> List[Dict[str, ContextConfig]]:
    """Define different contexts for testing."""
    return [
        {
            "name": "default",
            "config": None
        },
        {
            "name": "low_inventory",
            "config": ContextConfig(
                inventory=InventoryConfig(sku_levels={
                    'SKU001': 10,
                    'SKU002': 5,
                    'SKU003': 2
                })
            )
        },
        {
            "name": "high_capacity",
            "config": ContextConfig(
                warehouse=WarehouseConfig(
                    processing_capacity=1000,
                    shipping_capacity=800
                )
            )
        }
    ]

def execute_plan_with_contexts(
    api_key: str,
    plan: Plan,
    contexts: List[Dict[str, ContextConfig]]
) -> None:
    """Execute a single plan with multiple contexts."""
    # Use GPT-4 for execution
    class ExecutorConfig(ModelConfig):
        EXECUTOR_MODEL = 'gpt-4'
    
    for context_info in contexts:
        context_name = context_info["name"]
        context_config = context_info["config"]
        
        print(f"\nExecuting plan with {context_name} context...")
        executor = PolicyExecutor(
            api_key, 
            model_config=ExecutorConfig,
            context_config=context_config
        )
        executor.process_scenario(plan.scenario, existing_plan=plan)

def run_experiments():
    """Run comprehensive experiments with different plans and contexts."""
    api_key = get_openai_api_key()
    
    # Define scenarios to test
    scenario_names = ['basic', 'low_inventory', 'supplier_optimization']
    
    # Generate all plans first
    print("Generating plans...")
    plans = generate_plans(api_key, scenario_names)
    
    # Get test contexts
    contexts = get_test_contexts()
    
    # Execute each plan with different contexts
    for scenario_name, plan in plans.items():
        print(f"\n{'='*80}")
        print(f"Testing scenario: {scenario_name}")
        print(f"Plan generated using: {plan.model_used}")
        print(f"{'='*80}")
        
        execute_plan_with_contexts(api_key, plan, contexts)

def load_and_execute_existing_plan(plan_filename: str, context_name: str = "default"):
    """Load and execute a previously generated plan with a specific context."""
    api_key = get_openai_api_key()
    
    # Load the plan
    plan = Plan.load(plan_filename)
    
    # Get the specified context
    contexts = {ctx["name"]: ctx for ctx in get_test_contexts()}
    context_info = contexts.get(context_name, contexts["default"])
    
    # Execute the plan
    execute_plan_with_contexts(api_key, plan, [context_info])

def main():
    """Main function demonstrating different execution modes."""
    print("Running comprehensive experiments...")
    run_experiments()
    
    # Example of loading and re-running a specific plan
    print("\nDemonstrating plan reuse...")
    load_and_execute_existing_plan(
        "basic_plan.json",
        "low_inventory"
    )

if __name__ == "__main__":
    main()