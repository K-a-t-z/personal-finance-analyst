#!/usr/bin/env python3
"""
Evaluation runner for query endpoint.
Tests questions from questions_v1.jsonl against the /query endpoint.
"""
import json
import sys
import argparse
from pathlib import Path
from decimal import Decimal
from typing import Dict, Any, List, Optional, Callable
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import uuid

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.main import app
from app.core.db import Base, get_db, engine, SessionLocal
from app.core.config import get_settings
from app.core.models import Transaction, Ingest
from app.core.metrics import (
    get_monthly_totals,
    get_category_total,
    get_merchant_total,
    get_source_total
)

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


def setup_seeded_database():
    """Set up in-memory SQLite database with sample data."""
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=test_engine)
    test_session_local = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Seed database with sample transactions
    session = test_session_local()
    
    # Create an ingest record
    ingest_id = str(uuid.uuid4())
    ingest = Ingest(
        ingest_id=ingest_id,
        filename="eval_data.csv",
        row_count=10,
        status="success",
        error=None
    )
    session.add(ingest)
    session.flush()
    
    # Create sample transactions for 2025-06
    transactions = [
        # Food transactions
        Transaction(
            id=str(uuid.uuid4()),
            ingest_id=ingest_id,
            date=date(2025, 6, 5),
            year_month="2025-06",
            amount=Decimal("45.50"),
            abs_amount=Decimal("45.50"),
            where_="Grocery Store",
            what_="Groceries",
            category="Food",
            source="Credit Card"
        ),
        Transaction(
            id=str(uuid.uuid4()),
            ingest_id=ingest_id,
            date=date(2025, 6, 10),
            year_month="2025-06",
            amount=Decimal("25.00"),
            abs_amount=Decimal("25.00"),
            where_="Restaurant",
            what_="Dinner",
            category="Food",
            source="Cash"
        ),
        # Travel transaction
        Transaction(
            id=str(uuid.uuid4()),
            ingest_id=ingest_id,
            date=date(2025, 6, 15),
            year_month="2025-06",
            amount=Decimal("300.00"),
            abs_amount=Decimal("300.00"),
            where_="Airline",
            what_="Flight",
            category="Travel",
            source="Credit Card"
        ),
        # Uber transactions
        Transaction(
            id=str(uuid.uuid4()),
            ingest_id=ingest_id,
            date=date(2025, 6, 8),
            year_month="2025-06",
            amount=Decimal("15.50"),
            abs_amount=Decimal("15.50"),
            where_="Uber",
            what_="Ride",
            category="Travel",
            source="Credit Card"
        ),
        Transaction(
            id=str(uuid.uuid4()),
            ingest_id=ingest_id,
            date=date(2025, 6, 12),
            year_month="2025-06",
            amount=Decimal("22.00"),
            abs_amount=Decimal("22.00"),
            where_="Uber",
            what_="Ride",
            category="Travel",
            source="Credit Card"
        ),
        # Target transaction
        Transaction(
            id=str(uuid.uuid4()),
            ingest_id=ingest_id,
            date=date(2025, 6, 20),
            year_month="2025-06",
            amount=Decimal("85.00"),
            abs_amount=Decimal("85.00"),
            where_="Target",
            what_="Shopping",
            category="Essentials",
            source="Credit Card"
        ),
        # Amazon transaction
        Transaction(
            id=str(uuid.uuid4()),
            ingest_id=ingest_id,
            date=date(2025, 6, 18),
            year_month="2025-06",
            amount=Decimal("120.00"),
            abs_amount=Decimal("120.00"),
            where_="Amazon",
            what_="Online Purchase",
            category="Home",
            source="Chase"
        ),
        # Cash transaction
        Transaction(
            id=str(uuid.uuid4()),
            ingest_id=ingest_id,
            date=date(2025, 6, 22),
            year_month="2025-06",
            amount=Decimal("50.00"),
            abs_amount=Decimal("50.00"),
            where_="Coffee Shop",
            what_="Coffee",
            category="Food",
            source="Cash"
        ),
        # Chase transaction
        Transaction(
            id=str(uuid.uuid4()),
            ingest_id=ingest_id,
            date=date(2025, 6, 25),
            year_month="2025-06",
            amount=Decimal("200.00"),
            abs_amount=Decimal("200.00"),
            where_="Store",
            what_="Purchase",
            category="Personal",
            source="Chase"
        ),
        # Starbucks transaction
        Transaction(
            id=str(uuid.uuid4()),
            ingest_id=ingest_id,
            date=date(2025, 6, 28),
            year_month="2025-06",
            amount=Decimal("8.50"),
            abs_amount=Decimal("8.50"),
            where_="Starbucks",
            what_="Coffee",
            category="Food",
            source="Credit Card"
        ),
    ]
    
    for transaction in transactions:
        session.add(transaction)
    
    session.commit()
    session.close()
    
    # Override get_db dependency
    def override_get_db():
        db = test_session_local()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    return test_session_local


def setup_real_database(db_url: Optional[str] = None):
    """
    Set up connection to real database (no seeding).
    
    If db_url is provided, override get_db to use that database.
    Otherwise, use the existing app database without override.
    """
    if db_url:
        # Create a new engine with the provided URL
        connect_args = {}
        if db_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        
        real_engine = create_engine(db_url, connect_args=connect_args)
        real_session_local = sessionmaker(autocommit=False, autoflush=False, bind=real_engine)
        
        # Override get_db to use the custom database
        def override_get_db():
            db = real_session_local()
            try:
                yield db
            finally:
                db.close()
        
        app.dependency_overrides[get_db] = override_get_db
    else:
        # Use the existing app database without override
        real_session_local = SessionLocal
    
    # Do NOT seed data - use existing data
    
    return real_session_local


def load_questions(jsonl_path: Path) -> List[Dict[str, Any]]:
    """Load questions from JSONL file."""
    questions = []
    with open(jsonl_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(json.loads(line))
    return questions


def check_trace_present(response_data: Dict[str, Any]) -> tuple[bool, str]:
    """Check if trace exists and contains required keys."""
    if "trace" not in response_data:
        return False, "trace missing"
    
    trace = response_data["trace"]
    required_keys = [
        "intent", "resolved_month", "called_functions",
        "filters_used", "evidence_count_returned"
    ]
    
    missing = [key for key in required_keys if key not in trace]
    if missing:
        return False, f"trace missing keys: {missing}"
    
    return True, "pass"


def check_evidence_rule(response_data: Dict[str, Any]) -> tuple[bool, str]:
    """Check evidence rule: if numbers has expense_total/count, evidence must be present unless count==0."""
    numbers = response_data.get("numbers")
    if not numbers:
        return True, "pass"  # No numbers, rule doesn't apply
    
    has_expense_total = "expense_total" in numbers
    has_count = "count" in numbers
    
    if not (has_expense_total or has_count):
        return True, "pass"  # No expense_total or count, rule doesn't apply
    
    count = numbers.get("count", 0)
    if count == 0:
        return True, "pass"  # Count is 0, evidence can be empty
    
    evidence = response_data.get("evidence", [])
    if not evidence:
        return False, f"evidence missing but count={count} > 0"
    
    return True, "pass"


def check_intent_match(response_data: Dict[str, Any], expect_type: str) -> tuple[bool, str]:
    """Check if response intent matches expected type for non-clarify cases."""
    clarify_types = ["clarify_month", "clarify_entity"]
    if expect_type in clarify_types:
        return True, "pass"  # Skip for clarify cases
    
    trace = response_data.get("trace", {})
    actual_intent = trace.get("intent")
    
    if actual_intent != expect_type:
        return False, f"intent mismatch: expected {expect_type}, got {actual_intent}"
    
    return True, "pass"


def check_numeric_correctness(
    response_data: Dict[str, Any],
    expect: Dict[str, Any],
    db_session_factory
) -> tuple[bool, str]:
    """Check numeric correctness by comparing to actual DB queries."""
    expect_type = expect.get("type")
    
    if expect_type not in ["category_total", "merchant_total", "source_total", "monthly_summary"]:
        return True, "pass"  # Not a numeric check case
    
    trace = response_data.get("trace", {})
    month = trace.get("resolved_month")
    if not month:
        return False, "no resolved_month in trace"
    
    numbers = response_data.get("numbers")
    if not numbers:
        return False, "no numbers in response"
    
    # Create a session for this check
    db = db_session_factory()
    try:
        if expect_type == "category_total":
            category = expect.get("category")
            if not category:
                return False, "category missing in expect"
            expected = get_category_total(db, month, category)
            actual_expense = Decimal(str(numbers.get("expense_total", "0")))
            actual_count = numbers.get("count", 0)
            if actual_expense != expected["expense_total"]:
                return False, f"expense_total mismatch: expected {expected['expense_total']}, got {actual_expense}"
            if actual_count != expected["count"]:
                return False, f"count mismatch: expected {expected['count']}, got {actual_count}"
        
        elif expect_type == "merchant_total":
            merchant = expect.get("merchant")
            if not merchant:
                return False, "merchant missing in expect"
            expected = get_merchant_total(db, month, merchant)
            actual_expense = Decimal(str(numbers.get("expense_total", "0")))
            actual_count = numbers.get("count", 0)
            if actual_expense != expected["expense_total"]:
                return False, f"expense_total mismatch: expected {expected['expense_total']}, got {actual_expense}"
            if actual_count != expected["count"]:
                return False, f"count mismatch: expected {expected['count']}, got {actual_count}"
        
        elif expect_type == "source_total":
            source = expect.get("source")
            if not source:
                return False, "source missing in expect"
            expected = get_source_total(db, month, source)
            actual_expense = Decimal(str(numbers.get("expense_total", "0")))
            actual_count = numbers.get("count", 0)
            if actual_expense != expected["expense_total"]:
                return False, f"expense_total mismatch: expected {expected['expense_total']}, got {actual_expense}"
            if actual_count != expected["count"]:
                return False, f"count mismatch: expected {expected['count']}, got {actual_count}"
        
        elif expect_type == "monthly_summary":
            expected = get_monthly_totals(db, month)
            actual_expense = Decimal(str(numbers.get("expense_total", "0")))
            actual_count = numbers.get("transaction_count", 0)
            if actual_expense != expected["expense_total"]:
                return False, f"expense_total mismatch: expected {expected['expense_total']}, got {actual_expense}"
            if actual_count != expected["transaction_count"]:
                return False, f"transaction_count mismatch: expected {expected['transaction_count']}, got {actual_count}"
        
        return True, "pass"
    
    except Exception as e:
        return False, f"error computing expected: {str(e)}"
    finally:
        db.close()


def create_remote_client(base_url: str) -> Callable:
    """Create a client function for remote server using httpx."""
    if not HTTPX_AVAILABLE:
        raise ImportError("httpx is required for remote server mode. Install with: pip install httpx")
    
    def call_query(request_data: Dict[str, Any]) -> tuple[Dict[str, Any], int]:
        """Call /query endpoint on remote server."""
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(f"{base_url}/query", json=request_data)
                return response.json(), response.status_code
        except Exception as e:
            return {}, 500
    
    return call_query


def create_inprocess_client(db_mode: str = "real", db_url: Optional[str] = None) -> tuple[Callable, Callable, str]:
    """
    Create a client function for in-process testing using TestClient.
    
    Args:
        db_mode: "real" or "seeded"
        db_url: Optional database URL for real mode
        
    Returns:
        Tuple of (call_query function, get_db_session function, data_mode string)
    """
    if db_mode == "seeded":
        # Setup seeded in-memory database
        db_session_factory = setup_seeded_database()
        data_mode = "seeded"
    else:
        # Setup real database connection
        db_session_factory = setup_real_database(db_url)
        data_mode = "real"
    
    client = TestClient(app)
    
    def call_query(request_data: Dict[str, Any]) -> tuple[Dict[str, Any], int]:
        """Call /query endpoint in-process."""
        try:
            response = client.post("/query", json=request_data)
            return response.json(), response.status_code
        except Exception as e:
            return {}, 500
    
    def get_db_session():
        """Get database session for numeric correctness checks."""
        return db_session_factory()
    
    return call_query, get_db_session, data_mode


def run_evaluation(
    base_url: Optional[str] = None,
    inprocess: bool = True,
    db_mode: str = "real",
    db_url: Optional[str] = None
):
    """
    Run evaluation against questions_v1.jsonl.
    
    Args:
        base_url: Base URL for remote server (only used in remote mode)
        inprocess: Whether to run in-process (True) or remote (False)
        db_mode: "real" or "seeded" (only used in in-process mode)
        db_url: Optional database URL for real mode
    """
    # Setup
    eval_dir = Path(__file__).parent
    questions_path = eval_dir / "questions_v1.jsonl"
    report_path = eval_dir / "report.json"
    
    # Determine data mode
    data_mode = "real"  # Default for remote mode
    
    # Choose client mode
    if inprocess:
        print("Running in-process mode (TestClient)...")
        if db_mode == "seeded":
            print("Database mode: SEEDED (in-memory SQLite with synthetic data)")
            print("Setting up seeded test database...")
        else:
            db_display_url = db_url if db_url else get_settings().database_url
            print(f"Database mode: REAL (using existing database)")
            print(f"Database URL: {db_display_url}")
            print("Note: Using real ingested data, no synthetic seeding")
        
        call_query, get_db_session, data_mode = create_inprocess_client(db_mode, db_url)
        db_session_factory = get_db_session
    else:
        if not base_url:
            base_url = "http://127.0.0.1:8000"
        print(f"Running against remote server: {base_url}")
        print("Database mode: REAL (using server's database)")
        call_query = create_remote_client(base_url)
        # For remote mode, we can't easily get DB session, so skip numeric checks
        db_session_factory = None
    
    print(f"Loading questions from {questions_path}...")
    questions = load_questions(questions_path)
    
    print(f"Running {len(questions)} test cases...\n")
    
    results = []
    
    for question_data in questions:
        qid = question_data["id"]
        question = question_data["question"]
        month = question_data.get("month")
        expect = question_data["expect"]
        
        # Call /query endpoint
        request_data = {
            "question": question,
            "limit_evidence": 10
        }
        if month:
            request_data["month"] = month
        
        try:
            response_data, status_code = call_query(request_data)
        except Exception as e:
            response_data = {}
            status_code = 500
            error = str(e)
        
        # Run checks
        checks = {}
        
        # Check 1: trace_present
        passed, message = check_trace_present(response_data)
        checks["trace_present"] = {"passed": passed, "message": message}
        
        # Check 2: evidence_rule
        passed, message = check_evidence_rule(response_data)
        checks["evidence_rule"] = {"passed": passed, "message": message}
        
        # Check 3: intent_match
        passed, message = check_intent_match(response_data, expect.get("type"))
        checks["intent_match"] = {"passed": passed, "message": message}
        
        # Check 4: numeric_correctness (only in in-process mode)
        if db_session_factory:
            passed, message = check_numeric_correctness(response_data, expect, db_session_factory)
            checks["numeric_correctness"] = {"passed": passed, "message": message}
        else:
            checks["numeric_correctness"] = {"passed": True, "message": "skipped (remote mode)"}
        
        # Overall pass/fail
        all_passed = all(check["passed"] for check in checks.values())
        
        result = {
            "id": qid,
            "question": question,
            "month": month,
            "expect": expect,
            "status_code": status_code,
            "response": response_data,
            "checks": checks,
            "passed": all_passed
        }
        
        results.append(result)
        
        # Print status
        status = "✓" if all_passed else "✗"
        print(f"{status} {qid}: {question[:50]}...")
        if not all_passed:
            for check_name, check_result in checks.items():
                if not check_result["passed"]:
                    print(f"    {check_name}: {check_result['message']}")
    
    # Summary
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    
    # Calculate specific rates
    # Trace compliance rate
    trace_passed = sum(1 for r in results if r["checks"].get("trace_present", {}).get("passed", False))
    trace_compliance_rate = (trace_passed / total * 100) if total > 0 else 0.0
    
    # Evidence compliance rate
    evidence_passed = sum(1 for r in results if r["checks"].get("evidence_rule", {}).get("passed", False))
    evidence_compliance_rate = (evidence_passed / total * 100) if total > 0 else 0.0
    
    # Numeric accuracy rate (only for applicable cases)
    numeric_applicable_types = ["category_total", "merchant_total", "source_total", "monthly_summary"]
    numeric_applicable = [r for r in results if r["expect"].get("type") in numeric_applicable_types]
    numeric_applicable_count = len(numeric_applicable)
    numeric_passed = sum(1 for r in numeric_applicable if r["checks"].get("numeric_correctness", {}).get("passed", False))
    numeric_accuracy_rate = (numeric_passed / numeric_applicable_count * 100) if numeric_applicable_count > 0 else None
    
    # Clarification correctness rate (only for clarify cases)
    # Check if clarifying_question is present when expected
    clarify_types = ["clarify_month", "clarify_entity"]
    clarify_cases = [r for r in results if r["expect"].get("type") in clarify_types]
    clarify_count = len(clarify_cases)
    clarify_passed = sum(
        1 for r in clarify_cases 
        if r["response"].get("clarifying_question") is not None
    )
    clarification_correctness_rate = (clarify_passed / clarify_count * 100) if clarify_count > 0 else None
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Pass rate: {passed/total*100:.1f}%")
    
    print("\nCompliance Rates:")
    print(f"  Trace compliance rate: {trace_compliance_rate:.1f}% ({trace_passed}/{total})")
    print(f"  Evidence compliance rate: {evidence_compliance_rate:.1f}% ({evidence_passed}/{total})")
    if numeric_accuracy_rate is not None:
        print(f"  Numeric accuracy rate: {numeric_accuracy_rate:.1f}% ({numeric_passed}/{numeric_applicable_count})")
    else:
        print(f"  Numeric accuracy rate: N/A (no applicable cases)")
    if clarification_correctness_rate is not None:
        print(f"  Clarification correctness rate: {clarification_correctness_rate:.1f}% ({clarify_passed}/{clarify_count})")
    else:
        print(f"  Clarification correctness rate: N/A (no clarify cases)")
    
    # Check breakdown
    print("\nCheck Breakdown:")
    check_names = ["trace_present", "evidence_rule", "intent_match", "numeric_correctness"]
    for check_name in check_names:
        check_passed = sum(1 for r in results if r["checks"].get(check_name, {}).get("passed", False))
        print(f"  {check_name}: {check_passed}/{total} ({check_passed/total*100:.1f}%)")
    
    # Write report
    report = {
        "metadata": {
            "data_mode": data_mode,
            "inprocess": inprocess,
            "base_url": base_url if not inprocess else None,
            "db_url": db_url if inprocess and db_mode == "real" else None
        },
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed/total*100,
            "trace_compliance_rate": trace_compliance_rate,
            "evidence_compliance_rate": evidence_compliance_rate,
            "numeric_accuracy_rate": numeric_accuracy_rate,
            "clarification_correctness_rate": clarification_correctness_rate
        },
        "results": results
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\nDetailed report written to {report_path}")
    
    # Cleanup
    if inprocess and (db_mode == "seeded" or (db_mode == "real" and db_url)):
        # Clear overrides if we set them (seeded mode or real mode with custom db_url)
        app.dependency_overrides.clear()
    
    return report


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Run evaluation tests against /query endpoint"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://127.0.0.1:8000",
        help="Base URL for remote server (default: http://127.0.0.1:8000, only used with --remote)"
    )
    parser.add_argument(
        "--remote",
        action="store_true",
        help="Run against remote server instead of in-process mode (default: in-process)"
    )
    parser.add_argument(
        "--db-mode",
        type=str,
        choices=["real", "seeded"],
        default="real",
        help="Database mode: 'real' uses existing database, 'seeded' uses in-memory with synthetic data (default: real)"
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="Database URL for real mode (default: uses app settings, typically sqlite:///./finance.db)"
    )
    
    args = parser.parse_args()
    
    # Determine mode: inprocess is default unless --remote is specified
    inprocess = not args.remote
    base_url = args.base_url if args.remote else None
    
    # Validate db_mode (only relevant for in-process mode)
    if inprocess:
        db_mode = args.db_mode
        db_url = args.db_url
    else:
        # Remote mode always uses real database (server's database)
        db_mode = "real"
        db_url = None
    
    if args.remote and not HTTPX_AVAILABLE:
        print("Error: httpx is required for remote mode. Install with: pip install httpx")
        sys.exit(1)
    
    try:
        run_evaluation(
            base_url=base_url,
            inprocess=inprocess,
            db_mode=db_mode,
            db_url=db_url
        )
    except KeyboardInterrupt:
        print("\n\nEvaluation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError running evaluation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
