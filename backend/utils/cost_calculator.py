import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

# Pricing table for different models (cost per 1K tokens)
# Last updated: February 2026
PRICING = {
    "gpt-4-turbo": {
        "prompt": 0.01,      # $0.01 per 1K prompt tokens
        "completion": 0.03,  # $0.03 per 1K completion tokens
    },
    "gpt-4": {
        "prompt": 0.03,      # $0.03 per 1K prompt tokens
        "completion": 0.06,  # $0.06 per 1K completion tokens
    },
    "gpt-3.5-turbo": {
        "prompt": 0.0005,    # $0.0005 per 1K prompt tokens
        "completion": 0.0015,  # $0.0015 per 1K completion tokens
    },
}

# Default model
DEFAULT_MODEL = "gpt-4-turbo"


def get_model_pricing(model: str) -> Dict[str, float]:
    """
    Get pricing for a specific model
    
    Args:
        model: Model name (e.g., "gpt-4-turbo")
        
    Returns:
        Dict with "prompt" and "completion" rates per 1K tokens
    """
    if model not in PRICING:
        logger.warning(f"Model {model} not in pricing table, using default {DEFAULT_MODEL}")
        return PRICING[DEFAULT_MODEL]
    
    return PRICING[model]


def calculate_token_cost(prompt_tokens: int, completion_tokens: int, model: str) -> float:
    """
    Calculate total cost for a token usage
    
    Args:
        prompt_tokens: Number of prompt tokens used
        completion_tokens: Number of completion tokens used
        model: Model name
        
    Returns:
        Cost in USD (rounded to 6 decimal places)
    """
    pricing = get_model_pricing(model)
    
    # Calculate costs per 1K tokens
    prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
    completion_cost = (completion_tokens / 1000) * pricing["completion"]
    
    total_cost = prompt_cost + completion_cost
    
    return round(total_cost, 6)


def calculate_total_cost(total_tokens: int, model: str, prompt_completion_ratio: float = 0.7) -> float:
    """
    Calculate cost from total tokens when split is unknown
    
    Args:
        total_tokens: Total tokens used
        model: Model name
        prompt_completion_ratio: Approximate ratio of prompt:total tokens (default 70% prompt)
        
    Returns:
        Estimated cost in USD
    """
    prompt_tokens = int(total_tokens * prompt_completion_ratio)
    completion_tokens = total_tokens - prompt_tokens
    
    return calculate_token_cost(prompt_tokens, completion_tokens, model)


def get_all_models() -> list:
    """Get list of all supported models"""
    return list(PRICING.keys())


def format_cost(cost: float) -> str:
    """Format cost as USD string"""
    return f"${cost:.4f}"


def format_token_count(tokens: int) -> str:
    """Format token count with thousands separator"""
    return f"{tokens:,}"
