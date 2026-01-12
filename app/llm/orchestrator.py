import re
from typing import Optional, List

# Known categories for intent classification
KNOWN_CATEGORIES = ["Travel", "Essentials", "Food", "Personal", "Home", "Others"]


def classify_intent(question: str, known_sources: Optional[List[str]] = None) -> str:
    """
    Classify the intent of a financial query question.
    
    Priority order:
    1. top_merchants (top + merchant/where)
    2. category_breakdown (breakdown + category, or category + superlative)
    3. source_breakdown (breakdown + source)
    4. source_total (keywords using/via/with/from + known source)
    5. category_total (known category or "category" with a category value)
    6. merchant_total (explicit merchant phrase: "at <x>" or quoted merchant)
    7. monthly_summary (month exists + keywords: spent/spend/expense/expenses/total/net/overall)
    8. unknown
    
    Args:
        question: User question string
        known_sources: Optional list of known source names for better classification
        
    Returns:
        One of: "monthly_summary", "category_total", "merchant_total", "source_total",
        "top_merchants", "category_breakdown", "source_breakdown", "unknown"
    """
    if not question:
        return "unknown"
    
    question_lower = question.lower()
    
    # Priority 1: Check for top merchants
    if "top" in question_lower and ("merchant" in question_lower or "where" in question_lower):
        return "top_merchants"
    
    # Priority 2: Check for category breakdown
    if "breakdown" in question_lower and "category" in question_lower:
        return "category_breakdown"
    
    # Also check for superlative category questions (e.g., "which category did I spend the most on")
    if "category" in question_lower:
        superlative_keywords = ["most", "highest", "max", "maximum", "largest"]
        has_superlative = any(keyword in question_lower for keyword in superlative_keywords)
        if has_superlative:
            return "category_breakdown"
    
    # Priority 3: Check for source breakdown
    if "breakdown" in question_lower and "source" in question_lower:
        return "source_breakdown"
    
    # Priority 4: Check for source total with keywords: "using", "via", "with", "from"
    # Strengthened: If source keywords are present, try to extract a plausible source token
    # (either from known_sources OR as a fallback token immediately after keyword)
    source_keywords = ["using", "via", "with", "from"]
    has_source_keyword = any(keyword in question_lower for keyword in source_keywords)
    if has_source_keyword:
        # First try to extract from known_sources
        if known_sources:
            extracted_source = extract_source(question, known_sources)
            if extracted_source:
                return "source_total"
        
        # Fallback: Try to extract a plausible source token immediately after keyword
        # This handles cases like "using Cash" even if Cash isn't in known_sources for that month
        for keyword in source_keywords:
            # Pattern: keyword + source token (1-2 words, stopping at boundary words)
            keyword_pattern = rf'\b{re.escape(keyword)}\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)'
            match = re.search(keyword_pattern, question_lower)
            if match:
                potential_source = match.group(1).strip()
                if not potential_source:
                    continue
                
                # Remove trailing boundary words
                boundary_words = ["in", "for", "during", "this", "last", "on", "at", "the"]
                words = potential_source.split()
                while words and words[-1] in boundary_words:
                    words.pop()
                if words:
                    # Found a plausible source token after keyword
                    return "source_total"
    
    # Priority 5: Check for category total (known category or "category" with a category value)
    # Check if a known category is mentioned
    if extract_category(question, KNOWN_CATEGORIES) is not None:
        return "category_total"
    # Also check if "category" keyword appears (but not if it's a breakdown)
    if "category" in question_lower:
        return "category_total"
    
    # Priority 6: Check for merchant total
    # Merchant_total should trigger if:
    # - question contains "at" OR "on" OR contains a quoted phrase
    # - AND the extracted phrase is not a known category
    # - AND the question does NOT contain source keywords ("using", "via", "with", "from")
    
    # First check: does question contain source keywords? If yes, skip merchant_total
    source_keywords_check = ["using", "via", "with", "from"]
    has_source_keyword_in_question = any(keyword in question_lower for keyword in source_keywords_check)
    
    if not has_source_keyword_in_question:
        # Check for merchant signals: "at", "on", or quoted phrase
        quoted_merchant_pattern = r'["\']([^"\']+)["\']'
        at_on_merchant_pattern = r'\b(?:at|on)\s+(\w+(?:\s+\w+)*)'
        
        has_quoted_merchant = re.search(quoted_merchant_pattern, question)
        has_at_on_merchant = re.search(at_on_merchant_pattern, question_lower)
        
        if has_quoted_merchant or has_at_on_merchant:
            # Try to extract merchant and verify it's not a known category
            extracted_merchant = extract_merchant(question, KNOWN_CATEGORIES)
            if extracted_merchant:
                return "merchant_total"
    
    # Priority 7: Check for monthly summary (FINAL FALLBACK)
    # Only returns monthly_summary if:
    # - All other intent checks (top/breakdown/source/category/merchant) have failed
    # - Month exists in question
    # - Question contains spend keywords
    month = extract_month(question)
    if month:
        monthly_keywords = ["spent", "spend", "expense", "expenses", "total", "net", "overall"]
        has_monthly_keyword = any(keyword in question_lower for keyword in monthly_keywords)
        if has_monthly_keyword:
            return "monthly_summary"
    
    # Priority 8: unknown
    return "unknown"


# Month name mapping (case-insensitive)
MONTH_NAMES = {
    "jan": "01", "january": "01",
    "feb": "02", "february": "02",
    "mar": "03", "march": "03",
    "apr": "04", "april": "04",
    "may": "05",
    "jun": "06", "june": "06",
    "jul": "07", "july": "07",
    "aug": "08", "august": "08",
    "sep": "09", "september": "09",
    "oct": "10", "october": "10",
    "nov": "11", "november": "11",
    "dec": "12", "december": "12"
}


def extract_month(question: str) -> Optional[str]:
    """
    Extract month in "YYYY-MM" format from question.
    
    Supports:
    - "YYYY-MM" format (e.g., "2025-06")
    - Month names (e.g., "June 2025", "Jun 2025", "June, 2025")
    
    Args:
        question: User question string
        
    Returns:
        Month string in "YYYY-MM" format if found, None otherwise
    """
    if not question:
        return None
    
    # First, try YYYY-MM pattern
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
    
    # Then, try month name patterns: "Month YYYY" or "Month, YYYY"
    # Pattern: (Jan|January|Feb|...|Dec|December)[,]?\s+(\d{4})
    month_names_pattern = r'\b(' + '|'.join(MONTH_NAMES.keys()) + r')\b[,]?\s+(\d{4})\b'
    match = re.search(month_names_pattern, question, re.IGNORECASE)
    if match:
        month_name = match.group(1).lower()
        year = match.group(2)
        
        # Get month number from mapping
        month_num = MONTH_NAMES.get(month_name)
        if month_num:
            return f"{year}-{month_num}"
    
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
    
    Prioritizes strong signals like "using X", "via X", "with X", "from X".
    Matches case-insensitively and returns the canonical value from known_sources
    (preserving original capitalization).
    
    Args:
        question: User question string
        known_sources: List of known source names to match against
        
    Returns:
        Matched source name (canonical from known_sources) if found, None otherwise
    """
    if not question or not known_sources:
        return None
    
    question_lower = question.lower()
    
    # Priority 1: Strong signals - look for source after keywords: "using", "via", "with", "from"
    source_keywords = ["using", "via", "with", "from"]
    for keyword in source_keywords:
        # Pattern: keyword + source (e.g., "using Cash", "via Chase", "with Credit Card")
        # Extract word(s) after the keyword, up to 3 words or until a boundary word
        keyword_pattern = rf'\b{re.escape(keyword)}\s+([A-Za-z]+(?:\s+[A-Za-z]+){{0,2}})'
        match = re.search(keyword_pattern, question_lower)
        if match:
            potential_source = match.group(1).strip()
            if not potential_source:
                continue
            
            # Remove any trailing boundary words that might have been captured
            boundary_words = ["in", "for", "during", "this", "last", "on", "at", "the"]
            words = potential_source.split()
            # Remove trailing boundary words
            while words and words[-1] in boundary_words:
                words.pop()
            if not words:
                continue
            potential_source = " ".join(words)
            
            # Check if potential_source matches any known source (case-insensitive, exact match)
            for source in known_sources:
                if not source:
                    continue
                if source.lower() == potential_source.lower():
                    # Return canonical value from known_sources (preserves capitalization)
                    return source
            
            # Also check if potential_source contains a known source (for multi-word sources)
            # This handles cases like "Credit Card" when potential_source is "Credit Card Payment"
            for source in known_sources:
                if not source:
                    continue
                source_lower = source.lower()
                # Check if the known source appears as a whole phrase in potential_source
                if source_lower in potential_source.lower():
                    # Verify it's a word boundary match (not just substring)
                    source_pattern = r'\b' + re.escape(source_lower) + r'\b'
                    if re.search(source_pattern, potential_source.lower()):
                        return source
    
    # Priority 2: Fall back to matching sources anywhere in the question (case-insensitive)
    for source in known_sources:
        if not source:
            continue
        # Match whole word or phrase (case-insensitive)
        source_lower = source.lower()
        # Use word boundary matching to avoid partial matches
        pattern = r'\b' + re.escape(source_lower) + r'\b'
        if re.search(pattern, question_lower):
            # Return canonical value from known_sources (preserves capitalization)
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
