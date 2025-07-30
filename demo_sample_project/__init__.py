"""
E-commerce Platform Package

A comprehensive e-commerce platform demonstrating Python best practices
for documentation generation and API design.
"""

__version__ = "1.0.0"
__author__ = "Demo Team"
__email__ = "demo@ecommerce.com"

from .main import ProductManager, OrderProcessor
from .models import Customer, Product, Order, OrderItem, ShoppingCart
from .services import CustomerService, InventoryService, OrderService, NotificationService
from .utils import validate_email, format_currency, generate_order_number

__all__ = [
    "ProductManager",
    "OrderProcessor", 
    "Customer",
    "Product",
    "Order",
    "OrderItem",
    "ShoppingCart",
    "CustomerService",
    "InventoryService", 
    "OrderService",
    "NotificationService",
    "validate_email",
    "format_currency",
    "generate_order_number"
]