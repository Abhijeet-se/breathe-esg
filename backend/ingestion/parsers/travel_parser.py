"""
Corporate Travel Parser
========================

Parses corporate travel data (CSV or Excel).

Key Features:
- Supports multiple transport modes: flight, train, car, hotel
- Airport distance lookup table for common routes (20+ city pairs)
- Estimates missing distances from origin/destination codes
- All travel data is Scope 3 (indirect value chain emissions)

Fields:
    employee_name: Name of the traveling employee
    trip_type: 'one_way' or 'round_trip'
    transport_mode: 'flight', 'train', 'car', 'hotel'
    origin_code: Airport/city code for origin
    destination_code: Airport/city code for destination
    distance_km: Distance in kilometers (estimated if missing)
    cost: Trip cost
    date: Travel date
"""

import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Any, Optional

from .base import BaseParser

logger = logging.getLogger(__name__)

# ============================================================================
# AIRPORT DISTANCE LOOKUP TABLE
# ============================================================================
# Approximate great-circle distances between common airport pairs in kilometers.
# Used to estimate emissions when distance_km is not provided.
# These are one-way distances.
AIRPORT_DISTANCES = {
    # European routes
    ('FRA', 'LHR'): 654,    # Frankfurt - London Heathrow
    ('FRA', 'CDG'): 479,    # Frankfurt - Paris CDG
    ('FRA', 'AMS'): 365,    # Frankfurt - Amsterdam
    ('FRA', 'ZRH'): 306,    # Frankfurt - Zurich
    ('FRA', 'MUC'): 304,    # Frankfurt - Munich
    ('FRA', 'VIE'): 598,    # Frankfurt - Vienna
    ('FRA', 'BCN'): 1090,   # Frankfurt - Barcelona
    ('FRA', 'FCO'): 960,    # Frankfurt - Rome
    ('LHR', 'CDG'): 341,    # London - Paris
    ('LHR', 'AMS'): 371,    # London - Amsterdam
    ('LHR', 'BCN'): 1138,   # London - Barcelona
    ('LHR', 'MAD'): 1264,   # London - Madrid
    ('LHR', 'FCO'): 1435,   # London - Rome
    ('CDG', 'AMS'): 399,    # Paris - Amsterdam
    ('CDG', 'BCN'): 833,    # Paris - Barcelona
    ('MUC', 'VIE'): 357,    # Munich - Vienna
    ('MUC', 'ZRH'): 240,    # Munich - Zurich
    ('BER', 'FRA'): 432,    # Berlin - Frankfurt
    ('BER', 'MUC'): 504,    # Berlin - Munich
    ('BER', 'LHR'): 930,    # Berlin - London
    # Transatlantic routes
    ('FRA', 'JFK'): 6196,   # Frankfurt - New York JFK
    ('FRA', 'ORD'): 6966,   # Frankfurt - Chicago
    ('FRA', 'SFO'): 9140,   # Frankfurt - San Francisco
    ('LHR', 'JFK'): 5539,   # London - New York
    ('LHR', 'LAX'): 8759,   # London - Los Angeles
    ('LHR', 'ORD'): 6351,   # London - Chicago
    ('CDG', 'JFK'): 5839,   # Paris - New York
    # Asia-Pacific routes
    ('FRA', 'NRT'): 9365,   # Frankfurt - Tokyo Narita
    ('FRA', 'PEK'): 7870,   # Frankfurt - Beijing
    ('FRA', 'SIN'): 10278,  # Frankfurt - Singapore
    ('FRA', 'HKG'): 9135,   # Frankfurt - Hong Kong
    ('LHR', 'SIN'): 10860,  # London - Singapore
    ('LHR', 'HKG'): 9612,   # London - Hong Kong
    ('LHR', 'NRT'): 9568,   # London - Tokyo
    # Middle East
    ('FRA', 'DXB'): 4830,   # Frankfurt - Dubai
    ('LHR', 'DXB'): 5474,   # London - Dubai
    # US domestic routes
    ('JFK', 'LAX'): 3983,   # New York - Los Angeles
    ('JFK', 'ORD'): 1190,   # New York - Chicago
    ('JFK', 'SFO'): 4139,   # New York - San Francisco
    ('ORD', 'LAX'): 2807,   # Chicago - Los Angeles
    ('ORD', 'SFO'): 2977,   # Chicago - San Francisco
}


def lookup_distance(origin: str, destination: str) -> Optional[int]:
    """
    Look up distance between two airport codes.

    Checks both directions (A->B and B->A) since distance is symmetric.
    Returns None if the pair is not in the lookup table.
    """
    origin = origin.upper().strip()
    destination = destination.upper().strip()

    # Try both directions
    distance = AIRPORT_DISTANCES.get((origin, destination))
    if distance is None:
        distance = AIRPORT_DISTANCES.get((destination, origin))

    return distance


class TravelParser(BaseParser):
    """
    Parser for corporate travel data.

    All travel emissions are Scope 3 Category 6 (Business Travel).
    The parser handles multiple transport modes and can estimate
    distances for flights using the airport distance lookup table.
    """

    def get_source_type(self) -> str:
        return 'travel'

    def get_expected_headers(self) -> List[str]:
        return [
            'employee_name', 'trip_type', 'transport_mode',
            'origin_code', 'destination_code', 'distance_km',
            'cost', 'date',
        ]

    def get_header_mappings(self) -> Dict[str, str]:
        """Map common alternative header names to standard field names."""
        return {
            # Employee
            'Employee': 'employee_name',
            'Employee Name': 'employee_name',
            'Name': 'employee_name',
            'Traveler': 'employee_name',
            'Traveller': 'employee_name',
            'Mitarbeiter': 'employee_name',  # German
            # Trip type
            'Trip Type': 'trip_type',
            'Type': 'trip_type',
            'Direction': 'trip_type',
            'Reiseart': 'trip_type',  # German
            # Transport mode
            'Transport': 'transport_mode',
            'Transport Mode': 'transport_mode',
            'Mode': 'transport_mode',
            'Travel Mode': 'transport_mode',
            'Transportmittel': 'transport_mode',  # German
            # Origin/Destination
            'Origin': 'origin_code',
            'Origin Code': 'origin_code',
            'From': 'origin_code',
            'Departure': 'origin_code',
            'Abflugort': 'origin_code',  # German
            'Destination': 'destination_code',
            'Destination Code': 'destination_code',
            'To': 'destination_code',
            'Arrival': 'destination_code',
            'Zielort': 'destination_code',  # German
            # Distance
            'Distance': 'distance_km',
            'Distance (km)': 'distance_km',
            'KM': 'distance_km',
            'km': 'distance_km',
            'Miles': 'distance_km',  # Will need conversion
            'Entfernung': 'distance_km',  # German
            # Cost
            'Cost': 'cost',
            'Total Cost': 'cost',
            'Amount': 'cost',
            'Kosten': 'cost',  # German
            # Date
            'Date': 'date',
            'Travel Date': 'date',
            'Departure Date': 'date',
            'Reisedatum': 'date',  # German
            # Hotel-specific
            'Nights': 'nights',
            'Number of Nights': 'nights',
            'Nächte': 'nights',  # German
        }

    # Valid transport modes and their normalized names
    TRANSPORT_MODES = {
        'flight': 'flight',
        'fly': 'flight',
        'air': 'flight',
        'flug': 'flight',  # German
        'train': 'train',
        'rail': 'train',
        'zug': 'train',  # German
        'bahn': 'train',  # German
        'car': 'car',
        'auto': 'car',  # German
        'taxi': 'car',
        'rental': 'car',
        'rental car': 'car',
        'mietwagen': 'car',  # German
        'hotel': 'hotel',
        'accommodation': 'hotel',
        'unterkunft': 'hotel',  # German
        'bus': 'bus',
        'coach': 'bus',
    }

    def parse_row(self, row_data: Dict[str, str], row_number: int) -> Dict[str, Any]:
        """
        Parse a single travel record.

        Handles transport mode normalization, distance estimation for flights,
        and trip type multipliers for round trips.
        """
        # --- Transport mode (required) ---
        mode_raw = row_data.get('transport_mode', '').strip()
        if not mode_raw:
            raise ValueError(f"Row {row_number}: Missing transport mode")

        mode = self.TRANSPORT_MODES.get(mode_raw.lower())
        if not mode:
            raise ValueError(
                f"Row {row_number}: Unknown transport mode '{mode_raw}'. "
                f"Supported: {', '.join(sorted(set(self.TRANSPORT_MODES.values())))}"
            )

        # --- Date (required) ---
        date_raw = row_data.get('date', '').strip()
        if not date_raw:
            raise ValueError(f"Row {row_number}: Missing travel date")
        record_date = self._parse_date(date_raw, row_number)

        # --- Distance ---
        distance_raw = row_data.get('distance_km', '').strip()
        origin = row_data.get('origin_code', '').strip().upper()
        destination = row_data.get('destination_code', '').strip().upper()

        distance_km = None
        distance_estimated = False

        if distance_raw:
            # Parse provided distance
            dist_str = distance_raw.replace(',', '.')
            try:
                distance_km = Decimal(dist_str)
            except (InvalidOperation, ValueError):
                logger.warning(
                    f"Row {row_number}: Could not parse distance '{distance_raw}'"
                )

        # If distance not provided or invalid, try to estimate from airport codes
        if distance_km is None and origin and destination and mode == 'flight':
            estimated = lookup_distance(origin, destination)
            if estimated:
                distance_km = Decimal(str(estimated))
                distance_estimated = True
                logger.info(
                    f"Row {row_number}: Estimated distance {origin}->{destination} "
                    f"as {estimated} km"
                )
            else:
                raise ValueError(
                    f"Row {row_number}: No distance provided and route "
                    f"{origin}->{destination} not in lookup table"
                )

        # For hotel stays, distance is not applicable - use nights instead
        if mode == 'hotel':
            nights_raw = row_data.get('nights', '1').strip()
            try:
                nights = int(nights_raw) if nights_raw else 1
            except ValueError:
                nights = 1

            if distance_km is None:
                distance_km = Decimal(str(nights))  # Use nights as "quantity"

            return {
                'employee_name': row_data.get('employee_name', '').strip(),
                'trip_type': 'hotel_stay',
                'transport_mode': mode,
                'origin_code': origin,
                'destination_code': destination,
                'distance_km': distance_km,
                'nights': nights,
                'cost': self._parse_cost(row_data.get('cost', ''), row_number),
                'date': record_date,
                'quantity': Decimal(str(nights)),
                'unit': 'nights',
                'distance_estimated': False,
                'scope': 'scope_3',
                'category': 'Business Travel',
            }

        if distance_km is None:
            raise ValueError(
                f"Row {row_number}: Distance is required for {mode} travel"
            )

        if distance_km < 0:
            raise ValueError(f"Row {row_number}: Negative distance is not allowed")

        # --- Trip type ---
        trip_type_raw = row_data.get('trip_type', 'one_way').strip().lower()
        is_round_trip = trip_type_raw in (
            'round_trip', 'round trip', 'roundtrip', 'return',
            'hin und zurück', 'hin_und_zurueck',  # German
        )

        # Double distance for round trips
        effective_distance = distance_km * 2 if is_round_trip else distance_km

        # --- Cost (optional) ---
        cost = self._parse_cost(row_data.get('cost', ''), row_number)

        return {
            'employee_name': row_data.get('employee_name', '').strip(),
            'trip_type': 'round_trip' if is_round_trip else 'one_way',
            'transport_mode': mode,
            'origin_code': origin,
            'destination_code': destination,
            'distance_km': effective_distance,
            'cost': cost,
            'date': record_date,
            'quantity': effective_distance,
            'unit': 'km',
            'distance_estimated': distance_estimated,
            # Emissions classification
            'scope': 'scope_3',
            'category': 'Business Travel',
        }

    def _parse_date(self, date_str: str, row_number: int):
        """Parse a date string, trying multiple formats."""
        date_formats = [
            '%Y-%m-%d',
            '%d.%m.%Y',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%d-%m-%Y',
            '%Y%m%d',
            '%b %d, %Y',
            '%B %d, %Y',
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        raise ValueError(
            f"Row {row_number}: Cannot parse date '{date_str}'"
        )

    def _parse_cost(self, cost_raw: str, row_number: int) -> Optional[Decimal]:
        """Parse a cost value, returning None if empty or unparseable."""
        if not cost_raw or not cost_raw.strip():
            return None

        cost_str = cost_raw.strip().replace(',', '.')
        # Remove currency symbols
        for sym in ['$', '€', '£', '¥', 'USD', 'EUR', 'GBP']:
            cost_str = cost_str.replace(sym, '')
        cost_str = cost_str.strip()

        try:
            return Decimal(cost_str)
        except (InvalidOperation, ValueError):
            logger.warning(f"Row {row_number}: Could not parse cost '{cost_raw}'")
            return None
