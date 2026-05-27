"""
Normalization Engine
=====================

Converts raw parsed values into standard units and calculates CO2e emissions.

Design Decisions:
- All conversions go through a standard intermediate unit:
  - Volume: liters
  - Mass: kg
  - Energy: kWh
  - Distance: km
- Emission factors are based on IPCC/DEFRA 2023 averages
- The engine always preserves original_value and original_unit alongside
  normalized values for audit trail
- Each source type has its own normalization path since the inputs differ

Unit Conversion Pipeline:
    original_value (original_unit) -> normalized_value (normalized_unit) -> emissions_kg_co2e

Emission Factor Sources:
    - DEFRA 2023 Greenhouse Gas Reporting Conversion Factors
    - IPCC Guidelines for National Greenhouse Gas Inventories
    - Values are global averages suitable for a prototype
"""

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


class NormalizationEngine:
    """
    Converts raw values to standard units and calculates emissions.

    Usage:
        engine = NormalizationEngine()
        result = engine.normalize(parsed_data, source_type='sap_fuel')
        # result = {
        #     'normalized_value': Decimal('100.0'),
        #     'normalized_unit': 'liters',
        #     'emissions_kg_co2e': Decimal('268.0'),
        #     'scope': 'scope_1',
        #     'category': 'Stationary Combustion',
        # }
    """

    # ========================================================================
    # UNIT CONVERSIONS
    # ========================================================================
    # All conversions are expressed as: 1 source_unit = X target_units
    UNIT_CONVERSIONS = {
        # Volume conversions -> liters
        'liters': Decimal('1'),           # base unit
        'gallons': Decimal('3.78541'),    # 1 gallon = 3.78541 liters
        'l': Decimal('1'),
        # Mass conversions -> kg
        'kg': Decimal('1'),               # base unit
        'tonnes': Decimal('1000'),        # 1 tonne = 1000 kg
        't': Decimal('1000'),
        # Volume to liters (gas)
        'm3': Decimal('1000'),            # 1 m³ = 1000 liters (for liquid equiv.)
        # Energy conversions -> kWh
        'kWh': Decimal('1'),              # base unit
        'MWh': Decimal('1000'),           # 1 MWh = 1000 kWh
        'kwh': Decimal('1'),
        'mwh': Decimal('1000'),
        # Distance conversions -> km
        'km': Decimal('1'),               # base unit
        'miles': Decimal('1.60934'),      # 1 mile = 1.60934 km
        'mi': Decimal('1.60934'),
        # Special
        'nights': Decimal('1'),           # hotel nights - no conversion
    }

    # Target (normalized) units for each source unit
    NORMALIZED_UNITS = {
        'liters': 'liters',
        'gallons': 'liters',
        'l': 'liters',
        'kg': 'kg',
        'tonnes': 'kg',
        't': 'kg',
        'm3': 'm3',       # Keep m3 as-is for gas (emission factor is per m3)
        'kWh': 'kWh',
        'MWh': 'kWh',
        'kwh': 'kWh',
        'mwh': 'kWh',
        'km': 'km',
        'miles': 'km',
        'mi': 'km',
        'nights': 'nights',
    }

    # ========================================================================
    # EMISSION FACTORS (kg CO2e per unit)
    # ========================================================================
    # Based on DEFRA 2023 / IPCC guidelines
    EMISSION_FACTORS = {
        # Scope 1 - Direct fuel combustion (per liter unless noted)
        'diesel_per_liter': Decimal('2.68'),          # Diesel fuel
        'petrol_per_liter': Decimal('2.31'),          # Petrol/gasoline
        'natural_gas_per_m3': Decimal('2.0'),         # Natural gas per cubic meter
        'lpg_per_liter': Decimal('1.51'),             # Liquefied petroleum gas
        'heating_oil_per_liter': Decimal('2.54'),     # Heating oil
        'kerosene_per_liter': Decimal('2.54'),        # Kerosene / jet fuel
        'diesel_per_kg': Decimal('3.21'),             # Diesel by mass
        'petrol_per_kg': Decimal('3.10'),             # Petrol by mass

        # Scope 2 - Purchased energy
        'electricity_per_kwh': Decimal('0.38'),       # Global average grid factor

        # Scope 3 - Indirect emissions
        'flight_per_km': Decimal('0.255'),            # Economy class, medium-haul
        'train_per_km': Decimal('0.041'),             # Average rail
        'car_per_km': Decimal('0.21'),                # Average car
        'bus_per_km': Decimal('0.089'),               # Average bus
        'hotel_per_night': Decimal('31.1'),           # Average hotel stay
    }

    # Map fuel types to emission factor keys
    FUEL_EMISSION_KEYS = {
        'diesel': {
            'liters': 'diesel_per_liter',
            'kg': 'diesel_per_kg',
        },
        'petrol': {
            'liters': 'petrol_per_liter',
            'kg': 'petrol_per_kg',
        },
        'natural_gas': {
            'm3': 'natural_gas_per_m3',
        },
        'lpg': {
            'liters': 'lpg_per_liter',
        },
        'heating_oil': {
            'liters': 'heating_oil_per_liter',
        },
        'kerosene': {
            'liters': 'kerosene_per_liter',
        },
    }

    # Map transport modes to emission factor keys
    TRANSPORT_EMISSION_KEYS = {
        'flight': 'flight_per_km',
        'train': 'train_per_km',
        'car': 'car_per_km',
        'bus': 'bus_per_km',
        'hotel': 'hotel_per_night',
    }

    def normalize(self, raw_data: Dict[str, Any],
                  source_type: str) -> Dict[str, Any]:
        """
        Normalize a parsed record and calculate emissions.

        Routes to the appropriate normalization method based on source_type.

        Args:
            raw_data: Parsed data dict from a parser
            source_type: One of 'sap_fuel', 'electricity', 'travel'

        Returns:
            Dict with: normalized_value, normalized_unit, emissions_kg_co2e,
                       scope, category, original_value, original_unit
        """
        normalizers = {
            'sap_fuel': self._normalize_fuel,
            'electricity': self._normalize_electricity,
            'travel': self._normalize_travel,
        }

        normalizer = normalizers.get(source_type)
        if not normalizer:
            raise ValueError(f"Unknown source type: {source_type}")

        return normalizer(raw_data)

    def _normalize_fuel(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize SAP fuel/procurement data.

        Converts quantity to standard units and applies fuel-specific
        emission factors.
        """
        quantity = Decimal(str(data['quantity']))
        unit = data['unit']
        fuel_type = data['fuel_type']

        # Convert to normalized unit
        normalized_value, normalized_unit = self._convert_unit(quantity, unit)

        # Look up emission factor for this fuel type and unit
        fuel_factors = self.FUEL_EMISSION_KEYS.get(fuel_type, {})

        # For m3, use the value directly (don't convert to liters for gas)
        if unit == 'm3' or normalized_unit == 'm3':
            emission_key = fuel_factors.get('m3')
            emission_quantity = quantity  # Use original m3 value
        else:
            emission_key = fuel_factors.get(normalized_unit)
            emission_quantity = normalized_value

        if not emission_key:
            # Fall back to liters if available
            if normalized_unit == 'liters' and 'liters' in fuel_factors:
                emission_key = fuel_factors['liters']
                emission_quantity = normalized_value
            else:
                logger.warning(
                    f"No emission factor for {fuel_type} in {normalized_unit}, "
                    f"using diesel as fallback"
                )
                emission_key = 'diesel_per_liter'
                emission_quantity = normalized_value

        emission_factor = self.EMISSION_FACTORS.get(
            emission_key, Decimal('2.68')  # Default to diesel
        )
        emissions = (emission_quantity * emission_factor).quantize(
            Decimal('0.000001'), rounding=ROUND_HALF_UP
        )

        return {
            'original_value': quantity,
            'original_unit': unit,
            'normalized_value': normalized_value,
            'normalized_unit': normalized_unit,
            'emissions_kg_co2e': emissions,
            'scope': data.get('scope', 'scope_1'),
            'category': data.get('category', 'Stationary Combustion'),
        }

    def _normalize_electricity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize electricity consumption data.

        Ensures values are in kWh and applies grid emission factor.
        """
        quantity = Decimal(str(data['quantity']))
        unit = data.get('unit', 'kWh')
        original_unit = data.get('original_unit', unit)

        # Convert to kWh
        normalized_value, normalized_unit = self._convert_unit(quantity, unit)

        # Apply grid emission factor
        emission_factor = self.EMISSION_FACTORS['electricity_per_kwh']
        emissions = (normalized_value * emission_factor).quantize(
            Decimal('0.000001'), rounding=ROUND_HALF_UP
        )

        return {
            'original_value': quantity,
            'original_unit': original_unit,
            'normalized_value': normalized_value,
            'normalized_unit': normalized_unit,
            'emissions_kg_co2e': emissions,
            'scope': 'scope_2',
            'category': 'Purchased Electricity',
        }

    def _normalize_travel(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize travel data and calculate transport-specific emissions.

        Handles distance conversion and applies mode-specific emission factors.
        """
        transport_mode = data.get('transport_mode', 'flight')
        quantity = Decimal(str(data.get('quantity', data.get('distance_km', 0))))
        unit = data.get('unit', 'km')

        # Convert to standard unit
        if transport_mode == 'hotel':
            # Hotel: quantity is nights
            normalized_value = quantity
            normalized_unit = 'nights'
            emission_key = 'hotel_per_night'
        else:
            # Transport: quantity is distance
            normalized_value, normalized_unit = self._convert_unit(quantity, unit)
            emission_key = self.TRANSPORT_EMISSION_KEYS.get(
                transport_mode, 'car_per_km'
            )

        emission_factor = self.EMISSION_FACTORS.get(
            emission_key, Decimal('0.21')  # Default to car
        )
        emissions = (normalized_value * emission_factor).quantize(
            Decimal('0.000001'), rounding=ROUND_HALF_UP
        )

        return {
            'original_value': quantity,
            'original_unit': unit,
            'normalized_value': normalized_value,
            'normalized_unit': normalized_unit,
            'emissions_kg_co2e': emissions,
            'scope': 'scope_3',
            'category': 'Business Travel',
        }

    def _convert_unit(self, value: Decimal, unit: str) -> Tuple[Decimal, str]:
        """
        Convert a value from one unit to its normalized form.

        Returns (normalized_value, normalized_unit_name).

        For m3, we keep as-is because gas emission factors are per m3.
        For everything else, we convert to the standard base unit.
        """
        # Special case: m3 stays as m3 (gas emission factors are per m3)
        if unit in ('m3', 'm³'):
            return value, 'm3'

        conversion_factor = self.UNIT_CONVERSIONS.get(unit, Decimal('1'))
        normalized_unit = self.NORMALIZED_UNITS.get(unit, unit)

        normalized_value = (value * conversion_factor).quantize(
            Decimal('0.000001'), rounding=ROUND_HALF_UP
        )

        return normalized_value, normalized_unit
