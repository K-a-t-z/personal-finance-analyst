import re
from typing import Optional, List

# Known categories for intent classification
KNOWN_CATEGORIES = ["Travel", "Essentials", "Food", "Personal", "Home", "Others"]


def classify_intent(question: str) -> str:
    """
    Classify the intent of a financial query question.
    
    Args:
        question: User question string
        
    Returns:
        One of: "monthly_summary", "category_total", "merchant_total", "source_total",
        "top_merchants", "category_breakdown", "source_breakdown", "unknown"
    """
    if not question:
        return "unknown"
    
    question_lower = question.lower()
    
    # Check for breakdowns first (more specific)
    if "breakdown" in question_lower:
        if "category" in question_lower:
            return "category_breakdown"
        if "source" in question_lower:
            return "source_breakdown"
    
    # Check for top merchants
    if "top" in question_lower and ("merchant" in question_lower or "where" in question_lower):
        return "top_merchants"
    
    # Check for category total (check for known category names or "category" keyword)
    # This should come before merchant_total to prevent "Food" from being interpreted as a merchant
    if extract_category(question, KNOWN_CATEGORIES) is not None or "category" in question_lower:
        return "category_total"
    
    # Check for source total (but not if breakdown was already matched)
    if "source" in question_lower:
        return "source_total"
    
    # Check for merchant total (quoted phrase or after "at"/"on")
    # This comes after category_total to prevent category names from being interpreted as merchants
    merchant_pattern = r'["\']([^"\']+)["\']|(?:at|on)\s+(\w+(?:\s+\w+)*)'
    if re.search(merchant_pattern, question_lower):
        return "merchant_total"
    
    # Check for monthly summary (using extract_month and expanded keywords)
    # Only if none of the above entity-specific queries matched
    month = extract_month(question)
    if month:
        monthly_keywords = ["spend", "spent", "expense", "expenses", "total", "net"]
        has_monthly_keyword = any(keyword in question_lower for keyword in monthly_keywords)
        if has_monthly_keyword:
            return "monthly_summary"
    
    return "unknown"


def extract_month(question: str) -> Optional[str]:
    """
    Extract month in "YYYY-MM" format from question.
    
    Args:
        question: User question string
        
    Returns:
        Month string in "YYYY-MM" format if found, None otherwise
    """
    if not question:
        return None
    
    # Look for YYYY-MM pattern
    month_pattern = r'\b(\d{4}-\d{2})\b'
    match = re.search(month_pattern, question)
    if match:
        month_str = match.group(1)
        # Basic validation: month should be 01-12
        try:
            year, month_num = month_str.split("-")
            month_int = int(month_num)
            if 1 <= month_int <= 12:
                return month_str
        except (ValueError, AttributeError):
            pass
    
    return None


def extract_category(question: str, known_categories: List[str]) -> Optional[str]:
    """
    Extract category name from question by matching against known categories.
    
    Args:
        question: User question string
        known_categories: List of known category names to match against
        
    Returns:
        Matched category name if found, None otherwise
    """
    if not question or not known_categories:
        return None
    
    question_lower = question.lower()
    
    # Try exact match first (case-insensitive)
    for category in known_categories:
        if not category:
            continue
        # Match whole word or phrase
        category_lower = category.lower()
        # Use word boundary or phrase matching
        pattern = r'\b' + re.escape(category_lower) + r'\b'
        if re.search(pattern, question_lower):
            return category
    
    return None


def extract_source(question: str, known_sources: List[str]) -> Optional[str]:
    """
    Extract source name from question by matching against known sources.
    
    Args:
        question: User question string
        known_sources: List of known source names to match against
        
    Returns:
        Matched source name if found, None otherwise
    """
    if not question or not known_sources:
        return None
    
    question_lower = question.lower()
    
    # Try exact match first (case-insensitive)
    for source in known_sources:
        if not source:
            continue
        # Match whole word or phrase
        source_lower = source.lower()
        # Use word boundary or phrase matching
        pattern = r'\b' + re.escape(source_lower) + r'\b'
        if re.search(pattern, question_lower):
            return source
    
    return None


def extract_merchant(question: str, known_categories: Optional[List[str]] = None) -> Optional[str]:
    """
    Extract merchant name from question using simple heuristics.
    
    Looks for:
    - Quoted phrases: "Uber", 'Starbucks'
    - Phrases after "at" or "on": "at Target", "on Amazon"
      Stops at boundary tokens like "in", "for", "during", "this", "last", or month patterns
    
    Args:
        question: User question string
        known_categories: Optional list of known category names to filter out
        
    Returns:
        Extracted merchant name if found (and not a known category), None otherwise
    """
    if not question:
        return None
    
    merchant = None
    
    # First, try to find quoted phrases
    quoted_pattern = r'["\']([^"\']+)["\']'
    match = re.search(quoted_pattern, question)
    if match:
        merchant = match.group(1).strip()
    
    # Then, try to find phrase after "at" or "on"
    # Stop at boundary tokens: "in", "for", "during", "this", "last", or month pattern (YYYY-MM)
    if merchant is None:
        # Find position after "at" or "on"
        at_on_match = re.search(r'\b(?:at|on)\s+', question, re.IGNORECASE)
        if at_on_match:
            start_pos = at_on_match.end()
            remaining_text = question[start_pos:]
            
            # Find boundary tokens or month pattern
            boundary_pattern = r'\b(?:in|for|during|this|last)\b|\d{4}-\d{2}'
            boundary_match = re.search(boundary_pattern, remaining_text, re.IGNORECASE)
            
            if boundary_match:
                # Extract up to the boundary
                merchant = remaining_text[:boundary_match.start()].strip()
            else:
                # Extract to end of string
                merchant = remaining_text.strip()
    
    if not merchant:
        return None
    
    # Strip punctuation and extra spaces
    merchant = re.sub(r'[^\w\s]', '', merchant)  # Remove punctuation
    merchant = re.sub(r'\s+', ' ', merchant)  # Normalize spaces
    merchant = merchant.strip()
    
    # Check if merchant is empty after cleaning
    if not merchant:
        return None
    
    # Check if merchant matches any known category (case-insensitive)
    if known_categories:
        merchant_lower = merchant.lower()
        for category in known_categories:
            if category and category.lower() == merchant_lower:
                return None
    
    return merchant
