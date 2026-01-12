import pytest
from datetime import date
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import uuid

from app.main import app
from app.core.db import Base, get_db
from app.core.models import Transaction, Ingest


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Seed database with one Food transaction in 2025-05
    session = SessionLocal()
    
    # Create an ingest record
    ingest_id = str(uuid.uuid4())
    ingest = Ingest(
        ingest_id=ingest_id,
        filename="test.csv",
        row_count=1,
        status="success",
        error=None
    )
    session.add(ingest)
    session.flush()
    
    # Create one Food transaction in 2025-05
    transaction = Transaction(
        id=str(uuid.uuid4()),
        ingest_id=ingest_id,
        date=date(2025, 5, 10),
        year_month="2025-05",
        amount=Decimal("25.50"),
        abs_amount=Decimal("25.50"),
        where_="Grocery Store",
        what_="Groceries",
        category="Food",
        source="Credit Card"
    )
    session.add(transaction)
    session.commit()
    session.close()
    
    # Override get_db dependency
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield
    
    # Cleanup - clear dependency overrides after test
    app.dependency_overrides.clear()


def test_query_trace_shape(test_db):
    """Test that /query response trace contains all required keys."""
    client = TestClient(app)
    
    # Call /query with a category question
    response = client.post(
        "/query",
        json={
            "question": "How much did I spend on Food in 2025-05?",
            "month": "2025-05",
            "limit_evidence": 10
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Assert trace exists and contains all required keys
    assert "trace" in data
    trace = data["trace"]
    
    required_keys = [
        "intent",
        "resolved_month",
        "called_functions",
        "parameters",
        "filters_used",
        "evidence_count_returned",
        "notes"
    ]
    
    for key in required_keys:
        assert key in trace, f"Trace missing required key: {key}"
    
    # Assert trace values are appropriate
    assert trace["intent"] is not None
    assert trace["resolved_month"] == "2025-05"
    assert isinstance(trace["called_functions"], list)
    assert isinstance(trace["parameters"], dict)
    assert isinstance(trace["filters_used"], dict)
    assert isinstance(trace["evidence_count_returned"], int)
    assert isinstance(trace["notes"], list)
