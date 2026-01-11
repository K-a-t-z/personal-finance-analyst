import json
import uuid
from decimal import Decimal
from typing import List, Dict, Any
import pandas as pd

from app.utils.dates import parse_date
from app.utils.money import parse_amount

REQUIRED_COLUMNS = ["Date", "Amount", "Where?", "What?", "Category", "Source"]


def validate_columns(df: pd.DataFrame) -> None:
    """
    Validate that all required columns exist in the dataframe.
    
    Args:
        df: pandas DataFrame to validate
        
    Raises:
        ValueError: If any required columns are missing, with a list of missing columns
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError(f"Expected pandas DataFrame, got {type(df).__name__}")
    
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    
    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}. "
            f"Found columns: {list(df.columns)}. "
            f"Required columns (case sensitive): {REQUIRED_COLUMNS}"
        )


def normalize_transactions(df: pd.DataFrame, ingest_id: str) -> List[Dict[str, Any]]:
    """
    Normalize CSV dataframe rows into Transaction model-ready dictionaries.
    
    Args:
        df: pandas DataFrame with required columns
        ingest_id: UUID string of the ingest record
        
    Returns:
        List of dictionaries ready for Transaction model insertion
        
    Raises:
        ValueError: If parsing fails, with row index information for debugging
    """
    validate_columns(df)
    
    transactions = []
    
    for idx, row in df.iterrows():
        try:
            # Parse date
            date_str = str(row["Date"]) if pd.notna(row["Date"]) else ""
            parsed_date = parse_date(date_str)
            
            # Derive year_month as "YYYY-MM"
            year_month = parsed_date.strftime("%Y-%m")
            
            # Parse amount
            amount_str = str(row["Amount"]) if pd.notna(row["Amount"]) else ""
            amount = parse_amount(amount_str)
            
            # Compute abs_amount
            abs_amount = abs(amount)
            
            # Map CSV columns to model fields
            where_ = str(row["Where?"]) if pd.notna(row["Where?"]) else None
            what_ = str(row["What?"]) if pd.notna(row["What?"]) else None
            category = str(row["Category"]) if pd.notna(row["Category"]) else None
            source = str(row["Source"]) if pd.notna(row["Source"]) else None
            
            # Convert row to dict and store as JSON string
            raw_row = json.dumps(row.to_dict())
            
            # Generate UUID for transaction id
            transaction_id = str(uuid.uuid4())
            
            transaction = {
                "id": transaction_id,
                "ingest_id": ingest_id,
                "date": parsed_date,
                "year_month": year_month,
                "amount": amount,
                "abs_amount": abs_amount,
                "where_": where_,
                "what_": what_,
                "category": category,
                "source": source,
                "raw_row": raw_row,
            }
            
            transactions.append(transaction)
            
        except Exception as e:
            # Include row index (0-based) in error message for debugging
            row_num = idx + 1  # Convert to 1-based for user-friendly error message
            raise ValueError(
                f"Error processing row {row_num} (0-based index: {idx}): {str(e)}. "
                f"Row data: {row.to_dict()}"
            ) from e
    
    return transactions
