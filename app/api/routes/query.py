from typing import Dict, Any, List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.models import Transaction
from app.core.metrics import (
    get_monthly_totals,
    get_category_total,
    get_merchant_total,
    get_source_total,
    get_top_merchants,
    get_category_breakdown,
    get_source_breakdown
)
from app.core.evidence import get_evidence_rows
from app.llm.orchestrator import (
    classify_intent,
    extract_month,
    extract_category,
    extract_source,
    extract_merchant
)
from app.api.schemas import QueryRequest, QueryResponse, EvidenceRow

router = APIRouter()

# Known categories
KNOWN_CATEGORIES = ["Travel", "Essentials", "Food", "Personal", "Home", "Others"]


def _get_known_sources(db: Session, month: str) -> List[str]:
    """Get distinct sources from DB for a given month."""
    try:
        results = db.query(distinct(Transaction.source)).filter(
            Transaction.year_month == month,
            Transaction.source.isnot(None)
        ).all()
        return [source[0] for source in results if source[0]]
    except Exception:
        return []


def _format_amount(amount: Decimal) -> str:
    """Format Decimal amount as currency string."""
    return f"${amount:,.2f}"


def format_spend_phrase(intent: str, entity_value: Optional[str] = None) -> str:
    """
    Format the spend phrase based on intent and entity value.
    
    Args:
        intent: Intent type (category_total, merchant_total, source_total, monthly_summary)
        entity_value: The entity value (category name, merchant name, source name)
        
    Returns:
        Phrase string like "on {category}", "at {merchant}", "using {source}", or "" for monthly_summary
    """
    if intent == "category_total" and entity_value:
        return f"on {entity_value}"
    elif intent == "merchant_total" and entity_value:
        return f"at {entity_value}"
    elif intent == "source_total" and entity_value:
        return f"using {entity_value}"
    elif intent == "monthly_summary":
        return ""
    else:
        return ""


@router.post("/query")
async def query_finance(
    request: QueryRequest,
    db: Session = Depends(get_db)
) -> QueryResponse:
    """
    Handle financial queries with intent classification and deterministic computation.
    
    Args:
        request: QueryRequest with question, optional month, and limit_evidence
        db: Database session
        
    Returns:
        QueryResponse with final_answer, evidence, and trace
    """
    trace: Dict[str, Any] = {
        "intent": None,
        "resolved_month": None,
        "called_functions": [],
        "parameters": {},
        "filters_used": {},
        "evidence_count_returned": 0,
        "notes": []
    }
    
    # Step 1: Determine month
    month = request.month
    month_source = None
    if month:
        month_source = "request"
        trace["notes"].append("Month provided in request")
    else:
        month = extract_month(request.question)
        if month:
            month_source = "extracted"
            trace["notes"].append("Month extracted from question")
    
    if not month:
        trace["intent"] = "unknown"
        return QueryResponse(
            clarifying_question="Please specify a month in YYYY-MM format (e.g., 2025-05).",
            evidence=[],
            trace=trace
        )
    
    trace["resolved_month"] = month
    trace["parameters"]["month"] = month
    
    # Step 2: Load known categories and sources
    known_categories = KNOWN_CATEGORIES
    known_sources = _get_known_sources(db, month)
    trace["parameters"]["known_categories"] = known_categories
    trace["parameters"]["known_sources"] = known_sources
    
    # Step 3: Classify intent (pass known_sources for better classification)
    intent = classify_intent(request.question, known_sources=known_sources)
    trace["intent"] = intent
    
    # Step 4: Handle based on intent
    result_data: Dict[str, Any] = {}
    evidence_filters: Dict[str, Any] = {"kind": "expense"}  # Default to expense (month is passed separately)
    clarifying_question: str | None = None
    final_answer: str | None = None
    numbers: Dict[str, Any] | None = None
    entity_source: Optional[str] = None
    
    try:
        if intent == "monthly_summary":
            trace["called_functions"].append("get_monthly_totals")
            totals = get_monthly_totals(db, month)
            result_data = totals
            numbers = {
                "expense_total": str(totals["expense_total"]),
                "income_total": str(totals["income_total"]),
                "net_total": str(totals["net_total"]),
                "transaction_count": totals["transaction_count"]
            }
            spend_phrase = format_spend_phrase(intent, None)
            final_answer = (
                f"In {month}, you spent {_format_amount(totals['expense_total'])} "
                f"across {totals['transaction_count']} transactions. "
                f"Net total: {_format_amount(totals['net_total'])}."
            )
        
        elif intent == "category_total":
            category = extract_category(request.question, known_categories)
            if not category:
                clarifying_question = "Which category are you interested in? (e.g., Food, Travel, Essentials)"
                trace["notes"].append("Category could not be extracted from question")
            else:
                entity_source = "extracted"
                trace["called_functions"].append("get_category_total")
                trace["parameters"]["category"] = category
                trace["notes"].append("Category extracted from question")
                result = get_category_total(db, month, category)
                result_data = result
                evidence_filters["category"] = category
                numbers = {
                    "expense_total": str(result["expense_total"]),
                    "count": result["count"]
                }
                spend_phrase = format_spend_phrase(intent, category)
                final_answer = (
                    f"You spent {_format_amount(result['expense_total'])} "
                    f"{spend_phrase} in {month} across {result['count']} transactions."
                )
        
        elif intent == "merchant_total":
            merchant = extract_merchant(request.question, known_categories)
            if not merchant:
                clarifying_question = "Which merchant or store are you asking about? (e.g., 'at Target' or 'Uber')"
                trace["notes"].append("Merchant could not be extracted from question")
            else:
                entity_source = "extracted"
                trace["called_functions"].append("get_merchant_total")
                trace["parameters"]["merchant"] = merchant
                trace["notes"].append("Merchant extracted from question")
                result = get_merchant_total(db, month, merchant)
                result_data = result
                evidence_filters["merchant"] = merchant
                numbers = {
                    "expense_total": str(result["expense_total"]),
                    "count": result["count"]
                }
                spend_phrase = format_spend_phrase(intent, merchant)
                final_answer = (
                    f"You spent {_format_amount(result['expense_total'])} "
                    f"{spend_phrase} in {month} across {result['count']} transactions."
                )
        
        elif intent == "source_total":
            source = extract_source(request.question, known_sources)
            if not source:
                clarifying_question = "Which source are you interested in? Please specify the payment source."
                trace["notes"].append("Source could not be extracted from question")
            else:
                entity_source = "extracted"
                trace["called_functions"].append("get_source_total")
                trace["parameters"]["source"] = source
                trace["notes"].append("Source extracted from question")
                result = get_source_total(db, month, source)
                result_data = result
                evidence_filters["source"] = source
                numbers = {
                    "expense_total": str(result["expense_total"]),
                    "count": result["count"]
                }
                spend_phrase = format_spend_phrase(intent, source)
                final_answer = (
                    f"You spent {_format_amount(result['expense_total'])} "
                    f"{spend_phrase} in {month} across {result['count']} transactions."
                )
        
        elif intent == "top_merchants":
            trace["called_functions"].append("get_top_merchants")
            merchants = get_top_merchants(db, month, k=5)
            result_data = {"merchants": merchants}
            if merchants:
                top_list = ", ".join([f"{m['where']} ({_format_amount(m['expense_total'])})" for m in merchants[:3]])
                final_answer = f"Top merchants in {month}: {top_list}"
            else:
                final_answer = f"No merchant data found for {month}."
        
        elif intent == "category_breakdown":
            trace["called_functions"].append("get_category_breakdown")
            breakdown = get_category_breakdown(db, month)
            result_data = {"breakdown": breakdown}
            if breakdown:
                top_categories = ", ".join([f"{c['category']}: {_format_amount(c['expense_total'])}" for c in breakdown[:3]])
                final_answer = f"Category breakdown for {month}: {top_categories}"
            else:
                final_answer = f"No category data found for {month}."
        
        elif intent == "source_breakdown":
            trace["called_functions"].append("get_source_breakdown")
            breakdown = get_source_breakdown(db, month)
            result_data = {"breakdown": breakdown}
            if breakdown:
                top_sources = ", ".join([f"{s['source']}: {_format_amount(s['expense_total'])}" for s in breakdown[:3]])
                final_answer = f"Source breakdown for {month}: {top_sources}"
            else:
                final_answer = f"No source data found for {month}."
        
        else:  # unknown
            final_answer = (
                "I can help you with questions about your spending. "
                "Supported question types include: monthly summaries, category totals, "
                "merchant totals, source totals, top merchants, and category/source breakdowns. "
                "Please rephrase your question with a specific month (YYYY-MM format)."
            )
    
    except ValueError as e:
        clarifying_question = f"Invalid input: {str(e)}. Please check your question format."
    
    # Step 5: Build evidence
    evidence_rows_data = get_evidence_rows(db, month, evidence_filters, request.limit_evidence)
    evidence = [EvidenceRow(**row) for row in evidence_rows_data]
    
    # Step 6: Update trace with filters_used and evidence_count
    # filters_used should match evidence_filters exactly, but also include month
    trace["filters_used"] = {"month": month, **evidence_filters}
    trace["evidence_count_returned"] = len(evidence)
    
    # Step 7: Build response
    return QueryResponse(
        final_answer=final_answer,
        clarifying_question=clarifying_question,
        numbers=numbers,
        evidence=evidence,
        trace=trace
    )
