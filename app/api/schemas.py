import re
from datetime import date
from decimal import Decimal
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    """Request schema for query endpoint."""
    question: str
    month: Optional[str] = None
    limit_evidence: int = Field(default=20, ge=1, le=100)
    
    @field_validator("month")
    @classmethod
    def validate_month_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate month format is 'YYYY-MM' when provided."""
        if v is None:
            return v
        
        if not isinstance(v, str):
            raise ValueError(f"Month must be a string, got {type(v).__name__}")
        
        if not re.match(r"^\d{4}-\d{2}$", v):
            raise ValueError(
                f"Invalid month format '{v}'. Expected format: 'YYYY-MM' (e.g., '2025-05')"
            )
        
        # Validate month is between 01-12
        try:
            year, month_num = v.split("-")
            month_int = int(month_num)
            if month_int < 1 or month_int > 12:
                raise ValueError(
                    f"Invalid month '{v}'. Month must be between 01-12"
                )
        except ValueError as e:
            if "Invalid month" in str(e):
                raise
            raise ValueError(
                f"Invalid month format '{v}'. Expected format: 'YYYY-MM' (e.g., '2025-05')"
            ) from e
        
        return v


class EvidenceRow(BaseModel):
    """Schema for a single evidence transaction row."""
    transaction_id: str
    date: date
    where: Optional[str] = None
    what: Optional[str] = None
    amount: Decimal
    category: Optional[str] = None
    source: Optional[str] = None


class QueryResponse(BaseModel):
    """Response schema for query endpoint."""
    final_answer: Optional[str] = None
    clarifying_question: Optional[str] = None
    numbers: Optional[Dict[str, Any]] = None
    evidence: List[EvidenceRow] = Field(default_factory=list)
    trace: Dict[str, Any] = Field(default_factory=dict)
