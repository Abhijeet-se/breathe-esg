"""
Validation Engine
==================

Rule-based validation for parsed emissions data.

Design Decisions:
- Each validation rule is a separate method for testability and extensibility
- Validation results are structured dicts with field, rule, message, and severity
- Severity levels: 'error' (blocks approval), 'warning' (flags for review)
- Anomaly detection uses simple statistical thresholds (mean ± 3σ)
- The engine is stateless - it receives data and returns validation results

Validation Rules:
1. Missing required fields
2. Date validation (valid date, not in future, not too old)
3. Unit validation (recognized units only)
4. Negative value check
5. Duplicate detection (same source + date + value)
6. Anomaly detection (statistical outlier flagging)
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
import statistics

logger = logging.getLogger(__name__)


class ValidationResult:
    """
    Structured result from a single validation check.

    Attributes:
        field: Which field failed validation (None for record-level checks)
        rule: Machine-readable rule identifier (e.g., 'missing_field')
        message: Human-readable explanation
        severity: 'error' (blocks processing) or 'warning' (flags for review)
    """
    def __init__(self, field: Optional[str], rule: str, message: str,
                 severity: str = 'error'):
        self.field = field
        self.rule = rule
        self.message = message
        self.severity = severity

    def to_dict(self) -> Dict:
        return {
            'field': self.field,
            'rule': self.rule,
            'message': self.message,
            'severity': self.severity,
        }


class ValidationEngine:
    """
    Validates parsed emissions records against business rules.

    Usage:
        engine = ValidationEngine()
        errors = engine.validate_record(record, source_type='sap_fuel')
        suspicious, reason = engine.check_anomalies(record, historical_stats)

    Each check returns a list of ValidationResult objects. An empty list
    means the check passed.
    """

    # Required fields per source type
    REQUIRED_FIELDS = {
        'sap_fuel': ['fuel_type', 'quantity', 'unit', 'date'],
        'electricity': ['kwh_usage', 'billing_period_start', 'billing_period_end'],
        'travel': ['transport_mode', 'date', 'distance_km'],
    }

    # Valid units per source type
    VALID_UNITS = {
        'sap_fuel': {
            'liters', 'gallons', 'kg', 'tonnes', 'm3', 'kWh', 'MWh',
        },
        'electricity': {
            'kWh', 'MWh',
        },
        'travel': {
            'km', 'miles', 'nights',
        },
    }

    # Maximum reasonable values per unit (for anomaly detection)
    MAX_REASONABLE_VALUES = {
        'liters': Decimal('1000000'),      # 1M liters
        'gallons': Decimal('264000'),       # ~1M liters
        'kg': Decimal('1000000'),           # 1000 tonnes
        'tonnes': Decimal('10000'),         # 10K tonnes
        'm3': Decimal('100000'),            # 100K cubic meters
        'kWh': Decimal('100000000'),        # 100 GWh
        'MWh': Decimal('100000'),           # 100 GWh
        'km': Decimal('50000'),             # 50K km (around the world)
        'nights': Decimal('365'),           # 1 year
    }

    def validate_record(self, record: Dict[str, Any],
                        source_type: str) -> List[ValidationResult]:
        """
        Run all validation checks on a parsed record.

        Args:
            record: Parsed data dict from a parser
            source_type: One of 'sap_fuel', 'electricity', 'travel'

        Returns:
            List of ValidationResult objects (empty = all checks passed)
        """
        results = []

        # 1. Missing required fields
        required = self.REQUIRED_FIELDS.get(source_type, [])
        results.extend(self.missing_field_check(record, required))

        # 2. Date validation
        date_val = record.get('date')
        if date_val:
            date_error = self.date_validation(date_val)
            if date_error:
                results.append(date_error)

        # 3. Unit validation
        unit_val = record.get('unit', '')
        if unit_val:
            valid_units = self.VALID_UNITS.get(source_type, set())
            unit_error = self.unit_validation(unit_val, valid_units)
            if unit_error:
                results.append(unit_error)

        # 4. Negative value checks
        for field in ['quantity', 'kwh_usage', 'distance_km']:
            value = record.get(field)
            if value is not None:
                neg_error = self.negative_value_check(value, field)
                if neg_error:
                    results.append(neg_error)

        # 5. Reasonableness check
        quantity = record.get('quantity')
        unit = record.get('unit', '')
        if quantity is not None and unit:
            max_val = self.MAX_REASONABLE_VALUES.get(unit)
            if max_val and Decimal(str(quantity)) > max_val:
                results.append(ValidationResult(
                    field='quantity',
                    rule='unreasonable_value',
                    message=(
                        f"Value {quantity} {unit} exceeds reasonable maximum "
                        f"of {max_val} {unit}"
                    ),
                    severity='warning',
                ))

        return results

    def missing_field_check(self, record: Dict[str, Any],
                            required_fields: List[str]) -> List[ValidationResult]:
        """
        Check that all required fields are present and non-empty.

        Returns a ValidationResult for each missing field.
        """
        results = []
        for field in required_fields:
            value = record.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                results.append(ValidationResult(
                    field=field,
                    rule='missing_field',
                    message=f"Required field '{field}' is missing or empty",
                    severity='error',
                ))
        return results

    def date_validation(self, value) -> Optional[ValidationResult]:
        """
        Validate a date value.

        Checks:
        - Is it a valid date object?
        - Is it not in the future?
        - Is it not unreasonably old (before 2000)?
        """
        if not isinstance(value, date):
            return ValidationResult(
                field='date',
                rule='invalid_date',
                message=f"Invalid date value: {value}",
                severity='error',
            )

        today = date.today()

        # Check for future dates (with 1-day buffer for timezone issues)
        if value > today + timedelta(days=1):
            return ValidationResult(
                field='date',
                rule='future_date',
                message=f"Date {value} is in the future",
                severity='warning',
            )

        # Check for unreasonably old dates
        if value < date(2000, 1, 1):
            return ValidationResult(
                field='date',
                rule='old_date',
                message=f"Date {value} is before 2000 - please verify",
                severity='warning',
            )

        return None

    def unit_validation(self, value: str,
                        valid_units: set) -> Optional[ValidationResult]:
        """
        Check if the unit is in the set of recognized units.

        Returns None if valid, ValidationResult if not.
        """
        if not valid_units:
            return None

        if value not in valid_units:
            return ValidationResult(
                field='unit',
                rule='invalid_unit',
                message=(
                    f"Unit '{value}' is not recognized. "
                    f"Valid units: {', '.join(sorted(valid_units))}"
                ),
                severity='error',
            )
        return None

    def negative_value_check(self, value, field_name: str) -> Optional[ValidationResult]:
        """
        Check if a numeric value is negative.

        Negative emissions/usage values are almost always data errors.
        """
        try:
            numeric_val = Decimal(str(value))
            if numeric_val < 0:
                return ValidationResult(
                    field=field_name,
                    rule='negative_value',
                    message=f"Field '{field_name}' has negative value: {value}",
                    severity='error',
                )
        except Exception:
            pass
        return None

    def duplicate_check(self, record: Dict[str, Any],
                        existing_records: List[Dict[str, Any]]) -> Optional[ValidationResult]:
        """
        Check if a record appears to be a duplicate of existing records.

        A duplicate is defined as matching on: source_type + date + quantity + unit.
        This catches accidental re-uploads of the same data.

        Returns None if no duplicate found, ValidationResult if duplicate detected.
        """
        record_date = record.get('date')
        record_qty = str(record.get('quantity', ''))
        record_unit = record.get('unit', '')

        for existing in existing_records:
            if (existing.get('date') == record_date and
                    str(existing.get('quantity', '')) == record_qty and
                    existing.get('unit', '') == record_unit):
                return ValidationResult(
                    field=None,
                    rule='duplicate_record',
                    message=(
                        f"Possible duplicate: same date ({record_date}), "
                        f"quantity ({record_qty}), and unit ({record_unit})"
                    ),
                    severity='warning',
                )

        return None

    def anomaly_detection(self, value, field_name: str,
                          stats: Dict[str, Any]) -> tuple:
        """
        Detect statistical anomalies using mean ± 3 standard deviations.

        Args:
            value: The value to check
            field_name: Name of the field being checked
            stats: Dict with 'mean', 'std', and 'count' from historical data

        Returns:
            Tuple of (is_suspicious: bool, reason: str or None)
        """
        if not stats or stats.get('count', 0) < 5:
            # Not enough historical data for meaningful anomaly detection
            return False, None

        try:
            numeric_val = float(value)
            mean = float(stats.get('mean', 0))
            std = float(stats.get('std', 0))

            if std == 0:
                # All historical values are the same
                if numeric_val != mean:
                    return True, (
                        f"{field_name} value {value} differs from historical "
                        f"constant value of {mean}"
                    )
                return False, None

            # Z-score: how many standard deviations from the mean
            z_score = abs(numeric_val - mean) / std

            if z_score > 3:
                return True, (
                    f"{field_name} value {value} is {z_score:.1f} standard "
                    f"deviations from historical mean ({mean:.2f} ± {std:.2f}). "
                    f"This is a statistical outlier."
                )

        except (ValueError, TypeError, ZeroDivisionError):
            pass

        return False, None

    def compute_stats(self, values: List) -> Dict[str, Any]:
        """
        Compute basic statistics for a list of values.

        Used to feed into anomaly_detection().
        Returns dict with mean, std, count, min, max.
        """
        if not values:
            return {'mean': 0, 'std': 0, 'count': 0, 'min': 0, 'max': 0}

        float_values = []
        for v in values:
            try:
                float_values.append(float(v))
            except (ValueError, TypeError):
                continue

        if len(float_values) < 2:
            return {
                'mean': float_values[0] if float_values else 0,
                'std': 0,
                'count': len(float_values),
                'min': float_values[0] if float_values else 0,
                'max': float_values[0] if float_values else 0,
            }

        return {
            'mean': statistics.mean(float_values),
            'std': statistics.stdev(float_values),
            'count': len(float_values),
            'min': min(float_values),
            'max': max(float_values),
        }
