from typing import Dict, List, Any, Optional
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.models import Transaction
from app.core.metrics import _validate_month


def get_evidence_rows(
    db: Session,
    month: str,
    filters: Dict[str, Any],
    limit: int
) -> List[Dict[str, Any]]:
    """
    Get evidence transaction rows based on filters.
    
    Args:
        db: SQLAlchemy database session
        month: Month in "YYYY-MM" format
        filters: Dictionary that may include:
            - category: Filter by category name
            - source: Filter by source name
            - merchant: Filter by where_ field (case-insensitive)
        limit: Maximum number of rows to return
        
    Returns:
        List of dictionaries with transaction_id, date, where, what, amount,
        category, source. Ordered by abs_amount descending.
        Returns empty list if no results or invalid month.
    """
    # Validate month format
    try:
        _validate_month(month)
    except ValueError:
        return []
    
    # Start building the query
    query = db.query(Transaction).filter(
        and_(
            Transaction.year_month == month,
            Transaction.amount > 0  # Only expenses for spend questions
        )
    )
    
    # Apply filters
    if "category" in filters and filters["category"] is not None:
        query = query.filter(Transaction.category == filters["category"])
    
    if "source" in filters and filters["source"] is not None:
        query = query.filter(Transaction.source == filters["source"])
    
    if "merchant" in filters and filters["merchant"] is not None:
        # Case-insensitive matching for merchant (where_ field)
        merchant_lower = filters["merchant"].lower()
        query = query.filter(func.lower(Transaction.where_) == merchant_lower)
    
    # Order by abs_amount descending and limit
    query = query.order_by(Transaction.abs_amount.desc()).limit(limit)
    
    # Execute query and build result list
    transactions = query.all()
    
    evidence_rows = []
    for transaction in transactions:
        evidence_rows.append({
            "transaction_id": transaction.id,
            "date": transaction.date,
            "where": transaction.where_,
            "what": transaction.what_,
            "amount": transaction.amount,
            "category": transaction.category,
            "source": transaction.source
        })
    
    return evidence_rows
