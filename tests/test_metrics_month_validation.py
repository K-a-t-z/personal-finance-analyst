import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.db import Base
from app.core.models import Transaction, Ingest  # Import models to register with Base
from app.core.metrics import get_monthly_totals


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


class TestMetricsMonthValidation:
    """Tests for month validation in metrics functions."""
    
    def test_invalid_format_single_digit_month(self, db_session: Session):
        """Test that '2025-5' (single digit month) raises ValueError."""
        with pytest.raises(ValueError, match="Invalid month format"):
            get_monthly_totals(db_session, "2025-5")
    
    def test_invalid_format_non_numeric(self, db_session: Session):
        """Test that 'abcd-ef' (non-numeric) raises ValueError."""
        with pytest.raises(ValueError, match="Invalid month format"):
            get_monthly_totals(db_session, "abcd-ef")
    
    def test_valid_month_no_rows_returns_zeros(self, db_session: Session):
        """Test that valid month with no rows returns zeros and count is 0."""
        result = get_monthly_totals(db_session, "2025-05")
        
        assert result["expense_total"] == Decimal("0.00")
        assert result["income_total"] == Decimal("0.00")
        assert result["net_total"] == Decimal("0.00")
        assert result["transaction_count"] == 0
    
    def test_invalid_month_number_too_high(self, db_session: Session):
        """Test that month > 12 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid month.*Month must be between 01-12"):
            get_monthly_totals(db_session, "2025-13")
    
    def test_invalid_month_number_zero(self, db_session: Session):
        """Test that month 00 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid month.*Month must be between 01-12"):
            get_monthly_totals(db_session, "2025-00")
