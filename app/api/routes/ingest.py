import uuid
import io
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
import pandas as pd

from app.core.db import get_db
from app.core.models import Ingest, Transaction
from app.core.parsing import normalize_transactions, validate_columns

router = APIRouter()


@router.post("/ingest")
async def ingest_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Ingest a CSV file containing financial transactions.
    
    Accepts a CSV file with columns: Date, Amount, Where?, What?, Category, Source
    Returns ingestion summary with statistics.
    """
    ingest_id = str(uuid.uuid4())
    filename = file.filename or "unknown.csv"
    error_message: Optional[str] = None
    
    try:
        # Read CSV file content
        contents = await file.read()
        # Read CSV into pandas DataFrame
        df = pd.read_csv(io.BytesIO(contents))
        
        # Validate columns
        validate_columns(df)
        
        row_count = len(df)
        
        # Normalize transactions
        transactions = normalize_transactions(df, ingest_id)
        
        # Create Ingest record with status "success"
        ingest_record = Ingest(
            ingest_id=ingest_id,
            filename=filename,
            row_count=row_count,
            status="success",
            error=None
        )
        db.add(ingest_record)
        db.flush()  # Flush to get ingest_id available for foreign key
        
        # Bulk insert transactions
        if transactions:
            db.bulk_insert_mappings(Transaction, transactions)
        
        # Commit the transaction
        db.commit()
        
        # Calculate statistics from the dataframe
        # Date range
        date_min = None
        date_max = None
        if transactions:
            dates = [t["date"] for t in transactions]
            date_min = min(dates).isoformat()
            date_max = max(dates).isoformat()
        
        # Categories and sources from dataframe (using distinct logic)
        categories_seen = []
        if "Category" in df.columns:
            categories_seen = df["Category"].dropna().unique().tolist()
            categories_seen = [str(c) for c in categories_seen]
        
        sources_seen = []
        if "Source" in df.columns:
            sources_seen = df["Source"].dropna().unique().tolist()
            sources_seen = [str(s) for s in sources_seen]
        
        # Notes about sign convention
        notes = "Sign convention: expenses are positive numbers, income/settlements are negative numbers."
        
        return {
            "ingest_id": ingest_id,
            "row_count": row_count,
            "date_range": {
                "min": date_min,
                "max": date_max
            },
            "categories_seen": categories_seen,
            "sources_seen": sources_seen,
            "notes": notes
        }
        
    except ValueError as e:
        # Validation or parsing error
        error_message = str(e)
        row_count = 0
        
        # Try to get row count from dataframe if it was created
        try:
            if 'df' in locals():
                row_count = len(df)
        except:
            pass
        
        # Create Ingest record with status "failed"
        ingest_record = Ingest(
            ingest_id=ingest_id,
            filename=filename,
            row_count=row_count,
            status="failed",
            error=error_message
        )
        db.add(ingest_record)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "ingest_id": ingest_id,
                "error": error_message,
                "row_count": row_count
            }
        )
        
    except Exception as e:
        # Unexpected error
        error_message = f"Unexpected error: {str(e)}"
        row_count = 0
        
        # Try to get row count from dataframe if it was created
        try:
            if 'df' in locals():
                row_count = len(df)
        except:
            pass
        
        # Create Ingest record with status "failed"
        ingest_record = Ingest(
            ingest_id=ingest_id,
            filename=filename,
            row_count=row_count,
            status="failed",
            error=error_message
        )
        db.add(ingest_record)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "ingest_id": ingest_id,
                "error": error_message,
                "row_count": row_count
            }
        )
