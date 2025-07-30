"""
E-commerce Platform Main Application

This module serves as the entry point for the e-commerce platform,
providing core functionality for product management and user operations.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ProductManager:
    """Manages product catalog and inventory operations."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.products = {}
        logger.info("ProductManager initialized")

    def add_product(self, product_id: str, name: str, price: float, quantity: int) -> bool:
        product_data = {
            "name": name,
            "price": price,
            "quantity": quantity,
            "created_at": datetime.now()
        }
        self.products[product_id] = product_data
        logger.info(f"Product {product_id} added to catalog")
        return True

    def get_product(self, product_id: str) -> Optional[Dict]:
        return self.products.get(product_id)

    def update_inventory(self, product_id: str, quantity_change: int) -> bool:
        if product_id not in self.products:
            logger.error(f"Product {product_id} not found")
            return False
        
        current_quantity = self.products[product_id]["quantity"]
        new_quantity = current_quantity + quantity_change
        
        if new_quantity < 0:
            logger.warning(f"Insufficient inventory for product {product_id}")
            return False
        
        self.products[product_id]["quantity"] = new_quantity
        logger.info(f"Inventory updated for product {product_id}: {new_quantity}")
        return True

    def search_products(self, query: str) -> List[Dict]:
        results = []
        for product_id, product_data in self.products.items():
            if query.lower() in product_data["name"].lower():
                result = product_data.copy()
                result["id"] = product_id
                results.append(result)
        return results


class OrderProcessor:
    """Handles order processing and payment operations."""

    def __init__(self, product_manager: ProductManager):
        self.product_manager = product_manager
        self.orders = {}
        self.order_counter = 0

    def create_order(self, customer_id: str, items: List[Dict]) -> str:
        self.order_counter += 1
        order_id = f"ORDER_{self.order_counter:06d}"
        
        order_data = {
            "order_id": order_id,
            "customer_id": customer_id,
            "items": items,
            "status": "pending",
            "created_at": datetime.now(),
            "total_amount": self._calculate_total(items)
        }
        
        self.orders[order_id] = order_data
        logger.info(f"Order {order_id} created for customer {customer_id}")
        return order_id

    def _calculate_total(self, items: List[Dict]) -> float:
        total = 0.0
        for item in items:
            product = self.product_manager.get_product(item["product_id"])
            if product:
                total += product["price"] * item["quantity"]
        return total

    def process_payment(self, order_id: str, payment_method: str) -> bool:
        if order_id not in self.orders:
            logger.error(f"Order {order_id} not found")
            return False
        
        # Simulate payment processing
        logger.info(f"Processing payment for order {order_id} via {payment_method}")
        self.orders[order_id]["status"] = "paid"
        self.orders[order_id]["payment_method"] = payment_method
        self.orders[order_id]["paid_at"] = datetime.now()
        
        return True

    def get_order_status(self, order_id: str) -> Optional[str]:
        order = self.orders.get(order_id)
        return order["status"] if order else None


async def process_bulk_orders(order_processor: OrderProcessor, orders_data: List[Dict]) -> Dict[str, int]:
    processed_count = 0
    failed_count = 0
    
    for order_data in orders_data:
        try:
            order_id = order_processor.create_order(
                order_data["customer_id"],
                order_data["items"]
            )
            
            if order_processor.process_payment(order_id, order_data["payment_method"]):
                processed_count += 1
            else:
                failed_count += 1
                
        except Exception as e:
            logger.error(f"Failed to process order: {e}")
            failed_count += 1
    
    return {
        "processed": processed_count,
        "failed": failed_count,
        "total": len(orders_data)
    }


def setup_logging(log_level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


if __name__ == "__main__":
    setup_logging()
    
    # Initialize components
    product_manager = ProductManager("postgresql://localhost/ecommerce")
    order_processor = OrderProcessor(product_manager)
    
    # Add sample products
    product_manager.add_product("LAPTOP001", "Gaming Laptop", 1299.99, 10)
    product_manager.add_product("MOUSE001", "Wireless Mouse", 29.99, 50)
    
    # Create sample order
    order_id = order_processor.create_order("CUST001", [
        {"product_id": "LAPTOP001", "quantity": 1},
        {"product_id": "MOUSE001", "quantity": 2}
    ])
    
    # Process payment
    if order_processor.process_payment(order_id, "credit_card"):
        print(f"Order {order_id} processed successfully!")
    
    logger.info("Application startup completed")