from typing import Dict, List, Any, Optional
from sqlalchemy import and_
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
        month: Month in "YYYY-MM" format (required)
        filters: Dictionary that may include:
            - kind: "expense" (amount > 0) or "income" (amount < 0), defaults to "expense"
            - category: Filter by category name (exact match, case-sensitive)
            - merchant: Filter by where_ field (exact match, case-sensitive)
            - source: Filter by source name (exact match, case-sensitive)
        limit: Maximum number of rows to return
        
    Returns:
        List of dictionaries with transaction_id, date, where, what, amount,
        category, source. Ordered by abs_amount descending, then date descending.
        Returns empty list if no results, invalid month, or filters don't match.
    """
    # Validate month format
    try:
        _validate_month(month)
    except ValueError:
        return []
    
    # Determine amount filter based on kind
    kind = filters.get("kind", "expense")
    if kind == "expense":
        amount_filter = Transaction.amount > 0
    elif kind == "income":
        amount_filter = Transaction.amount < 0
    else:
        # Default to expense if invalid kind
        amount_filter = Transaction.amount > 0
    
    # Start building the query
    query = db.query(Transaction).filter(
        and_(
            Transaction.year_month == month,
            amount_filter
        )
    )
    
    # Apply filters (exact match, case-sensitive)
    if "category" in filters and filters["category"] is not None:
        query = query.filter(Transaction.category == filters["category"])
    
    if "source" in filters and filters["source"] is not None:
        query = query.filter(Transaction.source == filters["source"])
    
    if "merchant" in filters and filters["merchant"] is not None:
        # Exact match, case-sensitive for merchant (where_ field)
        query = query.filter(Transaction.where_ == filters["merchant"])
    
    # Order by abs_amount descending, then date descending
    query = query.order_by(Transaction.abs_amount.desc(), Transaction.date.desc()).limit(limit)
    
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
