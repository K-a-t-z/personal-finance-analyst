from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.metrics import (
    get_monthly_totals,
    get_category_breakdown,
    get_top_merchants,
    get_source_breakdown
)

router = APIRouter()


@router.get("/summary/monthly")
async def get_monthly_summary(
    month: str = Query(..., description="Month in YYYY-MM format"),
    top_k: int = Query(5, ge=1, le=20, description="Number of top merchants to return"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get monthly financial summary including totals, category breakdown,
    top merchants, and source breakdown.
    
    Args:
        month: Month in "YYYY-MM" format (required)
        top_k: Number of top merchants to return (default: 5, min: 1, max: 20)
        db: Database session
        
    Returns:
        JSON object with month, totals, by_category, top_merchants, and by_source
    """
    try:
        # Get monthly totals
        totals = get_monthly_totals(db, month)
        
        # Get category breakdown
        by_category = get_category_breakdown(db, month)
        
        # Get top merchants
        top_merchants = get_top_merchants(db, month, k=top_k)
        
        # Get source breakdown
        by_source = get_source_breakdown(db, month)
        
        return {
            "month": month,
            "totals": totals,
            "by_category": by_category,
            "top_merchants": top_merchants,
            "by_source": by_source
        }
        
    except ValueError as e:
        # Invalid month format or other validation error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
