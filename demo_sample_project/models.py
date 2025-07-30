"""
E-commerce Data Models

This module defines the core data models for the e-commerce platform,
including customer, product, and order entities.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentMethod(Enum):
    """Payment method enumeration."""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"


@dataclass
class Customer:
    """Customer data model for e-commerce platform."""
    
    customer_id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    created_at: datetime = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    @property
    def full_name(self) -> str:
        """Get customer's full name."""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert customer to dictionary."""
        return {
            "customer_id": self.customer_id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active
        }


@dataclass
class Product:
    """Product data model for inventory management."""
    
    product_id: str
    name: str
    description: str
    price: float
    quantity: int
    category: str
    sku: Optional[str] = None
    weight: Optional[float] = None
    dimensions: Optional[Dict[str, float]] = None
    is_active: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.price < 0:
            raise ValueError("Product price cannot be negative")
        if self.quantity < 0:
            raise ValueError("Product quantity cannot be negative")
    
    @property
    def is_in_stock(self) -> bool:
        """Check if product is in stock."""
        return self.quantity > 0 and self.is_active
    
    def update_stock(self, quantity_change: int) -> bool:
        """Update product stock quantity."""
        new_quantity = self.quantity + quantity_change
        if new_quantity < 0:
            return False
        self.quantity = new_quantity
        return True
    
    def calculate_total_price(self, quantity: int) -> float:
        """Calculate total price for given quantity."""
        return self.price * quantity


@dataclass
class OrderItem:
    """Individual item within an order."""
    
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    total_price: float = None
    
    def __post_init__(self):
        if self.total_price is None:
            self.total_price = self.unit_price * self.quantity
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert order item to dictionary."""
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_price": self.total_price
        }


@dataclass
class Order:
    """Order data model for order management."""
    
    order_id: str
    customer_id: str
    items: List[OrderItem]
    status: OrderStatus = OrderStatus.PENDING
    payment_method: Optional[PaymentMethod] = None
    total_amount: float = None
    created_at: datetime = None
    updated_at: datetime = None
    shipping_address: Optional[Dict[str, str]] = None
    notes: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.total_amount is None:
            self.total_amount = self.calculate_total()
    
    def calculate_total(self) -> float:
        """Calculate total order amount."""
        return sum(item.total_price for item in self.items)
    
    def add_item(self, item: OrderItem) -> None:
        """Add item to order."""
        self.items.append(item)
        self.total_amount = self.calculate_total()
        self.updated_at = datetime.now()
    
    def remove_item(self, product_id: str) -> bool:
        """Remove item from order by product ID."""
        original_count = len(self.items)
        self.items = [item for item in self.items if item.product_id != product_id]
        
        if len(self.items) < original_count:
            self.total_amount = self.calculate_total()
            self.updated_at = datetime.now()
            return True
        return False
    
    def update_status(self, new_status: OrderStatus) -> None:
        """Update order status."""
        self.status = new_status
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert order to dictionary."""
        return {
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "items": [item.to_dict() for item in self.items],
            "status": self.status.value,
            "payment_method": self.payment_method.value if self.payment_method else None,
            "total_amount": self.total_amount,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "shipping_address": self.shipping_address,
            "notes": self.notes
        }


class ShoppingCart:
    """Shopping cart for managing customer selections."""
    
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        self.items: List[OrderItem] = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def add_product(self, product: Product, quantity: int) -> bool:
        """Add product to cart."""
        if not product.is_in_stock or quantity > product.quantity:
            return False
        
        # Check if product already in cart
        for item in self.items:
            if item.product_id == product.product_id:
                item.quantity += quantity
                item.total_price = item.unit_price * item.quantity
                self.updated_at = datetime.now()
                return True
        
        # Add new item
        new_item = OrderItem(
            product_id=product.product_id,
            product_name=product.name,
            quantity=quantity,
            unit_price=product.price
        )
        self.items.append(new_item)
        self.updated_at = datetime.now()
        return True
    
    def remove_product(self, product_id: str) -> bool:
        """Remove product from cart."""
        original_count = len(self.items)
        self.items = [item for item in self.items if item.product_id != product_id]
        
        if len(self.items) < original_count:
            self.updated_at = datetime.now()
            return True
        return False
    
    def update_quantity(self, product_id: str, new_quantity: int) -> bool:
        """Update product quantity in cart."""
        if new_quantity <= 0:
            return self.remove_product(product_id)
        
        for item in self.items:
            if item.product_id == product_id:
                item.quantity = new_quantity
                item.total_price = item.unit_price * item.quantity
                self.updated_at = datetime.now()
                return True
        return False
    
    def get_total(self) -> float:
        """Get cart total amount."""
        return sum(item.total_price for item in self.items)
    
    def clear(self) -> None:
        """Clear all items from cart."""
        self.items.clear()
        self.updated_at = datetime.now()
    
    def to_order(self, order_id: str) -> Order:
        """Convert cart to order."""
        return Order(
            order_id=order_id,
            customer_id=self.customer_id,
            items=self.items.copy()
        )