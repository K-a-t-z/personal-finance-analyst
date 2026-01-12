import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import uuid

from app.core.db import Base
from app.core.models import Transaction, Ingest
from app.core.evidence import get_evidence_rows


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestEvidenceFilters:
    """Tests for get_evidence_rows filtering."""
    
    def test_filter_by_category(self, db_session: Session):
        """Test that get_evidence_rows filters by category correctly."""
        # Create an ingest record (required for foreign key)
        ingest_id = str(uuid.uuid4())
        ingest = Ingest(
            ingest_id=ingest_id,
            filename="test.csv",
            row_count=3,
            status="success",
            error=None
        )
        db_session.add(ingest)
        db_session.flush()
        
        # Insert 3 transactions in 2025-05: two Food expenses, one Travel expense
        transactions = [
            Transaction(
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
            ),
            Transaction(
                id=str(uuid.uuid4()),
                ingest_id=ingest_id,
                date=date(2025, 5, 15),
                year_month="2025-05",
                amount=Decimal("12.00"),
                abs_amount=Decimal("12.00"),
                where_="Restaurant",
                what_="Lunch",
                category="Food",
                source="Credit Card"
            ),
            Transaction(
                id=str(uuid.uuid4()),
                ingest_id=ingest_id,
                date=date(2025, 5, 20),
                year_month="2025-05",
                amount=Decimal("150.00"),
                abs_amount=Decimal("150.00"),
                where_="Airline",
                what_="Flight",
                category="Travel",
                source="Credit Card"
            )
        ]
        
        for transaction in transactions:
            db_session.add(transaction)
        
        db_session.commit()
        
        # Call get_evidence_rows with category filter
        results = get_evidence_rows(
            db_session,
            month="2025-05",
            filters={"kind": "expense", "category": "Food"},
            limit=10
        )
        
        # Assert all returned rows have category Food and amount > 0, and length is 2
        assert len(results) == 2
        for row in results:
            assert row["category"] == "Food"
            assert row["amount"] > 0
            assert row["transaction_id"] is not None
            assert row["date"] is not None
