"""Core business functions for the order fulfillment system."""

from datetime import datetime
from typing import Dict

class BusinessFunctions:
    def __init__(self, context: Dict):
        self.context = context

    def check_inventory(self, sku: str) -> Dict:
        """Check current inventory level for a product.
        :param sku: The stock keeping unit identifier
        :enum sku: SKU001,SKU002,SKU003
        """
        quantity = self.context['inventory'].get(sku, 0)
        return {'sku': sku, 'quantity': quantity}

    def get_pending_orders(self) -> Dict:
        """Get list of pending orders."""
        return self.context['orders']

    def allocate_inventory(self, order_id: str, sku: str, quantity: int) -> Dict:
        """Allocate inventory for an order.
        :param order_id: The order identifier
        :param sku: The stock keeping unit identifier
        :param quantity: The quantity to allocate
        """
        available = self.context['inventory'].get(sku, 0)
        if available >= quantity:
            self.context['inventory'][sku] -= quantity
            return {'order_id': order_id, 'allocated': quantity}
        return {'order_id': order_id, 'allocated': 0, 'error': 'Insufficient inventory'}

    def list_suppliers(self) -> Dict:
        """Get list of available suppliers."""
        return {'suppliers': list(self.context['suppliers'].keys())}

    def get_supplier_catalog(self, supplier_id: str) -> Dict:
        """Get supplier's available items and pricing.
        :param supplier_id: The supplier identifier
        """
        supplier = self.context['suppliers'].get(supplier_id)
        return supplier if supplier else {'error': f"Supplier {supplier_id} not found"}

    def create_purchase_order(self, supplier_id: str, sku: str, quantity: int) -> Dict:
        """Create a purchase order for items.
        :param supplier_id: The supplier identifier
        :param sku: The stock keeping unit to order
        :param quantity: The quantity to order
        """
        supplier = self.context['suppliers'].get(supplier_id)
        if not supplier:
            return {'error': f"Supplier {supplier_id} not found"}
        
        item = supplier['items'].get(sku)
        if not item:
            return {'error': f"SKU {sku} not available from supplier {supplier_id}"}
        
        if quantity < item['min_order']:
            return {'error': f"Quantity below minimum order of {item['min_order']}"}
        
        po_number = f"PO_{supplier_id}_{sku}"
        self.context['purchase_orders'] = self.context.get('purchase_orders', {})
        self.context['purchase_orders'][po_number] = {
            'supplier_id': supplier_id,
            'sku': sku,
            'quantity': quantity,
            'expected_delivery': supplier['lead_time_days'],
            'lead_time_days': supplier['lead_time_days']
        }
        return {'po_number': po_number, 'expected_delivery': supplier['lead_time_days']}

    def check_processing_capacity(self, time_frame: str) -> Dict:
        """Check available order processing capacity.
        :param time_frame: The time frame to check
        :enum time_frame: today,tomorrow,next_week
        """
        capacity = self.context['warehouse_capacity']['processing']
        return {'time_frame': time_frame, 'available_capacity': capacity}

    def schedule_processing(self, order_id: str, priority: str) -> Dict:
        """Schedule order processing.
        :param order_id: The order identifier
        :param priority: The processing priority level
        :enum priority: Standard,Express,Rush
        """
        if self.context['warehouse_capacity']['processing'] > 0:
            self.context['warehouse_capacity']['processing'] -= 1
            self.context['scheduled_processing'] = self.context.get('scheduled_processing', {})
            self.context['scheduled_processing'][order_id] = {
                'priority': priority,
                'status': 'Scheduled',
                'scheduled_at': datetime.now().isoformat()
            }
            return {'order_id': order_id, 'status': 'Scheduled', 'priority': priority}
        return {'error': 'No processing capacity available'}

    def notify_customer(self, customer_id: str, order_id: str, message: str) -> Dict:
        """Send notification to customer.
        :param customer_id: The customer identifier
        :param order_id: The order identifier
        :param message: The message to send
        """
        self.context['customer_notifications'] = self.context.get('customer_notifications', {})
        self.context['customer_notifications'][order_id] = {
            'customer_id': customer_id,
            'message': message,
            'sent_at': datetime.now().isoformat()
        }
        return {'customer_id': customer_id, 'order_id': order_id, 'notification_sent': True}

    def instructions_complete(self) -> Dict:
        """Indicate that the instructions are complete."""
        return {'status': 'Instructions complete'}

    def get_function_mapping(self) -> Dict:
        """Get mapping of function names to their implementations."""
        return {
            'check_inventory': self.check_inventory,
            'get_pending_orders': self.get_pending_orders,
            'allocate_inventory': self.allocate_inventory,
            'list_suppliers': self.list_suppliers,
            'get_supplier_catalog': self.get_supplier_catalog,
            'create_purchase_order': self.create_purchase_order,
            'check_processing_capacity': self.check_processing_capacity,
            'schedule_processing': self.schedule_processing,
            'notify_customer': self.notify_customer,
            'instructions_complete': self.instructions_complete,
        } 