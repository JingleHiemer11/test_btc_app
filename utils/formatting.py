def format_usd(value, decimals=0):
    """Format a float as USD string."""
    return f"${value:,.{decimals}f}"

def format_percent(value, decimals=1):
    """Format a float as percentage string."""
    return f"{value:.{decimals}f}%"

def format_ths(value):
    """Format as TH/s"""
    return f"{value:.0f} TH/s"

def format_kw(value):
    """Format as kW"""
    return f"{value:.2f} kW"

def format_btc(value, decimals=6):
    """Format BTC values with precision"""
    return f"{value:.{decimals}f} BTC"

def format_number(value, decimals=2):
    """Generic number formatter"""
    return f"{value:,.{decimals}f}"