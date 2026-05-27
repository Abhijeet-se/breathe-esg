"""
Electricity Bill Parser
========================

Parses utility electricity bill data (CSV or Excel).

Key Features:
- Handles meter-level billing data with period start/end dates
- Normalizes MWh to kWh for consistent unit handling
- Validates billing period consistency
- All electricity consumption is Scope 2 (indirect energy emissions)

Fields:
    meter_id: Utility meter identifier
    billing_period_start: Start date of the billing period
    billing_period_end: End date of the billing period
    kwh_usage: Energy consumption in kWh (or MWh, auto-converted)
    tariff_type: Rate tariff (e.g., 'peak', 'off-peak', 'flat')
    cost: Total cost for the billing period
    utility_provider: Name of the electricity utility
"""

import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Any

from .base import BaseParser

logger = logging.getLogger(__name__)


class ElectricityParser(BaseParser):
    """
    Parser for utility electricity billing data.

    Electricity consumption represents Scope 2 emissions (purchased electricity).
    The parser handles MWh<->kWh conversion and validates billing periods.
    """

    def get_source_type(self) -> str:
        return 'electricity'

    def get_expected_headers(self) -> List[str]:
        return [
            'meter_id', 'billing_period_start', 'billing_period_end',
            'kwh_usage', 'tariff_type', 'cost', 'utility_provider',
        ]

    def get_header_mappings(self) -> Dict[str, str]:
        """Map common alternative header names to standard field names."""
        return {
            # Meter ID variations
            'Meter ID': 'meter_id',
            'Meter Number': 'meter_id',
            'Meter': 'meter_id',
            'meter_number': 'meter_id',
            'meter_no': 'meter_id',
            'Zählernummer': 'meter_id',  # German
            # Billing period
            'Billing Period Start': 'billing_period_start',
            'Period Start': 'billing_period_start',
            'Start Date': 'billing_period_start',
            'start_date': 'billing_period_start',
            'Von': 'billing_period_start',  # German
            'Billing Period End': 'billing_period_end',
            'Period End': 'billing_period_end',
            'End Date': 'billing_period_end',
            'end_date': 'billing_period_end',
            'Bis': 'billing_period_end',  # German
            # Usage
            'kWh': 'kwh_usage',
            'kWh Usage': 'kwh_usage',
            'Usage (kWh)': 'kwh_usage',
            'Consumption': 'kwh_usage',
            'MWh': 'kwh_usage',   # Will be converted
            'MWh Usage': 'kwh_usage',
            'Usage': 'kwh_usage',
            'Verbrauch': 'kwh_usage',  # German
            # Tariff
            'Tariff': 'tariff_type',
            'Tariff Type': 'tariff_type',
            'Rate': 'tariff_type',
            'Rate Type': 'tariff_type',
            'Tarif': 'tariff_type',  # German
            # Cost
            'Cost': 'cost',
            'Total Cost': 'cost',
            'Amount': 'cost',
            'Kosten': 'cost',  # German
            # Provider
            'Utility': 'utility_provider',
            'Utility Provider': 'utility_provider',
            'Provider': 'utility_provider',
            'Supplier': 'utility_provider',
            'Versorger': 'utility_provider',  # German
        }

    def parse_row(self, row_data: Dict[str, str], row_number: int) -> Dict[str, Any]:
        """
        Parse a single electricity billing row.

        Validates billing periods, handles MWh->kWh conversion, and
        sets appropriate scope/category for emissions calculation.
        """
        # --- Required field checks ---
        kwh_raw = row_data.get('kwh_usage', '').strip()
        if not kwh_raw:
            raise ValueError(f"Row {row_number}: Missing kWh usage value")

        start_raw = row_data.get('billing_period_start', '').strip()
        if not start_raw:
            raise ValueError(f"Row {row_number}: Missing billing period start date")

        end_raw = row_data.get('billing_period_end', '').strip()
        if not end_raw:
            raise ValueError(f"Row {row_number}: Missing billing period end date")

        # --- Parse dates ---
        period_start = self._parse_date(start_raw, row_number, 'billing_period_start')
        period_end = self._parse_date(end_raw, row_number, 'billing_period_end')

        # Validate period consistency
        if period_end < period_start:
            raise ValueError(
                f"Row {row_number}: Billing period end ({period_end}) is before "
                f"start ({period_start})"
            )

        # --- Parse usage ---
        # Handle comma as decimal separator (European format)
        usage_str = kwh_raw.replace(',', '.')
        # Remove any unit suffixes
        for suffix in ['kwh', 'kWh', 'mwh', 'MWh', ' ']:
            usage_str = usage_str.replace(suffix, '')
        usage_str = usage_str.strip()

        try:
            usage = Decimal(usage_str)
        except (InvalidOperation, ValueError):
            raise ValueError(
                f"Row {row_number}: Invalid usage value '{kwh_raw}' - expected a number"
            )

        # Detect if value is in MWh (heuristic: if the original header contained
        # 'MWh' or value is suspiciously small for kWh)
        original_unit = 'kWh'
        # Check if original column header indicated MWh
        for key in row_data:
            if 'mwh' in key.lower():
                usage = usage * 1000  # Convert MWh to kWh
                original_unit = 'MWh'
                break

        if usage < 0:
            raise ValueError(f"Row {row_number}: Negative usage value is not allowed")

        # --- Parse cost (optional) ---
        cost_raw = row_data.get('cost', '').strip()
        cost = None
        if cost_raw:
            cost_str = cost_raw.replace(',', '.').replace('$', '').replace('€', '').replace('£', '').strip()
            try:
                cost = Decimal(cost_str)
            except (InvalidOperation, ValueError):
                # Cost is optional - log warning but don't fail
                logger.warning(f"Row {row_number}: Could not parse cost '{cost_raw}'")

        # Use billing period midpoint as the record date
        # This normalizes billing periods to a single date for reporting
        period_days = (period_end - period_start).days
        midpoint = period_start + (period_end - period_start) // 2

        return {
            'meter_id': row_data.get('meter_id', '').strip(),
            'billing_period_start': period_start,
            'billing_period_end': period_end,
            'kwh_usage': usage,
            'original_unit': original_unit,
            'tariff_type': row_data.get('tariff_type', '').strip() or 'standard',
            'cost': cost,
            'utility_provider': row_data.get('utility_provider', '').strip(),
            'period_days': period_days,
            # Emissions classification
            'date': midpoint,
            'quantity': usage,
            'unit': 'kWh',
            'scope': 'scope_2',
            'category': 'Purchased Electricity',
        }

    def _parse_date(self, date_str: str, row_number: int, field_name: str):
        """Parse a date string, trying multiple formats."""
        date_formats = [
            '%Y-%m-%d',    # ISO: 2024-01-01
            '%d.%m.%Y',    # German: 01.01.2024
            '%d/%m/%Y',    # European: 01/01/2024
            '%m/%d/%Y',    # US: 01/01/2024
            '%Y%m%d',      # Compact: 20240101
            '%d-%m-%Y',    # Alternative: 01-01-2024
            '%b %d, %Y',   # English: Jan 01, 2024
            '%B %d, %Y',   # English: January 01, 2024
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        raise ValueError(
            f"Row {row_number}: Cannot parse {field_name} date '{date_str}'"
        )
