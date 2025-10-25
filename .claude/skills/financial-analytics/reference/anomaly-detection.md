# Anomaly Detection

Identify unusual patterns, outliers, and potential fraud in financial data using statistical methods and machine learning techniques.

## Contents

- [Overview](#overview)
- [Statistical Outlier Detection](#statistical-outlier-detection)
  - [Z-Score Method](#z-score-method)
  - [Interquartile Range (IQR) Method](#interquartile-range-iqr-method)
- [Benford's Law (Fraud Detection)](#benfords-law-fraud-detection)
- [Time Series Anomalies](#time-series-anomalies)
  - [Moving Average Deviation](#moving-average-deviation)
  - [Seasonal Decomposition Anomalies](#seasonal-decomposition-anomalies)
- [Transaction Pattern Anomalies](#transaction-pattern-anomalies)
  - [Unusual Transaction Amounts](#unusual-transaction-amounts)
  - [Velocity Checks](#velocity-checks)
- [Control Charts](#control-charts)
- [Threshold Alerts](#threshold-alerts)
- [Visualization](#visualization)
- [Best Practices](#best-practices)
- [Use Cases](#use-cases)

## Overview

Anomaly detection helps finance teams identify:
- Fraudulent transactions
- Data entry errors
- Unusual spending patterns
- Revenue anomalies
- Process violations
- Control failures

## Statistical Outlier Detection

### Z-Score Method

Identify values that deviate significantly from the mean.

```python
from decimal import Decimal
import pandas as pd
import numpy as np
from dataclasses import dataclass

@dataclass
class OutlierResult:
    """Outlier detection result."""

    value: Decimal
    z_score: float
    is_outlier: bool
    severity: str  # 'normal', 'moderate', 'severe'

def calculate_z_score(
    value: Decimal,
    mean: Decimal,
    std_dev: Decimal,
) -> float:
    """
    Calculate Z-score for a value.

    Formula: Z = (X - μ) / σ

    Args:
        value: Value to test
        mean: Population mean
        std_dev: Population standard deviation

    Returns:
        Z-score (number of standard deviations from mean)
    """
    if std_dev == Decimal('0'):
        return 0.0

    z_score = (value - mean) / std_dev
    return float(z_score)

def detect_outliers_zscore(
    data: pd.Series,
    threshold: float = 3.0,
) -> list[OutlierResult]:
    """
    Detect outliers using Z-score method.

    Args:
        data: Numeric data series
        threshold: Z-score threshold (default 3.0 = 99.7% confidence)

    Returns:
        List of outlier results

    Interpretation:
    - |Z| > 3: Severe outlier (99.7% confidence)
    - |Z| > 2: Moderate outlier (95% confidence)
    - |Z| <= 2: Normal variation
    """
    mean = Decimal(str(data.mean()))
    std_dev = Decimal(str(data.std()))

    results: list[OutlierResult] = []

    for value in data:
        decimal_value = Decimal(str(value))
        z_score = calculate_z_score(decimal_value, mean, std_dev)

        is_outlier = abs(z_score) > threshold

        if abs(z_score) > 3:
            severity = 'severe'
        elif abs(z_score) > 2:
            severity = 'moderate'
        else:
            severity = 'normal'

        results.append(
            OutlierResult(
                value=decimal_value,
                z_score=z_score,
                is_outlier=is_outlier,
                severity=severity,
            )
        )

    return results
```

### Interquartile Range (IQR) Method

More robust to extreme values than Z-score.

```python
def detect_outliers_iqr(
    data: pd.Series,
    multiplier: float = 1.5,
) -> dict:
    """
    Detect outliers using Interquartile Range method.

    Args:
        data: Numeric data series
        multiplier: IQR multiplier (1.5 = moderate, 3.0 = extreme)

    Returns:
        Dictionary with outlier statistics

    Method:
    - Q1 = 25th percentile
    - Q3 = 75th percentile
    - IQR = Q3 - Q1
    - Lower bound = Q1 - (multiplier × IQR)
    - Upper bound = Q3 + (multiplier × IQR)
    """
    q1 = data.quantile(0.25)
    q3 = data.quantile(0.75)
    iqr = q3 - q1

    lower_bound = q1 - (multiplier * iqr)
    upper_bound = q3 + (multiplier * iqr)

    outliers = data[(data < lower_bound) | (data > upper_bound)]

    return {
        'q1': q1,
        'q3': q3,
        'iqr': iqr,
        'lower_bound': lower_bound,
        'upper_bound': upper_bound,
        'outlier_count': len(outliers),
        'outlier_values': outliers.tolist(),
        'outlier_indices': outliers.index.tolist(),
    }
```

## Benford's Law (Fraud Detection)

Detect unnatural digit patterns that may indicate fraud.

```python
from collections import Counter

def calculate_benford_expected() -> dict[int, float]:
    """
    Calculate expected frequencies for first digits (Benford's Law).

    Returns:
        Dictionary mapping digit to expected frequency percentage
    """
    return {
        1: 30.1,
        2: 17.6,
        3: 12.5,
        4: 9.7,
        5: 7.9,
        6: 6.7,
        7: 5.8,
        8: 5.1,
        9: 4.6,
    }

def extract_first_digit(value: Decimal) -> int | None:
    """Extract first significant digit from a number."""
    # Convert to string and remove decimal point
    value_str = str(abs(value)).replace('.', '').lstrip('0')

    if not value_str:
        return None

    return int(value_str[0])

def benford_analysis(
    amounts: list[Decimal],
) -> dict:
    """
    Perform Benford's Law analysis on financial amounts.

    Args:
        amounts: List of financial transaction amounts

    Returns:
        Dictionary with actual vs expected frequencies and chi-square test

    Use Case: Detect fabricated or manipulated financial data
    """
    # Extract first digits
    first_digits = [extract_first_digit(amt) for amt in amounts]
    first_digits = [d for d in first_digits if d is not None]

    if not first_digits:
        return {'error': 'No valid digits to analyze'}

    # Count occurrences
    digit_counts = Counter(first_digits)
    total_count = len(first_digits)

    # Calculate actual frequencies
    actual_freq = {
        digit: (count / total_count * 100)
        for digit, count in digit_counts.items()
    }

    # Get expected frequencies
    expected_freq = calculate_benford_expected()

    # Calculate chi-square statistic
    chi_square = sum(
        ((actual_freq.get(digit, 0) - expected_freq[digit]) ** 2) / expected_freq[digit]
        for digit in range(1, 10)
    )

    # Chi-square critical value at 95% confidence with 8 degrees of freedom = 15.51
    suspicious = chi_square > 15.51

    return {
        'total_samples': total_count,
        'actual_frequencies': actual_freq,
        'expected_frequencies': expected_freq,
        'chi_square_statistic': chi_square,
        'is_suspicious': suspicious,
        'interpretation': (
            'SUSPICIOUS: Distribution significantly deviates from Benford\'s Law'
            if suspicious else
            'NORMAL: Distribution follows Benford\'s Law'
        ),
    }
```

## Time Series Anomalies

### Moving Average Deviation

```python
def detect_moving_average_anomalies(
    data: pd.Series,
    window: int = 7,
    threshold_std: float = 2.0,
) -> pd.DataFrame:
    """
    Detect anomalies using moving average and standard deviation.

    Args:
        data: Time series data
        window: Moving average window
        threshold_std: Standard deviation threshold

    Returns:
        DataFrame with anomaly flags
    """
    # Calculate moving statistics
    rolling_mean = data.rolling(window=window).mean()
    rolling_std = data.rolling(window=window).std()

    # Calculate bounds
    upper_bound = rolling_mean + (threshold_std * rolling_std)
    lower_bound = rolling_mean - (threshold_std * rolling_std)

    # Flag anomalies
    anomalies = (data > upper_bound) | (data < lower_bound)

    results = pd.DataFrame({
        'value': data,
        'rolling_mean': rolling_mean,
        'rolling_std': rolling_std,
        'upper_bound': upper_bound,
        'lower_bound': lower_bound,
        'is_anomaly': anomalies,
    })

    return results
```

### Seasonal Decomposition Anomalies

```python
from statsmodels.tsa.seasonal import seasonal_decompose

def detect_seasonal_anomalies(
    data: pd.Series,
    period: int = 12,
    threshold: float = 2.0,
) -> pd.DataFrame:
    """
    Detect anomalies in seasonal time series.

    Args:
        data: Time series data (must have DatetimeIndex)
        period: Seasonal period (12 for monthly, 4 for quarterly)
        threshold: Residual threshold in standard deviations

    Returns:
        DataFrame with seasonal decomposition and anomalies
    """
    # Decompose
    decomposition = seasonal_decompose(data, model='additive', period=period)

    # Calculate residual statistics
    residual_std = decomposition.resid.std()
    residual_threshold = threshold * residual_std

    # Flag anomalies
    anomalies = abs(decomposition.resid) > residual_threshold

    results = pd.DataFrame({
        'original': data,
        'trend': decomposition.trend,
        'seasonal': decomposition.seasonal,
        'residual': decomposition.resid,
        'is_anomaly': anomalies,
    })

    return results
```

## Transaction Pattern Anomalies

### Unusual Transaction Amounts

```python
@dataclass
class TransactionAnomaly:
    """Transaction anomaly details."""

    transaction_id: str
    amount: Decimal
    date: pd.Timestamp
    anomaly_type: str
    severity: str
    explanation: str

def detect_transaction_anomalies(
    transactions: pd.DataFrame,
    amount_column: str = 'amount',
) -> list[TransactionAnomaly]:
    """
    Detect anomalous transactions using multiple methods.

    Args:
        transactions: DataFrame with transaction data
        amount_column: Column name containing amounts

    Returns:
        List of detected anomalies
    """
    anomalies: list[TransactionAnomaly] = []

    # Method 1: Round number detection
    amounts = transactions[amount_column]
    round_numbers = amounts[amounts % 1000 == 0]

    for idx in round_numbers.index:
        if transactions.loc[idx, amount_column] > 10000:
            anomalies.append(
                TransactionAnomaly(
                    transaction_id=str(transactions.loc[idx, 'id']),
                    amount=Decimal(str(transactions.loc[idx, amount_column])),
                    date=transactions.loc[idx, 'date'],
                    anomaly_type='round_number',
                    severity='low',
                    explanation='Large round number transaction',
                )
            )

    # Method 2: Statistical outliers (Z-score)
    outliers_zscore = detect_outliers_zscore(amounts, threshold=3.0)

    for idx, result in enumerate(outliers_zscore):
        if result.is_outlier and result.severity == 'severe':
            anomalies.append(
                TransactionAnomaly(
                    transaction_id=str(transactions.iloc[idx]['id']),
                    amount=result.value,
                    date=transactions.iloc[idx]['date'],
                    anomaly_type='statistical_outlier',
                    severity='high',
                    explanation=f'Z-score: {result.z_score:.2f}',
                )
            )

    # Method 3: Duplicate amounts on same day
    duplicate_check = transactions.groupby(['date', amount_column]).size()
    duplicates = duplicate_check[duplicate_check > 1]

    for (date, amount), count in duplicates.items():
        matching_txns = transactions[
            (transactions['date'] == date) &
            (transactions[amount_column] == amount)
        ]

        for idx in matching_txns.index:
            anomalies.append(
                TransactionAnomaly(
                    transaction_id=str(transactions.loc[idx, 'id']),
                    amount=Decimal(str(amount)),
                    date=date,
                    anomaly_type='duplicate_amount',
                    severity='medium',
                    explanation=f'{count} transactions with same amount on same day',
                )
            )

    return anomalies
```

### Velocity Checks

```python
def detect_velocity_anomalies(
    transactions: pd.DataFrame,
    vendor_id_column: str = 'vendor_id',
    amount_column: str = 'amount',
    time_window_days: int = 1,
    max_transactions: int = 10,
    max_amount: Decimal = Decimal('50000'),
) -> pd.DataFrame:
    """
    Detect unusual transaction velocity (frequency and volume).

    Args:
        transactions: DataFrame with transactions
        vendor_id_column: Vendor ID column
        amount_column: Amount column
        time_window_days: Time window for velocity check
        max_transactions: Max transactions per vendor per window
        max_amount: Max total amount per vendor per window

    Returns:
        DataFrame with velocity violations
    """
    # Sort by vendor and date
    sorted_txns = transactions.sort_values([vendor_id_column, 'date'])

    violations = []

    for vendor_id in sorted_txns[vendor_id_column].unique():
        vendor_txns = sorted_txns[sorted_txns[vendor_id_column] == vendor_id]

        # Rolling window velocity check
        for i in range(len(vendor_txns)):
            current_date = vendor_txns.iloc[i]['date']
            window_start = current_date - pd.Timedelta(days=time_window_days)

            window_txns = vendor_txns[
                (vendor_txns['date'] >= window_start) &
                (vendor_txns['date'] <= current_date)
            ]

            txn_count = len(window_txns)
            total_amount = Decimal(str(window_txns[amount_column].sum()))

            if txn_count > max_transactions or total_amount > max_amount:
                violations.append({
                    'vendor_id': vendor_id,
                    'date': current_date,
                    'transaction_count': txn_count,
                    'total_amount': total_amount,
                    'violation_type': (
                        'count' if txn_count > max_transactions else 'amount'
                    ),
                })

    return pd.DataFrame(violations)
```

## Control Charts

Statistical process control for monitoring financial metrics.

```python
def create_control_chart(
    data: pd.Series,
    control_limit_sigma: float = 3.0,
) -> dict:
    """
    Create control chart for financial metric monitoring.

    Args:
        data: Time series of metric values
        control_limit_sigma: Number of standard deviations for control limits

    Returns:
        Dictionary with control chart parameters

    Use Case: Monitor metrics like daily revenue, expense ratios, margins
    """
    mean = data.mean()
    std_dev = data.std()

    ucl = mean + (control_limit_sigma * std_dev)  # Upper control limit
    lcl = mean - (control_limit_sigma * std_dev)  # Lower control limit

    # Detect out-of-control points
    out_of_control = data[(data > ucl) | (data < lcl)]

    # Detect trends (7+ consecutive points on one side of mean)
    above_mean = (data > mean).astype(int)
    trend_violations = []

    consecutive = 0
    for i, value in enumerate(above_mean):
        if i > 0 and value == above_mean.iloc[i-1]:
            consecutive += 1
        else:
            consecutive = 1

        if consecutive >= 7:
            trend_violations.append(i)

    return {
        'mean': mean,
        'std_dev': std_dev,
        'ucl': ucl,
        'lcl': lcl,
        'out_of_control_count': len(out_of_control),
        'out_of_control_indices': out_of_control.index.tolist(),
        'trend_violations': trend_violations,
    }
```

## Threshold Alerts

Simple rule-based anomaly detection.

```python
@dataclass
class ThresholdRule:
    """Threshold-based alert rule."""

    metric_name: str
    threshold: Decimal
    comparison: str  # 'greater_than', 'less_than', 'equal_to'
    severity: str  # 'critical', 'warning', 'info'

def evaluate_threshold_rules(
    current_value: Decimal,
    rules: list[ThresholdRule],
) -> list[str]:
    """
    Evaluate value against threshold rules.

    Returns:
        List of alert messages
    """
    alerts = []

    for rule in rules:
        triggered = False

        if rule.comparison == 'greater_than' and current_value > rule.threshold:
            triggered = True
        elif rule.comparison == 'less_than' and current_value < rule.threshold:
            triggered = True
        elif rule.comparison == 'equal_to' and current_value == rule.threshold:
            triggered = True

        if triggered:
            alert = (
                f"[{rule.severity.upper()}] {rule.metric_name}: "
                f"${current_value:,.2f} {rule.comparison.replace('_', ' ')} "
                f"${rule.threshold:,.2f}"
            )
            alerts.append(alert)

    return alerts

# Example usage
rules = [
    ThresholdRule(
        metric_name="Daily Expense",
        threshold=Decimal('50000'),
        comparison='greater_than',
        severity='warning',
    ),
    ThresholdRule(
        metric_name="Daily Expense",
        threshold=Decimal('100000'),
        comparison='greater_than',
        severity='critical',
    ),
]
```

## Visualization

```python
import matplotlib.pyplot as plt

def plot_anomalies(
    data: pd.Series,
    anomalies: pd.Series,
    title: str = "Anomaly Detection",
):
    """
    Visualize detected anomalies.

    Args:
        data: Original time series
        anomalies: Boolean series indicating anomalies
        title: Plot title
    """
    fig, ax = plt.subplots(figsize=(14, 6))

    # Plot normal points
    ax.plot(data.index, data.values, 'o-', color='blue', alpha=0.6, label='Normal')

    # Highlight anomalies
    anomaly_points = data[anomalies]
    ax.scatter(
        anomaly_points.index,
        anomaly_points.values,
        color='red',
        s=100,
        marker='X',
        label='Anomaly',
        zorder=5
    )

    ax.set_title(title)
    ax.set_xlabel('Date')
    ax.set_ylabel('Value')
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig('anomalies.png', dpi=300, bbox_inches='tight')
    plt.close()
```

## Best Practices

### 1. Use Multiple Methods

Combine statistical methods (Z-score, IQR) with domain rules (thresholds, patterns) for robust detection.

### 2. Set Appropriate Thresholds

Balance sensitivity (catching all anomalies) with specificity (avoiding false positives).

### 3. Investigate Before Acting

Not all anomalies are problems - some may be legitimate business events (acquisitions, seasonal peaks, etc.).

### 4. Document Findings

Maintain an audit trail of detected anomalies and investigation outcomes.

### 5. Continuous Monitoring

Automated anomaly detection should run continuously, not just during audits.

## Use Cases

- **Fraud Detection**: Benford's Law + transaction pattern analysis
- **Data Quality**: Statistical outliers + duplicate detection
- **Process Monitoring**: Control charts + velocity checks
- **Expense Management**: Threshold alerts + moving average deviation
- **Revenue Assurance**: Time series anomalies + seasonal analysis
