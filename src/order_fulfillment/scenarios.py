"""Scenario definitions for the order fulfillment system."""

class Scenarios:
    """Collection of test scenarios for the system."""
    
    BASIC_FULFILLMENT = """
We need to process our latest batch of incoming orders. Review all pending orders 
and develop a fulfillment strategy. Start by assessing our current inventory and 
identify any components we need to source from our suppliers. Look at our production 
capacity and schedule manufacturing accordingly. For any items we're short on, place 
orders with our suppliers right away. Once products are ready, coordinate shipping 
to the customer, and make sure to keep customers informed throughout the 
process. The key priority is to ship whatever we can immediately while setting up 
the pipeline for any backordered items.
"""

    LOW_INVENTORY = """
Process an order for 200 units of SKU001 (more than current inventory).
The system should:
1. Check current inventory
2. Identify the shortage
3. Create appropriate purchase orders
4. Notify the customer about partial fulfillment or delay
"""

    SUPPLIER_OPTIMIZATION = """
Need to order SKU002 from suppliers.
Compare offers from both suppliers:
- SUP001: $15.00 per unit, min order 30
- SUP002: $16.00 per unit, min order 25
Choose the most cost-effective option considering lead times and minimum orders.
"""

    @classmethod
    def get_scenario(cls, name: str) -> str:
        """Get a scenario by name."""
        scenarios = {
            'basic': cls.BASIC_FULFILLMENT,
            'low_inventory': cls.LOW_INVENTORY,
            'supplier_optimization': cls.SUPPLIER_OPTIMIZATION,
        }
        return scenarios.get(name, cls.BASIC_FULFILLMENT)