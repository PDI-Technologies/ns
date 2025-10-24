# Duplicate Vendor Detection

## Overview

Duplicate vendors waste money through:
- Lost volume discounts
- Redundant vendor onboarding
- Scattered spend data
- Inefficient payment processing
- Weak negotiating position

Typical duplicate rates: 5-15% in large organizations.

## String Similarity Algorithms

### 1. SequenceMatcher (Python difflib)

**Best for**: General-purpose fuzzy matching

```python
from difflib import SequenceMatcher

def similarity_ratio(s1: str, s2: str) -> float:
    """Calculate similarity using SequenceMatcher (0.0 to 1.0)."""
    return SequenceMatcher(None, s1.lower().strip(), s2.lower().strip()).ratio()

# Example
similarity_ratio("Acme Corp", "Acme Corporation")  # 0.76
similarity_ratio("Acme Corp", "ACME CORP")         # 1.0 (case insensitive)
```

**Advantages**: Fast, built-in, handles typos well
**Disadvantages**: Sensitive to word order

### 2. Levenshtein Distance

**Best for**: Typo detection, character-level differences

```python
def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate minimum edit distance between strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def normalized_levenshtein(s1: str, s2: str) -> float:
    """Normalize to 0.0-1.0 similarity score."""
    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return 1 - (distance / max_len) if max_len > 0 else 1.0
```

### 3. Token-Based Matching

**Best for**: Different word orders ("ABC Company Inc" vs "Company ABC Inc")

```python
def token_similarity(s1: str, s2: str) -> float:
    """Compare as sets of tokens."""
    tokens1 = set(s1.lower().split())
    tokens2 = set(s2.lower().split())

    intersection = tokens1 & tokens2
    union = tokens1 | tokens2

    return len(intersection) / len(union) if union else 0.0

# Example
token_similarity("ABC Company Inc", "Company ABC Incorporated")  # 0.5
```

### 4. Jaccard Similarity

**Best for**: Set-based comparison

```python
def jaccard_similarity(s1: str, s2: str, n: int = 2) -> float:
    """Compare n-grams (character sequences)."""
    def ngrams(s: str, n: int) -> set:
        s = s.lower().strip()
        return {s[i:i+n] for i in range(len(s) - n + 1)}

    grams1 = ngrams(s1, n)
    grams2 = ngrams(s2, n)

    intersection = grams1 & grams2
    union = grams1 | grams2

    return len(intersection) / len(union) if union else 0.0
```

## Multi-Factor Matching

Combine multiple signals for higher accuracy.

### Composite Scoring
```python
from dataclasses import dataclass

@dataclass
class VendorMatch:
    name_similarity: float
    address_similarity: float
    tax_id_match: bool
    email_domain_match: bool
    phone_match: bool
    confidence_score: float

def multi_factor_match(v1: Vendor, v2: Vendor) -> VendorMatch:
    """Use multiple factors for matching."""
    # Name similarity
    name_sim = similarity_ratio(v1.name, v2.name)

    # Address similarity (if available)
    address_sim = 0.0
    if v1.address and v2.address:
        address_sim = similarity_ratio(v1.address, v2.address)

    # Tax ID exact match
    tax_match = bool(v1.tax_id and v2.tax_id and v1.tax_id == v2.tax_id)

    # Email domain match
    email_match = False
    if v1.email and v2.email:
        domain1 = v1.email.split('@')[-1]
        domain2 = v2.email.split('@')[-1]
        email_match = domain1 == domain2

    # Phone match (normalize first)
    phone_match = False
    if v1.phone and v2.phone:
        phone1 = ''.join(c for c in v1.phone if c.isdigit())
        phone2 = ''.join(c for c in v2.phone if c.isdigit())
        phone_match = phone1 == phone2

    # Calculate composite confidence
    confidence = (
        name_sim * 0.5 +           # 50% weight on name
        address_sim * 0.2 +        # 20% weight on address
        (1.0 if tax_match else 0.0) * 0.2 +   # 20% for tax ID
        (1.0 if email_match else 0.0) * 0.05 + # 5% for email domain
        (1.0 if phone_match else 0.0) * 0.05   # 5% for phone
    )

    return VendorMatch(
        name_similarity=name_sim,
        address_similarity=address_sim,
        tax_id_match=tax_match,
        email_domain_match=email_match,
        phone_match=phone_match,
        confidence_score=confidence
    )
```

## Threshold Selection

### Conservative (High Precision)
- **Threshold**: 0.90+
- **Use when**: Manual review capacity is low
- **Result**: Few false positives, may miss some duplicates

### Moderate (Balanced)
- **Threshold**: 0.85
- **Use when**: Standard duplicate detection
- **Result**: Good balance of precision and recall

### Aggressive (High Recall)
- **Threshold**: 0.75
- **Use when**: Initial data cleansing, plenty of review capacity
- **Result**: Catch more duplicates, more false positives

### Tuning Approach
1. Start with 0.85 threshold
2. Review 50 matches manually
3. Calculate precision (% true duplicates)
4. Adjust threshold based on acceptable false positive rate

## Performance Optimization

### For Large Datasets

**Problem**: O(n²) comparison of all pairs

**Solutions**:

1. **Blocking**: Pre-filter candidates
```python
def blocking_key(vendor_name: str) -> str:
    """Create blocking key (first 3 chars)."""
    normalized = ''.join(c for c in vendor_name if c.isalnum())
    return normalized[:3].lower()

def find_duplicates_with_blocking(vendors: list[Vendor], threshold: float):
    """Use blocking to reduce comparisons."""
    # Group by blocking key
    blocks = {}
    for vendor in vendors:
        key = blocking_key(vendor.name)
        blocks.setdefault(key, []).append(vendor)

    # Compare only within blocks
    duplicates = []
    for block_vendors in blocks.values():
        for i, v1 in enumerate(block_vendors):
            for v2 in block_vendors[i+1:]:
                sim = similarity_ratio(v1.name, v2.name)
                if sim >= threshold:
                    duplicates.append((v1, v2, sim))

    return duplicates
```

2. **Parallel Processing**: Use multiprocessing for large comparisons
3. **Database Indexing**: Index on normalized names for SQL-based matching

## Common Patterns

### Vendor Name Variations

**Legal suffixes**: Remove before comparison
- Inc, LLC, Ltd, Corporation, Corp, Co, Company
- GmbH, SA, AB, SpA, SRL
- The, A, An (at start)

```python
import re

LEGAL_SUFFIXES = [
    r'\bInc\.?$', r'\bLLC\.?$', r'\bLtd\.?$', r'\bCorp\.?$',
    r'\bCorporation$', r'\bCompany$', r'\bCo\.?$',
]

def normalize_vendor_name(name: str) -> str:
    """Remove legal suffixes and normalize."""
    normalized = name.strip()

    for pattern in LEGAL_SUFFIXES:
        normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)

    # Remove extra whitespace
    normalized = ' '.join(normalized.split())

    return normalized.lower()
```

### Address Normalization

```python
def normalize_address(address: str) -> str:
    """Standardize address for comparison."""
    # Normalize common abbreviations
    replacements = {
        r'\bStreet\b': 'St',
        r'\bAvenue\b': 'Ave',
        r'\bBoulevard\b': 'Blvd',
        r'\bRoad\b': 'Rd',
        r'\bDrive\b': 'Dr',
        r'\bSuite\b': 'Ste',
        r'\bApartment\b': 'Apt',
    }

    normalized = address.lower()
    for pattern, replacement in replacements.items():
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

    # Remove punctuation
    normalized = re.sub(r'[^\w\s]', '', normalized)

    return ' '.join(normalized.split())
```

## Output Formats

### Duplicate Report Structure

```python
@dataclass
class DuplicateReport:
    """Duplicate vendor analysis results."""
    total_vendors: int
    duplicate_pairs: int
    estimated_duplicate_count: int
    potential_savings: float
    confidence_distribution: dict[str, int]  # High/Medium/Low counts
    recommendations: list[str]

def generate_duplicate_report(
    duplicates: list[DuplicatePair],
    threshold: float
) -> DuplicateReport:
    """Generate executive summary of duplicates."""
    # Categorize by confidence
    high_confidence = [d for d in duplicates if d.similarity >= 0.95]
    medium_confidence = [d for d in duplicates if 0.85 <= d.similarity < 0.95]
    low_confidence = [d for d in duplicates if d.similarity < 0.85]

    # Estimate unique vendors (each duplicate = 2 vendors)
    estimated_duplicates = len(duplicates)  # Conservative

    # Generate recommendations
    recommendations = []
    if len(high_confidence) > 0:
        recommendations.append(
            f"High priority: Review {len(high_confidence)} high-confidence duplicates"
        )
    if len(medium_confidence) > 10:
        recommendations.append(
            f"Medium priority: {len(medium_confidence)} potential duplicates need review"
        )

    return DuplicateReport(
        total_vendors=count_unique_vendors(duplicates),
        duplicate_pairs=len(duplicates),
        estimated_duplicate_count=estimated_duplicates,
        potential_savings=estimate_savings(duplicates),
        confidence_distribution={
            'high': len(high_confidence),
            'medium': len(medium_confidence),
            'low': len(low_confidence)
        },
        recommendations=recommendations
    )
```

## Best Practices

1. **Always normalize before comparing**: lowercase, trim whitespace, remove punctuation
2. **Use multi-factor matching**: Don't rely on name alone
3. **Set appropriate thresholds**: Start conservative (0.85+)
4. **Validate with manual review**: Sample matches to tune threshold
5. **Document decisions**: Log why duplicates were merged/not merged
6. **Consider operational impact**: Some "duplicates" are intentional (different divisions)
7. **Track over time**: Monitor duplicate rate as KPI

## Anti-Patterns

❌ **Exact string matching only**: Misses typos and variations
❌ **Too aggressive threshold** (<0.75): Too many false positives
❌ **Ignoring context**: Same name, different cities = not duplicates
❌ **Automatic merging**: Always require human review before merge
❌ **No normalization**: "ABC Inc" vs "abc inc" treated as different

---

*Reference this document when implementing duplicate vendor detection in procurement or vendor management systems.*
