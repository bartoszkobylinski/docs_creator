"""
E-commerce Utility Functions

This module contains utility functions and helpers used throughout
the e-commerce platform for common operations and data processing.
"""

import re
import hashlib
import secrets
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from email.utils import parseaddr


logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email is valid, False otherwise
    """
    if not email or len(email) > 254:
        return False
    
    # Basic regex pattern for email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if phone is valid, False otherwise
    """
    if not phone:
        return True  # Phone is optional
    
    # Remove all non-digit characters
    digits_only = re.sub(r'[^\d]', '', phone)
    
    # Check if it's between 10-15 digits (international format)
    return 10 <= len(digits_only) <= 15


def format_currency(amount: Union[float, Decimal], currency: str = "USD") -> str:
    """
    Format amount as currency string.
    
    Args:
        amount: Amount to format
        currency: Currency code (default: USD)
        
    Returns:
        Formatted currency string
    """
    if isinstance(amount, float):
        amount = Decimal(str(amount))
    
    # Round to 2 decimal places
    amount = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    currency_symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥"
    }
    
    symbol = currency_symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"


def calculate_tax(amount: float, tax_rate: float = 0.08) -> float:
    """
    Calculate tax amount.
    
    Args:
        amount: Base amount
        tax_rate: Tax rate (default: 8%)
        
    Returns:
        Tax amount
    """
    return round(amount * tax_rate, 2)


def calculate_shipping(weight: float, distance: float = 100.0) -> float:
    """
    Calculate shipping cost based on weight and distance.
    
    Args:
        weight: Package weight in kg
        distance: Shipping distance in km (default: 100)
        
    Returns:
        Shipping cost
    """
    base_rate = 5.00  # Base shipping cost
    weight_rate = 2.00  # Cost per kg
    distance_rate = 0.01  # Cost per km
    
    shipping_cost = base_rate + (weight * weight_rate) + (distance * distance_rate)
    return round(shipping_cost, 2)


def generate_order_number() -> str:
    """
    Generate unique order number.
    
    Returns:
        Unique order number string
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = secrets.token_hex(3).upper()
    return f"ORD-{timestamp}-{random_suffix}"


def generate_sku(product_name: str, category: str) -> str:
    """
    Generate SKU from product name and category.
    
    Args:
        product_name: Name of the product
        category: Product category
        
    Returns:
        Generated SKU
    """
    # Take first 3 letters of category
    cat_prefix = re.sub(r'[^A-Za-z]', '', category)[:3].upper()
    
    # Take first 4 letters of product name
    name_prefix = re.sub(r'[^A-Za-z]', '', product_name)[:4].upper()
    
    # Generate random suffix
    suffix = secrets.token_hex(2).upper()
    
    return f"{cat_prefix}-{name_prefix}-{suffix}"


def hash_password(password: str) -> str:
    """
    Hash password using SHA-256 with salt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify password against hash.
    
    Args:
        password: Plain text password
        hashed: Hashed password string
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        salt, password_hash = hashed.split(':', 1)
        return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
    except ValueError:
        return False


def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize string input by removing harmful characters.
    
    Args:
        text: Text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not text:
        return ""
    
    # Remove control characters and normalize whitespace
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length].strip()
    
    return sanitized


def parse_search_query(query: str) -> Dict[str, List[str]]:
    """
    Parse search query into keywords and filters.
    
    Args:
        query: Search query string
        
    Returns:
        Dictionary with parsed query components
    """
    result = {
        "keywords": [],
        "categories": [],
        "price_min": None,
        "price_max": None
    }
    
    # Extract category filters (category:electronics)
    category_matches = re.findall(r'category:(\w+)', query, re.IGNORECASE)
    result["categories"] = category_matches
    
    # Extract price filters (price:10-50)
    price_match = re.search(r'price:(\d+)-(\d+)', query, re.IGNORECASE)
    if price_match:
        result["price_min"] = float(price_match.group(1))
        result["price_max"] = float(price_match.group(2))
    
    # Remove filters from query and extract keywords
    clean_query = re.sub(r'(category|price):[^\s]+', '', query, flags=re.IGNORECASE)
    keywords = [word.strip() for word in clean_query.split() if word.strip()]
    result["keywords"] = keywords
    
    return result


def calculate_discount(original_price: float, discount_percent: float) -> Dict[str, float]:
    """
    Calculate discount amount and final price.
    
    Args:
        original_price: Original price
        discount_percent: Discount percentage (0-100)
        
    Returns:
        Dictionary with discount details
    """
    if discount_percent < 0 or discount_percent > 100:
        raise ValidationError("Discount percentage must be between 0 and 100")
    
    discount_amount = round(original_price * (discount_percent / 100), 2)
    final_price = round(original_price - discount_amount, 2)
    
    return {
        "original_price": original_price,
        "discount_percent": discount_percent,
        "discount_amount": discount_amount,
        "final_price": final_price,
        "savings": discount_amount
    }


def format_date(date: datetime, format_type: str = "short") -> str:
    """
    Format datetime object to string.
    
    Args:
        date: Datetime object to format
        format_type: Format type ("short", "long", "iso")
        
    Returns:
        Formatted date string
    """
    formats = {
        "short": "%Y-%m-%d",
        "long": "%B %d, %Y at %I:%M %p",
        "iso": "%Y-%m-%dT%H:%M:%S",
        "display": "%m/%d/%Y"
    }
    
    format_string = formats.get(format_type, formats["short"])
    return date.strftime(format_string)


def get_date_range(period: str) -> tuple[datetime, datetime]:
    """
    Get date range for common periods.
    
    Args:
        period: Period type ("today", "week", "month", "year")
        
    Returns:
        Tuple of (start_date, end_date)
    """
    now = datetime.now()
    
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif period == "week":
        start = now - timedelta(days=7)
        end = now
    elif period == "month":
        start = now - timedelta(days=30)
        end = now
    elif period == "year":
        start = now - timedelta(days=365)
        end = now
    else:
        start = now
        end = now
    
    return start, end


def paginate_results(items: List[Any], page: int = 1, per_page: int = 20) -> Dict[str, Any]:
    """
    Paginate list of items.
    
    Args:
        items: List of items to paginate
        page: Page number (1-based)
        per_page: Items per page
        
    Returns:
        Dictionary with pagination details
    """
    total_items = len(items)
    total_pages = (total_items + per_page - 1) // per_page
    
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages if total_pages > 0 else 1
    
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    page_items = items[start_index:end_index]
    
    return {
        "items": page_items,
        "current_page": page,
        "per_page": per_page,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "prev_page": page - 1 if page > 1 else None,
        "next_page": page + 1 if page < total_pages else None
    }


class Logger:
    """Simple logging utility class."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)
    
    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)