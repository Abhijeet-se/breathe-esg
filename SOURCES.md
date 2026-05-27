# SOURCES.md — Emission Factor Sources & Assumptions

This document provides citations, sources, and methodology notes for all emission
factors and conversion constants used in the Breathe ESG platform.

---

## Emission Factor Sources

### Scope 1 — Direct Emissions (Fuel Combustion)

| Fuel Type     | Factor           | Value        | Unit         | Source                    | Year  |
|---------------|------------------|--------------|--------------|---------------------------|-------|
| Diesel        | Combustion       | 2.68         | kg CO2e/liter| DEFRA GHG Conversion      | 2023  |
| Petrol/Gasoline| Combustion      | 2.31         | kg CO2e/liter| DEFRA GHG Conversion      | 2023  |
| Natural Gas   | Combustion       | 2.00         | kg CO2e/m³   | DEFRA GHG Conversion      | 2023  |
| LPG           | Combustion       | 1.56         | kg CO2e/liter| DEFRA GHG Conversion      | 2023  |
| Coal          | Combustion       | 2,256        | kg CO2e/tonne| DEFRA GHG Conversion      | 2023  |

**Reference:**
UK Government Department for Environment, Food & Rural Affairs (DEFRA).
"UK Government GHG Conversion Factors for Company Reporting."
Published annually at: https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting

### Scope 2 — Indirect Emissions (Purchased Electricity)

| Region        | Factor           | Value        | Unit         | Source                    | Year  |
|---------------|------------------|--------------|--------------|---------------------------|-------|
| Global Average| Grid intensity   | 0.380        | kg CO2e/kWh  | IEA Emission Factors      | 2023  |
| USA Average   | Grid intensity   | 0.387        | kg CO2e/kWh  | EPA eGRID                 | 2023  |
| EU Average    | Grid intensity   | 0.230        | kg CO2e/kWh  | EEA                       | 2023  |
| India Average | Grid intensity   | 0.708        | kg CO2e/kWh  | CEA CO2 Database          | 2023  |
| UK Average    | Grid intensity   | 0.207        | kg CO2e/kWh  | DEFRA                     | 2023  |

**Implementation Note:**
The prototype uses the **Global Average (0.38 kg CO2e/kWh)** as the default.
Production versions should support location-specific factors based on the utility
provider's grid region.

**Reference:**
International Energy Agency (IEA). "Emission Factors."
https://www.iea.org/data-and-statistics/data-tools/emission-factors

### Scope 3 — Indirect Value Chain Emissions (Business Travel)

| Transport Mode| Factor           | Value        | Unit              | Source            | Year  |
|---------------|------------------|--------------|-------------------|-------------------|-------|
| Flight (Econ.)| Short-haul (<500km)| 0.255      | kg CO2e/pax-km    | DEFRA             | 2023  |
| Flight (Econ.)| Medium-haul      | 0.156        | kg CO2e/pax-km    | DEFRA             | 2023  |
| Flight (Econ.)| Long-haul (>3700km)| 0.150      | kg CO2e/pax-km    | DEFRA             | 2023  |
| Flight (Biz)  | Multiplier       | 2.9x economy | multiplier        | DEFRA             | 2023  |
| Train         | Average          | 0.041        | kg CO2e/pax-km    | DEFRA             | 2023  |
| Car/Taxi      | Average          | 0.210        | kg CO2e/km         | EPA               | 2023  |
| Hotel         | Per room-night   | 31.1         | kg CO2e/room-night | Cornell CHSB     | 2022  |

**Implementation Note:**
The prototype uses the **medium-haul economy flight factor (0.255 kg CO2e/pax-km)**
as a simplified default for all flights. Future versions should apply distance-based
tiering and class multipliers.

**Reference:**
- DEFRA. "UK Government GHG Conversion Factors for Company Reporting — Business Travel."
- US Environmental Protection Agency (EPA). "Emission Factors for Greenhouse Gas Inventories."
  https://www.epa.gov/climateleadership/ghg-emission-factors-hub
- Cornell Hotel Sustainability Benchmarking (CHSB) Study.

---

## Unit Conversion Constants

| From           | To             | Factor       | Notes                          |
|----------------|----------------|--------------|--------------------------------|
| Gallons (US)   | Liters         | 3.78541      | US liquid gallon               |
| Gallons (UK)   | Liters         | 4.54609      | Imperial gallon                |
| Tonnes         | Kilograms      | 1,000        | Metric tonne                   |
| Pounds (lb)    | Kilograms      | 0.453592     |                                |
| MWh            | kWh            | 1,000        |                                |
| GJ             | kWh            | 277.778      |                                |
| Miles          | Kilometers     | 1.60934      |                                |
| Cubic feet     | Cubic meters   | 0.0283168    |                                |
| Therms         | kWh            | 29.3071      | Natural gas billing            |

---

## Airport Distance Lookup Table

The travel parser includes a lookup table for estimating distances between
common airport code pairs when distance is not provided in the upload:

| Origin | Destination | Distance (km) | Source                      |
|--------|-------------|---------------|-----------------------------|
| JFK    | LHR         | 5,539         | Great Circle Mapper         |
| LAX    | SFO         | 543           | Great Circle Mapper         |
| LHR    | CDG         | 340           | Great Circle Mapper         |
| SIN    | HKG         | 2,581         | Great Circle Mapper         |
| DXB    | LHR         | 5,474         | Great Circle Mapper         |
| FRA    | JFK         | 6,196         | Great Circle Mapper         |
| SYD    | MEL         | 713           | Great Circle Mapper         |
| NRT    | LAX         | 8,757         | Great Circle Mapper         |
| ORD    | ATL         | 975           | Great Circle Mapper         |
| BOM    | DEL         | 1,148         | Great Circle Mapper         |
| PEK    | PVG         | 1,075         | Great Circle Mapper         |
| AMS    | FRA         | 312           | Great Circle Mapper         |
| DFW    | MIA         | 1,757         | Great Circle Mapper         |
| SEA    | LAX         | 1,535         | Great Circle Mapper         |
| BOS    | ORD         | 1,367         | Great Circle Mapper         |
| DEL    | BLR         | 1,740         | Great Circle Mapper         |
| LHR    | DXB         | 5,474         | Great Circle Mapper         |
| SFO    | NRT         | 8,270         | Great Circle Mapper         |
| MUC    | LHR         | 919           | Great Circle Mapper         |
| ICN    | NRT         | 1,200         | Great Circle Mapper         |

**Reference:**
Great Circle Mapper. "Airport Distance Calculator."
https://www.greatcirclemapper.net/

---

## Assumptions & Limitations

### General Assumptions
1. **Well-to-tank emissions are excluded.** Only combustion/use-phase emissions are counted.
   Production versions should include upstream emissions per GHG Protocol guidance.

2. **Electricity factors use location-based method.** The GHG Protocol allows both
   location-based and market-based Scope 2 accounting. We default to location-based
   using grid average factors.

3. **Radiative Forcing Index (RFI) for flights is not applied.** Some methodologies
   multiply flight emissions by 1.9x to account for non-CO2 effects at altitude.
   This is not included in the prototype.

4. **All emissions are reported in kg CO2e** (carbon dioxide equivalent), which
   includes CO2, CH4, and N2O weighted by Global Warming Potential (GWP100).

### Data Quality Assumptions
1. Uploaded data is assumed to be in the correct currency for cost fields.
   Currency conversion is not performed.

2. Fuel type identification relies on the text labels in the upload.
   Ambiguous fuel types default to diesel as a conservative assumption.

3. German header auto-detection checks for the presence of known German column
   names. Mixed German/English headers may cause parsing errors.

### Calculation Limitations
1. Emission factors are static and hardcoded. They do not update automatically
   when new DEFRA/EPA factors are published.

2. Scope 2 uses a single global average factor. Location-specific factors would
   improve accuracy by 30-60% depending on the grid mix.

3. Travel distance estimation from airport codes uses great-circle distance,
   which underestimates actual flight distance by approximately 5-10%.

4. Hotel emissions use a single global average. Actual emissions vary significantly
   by hotel size, location, and energy source.

---

## Regulatory Framework References

| Standard          | Description                                        | URL                                           |
|-------------------|----------------------------------------------------|-----------------------------------------------|
| GHG Protocol      | Corporate accounting and reporting standard         | https://ghgprotocol.org/                      |
| CSRD              | EU Corporate Sustainability Reporting Directive     | https://ec.europa.eu/                         |
| TCFD              | Task Force on Climate-Related Financial Disclosures | https://www.fsb-tcfd.org/                     |
| CDP               | Carbon Disclosure Project questionnaire             | https://www.cdp.net/                          |
| ISO 14064         | GHG quantification and reporting                    | https://www.iso.org/standard/66453.html       |
| SEC Climate Rule  | US SEC climate disclosure requirements              | https://www.sec.gov/                          |

---

## Version History

| Version | Date       | Changes                           |
|---------|------------|-----------------------------------|
| 1.0     | 2026-05-27 | Initial factor set (DEFRA 2023)   |
