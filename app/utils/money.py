from decimal import Decimal, InvalidOperation


def parse_amount(value: str) -> Decimal:
    """
    Parse a monetary amount string into a Decimal.
    
    Accepts strings like:
    - "$6.15" -> Decimal('6.15')
    - "6.15" -> Decimal('6.15')
    - "-$10.00" -> Decimal('-10.00')
    - "-10.00" -> Decimal('-10.00')
    - "$1,234.56" -> Decimal('1234.56')
    
    Args:
        value: Monetary amount string to parse
        
    Returns:
        Decimal quantized to 2 decimal places
        
    Raises:
        ValueError: If the amount string cannot be parsed
    """
    if not isinstance(value, str):
        raise ValueError(f"Expected string, got {type(value).__name__}")
    
    # Strip whitespace
    value = value.strip()
    
    if not value:
        raise ValueError("Empty amount string cannot be parsed")
    
    # Remove $ and comma symbols
    cleaned = value.replace("$", "").replace(",", "")
    
    if not cleaned:
        raise ValueError(f"Amount string '{value}' contains no numeric value after removing symbols")
    
    try:
        # Parse to Decimal (preserves sign as provided)
        amount = Decimal(cleaned)
        # Quantize to 2 decimal places
        return amount.quantize(Decimal("0.01"))
    except InvalidOperation as e:
        raise ValueError(
            f"Failed to parse amount '{value}'. Expected a numeric value "
            f"(e.g., '$6.15', '6.15', '-$10.00', '-10.00'). Original error: {str(e)}"
        ) from e
