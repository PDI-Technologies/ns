# Data Quality

Vendor master data cleansing, address standardization, normalization rules, and validation patterns.

## Overview

Data quality is foundational for accurate vendor spend analysis. Poor data quality leads to:

**Problems:**
- Duplicate vendors undetected (different names for same vendor)
- Inaccurate spend aggregation
- Failed consolidation opportunities
- Unreliable reporting
- Payment processing errors

**Solution:**
- Standardize vendor names (remove legal suffixes, normalize case)
- Normalize addresses (standardize abbreviations)
- Validate tax IDs, phone numbers, emails
- Fail-fast on missing critical fields

**Typical Data Quality Issues:**
- 30-50% of vendors have inconsistent names
- 20-40% have incomplete address data
- 10-20% have invalid or missing contact information
- 5-15% are duplicates

## Vendor Name Normalization

### Remove Legal Suffixes

Standardize company names for comparison by removing legal entity indicators.

```python
import re

LEGAL_SUFFIXES = [
    r'\bInc\.?$',
    r'\bIncorporated$',
    r'\bLLC\.?$',
    r'\bL\.L\.C\.?$',
    r'\bLtd\.?$',
    r'\bLimited$',
    r'\bCorp\.?$',
    r'\bCorporation$',
    r'\bCo\.?$',
    r'\bCompany$',
    r'\bL\.P\.?$',
    r'\bLLP\.?$',
    r'\bPLC\.?$',
    r'\bGmbH$',
    r'\bS\.A\.?$',
    r'\bA\.G\.?$',
]

LEADING_ARTICLES = [r'^The\s+', r'^A\s+', r'^An\s+']

def normalize_vendor_name(name: str) -> str:
    """
    Normalize vendor name for comparison.

    Args:
        name: Raw vendor name

    Returns:
        Normalized name (lowercase, no legal suffixes, trimmed)
    """
    if not name:
        return ""

    normalized = name.strip()

    # Remove leading articles
    for pattern in LEADING_ARTICLES:
        normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)

    # Remove legal suffixes
    for pattern in LEGAL_SUFFIXES:
        normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)

    # Remove extra whitespace
    normalized = ' '.join(normalized.split())

    # Lowercase for comparison
    normalized = normalized.lower()

    # Remove special characters (keep alphanumeric and spaces)
    normalized = re.sub(r'[^a-z0-9\s]', '', normalized)

    return normalized.strip()

# Examples:
# "Acme Corporation" → "acme"
# "The ABC Company, Inc." → "abc company"
# "XYZ Co., LLC" → "xyz"
```

**Normalization Rules:**
- Convert to lowercase
- Remove legal entity suffixes (Inc, LLC, Corp, Ltd, etc.)
- Remove leading articles (The, A, An)
- Remove punctuation and special characters
- Collapse multiple spaces to single space
- Trim leading/trailing whitespace

## Address Normalization

### Standardize Address Format

Normalize addresses for comparison and deduplication.

```python
ADDRESS_ABBREVIATIONS = {
    r'\bStreet\b': 'St',
    r'\bAvenue\b': 'Ave',
    r'\bBoulevard\b': 'Blvd',
    r'\bRoad\b': 'Rd',
    r'\bDrive\b': 'Dr',
    r'\bLane\b': 'Ln',
    r'\bCourt\b': 'Ct',
    r'\bPlace\b': 'Pl',
    r'\bSuite\b': 'Ste',
    r'\bApartment\b': 'Apt',
    r'\bBuilding\b': 'Bldg',
    r'\bFloor\b': 'Fl',
    r'\bNorth\b': 'N',
    r'\bSouth\b': 'S',
    r'\bEast\b': 'E',
    r'\bWest\b': 'W',
}

def normalize_address(address: str) -> str:
    """
    Standardize address for comparison.

    Args:
        address: Raw address string

    Returns:
        Normalized address
    """
    if not address:
        return ""

    normalized = address.lower()

    # Apply abbreviations
    for pattern, replacement in ADDRESS_ABBREVIATIONS.items():
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

    # Remove punctuation
    normalized = re.sub(r'[^\w\s]', '', normalized)

    # Collapse whitespace
    normalized = ' '.join(normalized.split())

    return normalized

# Examples:
# "123 Main Street, Suite 200" → "123 main st ste 200"
# "1000 North First Avenue" → "1000 n first ave"
```

## Phone Number Normalization

### Extract Digits Only

Normalize phone numbers to digits-only format for comparison.

```python
def normalize_phone(phone: str | None) -> str:
    """
    Normalize phone number to digits only.

    Args:
        phone: Raw phone number

    Returns:
        Digits-only phone number
    """
    if not phone:
        return ""

    # Extract digits only
    digits = ''.join(c for c in phone if c.isdigit())

    # Remove country code if present (assume US: starts with 1)
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]

    return digits

# Examples:
# "(555) 123-4567" → "5551234567"
# "+1-555-123-4567" → "5551234567"
# "555.123.4567" → "5551234567"
```

## Email Normalization and Validation

### Standardize Email Format

```python
def normalize_email(email: str | None) -> str:
    """
    Normalize email address.

    Args:
        email: Raw email address

    Returns:
        Normalized email (lowercase, trimmed)
    """
    if not email:
        return ""

    # Lowercase and trim
    normalized = email.lower().strip()

    # Basic validation
    if '@' not in normalized or '.' not in normalized:
        return ""  # Invalid email

    return normalized

def extract_email_domain(email: str) -> str:
    """Extract domain from email address."""
    if not email or '@' not in email:
        return ""

    return email.split('@')[-1].lower()

# Example:
# "John.Doe@AcmeCorp.COM" → "john.doe@acmecorp.com"
# Domain: "acmecorp.com"
```

## Tax ID Validation

### Validate and Normalize Tax IDs

```python
def normalize_tax_id(tax_id: str | None, country: str = 'US') -> str:
    """
    Normalize tax ID (EIN for US).

    Args:
        tax_id: Raw tax ID
        country: Country code (default: US)

    Returns:
        Normalized tax ID (digits only)
    """
    if not tax_id:
        return ""

    # Extract digits only
    digits = ''.join(c for c in tax_id if c.isdigit())

    # Validate length
    if country == 'US' and len(digits) != 9:
        return ""  # Invalid US EIN

    return digits

def validate_ein(ein: str) -> bool:
    """
    Validate US Employer Identification Number (EIN).

    Format: XX-XXXXXXX (9 digits total)
    """
    digits = ''.join(c for c in ein if c.isdigit())

    # Must be 9 digits
    if len(digits) != 9:
        return False

    # First two digits (prefix) must be valid
    prefix = int(digits[:2])
    valid_prefixes = list(range(1, 100))
    valid_prefixes.remove(7)  # 07 not used
    valid_prefixes.remove(8)  # 08 not used
    valid_prefixes.remove(9)  # 09 not used
    valid_prefixes.remove(17)  # 17 not used
    valid_prefixes.remove(18)  # 18 not used
    valid_prefixes.remove(19)  # 19 not used
    valid_prefixes.remove(28)  # 28 not used
    valid_prefixes.remove(29)  # 29 not used
    valid_prefixes.remove(49)  # 49 not used
    valid_prefixes.remove(69)  # 69 not used
    valid_prefixes.remove(70)  # 70 not used
    valid_prefixes.remove(78)  # 78 not used
    valid_prefixes.remove(79)  # 79 not used
    valid_prefixes.remove(89)  # 89 not used

    return prefix in valid_prefixes
```

## Data Validation Rules

### Fail-Fast Validation

Validate vendor data before processing, fail immediately on critical errors.

```python
from dataclasses import dataclass

@dataclass
class ValidationError:
    """Data validation error."""
    field: str
    value: any
    error_message: str

def validate_vendor_record(vendor: Vendor) -> list[ValidationError]:
    """
    Validate vendor record for data quality.

    Args:
        vendor: Vendor record to validate

    Returns:
        List of validation errors (empty = valid)
    """
    errors = []

    # Critical fields - fail if missing
    if not vendor.id:
        errors.append(ValidationError(
            field='id',
            value=None,
            error_message='Vendor ID is required'
        ))

    if not vendor.entity_id and not vendor.company_name:
        errors.append(ValidationError(
            field='name',
            value=None,
            error_message='Vendor must have entity_id or company_name'
        ))

    # Data format validation
    if vendor.email and '@' not in vendor.email:
        errors.append(ValidationError(
            field='email',
            value=vendor.email,
            error_message='Invalid email format'
        ))

    if vendor.phone:
        digits = ''.join(c for c in vendor.phone if c.isdigit())
        if len(digits) < 10:
            errors.append(ValidationError(
                field='phone',
                value=vendor.phone,
                error_message='Phone number must have at least 10 digits'
            ))

    # Business logic validation
    if vendor.balance is not None and vendor.balance < 0:
        errors.append(ValidationError(
            field='balance',
            value=vendor.balance,
            error_message='Vendor balance cannot be negative'
        ))

    return errors

def validate_transaction_record(transaction: Transaction) -> list[ValidationError]:
    """Validate transaction record."""
    errors = []

    # Required fields
    if not transaction.vendor_id:
        errors.append(ValidationError('vendor_id', None, 'Vendor ID required'))

    if not transaction.amount:
        errors.append(ValidationError('amount', None, 'Amount required'))

    if not transaction.tran_date:
        errors.append(ValidationError('tran_date', None, 'Transaction date required'))

    # Data validation
    if transaction.amount is not None and transaction.amount <= 0:
        errors.append(ValidationError('amount', transaction.amount, 'Amount must be positive'))

    # Date validation (no future dates)
    if transaction.tran_date and transaction.tran_date > datetime.now():
        errors.append(ValidationError('tran_date', transaction.tran_date, 'Transaction date cannot be future'))

    return errors
```

## Data Cleansing Pipeline

### Multi-Stage Cleansing Process

```python
def cleanse_vendor_data(vendors: list[Vendor]) -> list[Vendor]:
    """
    Cleanse vendor master data.

    Stages:
    1. Validate required fields
    2. Normalize names and addresses
    3. Standardize phone/email
    4. Remove invalid records
    5. Flag quality issues

    Args:
        vendors: Raw vendor list

    Returns:
        Cleansed vendor list
    """
    cleansed = []
    rejected = []

    for vendor in vendors:
        # Stage 1: Validate
        errors = validate_vendor_record(vendor)

        if errors:
            rejected.append({'vendor': vendor, 'errors': errors})
            continue

        # Stage 2: Normalize name
        if vendor.company_name:
            vendor.normalized_name = normalize_vendor_name(vendor.company_name)
        else:
            vendor.normalized_name = normalize_vendor_name(vendor.entity_id)

        # Stage 3: Normalize contact info
        if vendor.email:
            vendor.normalized_email = normalize_email(vendor.email)

        if vendor.phone:
            vendor.normalized_phone = normalize_phone(vendor.phone)

        # Stage 4: Flag quality issues
        vendor.quality_flags = assess_data_quality(vendor)

        cleansed.append(vendor)

    # Log rejected records
    log_rejected_vendors(rejected)

    return cleansed

def assess_data_quality(vendor: Vendor) -> list[str]:
    """Flag data quality issues."""
    flags = []

    if not vendor.email:
        flags.append('MISSING_EMAIL')

    if not vendor.phone:
        flags.append('MISSING_PHONE')

    if not vendor.company_name:
        flags.append('MISSING_COMPANY_NAME')

    if len(vendor.entity_id) < 3:
        flags.append('SHORT_ENTITY_ID')

    return flags
```

## Deduplication Before Analysis

### Pre-Analysis Cleansing

Identify and flag obvious duplicates before analysis begins.

```python
def flag_obvious_duplicates(vendors: list[Vendor], threshold: float = 0.95) -> list[Vendor]:
    """
    Flag high-confidence duplicates before analysis.

    Use high threshold (0.95) to catch only obvious duplicates.
    More thorough duplicate detection done in analysis phase.

    Args:
        vendors: Vendor list
        threshold: Similarity threshold (default 0.95 = very high confidence)

    Returns:
        Vendor list with duplicate flags
    """
    from difflib import SequenceMatcher

    for i, vendor1 in enumerate(vendors):
        if vendor1.duplicate_flag:
            continue  # Already flagged

        name1 = vendor1.normalized_name or vendor1.company_name

        for vendor2 in vendors[i+1:]:
            if vendor2.duplicate_flag:
                continue

            name2 = vendor2.normalized_name or vendor2.company_name

            # Quick similarity check
            similarity = SequenceMatcher(None, name1, name2).ratio()

            if similarity >= threshold:
                # Flag as likely duplicate
                vendor1.duplicate_flag = True
                vendor1.duplicate_of = vendor2.id
                vendor2.duplicate_flag = True
                vendor2.duplicate_of = vendor1.id
                break  # Move to next vendor

    return vendors
```

## Data Validation Schema

### Fail-Fast Validation Rules

Enforce data quality standards with fail-fast approach.

```python
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class VendorDataQuality(BaseModel):
    """
    Vendor data quality model with validation.

    Fails immediately if critical data is missing or invalid.
    """
    vendor_id: str = Field(..., min_length=1, description="Vendor ID (required)")
    vendor_name: str = Field(..., min_length=2, description="Vendor name (required)")
    email: str | None = Field(None, description="Email address")
    phone: str | None = Field(None, description="Phone number")
    tax_id: str | None = Field(None, description="Tax ID")
    currency: str | None = Field(None, description="Currency code")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        """Validate email format."""
        if v and '@' not in v:
            raise ValueError(f'Invalid email format: {v}')
        return v.lower() if v else None

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        """Validate phone number."""
        if v:
            digits = ''.join(c for c in v if c.isdigit())
            if len(digits) < 10:
                raise ValueError(f'Phone number must have at least 10 digits: {v}')
        return v

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str | None) -> str | None:
        """Validate currency code (ISO 4217)."""
        valid_currencies = {'USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY', 'CNY'}
        if v and v not in valid_currencies:
            raise ValueError(f'Invalid currency code: {v}')
        return v

class TransactionDataQuality(BaseModel):
    """Transaction data quality model with validation."""
    transaction_id: str = Field(..., min_length=1)
    vendor_id: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0, description="Amount must be positive")
    tran_date: datetime = Field(..., description="Transaction date required")
    currency: str = Field(..., description="Currency required")

    @field_validator('tran_date')
    @classmethod
    def validate_tran_date(cls, v: datetime) -> datetime:
        """Validate transaction date is not in future."""
        if v > datetime.now():
            raise ValueError(f'Transaction date cannot be in future: {v}')
        return v
```

## Data Quality Metrics

### Track Data Quality KPIs

```python
@dataclass
class DataQualityReport:
    """Data quality assessment."""
    total_vendors: int
    vendors_with_email: int
    vendors_with_phone: int
    vendors_with_address: int
    vendors_with_tax_id: int
    invalid_emails: int
    invalid_phones: int
    duplicate_rate: float
    completeness_score: float
    quality_grade: str

def assess_data_quality(vendors: list[Vendor]) -> DataQualityReport:
    """Generate data quality report."""
    total = len(vendors)
    with_email = sum(1 for v in vendors if v.email)
    with_phone = sum(1 for v in vendors if v.phone)
    with_address = sum(1 for v in vendors if v.address)
    with_tax_id = sum(1 for v in vendors if v.tax_id)

    invalid_emails = sum(1 for v in vendors if v.email and '@' not in v.email)
    invalid_phones = sum(1 for v in vendors if v.phone and len(''.join(c for c in v.phone if c.isdigit())) < 10)

    # Completeness score (0-100)
    completeness = (
        (with_email / total) * 0.3 +
        (with_phone / total) * 0.2 +
        (with_address / total) * 0.3 +
        (with_tax_id / total) * 0.2
    ) * 100 if total > 0 else 0

    # Quality grade
    if completeness >= 90:
        grade = 'A'
    elif completeness >= 80:
        grade = 'B'
    elif completeness >= 70:
        grade = 'C'
    else:
        grade = 'F'

    return DataQualityReport(
        total_vendors=total,
        vendors_with_email=with_email,
        vendors_with_phone=with_phone,
        vendors_with_address=with_address,
        vendors_with_tax_id=with_tax_id,
        invalid_emails=invalid_emails,
        invalid_phones=invalid_phones,
        duplicate_rate=0,  # Calculate separately
        completeness_score=completeness,
        quality_grade=grade
    )
```

## Best Practices

### Cleansing Strategy
1. **Validate first** - Fail-fast on critical missing fields
2. **Normalize second** - Standardize names, addresses, contact info
3. **Deduplicate third** - Use normalized data for matching
4. **Enrich last** - Add missing data from external sources

### Data Standards
- **Required fields:** Vendor ID, vendor name, amount (for transactions), date (for transactions)
- **Recommended fields:** Email, phone, address, tax ID, currency, payment terms
- **Optional fields:** Website, industry, category, risk rating

### Normalization Approach
- Apply normalization before storage (cleanse on import)
- Store both raw and normalized values
- Use normalized values for matching and comparison
- Display raw values to users

### Fail-Fast Rules
- Missing vendor ID → Reject record
- Missing amount on transaction → Reject record
- Missing date on transaction → Reject record
- Invalid currency code → Reject record
- Future transaction date → Reject record
- Negative transaction amount → Flag for review (could be credit memo)

### Quality Monitoring
- Track completeness score over time
- Monitor validation failure rate
- Set data quality KPIs (>80% completeness target)
- Generate monthly data quality reports
- Alert on quality degradation

## Data Quality Dashboard

### Key Metrics to Track

```python
def generate_quality_dashboard(vendors: list[Vendor], transactions: list[Transaction]):
    """Generate data quality dashboard metrics."""
    vendor_quality = assess_data_quality(vendors)
    transaction_quality = assess_transaction_quality(transactions)

    return {
        'vendor_metrics': {
            'total': vendor_quality.total_vendors,
            'completeness': vendor_quality.completeness_score,
            'grade': vendor_quality.quality_grade,
            'missing_email_pct': (1 - vendor_quality.vendors_with_email / vendor_quality.total_vendors) * 100,
            'missing_phone_pct': (1 - vendor_quality.vendors_with_phone / vendor_quality.total_vendors) * 100
        },
        'transaction_metrics': {
            'total': transaction_quality.total_transactions,
            'invalid_count': transaction_quality.invalid_transactions,
            'invalid_rate': transaction_quality.invalid_rate,
            'missing_vendor_links': transaction_quality.missing_vendor_links
        },
        'recommendations': generate_quality_recommendations(vendor_quality, transaction_quality)
    }

def generate_quality_recommendations(vendor_quality, transaction_quality):
    """Generate data quality improvement recommendations."""
    recommendations = []

    if vendor_quality.completeness_score < 70:
        recommendations.append('CRITICAL: Vendor data completeness below 70% - enforce data entry requirements')

    if transaction_quality.invalid_rate > 0.05:
        recommendations.append('HIGH: Transaction error rate >5% - review import processes')

    if vendor_quality.duplicate_rate > 0.15:
        recommendations.append('MEDIUM: Duplicate rate >15% - implement cleansing project')

    return recommendations
```

## Custom Field Quality Checks

NetSuite custom vendor fields (custentity_*) require specific quality checks beyond standard field validation.

### Field Completeness Analysis

Check what percentage of vendors have each custom field populated:

```python
from vendor_analysis.db.query_helpers import CustomFieldQuery

def check_custom_field_completeness(session):
    """Analyze custom field population rates

    Returns:
        Dict with field population statistics
    """
    fields = CustomFieldQuery.list_all_custom_fields(session)
    total_vendors = session.query(VendorRecord).count()

    completeness = {}

    for field_name, count in fields.items():
        percentage = (count / total_vendors) * 100

        completeness[field_name] = {
            "vendor_count": count,
            "total_vendors": total_vendors,
            "population_rate": percentage,
            "status": (
                "Excellent" if percentage >= 95 else
                "Good" if percentage >= 80 else
                "Fair" if percentage >= 50 else
                "Poor"
            )
        }

    return completeness

# Example output:
# {
#   "custentity_region": {
#     "vendor_count": 4950,
#     "total_vendors": 5000,
#     "population_rate": 99.0,
#     "status": "Excellent"
#   },
#   "custentity_optional_field": {
#     "vendor_count": 150,
#     "total_vendors": 5000,
#     "population_rate": 3.0,
#     "status": "Poor"
#   }
# }
```

**Use case:** Determine which custom fields are reliable for segmentation and analytics.

### Deprecated Field Detection

Identify fields that have stopped appearing in recent syncs:

```python
from datetime import datetime, timedelta

def find_deprecated_custom_fields(session, days_threshold=30):
    """Find custom fields that may be deprecated

    Args:
        days_threshold: Days since last seen to consider deprecated

    Returns:
        Dict of potentially deprecated fields
    """
    cutoff_date = datetime.now() - timedelta(days=days_threshold)

    vendors = session.query(VendorRecord).all()

    field_last_seen = {}

    for vendor in vendors:
        if not vendor.custom_fields:
            continue

        for field_name, field_data in vendor.custom_fields.items():
            if not isinstance(field_data, dict):
                continue

            last_seen_str = field_data.get('last_seen')
            if not last_seen_str:
                continue

            last_seen = datetime.fromisoformat(last_seen_str)

            if field_name not in field_last_seen or last_seen > field_last_seen[field_name]:
                field_last_seen[field_name] = last_seen

    # Find fields not seen recently
    deprecated = {}
    for field_name, last_seen in field_last_seen.items():
        if last_seen < cutoff_date:
            days_ago = (datetime.now() - last_seen).days
            deprecated[field_name] = {
                "last_seen": last_seen.isoformat(),
                "days_ago": days_ago,
                "status": "Likely deprecated"
            }

    return deprecated
```

**Use case:** Clean up analytics queries that reference old custom fields.

### Field Value Consistency

Check for inconsistent values in custom fields:

```python
def check_field_value_consistency(session, field_name):
    """Analyze value consistency for a custom field

    Returns:
        Value distribution and quality metrics
    """
    vendors = session.query(VendorRecord).all()

    values = []
    for vendor in vendors:
        if not vendor.custom_fields:
            continue

        field_data = vendor.custom_fields.get(field_name, {})
        value = field_data.get('value') if isinstance(field_data, dict) else field_data

        if value:
            values.append(value)

    if not values:
        return {"error": "Field not found in any vendor"}

    # Value distribution
    from collections import Counter
    distribution = Counter(values)

    # Quality metrics
    unique_count = len(distribution)
    total_count = len(values)

    return {
        "field_name": field_name,
        "total_values": total_count,
        "unique_values": unique_count,
        "top_values": distribution.most_common(10),
        "consistency_score": 1.0 if unique_count <= 10 else 0.5 if unique_count <= 50 else 0.2
    }

# Example usage:
# check_field_value_consistency(session, 'custentity_region')
# {
#   "field_name": "custentity_region",
#   "total_values": 5000,
#   "unique_values": 4,
#   "top_values": [("West", 2000), ("East", 1800), ("Central", 900), ("South", 300)],
#   "consistency_score": 1.0  # Only 4 values = highly consistent
# }
```

**Use case:** Identify fields with messy or inconsistent values that need standardization.

**Reference:** `/opt/ns/apps/vendor-analysis/src/vendor_analysis/db/query_helpers.py`

## Related Documentation

- **[Duplicate Detection](duplicate-detection.md)** - Uses normalized data for matching
- **[Spend Analysis](spend-analysis.md)** - Requires clean data for accuracy
- **[Cost Optimization](cost-optimization.md)** - Clean data enables consolidation

---

*Generic data quality patterns applicable to any vendor master data cleansing project*
