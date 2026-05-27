"""
SAP Fuel & Procurement Parser
==============================

Parses SAP-exported fuel and procurement data files (CSV or Excel).

Key Features:
- Auto-detects German vs English column headers
- Handles German date formats (DD.MM.YYYY) alongside ISO (YYYY-MM-DD)
- Supports multiple fuel types and unit variations
- Maps procurement categories to emission scopes (Scope 1 for direct fuel use)

German Header Mappings:
    Werk -> plant_code
    Material -> material_code
    Kraftstoffart -> fuel_type
    Menge -> quantity
    Einheit -> unit
    Beschaffungskategorie -> procurement_category
    Datum -> date
    Lieferant -> vendor
"""

import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Any

from .base import BaseParser

logger = logging.getLogger(__name__)

# Known fuel types and their normalized names
# This handles both German and English fuel names
FUEL_TYPE_MAP = {
    # German fuel names
    'diesel': 'diesel',
    'dieselkraftstoff': 'diesel',
    'benzin': 'petrol',
    'superbenzin': 'petrol',
    'erdgas': 'natural_gas',
    'flüssiggas': 'lpg',
    'heizöl': 'heating_oil',
    'kerosin': 'kerosene',
    # English fuel names
    'petrol': 'petrol',
    'gasoline': 'petrol',
    'natural gas': 'natural_gas',
    'natural_gas': 'natural_gas',
    'lpg': 'lpg',
    'heating oil': 'heating_oil',
    'heating_oil': 'heating_oil',
    'kerosene': 'kerosene',
    'jet fuel': 'kerosene',
    'jet_fuel': 'kerosene',
    'propane': 'lpg',
}

# Valid units for fuel/procurement data
VALID_UNITS = {
    'l', 'liter', 'liters', 'litre', 'litres', 'ltr',
    'gal', 'gallon', 'gallons',
    'kg', 'kilogram', 'kilograms',
    't', 'tonne', 'tonnes', 'ton', 'tons',
    'm3', 'm³', 'cubic_meter', 'cubic meter', 'cubic meters',
    'kwh', 'mwh',
}


class SAPParser(BaseParser):
    """
    Parser for SAP Fuel & Procurement CSV/Excel exports.

    Handles both German and English header formats. SAP exports from German
    installations typically use German column names and DD.MM.YYYY dates.

    All SAP fuel/procurement data is categorized as Scope 1 (direct emissions)
    since it represents fuel directly consumed by the reporting organization.
    """

    def get_source_type(self) -> str:
        return 'sap_fuel'

    def get_expected_headers(self) -> List[str]:
        """Standard (English) header names for SAP fuel data."""
        return [
            'plant_code', 'material_code', 'fuel_type', 'quantity',
            'unit', 'procurement_category', 'date', 'vendor',
        ]

    def get_header_mappings(self) -> Dict[str, str]:
        """
        Map German SAP headers to standard English names.

        These mappings handle the most common SAP ERP column names.
        The system also supports case-insensitive matching.
        """
        return {
            # German -> English mappings
            'Werk': 'plant_code',
            'Werks': 'plant_code',
            'Material': 'material_code',
            'Materialnummer': 'material_code',
            'Kraftstoffart': 'fuel_type',
            'Brennstoffart': 'fuel_type',
            'Menge': 'quantity',
            'Bestellmenge': 'quantity',
            'Einheit': 'unit',
            'Mengeneinheit': 'unit',
            'Beschaffungskategorie': 'procurement_category',
            'Einkaufsgruppe': 'procurement_category',
            'Datum': 'date',
            'Buchungsdatum': 'date',
            'Belegdatum': 'date',
            'Lieferant': 'vendor',
            'Lieferantenname': 'vendor',
            'Kreditor': 'vendor',
            # English variations
            'Plant': 'plant_code',
            'Plant Code': 'plant_code',
            'Material Code': 'material_code',
            'Fuel Type': 'fuel_type',
            'Fuel': 'fuel_type',
            'Quantity': 'quantity',
            'Amount': 'quantity',
            'Unit': 'unit',
            'UoM': 'unit',
            'Unit of Measure': 'unit',
            'Category': 'procurement_category',
            'Procurement Category': 'procurement_category',
            'Date': 'date',
            'Posting Date': 'date',
            'Document Date': 'date',
            'Vendor': 'vendor',
            'Supplier': 'vendor',
            'Vendor Name': 'vendor',
        }

    def parse_row(self, row_data: Dict[str, str], row_number: int) -> Dict[str, Any]:
        """
        Parse a single SAP fuel/procurement row.

        Validates required fields, parses dates (German & ISO formats),
        normalizes fuel types, and validates units.

        Returns parsed dict with typed values ready for normalization.
        """
        # --- Required field checks ---
        fuel_type_raw = row_data.get('fuel_type', '').strip()
        if not fuel_type_raw:
            raise ValueError(f"Row {row_number}: Missing fuel_type")

        quantity_raw = row_data.get('quantity', '').strip()
        if not quantity_raw:
            raise ValueError(f"Row {row_number}: Missing quantity")

        unit_raw = row_data.get('unit', '').strip()
        if not unit_raw:
            raise ValueError(f"Row {row_number}: Missing unit")

        date_raw = row_data.get('date', '').strip()
        if not date_raw:
            raise ValueError(f"Row {row_number}: Missing date")

        # --- Parse quantity ---
        # Handle German number format: 1.234,56 -> 1234.56
        quantity_str = quantity_raw.replace('.', '').replace(',', '.')
        try:
            quantity = Decimal(quantity_str)
        except (InvalidOperation, ValueError):
            raise ValueError(
                f"Row {row_number}: Invalid quantity '{quantity_raw}' - "
                f"expected a number"
            )

        if quantity < 0:
            raise ValueError(
                f"Row {row_number}: Negative quantity {quantity} is not allowed"
            )

        # --- Parse date ---
        record_date = self._parse_date(date_raw, row_number)

        # --- Normalize fuel type ---
        fuel_type_lower = fuel_type_raw.lower().strip()
        fuel_type = FUEL_TYPE_MAP.get(fuel_type_lower)
        if not fuel_type:
            raise ValueError(
                f"Row {row_number}: Unknown fuel type '{fuel_type_raw}'. "
                f"Supported types: {', '.join(sorted(set(FUEL_TYPE_MAP.values())))}"
            )

        # --- Validate unit ---
        unit_lower = unit_raw.lower().strip()
        if unit_lower not in VALID_UNITS:
            raise ValueError(
                f"Row {row_number}: Invalid unit '{unit_raw}'. "
                f"Supported units: {', '.join(sorted(VALID_UNITS))}"
            )

        # Normalize unit name
        unit_normalized = self._normalize_unit(unit_lower)

        return {
            'plant_code': row_data.get('plant_code', '').strip(),
            'material_code': row_data.get('material_code', '').strip(),
            'fuel_type': fuel_type,
            'quantity': quantity,
            'unit': unit_normalized,
            'procurement_category': row_data.get('procurement_category', '').strip(),
            'date': record_date,
            'vendor': row_data.get('vendor', '').strip(),
            # Emissions classification
            'scope': 'scope_1',
            'category': 'Stationary Combustion',
        }

    def _parse_date(self, date_str: str, row_number: int):
        """
        Parse a date string, trying German format first, then ISO format.

        Supported formats:
        - DD.MM.YYYY (German, most common in SAP)
        - YYYY-MM-DD (ISO)
        - DD/MM/YYYY (alternative European)
        - MM/DD/YYYY (US format)
        """
        date_formats = [
            '%d.%m.%Y',    # German: 31.12.2024
            '%Y-%m-%d',    # ISO: 2024-12-31
            '%d/%m/%Y',    # European: 31/12/2024
            '%m/%d/%Y',    # US: 12/31/2024
            '%d.%m.%y',    # Short German: 31.12.24
            '%Y%m%d',      # Compact: 20241231
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        raise ValueError(
            f"Row {row_number}: Unable to parse date '{date_str}'. "
            f"Supported formats: DD.MM.YYYY, YYYY-MM-DD, DD/MM/YYYY"
        )

    def _normalize_unit(self, unit_lower: str) -> str:
        """Normalize unit variations to standard names."""
        unit_map = {
            'l': 'liters', 'liter': 'liters', 'litre': 'liters',
            'litres': 'liters', 'liters': 'liters', 'ltr': 'liters',
            'gal': 'gallons', 'gallon': 'gallons', 'gallons': 'gallons',
            'kg': 'kg', 'kilogram': 'kg', 'kilograms': 'kg',
            't': 'tonnes', 'tonne': 'tonnes', 'tonnes': 'tonnes',
            'ton': 'tonnes', 'tons': 'tonnes',
            'm3': 'm3', 'm³': 'm3', 'cubic_meter': 'm3',
            'cubic meter': 'm3', 'cubic meters': 'm3',
            'kwh': 'kWh', 'mwh': 'MWh',
        }
        return unit_map.get(unit_lower, unit_lower)
