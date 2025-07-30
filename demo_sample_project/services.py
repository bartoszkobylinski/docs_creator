"""
E-commerce Business Services

This module contains the business logic services for the e-commerce platform,
including customer management, inventory control, and order processing.
"""

import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

from models import Customer, Product, Order, OrderItem, OrderStatus, PaymentMethod, ShoppingCart

logger = logging.getLogger(__name__)


class CustomerService:
    """Service for managing customer operations."""
    
    def __init__(self, data_file: str = "customers.json"):
        self.data_file = Path(data_file)
        self.customers: Dict[str, Customer] = {}
        self._load_customers()
    
    def _load_customers(self) -> None:
        """Load customers from JSON file."""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    for customer_data in data:
                        customer_data['created_at'] = datetime.fromisoformat(customer_data['created_at'])
                        customer = Customer(**customer_data)
                        self.customers[customer.customer_id] = customer
                logger.info(f"Loaded {len(self.customers)} customers")
            except Exception as e:
                logger.error(f"Failed to load customers: {e}")
    
    def _save_customers(self) -> None:
        """Save customers to JSON file."""
        try:
            data = [customer.to_dict() for customer in self.customers.values()]
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.customers)} customers")
        except Exception as e:
            logger.error(f"Failed to save customers: {e}")
    
    def create_customer(self, email: str, first_name: str, last_name: str, 
                       phone: Optional[str] = None) -> Optional[Customer]:
        """Create a new customer."""
        # Check if email already exists
        for customer in self.customers.values():
            if customer.email.lower() == email.lower():
                logger.warning(f"Customer with email {email} already exists")
                return None
        
        customer_id = f"CUST_{len(self.customers) + 1:06d}"
        customer = Customer(
            customer_id=customer_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone
        )
        
        self.customers[customer_id] = customer
        self._save_customers()
        logger.info(f"Created customer {customer_id}: {customer.full_name}")
        return customer
    
    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID."""
        return self.customers.get(customer_id)
    
    def get_customer_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email address."""
        for customer in self.customers.values():
            if customer.email.lower() == email.lower():
                return customer
        return None
    
    def update_customer(self, customer_id: str, **kwargs) -> bool:
        """Update customer information."""
        customer = self.customers.get(customer_id)
        if not customer:
            return False
        
        for key, value in kwargs.items():
            if hasattr(customer, key):
                setattr(customer, key, value)
        
        self._save_customers()
        logger.info(f"Updated customer {customer_id}")
        return True
    
    def deactivate_customer(self, customer_id: str) -> bool:
        """Deactivate a customer account."""
        return self.update_customer(customer_id, is_active=False)
    
    def get_active_customers(self) -> List[Customer]:
        """Get all active customers."""
        return [c for c in self.customers.values() if c.is_active]


class InventoryService:
    """Service for managing product inventory."""
    
    def __init__(self, data_file: str = "products.json"):
        self.data_file = Path(data_file)
        self.products: Dict[str, Product] = {}
        self._load_products()
    
    def _load_products(self) -> None:
        """Load products from JSON file."""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    for product_data in data:
                        product_data['created_at'] = datetime.fromisoformat(product_data['created_at'])
                        product = Product(**product_data)
                        self.products[product.product_id] = product
                logger.info(f"Loaded {len(self.products)} products")
            except Exception as e:
                logger.error(f"Failed to load products: {e}")
    
    def _save_products(self) -> None:
        """Save products to JSON file."""
        try:
            data = []
            for product in self.products.values():
                product_dict = {
                    "product_id": product.product_id,
                    "name": product.name,
                    "description": product.description,
                    "price": product.price,
                    "quantity": product.quantity,
                    "category": product.category,
                    "sku": product.sku,
                    "weight": product.weight,
                    "dimensions": product.dimensions,
                    "is_active": product.is_active,
                    "created_at": product.created_at.isoformat()
                }
                data.append(product_dict)
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.products)} products")
        except Exception as e:
            logger.error(f"Failed to save products: {e}")
    
    def add_product(self, name: str, description: str, price: float, 
                   quantity: int, category: str, **kwargs) -> Product:
        """Add a new product to inventory."""
        product_id = f"PROD_{len(self.products) + 1:06d}"
        
        product = Product(
            product_id=product_id,
            name=name,
            description=description,
            price=price,
            quantity=quantity,
            category=category,
            **kwargs
        )
        
        self.products[product_id] = product
        self._save_products()
        logger.info(f"Added product {product_id}: {name}")
        return product
    
    def get_product(self, product_id: str) -> Optional[Product]:
        """Get product by ID."""
        return self.products.get(product_id)
    
    def search_products(self, query: str, category: Optional[str] = None) -> List[Product]:
        """Search products by name or description."""
        results = []
        query_lower = query.lower()
        
        for product in self.products.values():
            if not product.is_active:
                continue
            
            if category and product.category.lower() != category.lower():
                continue
            
            if (query_lower in product.name.lower() or 
                query_lower in product.description.lower()):
                results.append(product)
        
        return results
    
    def get_products_by_category(self, category: str) -> List[Product]:
        """Get all products in a category."""
        return [p for p in self.products.values() 
                if p.category.lower() == category.lower() and p.is_active]
    
    def update_stock(self, product_id: str, quantity_change: int) -> bool:
        """Update product stock quantity."""
        product = self.products.get(product_id)
        if not product:
            return False
        
        if product.update_stock(quantity_change):
            self._save_products()
            logger.info(f"Updated stock for {product_id}: {product.quantity}")
            return True
        return False
    
    def get_low_stock_products(self, threshold: int = 10) -> List[Product]:
        """Get products with low stock."""
        return [p for p in self.products.values() 
                if p.is_active and p.quantity <= threshold]
    
    def check_availability(self, product_id: str, requested_quantity: int) -> bool:
        """Check if requested quantity is available."""
        product = self.products.get(product_id)
        return (product and product.is_active and 
                product.quantity >= requested_quantity)


class OrderService:
    """Service for managing orders and order processing."""
    
    def __init__(self, data_file: str = "orders.json"):
        self.data_file = Path(data_file)
        self.orders: Dict[str, Order] = {}
        self.order_counter = 0
        self._load_orders()
    
    def _load_orders(self) -> None:
        """Load orders from JSON file."""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    for order_data in data:
                        # Convert string dates back to datetime objects
                        order_data['created_at'] = datetime.fromisoformat(order_data['created_at'])
                        order_data['updated_at'] = datetime.fromisoformat(order_data['updated_at'])
                        order_data['status'] = OrderStatus(order_data['status'])
                        if order_data['payment_method']:
                            order_data['payment_method'] = PaymentMethod(order_data['payment_method'])
                        
                        # Convert items
                        items = []
                        for item_data in order_data['items']:
                            items.append(OrderItem(**item_data))
                        order_data['items'] = items
                        
                        order = Order(**order_data)
                        self.orders[order.order_id] = order
                        
                        # Update counter
                        order_num = int(order.order_id.split('_')[1])
                        if order_num > self.order_counter:
                            self.order_counter = order_num
                            
                logger.info(f"Loaded {len(self.orders)} orders")
            except Exception as e:
                logger.error(f"Failed to load orders: {e}")
    
    def _save_orders(self) -> None:
        """Save orders to JSON file."""
        try:
            data = [order.to_dict() for order in self.orders.values()]
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.orders)} orders")
        except Exception as e:
            logger.error(f"Failed to save orders: {e}")
    
    def create_order_from_cart(self, cart: ShoppingCart) -> Order:
        """Create order from shopping cart."""
        self.order_counter += 1
        order_id = f"ORDER_{self.order_counter:06d}"
        
        order = cart.to_order(order_id)
        self.orders[order_id] = order
        self._save_orders()
        
        logger.info(f"Created order {order_id} for customer {cart.customer_id}")
        return order
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        return self.orders.get(order_id)
    
    def get_customer_orders(self, customer_id: str) -> List[Order]:
        """Get all orders for a customer."""
        return [order for order in self.orders.values() 
                if order.customer_id == customer_id]
    
    def update_order_status(self, order_id: str, new_status: OrderStatus) -> bool:
        """Update order status."""
        order = self.orders.get(order_id)
        if not order:
            return False
        
        order.update_status(new_status)
        self._save_orders()
        logger.info(f"Updated order {order_id} status to {new_status.value}")
        return True
    
    def process_payment(self, order_id: str, payment_method: PaymentMethod) -> bool:
        """Process payment for an order."""
        order = self.orders.get(order_id)
        if not order or order.status != OrderStatus.PENDING:
            return False
        
        # Simulate payment processing
        try:
            # In real implementation, this would integrate with payment gateway
            order.payment_method = payment_method
            order.update_status(OrderStatus.PAID)
            self._save_orders()
            
            logger.info(f"Payment processed for order {order_id} via {payment_method.value}")
            return True
        except Exception as e:
            logger.error(f"Payment processing failed for order {order_id}: {e}")
            return False
    
    def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        """Get orders by status."""
        return [order for order in self.orders.values() if order.status == status]
    
    def get_recent_orders(self, days: int = 7) -> List[Order]:
        """Get orders from recent days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        return [order for order in self.orders.values() 
                if order.created_at >= cutoff_date]
    
    def calculate_revenue(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate revenue for date range."""
        total = 0.0
        for order in self.orders.values():
            if (order.status == OrderStatus.PAID and 
                start_date <= order.created_at <= end_date):
                total += order.total_amount
        return total


class NotificationService:
    """Service for sending notifications."""
    
    def __init__(self):
        self.notification_log = []
    
    def send_order_confirmation(self, order: Order, customer: Customer) -> bool:
        """Send order confirmation notification."""
        message = f"Order {order.order_id} confirmed for {customer.full_name}"
        self.notification_log.append({
            "type": "order_confirmation",
            "recipient": customer.email,
            "message": message,
            "timestamp": datetime.now()
        })
        logger.info(f"Sent order confirmation: {message}")
        return True
    
    def send_payment_confirmation(self, order: Order, customer: Customer) -> bool:
        """Send payment confirmation notification."""
        message = f"Payment of ${order.total_amount:.2f} confirmed for order {order.order_id}"
        self.notification_log.append({
            "type": "payment_confirmation",
            "recipient": customer.email,
            "message": message,
            "timestamp": datetime.now()
        })
        logger.info(f"Sent payment confirmation: {message}")
        return True
    
    def send_shipping_notification(self, order: Order, customer: Customer, tracking_number: str) -> bool:
        """Send shipping notification."""
        message = f"Order {order.order_id} has shipped. Tracking: {tracking_number}"
        self.notification_log.append({
            "type": "shipping_notification",
            "recipient": customer.email,
            "message": message,
            "timestamp": datetime.now()
        })
        logger.info(f"Sent shipping notification: {message}")
        return True
    
    def send_low_stock_alert(self, product: Product, threshold: int) -> bool:
        """Send low stock alert to admin."""
        message = f"Low stock alert: {product.name} has {product.quantity} units (threshold: {threshold})"
        self.notification_log.append({
            "type": "low_stock_alert",
            "recipient": "admin@ecommerce.com",
            "message": message,
            "timestamp": datetime.now()
        })
        logger.info(f"Sent low stock alert: {message}")
        return True
    
    def get_notification_history(self, limit: int = 50) -> List[Dict]:
        """Get recent notification history."""
        return self.notification_log[-limit:]