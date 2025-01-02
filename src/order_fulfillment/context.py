"""Context management for the order fulfillment system."""

import copy
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class InventoryConfig:
    """Configuration for inventory levels."""
    sku_levels: Dict[str, int] = field(default_factory=lambda: {
        'SKU001': 100,
        'SKU002': 75,
        'SKU003': 50
    })

@dataclass
class OrderConfig:
    """Configuration for initial orders."""
    orders: list = field(default_factory=lambda: [
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
    ])

@dataclass
class SupplierConfig:
    """Configuration for suppliers."""
    suppliers: Dict[str, Dict] = field(default_factory=lambda: {
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
    })

@dataclass
class WarehouseConfig:
    """Configuration for warehouse capacity."""
    processing_capacity: int = 200
    shipping_capacity: int = 150

@dataclass
class ContextConfig:
    """Complete configuration for the business context."""
    inventory: InventoryConfig = field(default_factory=InventoryConfig)
    orders: OrderConfig = field(default_factory=OrderConfig)
    suppliers: SupplierConfig = field(default_factory=SupplierConfig)
    warehouse: WarehouseConfig = field(default_factory=WarehouseConfig)

class Context:
    """Manages the application context and state."""
    
    def __init__(self, config: Optional[ContextConfig] = None):
        """Initialize context with optional configuration."""
        self.config = config or ContextConfig()
        self.context = self._create_context_from_config()

    def _create_context_from_config(self) -> Dict[str, Any]:
        """Create context dictionary from configuration."""
        return {
            'inventory': self.config.inventory.sku_levels,
            'orders': self.config.orders.orders,
            'suppliers': self.config.suppliers.suppliers,
            'warehouse_capacity': {
                'processing': self.config.warehouse.processing_capacity,
                'shipping': self.config.warehouse.shipping_capacity
            }
        }

    def get_context(self) -> Dict[str, Any]:
        """Get the current context."""
        return copy.deepcopy(self.context)

    @classmethod
    def create_context(cls, config: Optional[ContextConfig] = None) -> Dict[str, Any]:
        """Create a new context with optional configuration."""
        context_manager = cls(config)
        return context_manager.get_context()

    @classmethod
    def create_low_inventory_context(cls) -> Dict[str, Any]:
        """Create a context with low inventory levels."""
        config = ContextConfig(
            inventory=InventoryConfig(sku_levels={
                'SKU001': 10,
                'SKU002': 5,
                'SKU003': 2
            })
        )
        return cls.create_context(config)

    @classmethod
    def create_high_demand_context(cls) -> Dict[str, Any]:
        """Create a context with high order demand."""
        config = ContextConfig(
            orders=OrderConfig(orders=[
                {
                    'order_id': 'ORD001',
                    'items': [
                        {'sku': 'SKU001', 'quantity': 300},
                        {'sku': 'SKU002', 'quantity': 200}
                    ],
                    'customer_id': 'CUST001',
                    'priority': 'Rush'
                }
            ])
        )
        return cls.create_context(config)