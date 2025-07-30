"""
OpenAI model pricing constants and cost calculation utilities.
"""

from typing import Dict, Optional

# OpenAI model pricing in USD per million tokens
# Source: https://openai.com/pricing (updated regularly)
MODEL_PRICING_PER_MILLION = {
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
    "gpt-4.1-nano-2025-04-14": {"input": 0.10, "output": 0.40},  # Same as gpt-4.1-nano
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "o3": {"input": 2.00, "output": 8.00},
    "o4-mini": {"input": 1.10, "output": 4.40},
    # Fallback pricing for unknown models
    "default": {"input": 1.00, "output": 3.00}
}

# Convert to per-token pricing
MODEL_PRICING = {}
for model, prices in MODEL_PRICING_PER_MILLION.items():
    MODEL_PRICING[model] = {
        "input": prices["input"] / 1_000_000,  # Convert to per-token
        "output": prices["output"] / 1_000_000
    }

def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> Optional[float]:
    """
    Calculate the cost of an OpenAI API call.
    
    Args:
        model: The OpenAI model used (e.g., "gpt-4.1-nano")
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens
        
    Returns:
        Cost in USD, or None if model pricing not found
    """
    # Clean model name (remove any version suffixes)
    model_key = model.lower()
    
    # Get pricing for the model
    pricing = MODEL_PRICING.get(model_key)
    if not pricing:
        # Try to find similar model or use default
        for known_model in MODEL_PRICING:
            if known_model in model_key or model_key in known_model:
                pricing = MODEL_PRICING[known_model]
                break
        else:
            pricing = MODEL_PRICING["default"]
    
    # Calculate costs
    input_cost = prompt_tokens * pricing["input"]
    output_cost = completion_tokens * pricing["output"]
    total_cost = input_cost + output_cost
    
    return round(total_cost, 6)

def get_model_pricing_display(model: str) -> str:
    """
    Get a display string for model pricing.
    
    Args:
        model: The OpenAI model name
        
    Returns:
        Formatted pricing string
    """
    pricing = MODEL_PRICING.get(model.lower(), MODEL_PRICING["default"])
    return f"${pricing['input']:.5f}/${pricing['output']:.5f}"

def get_estimated_cost(model: str, estimated_tokens: int) -> float:
    """
    Estimate cost for a given number of tokens (assuming 70% input, 30% output).
    
    Args:
        model: The OpenAI model name
        estimated_tokens: Total estimated tokens
        
    Returns:
        Estimated cost in USD
    """
    pricing = MODEL_PRICING.get(model.lower(), MODEL_PRICING["default"])
    
    # Assume typical distribution: 70% input, 30% output
    input_tokens = int(estimated_tokens * 0.7)
    output_tokens = int(estimated_tokens * 0.3)
    
    input_cost = input_tokens * pricing["input"]
    output_cost = output_tokens * pricing["output"]
    
    return round(input_cost + output_cost, 6)

def format_cost(cost: float) -> str:
    """
    Format cost for display.
    
    Args:
        cost: Cost in USD
        
    Returns:
        Formatted cost string
    """
    if cost < 0.001:
        return f"${cost:.6f}"
    elif cost < 0.01:
        return f"${cost:.5f}"
    elif cost < 1.0:
        return f"${cost:.4f}"
    else:
        return f"${cost:.2f}"