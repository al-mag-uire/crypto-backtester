from typing import Dict, Any, List, Union
from datetime import datetime, timedelta
import pandas as pd

def validate_params(params: Dict[str, Any], required: List[str]) -> None:
    """
    Validate that all required parameters are present.
    
    Args:
        params: Dictionary of parameters
        required: List of required parameter keys
    
    Raises:
        ValueError: If any required parameter is missing
    """
    missing = [param for param in required if param not in params]
    if missing:
        raise ValueError(f"Missing required parameters: {', '.join(missing)}")

def calculate_returns(prices: Union[pd.Series, List[float]]) -> float:
    """
    Calculate percentage returns from a series of prices.
    
    Args:
        prices: Series or list of prices
        
    Returns:
        float: Percentage return
    """
    if isinstance(prices, list):
        prices = pd.Series(prices)
    return ((prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0]) * 100

def calculate_drawdown(equity: pd.Series) -> pd.Series:
    """
    Calculate drawdown series from equity curve.
    
    Args:
        equity: Series of equity values
        
    Returns:
        pd.Series: Drawdown series
    """
    rolling_max = equity.cummax()
    drawdown = (equity - rolling_max) / rolling_max * 100
    return drawdown

def get_timestamp_range(days: int) -> tuple:
    """
    Get start and end timestamps for a given number of days.
    
    Args:
        days: Number of days
        
    Returns:
        tuple: (start_timestamp, end_timestamp)
    """
    end = datetime.now()
    start = end - timedelta(days=days)
    return start.timestamp(), end.timestamp()
