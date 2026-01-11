import re
from decimal import Decimal
from typing import Dict, List, Any
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.core.models import Transaction


def _validate_month(month: str) -> None:
    """
    Validate month format is "YYYY-MM".
    
    Args:
        month: Month string to validate
        
    Raises:
        ValueError: If month format is invalid
    """
    if not isinstance(month, str):
        raise ValueError(f"Month must be a string, got {type(month).__name__}")
    
    if not re.match(r"^\d{4}-\d{2}$", month):
        raise ValueError(
            f"Invalid month format '{month}'. Expected format: 'YYYY-MM' (e.g., '2025-05')"
        )
    
    # Validate month is between 01-12
    try:
        year, month_num = month.split("-")
        month_int = int(month_num)
        if month_int < 1 or month_int > 12:
            raise ValueError(
                f"Invalid month '{month}'. Month must be between 01-12"
            )
    except ValueError as e:
        if "Invalid month" in str(e):
            raise
        raise ValueError(
            f"Invalid month format '{month}'. Expected format: 'YYYY-MM' (e.g., '2025-05')"
        ) from e


def get_monthly_totals(db: Session, month: str) -> Dict[str, Decimal]:
    """
    Get monthly totals for expenses, income, net, and transaction count.
    
    Args:
        db: SQLAlchemy database session
        month: Month in "YYYY-MM" format
        
    Returns:
        Dictionary with expense_total, income_total, net_total (all Decimal),
        and transaction_count (int)
    """
    _validate_month(month)
    
    # Base query filtered by month
    base_query = db.query(Transaction).filter(Transaction.year_month == month)
    
    # Expense total (amount > 0)
    expense_total = db.query(func.sum(Transaction.amount)).filter(
        and_(Transaction.year_month == month, Transaction.amount > 0)
    ).scalar() or Decimal("0.00")
    
    # Income total (amount < 0)
    income_total = db.query(func.sum(Transaction.amount)).filter(
        and_(Transaction.year_month == month, Transaction.amount < 0)
    ).scalar() or Decimal("0.00")
    
    # Net total (sum of all amounts)
    net_total = db.query(func.sum(Transaction.amount)).filter(
        Transaction.year_month == month
    ).scalar() or Decimal("0.00")
    
    # Transaction count
    transaction_count = base_query.count()
    
    # Quantize all Decimal values to 2 decimal places
    expense_total = Decimal(expense_total).quantize(Decimal("0.01"))
    income_total = Decimal(income_total).quantize(Decimal("0.01"))
    net_total = Decimal(net_total).quantize(Decimal("0.01"))
    
    return {
        "expense_total": expense_total,
        "income_total": income_total,
        "net_total": net_total,
        "transaction_count": transaction_count
    }


def get_category_breakdown(db: Session, month: str) -> List[Dict[str, Any]]:
    """
    Get expense breakdown by category for a given month.
    
    Args:
        db: SQLAlchemy database session
        month: Month in "YYYY-MM" format
        
    Returns:
        List of dictionaries with 'category' and 'expense_total' (Decimal),
        ordered by expense_total descending
    """
    _validate_month(month)
    
    results = db.query(
        Transaction.category,
        func.sum(Transaction.amount).label('expense_total')
    ).filter(
        and_(Transaction.year_month == month, Transaction.amount > 0)
    ).group_by(Transaction.category).order_by(
        func.sum(Transaction.amount).desc()
    ).all()
    
    breakdown = []
    for category, total in results:
        if category is not None:  # Skip NULL categories
            quantized_total = Decimal(total).quantize(Decimal("0.01"))
            breakdown.append({
                "category": category,
                "expense_total": quantized_total
            })
    
    return breakdown


def get_top_merchants(db: Session, month: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Get top merchants by expense total for a given month.
    
    Args:
        db: SQLAlchemy database session
        month: Month in "YYYY-MM" format
        k: Number of top merchants to return (default: 5)
        
    Returns:
        List of dictionaries with 'where', 'expense_total' (Decimal), and 'count' (int),
        ordered by expense_total descending
    """
    _validate_month(month)
    
    results = db.query(
        Transaction.where_,
        func.sum(Transaction.amount).label('expense_total'),
        func.count(Transaction.id).label('count')
    ).filter(
        and_(Transaction.year_month == month, Transaction.amount > 0)
    ).group_by(Transaction.where_).order_by(
        func.sum(Transaction.amount).desc()
    ).limit(k).all()
    
    merchants = []
    for where, total, count in results:
        if where is not None:  # Skip NULL where_
            quantized_total = Decimal(total).quantize(Decimal("0.01"))
            merchants.append({
                "where": where,
                "expense_total": quantized_total,
                "count": count
            })
    
    return merchants


def get_source_breakdown(db: Session, month: str) -> List[Dict[str, Any]]:
    """
    Get expense breakdown by source for a given month.
    
    Args:
        db: SQLAlchemy database session
        month: Month in "YYYY-MM" format
        
    Returns:
        List of dictionaries with 'source' and 'expense_total' (Decimal),
        ordered by expense_total descending
    """
    _validate_month(month)
    
    results = db.query(
        Transaction.source,
        func.sum(Transaction.amount).label('expense_total')
    ).filter(
        and_(Transaction.year_month == month, Transaction.amount > 0)
    ).group_by(Transaction.source).order_by(
        func.sum(Transaction.amount).desc()
    ).all()
    
    breakdown = []
    for source, total in results:
        if source is not None:  # Skip NULL sources
            quantized_total = Decimal(total).quantize(Decimal("0.01"))
            breakdown.append({
                "source": source,
                "expense_total": quantized_total
            })
    
    return breakdown
