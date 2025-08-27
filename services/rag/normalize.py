"""
Query normalization for legal RAG system.

Standardizes user query phrasing to improve retrieval consistency.
Focused on La Plata County legal and municipal code queries.
"""

import re
from typing import List, Tuple


def normalize_legal_query(query: str) -> str:
    """
    Normalize legal query for better retrieval consistency.
    
    Args:
        query: Raw user query string
        
    Returns:
        Normalized query string optimized for legal document retrieval
    """
    if not query or not isinstance(query, str):
        return query
    
    # Convert to lowercase for pattern matching
    normalized = query.lower().strip()
    
    # Legal-specific normalization patterns
    # Each pattern maps verbose questions to concise search terms
    
    patterns = [
        # Requirements questions
        (r"what are the requirements for (.*?)(?:\s+in\s+la\s+plata\s+county)?(?:\?)?$", r"\1 requirements"),
        (r"what are the (.+?) requirements(?:\s+in\s+la\s+plata\s+county)?(?:\?)?$", r"\1 requirements"),
        (r"tell me about the requirements for (.*?)(?:\s+in\s+la\s+plata\s+county)?(?:\?)?$", r"\1 requirements"),
        
        # Process questions  
        (r"how do i (.+?)(?:\s+in\s+la\s+plata\s+county)?(?:\?)?$", r"\1 process"),
        (r"what is the process (?:to|for) (.+?)(?:\s+in\s+la\s+plata\s+county)?(?:\?)?$", r"\1 process"),
        (r"how to (.+?)(?:\s+in\s+la\s+plata\s+county)?(?:\?)?$", r"\1 process"),
        
        # Permit questions
        (r"do i need a permit (?:to|for) (.+?)(?:\s+in\s+la\s+plata\s+county)?(?:\?)?$", r"\1 permit requirements"),
        (r"what permits? are (?:required|needed) (?:to|for) (.+?)(?:\s+in\s+la\s+plata\s+county)?(?:\?)?$", r"\1 permit requirements"),
        
        # Definition questions
        (r"what is (?:a |an |the )?(.+?)(?:\s+in\s+la\s+plata\s+county)?(?:\?)?$", r"\1 definition"),
        (r"define (.+?)(?:\s+in\s+la\s+plata\s+county)?(?:\?)?$", r"\1 definition"),
        (r"tell me about (.+?)(?:\s+in\s+la\s+plata\s+county)?(?:\?)?$", r"\1"),
        
        # Procedure questions
        (r"what are the steps (?:to|for) (.+?)(?:\s+in\s+la\s+plata\s+county)?(?:\?)?$", r"\1 procedures"),
        (r"what is the procedure (?:to|for) (.+?)(?:\s+in\s+la\s+plata\s+county)?(?:\?)?$", r"\1 procedures"),
        
        # Rules/regulations questions
        (r"what are the rules (?:for|about) (.+?)(?:\s+in\s+la\s+plata\s+county)?(?:\?)?$", r"\1 regulations"),
        (r"what regulations apply to (.+?)(?:\s+in\s+la\s+plata\s+county)?(?:\?)?$", r"\1 regulations"),
        
        # Can I / May I questions
        (r"can i (.+?)(?:\s+in\s+la\s+plata\s+county)?(?:\?)?$", r"\1 regulations"),
        (r"may i (.+?)(?:\s+in\s+la\s+plata\s+county)?(?:\?)?$", r"\1 regulations"),
        (r"am i allowed to (.+?)(?:\s+in\s+la\s+plata\s+county)?(?:\?)?$", r"\1 regulations"),
        
        # Where/How to apply questions
        (r"where do i apply for (.+?)(?:\s+in\s+la\s+plata\s+county)?(?:\?)?$", r"\1 application process"),
        (r"how do i apply for (.+?)(?:\s+in\s+la\s+plata\s+county)?(?:\?)?$", r"\1 application process"),
    ]
    
    # Apply normalization patterns
    for pattern, replacement in patterns:
        match = re.search(pattern, normalized)
        if match:
            normalized = re.sub(pattern, replacement, normalized)
            break  # Apply only the first matching pattern
    
    # Legal term standardization
    term_standardization = [
        # Subdivision terms
        (r"\bsubdivide\b", "subdivision"),
        (r"\bsubdividing\b", "subdivision"),  
        (r"\bminor subdivision\b", "minor subdivision"),  # Keep as-is
        (r"\bmajor subdivision\b", "major subdivision"),  # Keep as-is
        
        # Permit terms
        (r"\bpermits?\b", "permit"),
        (r"\blicense[s]?\b", "permit"), 
        (r"\bapproval[s]?\b", "permit"),
        
        # Property terms
        (r"\bproperties\b", "property"),
        (r"\breal estate\b", "property"),
        (r"\bland\b", "property"),
        (r"\blot[s]?\b", "lot"),
        
        # Building terms
        (r"\bconstruction\b", "building"),
        (r"\bconstruct\b", "building"),
        (r"\bbuild\b", "building"),
        
        # Development terms
        (r"\bdevelop\b", "development"),
        (r"\bdeveloping\b", "development"),
        
        # Use terms
        (r"\bcommercial use\b", "commercial"),
        (r"\bresidential use\b", "residential"),
        (r"\bindustrial use\b", "industrial"),
    ]
    
    for pattern, replacement in term_standardization:
        normalized = re.sub(pattern, replacement, normalized)
    
    # Clean up extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    # Remove redundant location references (already implied)
    normalized = re.sub(r'\s+(?:in\s+)?la\s+plata\s+county\s*', '', normalized)
    
    return normalized


def get_query_variations(query: str) -> List[str]:
    """
    Generate query variations to improve retrieval robustness.
    
    Args:
        query: Normalized query string
        
    Returns:
        List of query variations to try in order of preference
    """
    variations = [query]  # Start with the normalized query
    
    # Add specific variations for known problematic patterns
    if "minor subdivision" in query:
        variations.extend([
            "minor subdivision requirements",
            "minor subdivision procedures", 
            "section 67-4",
            "subdivision three lots or fewer"
        ])
    
    if "major subdivision" in query:
        variations.extend([
            "major subdivision requirements",
            "major subdivision procedures",
            "section 67-3", 
            "subdivision four lots or more"
        ])
    
    if "building permit" in query:
        variations.extend([
            "building permit requirements",
            "building permit process",
            "construction permit"
        ])
        
    if "land use" in query:
        variations.extend([
            "land use permit",
            "land use procedures",
            "zoning"
        ])
    
    # Remove duplicates while preserving order
    unique_variations = []
    seen = set()
    for var in variations:
        if var not in seen:
            unique_variations.append(var)
            seen.add(var)
    
    return unique_variations


def debug_normalization(original_query: str) -> dict:
    """
    Debug function to see normalization process.
    
    Args:
        original_query: Original user query
        
    Returns:
        Dictionary with normalization steps and results
    """
    normalized = normalize_legal_query(original_query)
    variations = get_query_variations(normalized)
    
    return {
        "original": original_query,
        "normalized": normalized,
        "changed": original_query.lower().strip() != normalized,
        "variations": variations,
        "variation_count": len(variations)
    }


# Common legal query test cases for validation
TEST_QUERIES = [
    "What are the requirements for a minor subdivision in La Plata County?",
    "How do I apply for a building permit?", 
    "What is the process to subdivide my property?",
    "Do I need a permit to build a deck?",
    "What are the zoning requirements for commercial development?",
    "Can I subdivide my land into 2 lots?",
    "Tell me about major subdivision procedures",
    "What permits are required for construction?",
    "How to get approval for land development?",
    "What is a minor subdivision?"
]


def test_normalization() -> None:
    """Test function to validate normalization patterns."""
    print("Query Normalization Test Results:")
    print("=" * 50)
    
    for query in TEST_QUERIES:
        result = debug_normalization(query)
        print(f"Original: {result['original']}")
        print(f"Normalized: {result['normalized']}")
        if result['changed']:
            print(f"✅ Changed")
        else:
            print(f"➡️  No change needed")
        if len(result['variations']) > 1:
            print(f"Variations: {result['variations'][1:]}")
        print("-" * 30)


if __name__ == "__main__":
    test_normalization()