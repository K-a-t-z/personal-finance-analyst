from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    Column, String, Integer, Date, DateTime, Numeric, Text, ForeignKey, Index
)
from sqlalchemy.orm import relationship
import uuid

from app.core.db import Base


class Ingest(Base):
    """Model for tracking CSV file ingestion."""
    __tablename__ = "ingest"
    
    ingest_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    filename = Column(String(255), nullable=False)
    row_count = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)
    error = Column(Text, nullable=True)
    
    # Relationship to transactions
    transactions = relationship("Transaction", back_populates="ingest")


class Transaction(Base):
    """Model for financial transactions from CSV data."""
    __tablename__ = "transactions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ingest_id = Column(String(36), ForeignKey("ingest.ingest_id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    year_month = Column(String(7), nullable=False, index=True)  # Format: "YYYY-MM"
    amount = Column(Numeric(10, 2), nullable=False)
    abs_amount = Column(Numeric(10, 2), nullable=False)
    where_ = Column(String(255), nullable=True, index=True)  # Maps to "Where?" CSV column
    what_ = Column(String(255), nullable=True)  # Maps to "What?" CSV column
    category = Column(String(100), nullable=True, index=True)
    source = Column(String(100), nullable=True, index=True)
    raw_row = Column(Text, nullable=True)  # Store original CSV row as JSON string
    
    # Relationship to ingest
    ingest = relationship("Ingest", back_populates="transactions")
    
    # Composite indexes for month filtering
    __table_args__ = (
        Index("idx_category_year_month", "category", "year_month"),
        Index("idx_where_year_month", "where_", "year_month"),
        Index("idx_source_year_month", "source", "year_month"),
    )
