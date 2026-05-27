"""
Management Command: create_sample_data
=======================================

Creates demo tenants, users, data sources, and sample upload batches
for development and demonstration purposes.

Usage:
    python manage.py create_sample_data

Creates:
    - 2 Tenants: "Acme Corp" and "Globex Industries"
    - 4 Users: analyst + admin for each tenant
    - 6 Data Sources: SAP Fuel, Electricity, Travel for each tenant
    - Sample upload batches with normalized records

Demo Credentials:
    analyst@acme.com / password123
    admin@acme.com   / password123
    analyst@globex.com / password123
    admin@globex.com   / password123
"""

import uuid
import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from tenants.models import Tenant, User
from ingestion.models import (
    DataSource, UploadBatch, RawRecord, NormalizedRecord,
    AuditLog, ApprovalRecord,
)


class Command(BaseCommand):
    help = 'Create sample tenants, users, data sources, and demo data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Creating sample data...'))

        # ── Tenants ──────────────────────────────────────────────
        acme, _ = Tenant.objects.get_or_create(
            domain='acme',
            defaults={'name': 'Acme Corporation', 'is_active': True}
        )
        globex, _ = Tenant.objects.get_or_create(
            domain='globex',
            defaults={'name': 'Globex Industries', 'is_active': True}
        )
        self.stdout.write(f'  [OK] Tenants: {acme.name}, {globex.name}')

        # ── Users ────────────────────────────────────────────────
        users_data = [
            {'email': 'analyst@acme.com', 'username': 'analyst_acme',
             'first_name': 'Sarah', 'last_name': 'Chen',
             'role': 'analyst', 'tenant': acme},
            {'email': 'admin@acme.com', 'username': 'admin_acme',
             'first_name': 'James', 'last_name': 'Wilson',
             'role': 'admin', 'tenant': acme},
            {'email': 'analyst@globex.com', 'username': 'analyst_globex',
             'first_name': 'Maria', 'last_name': 'Garcia',
             'role': 'analyst', 'tenant': globex},
            {'email': 'admin@globex.com', 'username': 'admin_globex',
             'first_name': 'David', 'last_name': 'Park',
             'role': 'admin', 'tenant': globex},
        ]

        created_users = {}
        for udata in users_data:
            user, created = User.objects.get_or_create(
                email=udata['email'],
                defaults={
                    'username': udata['username'],
                    'first_name': udata['first_name'],
                    'last_name': udata['last_name'],
                    'role': udata['role'],
                    'tenant': udata['tenant'],
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            created_users[udata['email']] = user
            self.stdout.write(f'  [OK] User: {user.email} ({user.role})')

        # ── Data Sources ─────────────────────────────────────────
        sources = {}
        for tenant in [acme, globex]:
            for src_type, name_template in [
                ('sap_fuel', '{} SAP Fuel & Procurement'),
                ('electricity', '{} Utility Electricity'),
                ('travel', '{} Corporate Travel'),
            ]:
                src, _ = DataSource.objects.get_or_create(
                    tenant=tenant,
                    source_type=src_type,
                    defaults={
                        'name': name_template.format(tenant.name),
                        'header_mappings': None,
                    }
                )
                sources[(tenant.domain, src_type)] = src
                self.stdout.write(f'  [OK] DataSource: {src.name}')

        # ── Sample Data for Acme ─────────────────────────────────
        analyst = created_users['analyst@acme.com']
        admin_user = created_users['admin@acme.com']

        # --- SAP Fuel batch ---
        sap_source = sources[('acme', 'sap_fuel')]
        sap_batch, created = UploadBatch.objects.get_or_create(
            tenant=acme,
            data_source=sap_source,
            file_name='sap_fuel_q1_2024.csv',
            defaults={
                'status': 'completed',
                'total_rows': 15,
                'parsed_rows': 12,
                'failed_rows': 2,
                'suspicious_rows': 1,
                'approved_rows': 5,
                'uploaded_by': analyst,
            }
        )

        if created:
            self._create_sap_records(sap_batch, acme, analyst, admin_user)
            self.stdout.write(f'  [OK] SAP Fuel batch: {sap_batch.total_rows} rows')

        # --- Electricity batch ---
        elec_source = sources[('acme', 'electricity')]
        elec_batch, created = UploadBatch.objects.get_or_create(
            tenant=acme,
            data_source=elec_source,
            file_name='electricity_bills_2024.csv',
            defaults={
                'status': 'completed',
                'total_rows': 12,
                'parsed_rows': 10,
                'failed_rows': 1,
                'suspicious_rows': 1,
                'approved_rows': 3,
                'uploaded_by': analyst,
            }
        )

        if created:
            self._create_electricity_records(elec_batch, acme, analyst, admin_user)
            self.stdout.write(f'  [OK] Electricity batch: {elec_batch.total_rows} rows')

        # --- Travel batch ---
        travel_source = sources[('acme', 'travel')]
        travel_batch, created = UploadBatch.objects.get_or_create(
            tenant=acme,
            data_source=travel_source,
            file_name='corporate_travel_2024.csv',
            defaults={
                'status': 'completed',
                'total_rows': 10,
                'parsed_rows': 8,
                'failed_rows': 1,
                'suspicious_rows': 1,
                'approved_rows': 2,
                'uploaded_by': analyst,
            }
        )

        if created:
            self._create_travel_records(travel_batch, acme, analyst, admin_user)
            self.stdout.write(f'  [OK] Travel batch: {travel_batch.total_rows} rows')

        self.stdout.write(self.style.SUCCESS(
            '\n[DONE] Sample data created successfully!\n'
            '\nDemo credentials:\n'
            '  analyst@acme.com  / password123\n'
            '  admin@acme.com    / password123\n'
        ))

    # ─── SAP Fuel Record Generator ─────────────────────────────
    def _create_sap_records(self, batch, tenant, analyst, admin_user):
        fuel_rows = [
            {'plant_code': 'DE-01', 'material_code': 'MAT-1001', 'fuel_type': 'diesel',
             'quantity': 500, 'unit': 'liters', 'vendor': 'Shell GmbH',
             'date': '2024-01-15', 'status': 'approved'},
            {'plant_code': 'DE-01', 'material_code': 'MAT-1002', 'fuel_type': 'petrol',
             'quantity': 200, 'unit': 'liters', 'vendor': 'BP Deutschland',
             'date': '2024-01-20', 'status': 'approved'},
            {'plant_code': 'DE-02', 'material_code': 'MAT-2001', 'fuel_type': 'diesel',
             'quantity': 750, 'unit': 'liters', 'vendor': 'TotalEnergies',
             'date': '2024-02-01', 'status': 'parsed'},
            {'plant_code': 'DE-02', 'material_code': 'MAT-2002', 'fuel_type': 'natural_gas',
             'quantity': 120, 'unit': 'm3', 'vendor': 'Uniper SE',
             'date': '2024-02-10', 'status': 'parsed'},
            {'plant_code': 'US-01', 'material_code': 'MAT-3001', 'fuel_type': 'diesel',
             'quantity': 300, 'unit': 'gallons', 'vendor': 'ExxonMobil',
             'date': '2024-02-15', 'status': 'approved'},
            {'plant_code': 'US-01', 'material_code': 'MAT-3002', 'fuel_type': 'petrol',
             'quantity': 150, 'unit': 'gallons', 'vendor': 'Chevron',
             'date': '2024-02-20', 'status': 'approved'},
            {'plant_code': 'DE-03', 'material_code': 'MAT-4001', 'fuel_type': 'diesel',
             'quantity': 1200, 'unit': 'liters', 'vendor': 'Aral AG',
             'date': '2024-03-01', 'status': 'parsed'},
            {'plant_code': 'DE-03', 'material_code': 'MAT-4002', 'fuel_type': 'diesel',
             'quantity': 15000, 'unit': 'liters', 'vendor': 'Shell GmbH',
             'date': '2024-03-05', 'status': 'suspicious'},
            {'plant_code': 'DE-01', 'material_code': 'MAT-1003', 'fuel_type': 'lpg',
             'quantity': 80, 'unit': 'liters', 'vendor': 'Primagas',
             'date': '2024-03-10', 'status': 'parsed'},
            {'plant_code': 'DE-01', 'material_code': 'MAT-1004', 'fuel_type': 'diesel',
             'quantity': -50, 'unit': 'liters', 'vendor': 'Shell GmbH',
             'date': '2024-03-12', 'status': 'failed'},
            {'plant_code': 'DE-02', 'material_code': 'MAT-2003', 'fuel_type': 'diesel',
             'quantity': 420, 'unit': 'liters', 'vendor': 'TotalEnergies',
             'date': '2024-03-15', 'status': 'approved'},
            {'plant_code': '', 'material_code': '', 'fuel_type': 'unknown',
             'quantity': 0, 'unit': '', 'vendor': '',
             'date': 'invalid', 'status': 'failed'},
        ]

        emission_factors = {'diesel': 2.68, 'petrol': 2.31, 'natural_gas': 2.0, 'lpg': 1.56}
        gallon_to_liter = 3.78541

        for i, row in enumerate(fuel_rows):
            raw = RawRecord.objects.create(
                batch=batch, row_number=i + 1, original_data=row,
            )
            qty = max(abs(row['quantity']), 0.001)
            unit = row['unit']
            norm_val = qty * gallon_to_liter if unit == 'gallons' else qty
            factor = emission_factors.get(row['fuel_type'], 2.68)
            emissions = Decimal(str(round(norm_val * factor, 4)))

            validation_errors = []
            suspicious_flag = False
            suspicious_reason = None
            if row['status'] == 'failed':
                validation_errors = [{'field': 'quantity', 'rule': 'negative_value',
                                      'message': 'Quantity cannot be negative', 'severity': 'error'}]
            if row['status'] == 'suspicious':
                suspicious_flag = True
                suspicious_reason = 'Quantity 15000 liters exceeds 3σ threshold'
                validation_errors = [{'field': 'quantity', 'rule': 'anomaly_detection',
                                      'message': 'Value exceeds statistical threshold', 'severity': 'warning'}]

            record_date = date.today()
            try:
                record_date = date.fromisoformat(row['date'])
            except (ValueError, TypeError):
                pass

            nr = NormalizedRecord.objects.create(
                raw_record=raw, tenant=tenant, batch=batch,
                source_type='sap_fuel', scope='scope_1',
                category='Stationary Combustion',
                record_date=record_date,
                original_unit=unit or 'unknown',
                original_value=Decimal(str(abs(row['quantity']))),
                normalized_unit='liters',
                normalized_value=Decimal(str(round(norm_val, 4))),
                emissions_kg_co2e=emissions,
                status=row['status'],
                validation_errors=validation_errors,
                suspicious_flag=suspicious_flag,
                suspicious_reason=suspicious_reason,
                approved_by=admin_user if row['status'] == 'approved' else None,
                approved_at=timezone.now() if row['status'] == 'approved' else None,
            )

            AuditLog.objects.create(
                normalized_record=nr, action='create',
                new_value=f'Parsed from row {i+1}', changed_by=analyst,
            )
            if row['status'] == 'approved':
                AuditLog.objects.create(
                    normalized_record=nr, action='approve',
                    field_name='status', old_value='parsed',
                    new_value='approved', changed_by=admin_user,
                )
                ApprovalRecord.objects.create(
                    normalized_record=nr, reviewer=admin_user,
                    action='approve', comments='Verified against procurement records',
                )

    # ─── Electricity Record Generator ──────────────────────────
    def _create_electricity_records(self, batch, tenant, analyst, admin_user):
        elec_rows = [
            {'meter_id': 'MTR-001', 'kwh': 12500, 'tariff': 'commercial',
             'cost': 1875.00, 'provider': 'E.ON', 'date': '2024-01-31',
             'status': 'approved'},
            {'meter_id': 'MTR-002', 'kwh': 8200, 'tariff': 'industrial',
             'cost': 1148.00, 'provider': 'RWE', 'date': '2024-01-31',
             'status': 'parsed'},
            {'meter_id': 'MTR-001', 'kwh': 13100, 'tariff': 'commercial',
             'cost': 1965.00, 'provider': 'E.ON', 'date': '2024-02-29',
             'status': 'approved'},
            {'meter_id': 'MTR-003', 'kwh': 4500, 'tariff': 'residential',
             'cost': 720.00, 'provider': 'Vattenfall', 'date': '2024-02-29',
             'status': 'parsed'},
            {'meter_id': 'MTR-002', 'kwh': 9500, 'tariff': 'industrial',
             'cost': 1330.00, 'provider': 'RWE', 'date': '2024-02-29',
             'status': 'parsed'},
            {'meter_id': 'MTR-001', 'kwh': 95000, 'tariff': 'commercial',
             'cost': 14250.00, 'provider': 'E.ON', 'date': '2024-03-31',
             'status': 'suspicious'},
            {'meter_id': 'MTR-004', 'kwh': 6200, 'tariff': 'commercial',
             'cost': 930.00, 'provider': 'EnBW', 'date': '2024-03-31',
             'status': 'parsed'},
            {'meter_id': 'MTR-002', 'kwh': 7800, 'tariff': 'industrial',
             'cost': 1092.00, 'provider': 'RWE', 'date': '2024-03-31',
             'status': 'approved'},
            {'meter_id': '', 'kwh': -100, 'tariff': '', 'cost': 0,
             'provider': '', 'date': '2024-03-31', 'status': 'failed'},
            {'meter_id': 'MTR-005', 'kwh': 5400, 'tariff': 'commercial',
             'cost': 810.00, 'provider': 'E.ON', 'date': '2024-03-31',
             'status': 'parsed'},
        ]

        factor = Decimal('0.38')

        for i, row in enumerate(elec_rows):
            raw = RawRecord.objects.create(
                batch=batch, row_number=i + 1, original_data=row,
            )

            kwh = max(abs(row['kwh']), 1)
            emissions = Decimal(str(kwh)) * factor

            validation_errors = []
            suspicious_flag = False
            suspicious_reason = None
            if row['status'] == 'failed':
                validation_errors = [{'field': 'meter_id', 'rule': 'missing_field',
                                      'message': 'Meter ID is required', 'severity': 'error'}]
            if row['status'] == 'suspicious':
                suspicious_flag = True
                suspicious_reason = 'kWh usage 95000 exceeds 3σ threshold (avg ~8000)'

            record_date = date.today()
            try:
                record_date = date.fromisoformat(row['date'])
            except (ValueError, TypeError):
                pass

            nr = NormalizedRecord.objects.create(
                raw_record=raw, tenant=tenant, batch=batch,
                source_type='electricity', scope='scope_2',
                category='Purchased Electricity',
                record_date=record_date,
                original_unit='kWh',
                original_value=Decimal(str(abs(row['kwh']))),
                normalized_unit='kWh',
                normalized_value=Decimal(str(kwh)),
                emissions_kg_co2e=emissions,
                status=row['status'],
                validation_errors=validation_errors,
                suspicious_flag=suspicious_flag,
                suspicious_reason=suspicious_reason,
                approved_by=admin_user if row['status'] == 'approved' else None,
                approved_at=timezone.now() if row['status'] == 'approved' else None,
            )

            AuditLog.objects.create(
                normalized_record=nr, action='create',
                new_value=f'Parsed from row {i+1}', changed_by=analyst,
            )

    # ─── Travel Record Generator ───────────────────────────────
    def _create_travel_records(self, batch, tenant, analyst, admin_user):
        travel_rows = [
            {'employee': 'John Smith', 'trip_type': 'business', 'mode': 'flight',
             'origin': 'JFK', 'destination': 'LHR', 'distance_km': 5539,
             'cost': 2400, 'date': '2024-01-10', 'status': 'approved'},
            {'employee': 'Jane Doe', 'trip_type': 'business', 'mode': 'train',
             'origin': 'London', 'destination': 'Paris', 'distance_km': 460,
             'cost': 180, 'date': '2024-01-15', 'status': 'approved'},
            {'employee': 'Bob Johnson', 'trip_type': 'conference', 'mode': 'flight',
             'origin': 'LAX', 'destination': 'SFO', 'distance_km': 543,
             'cost': 320, 'date': '2024-02-05', 'status': 'parsed'},
            {'employee': 'Alice Brown', 'trip_type': 'client_visit', 'mode': 'car',
             'origin': 'Munich', 'destination': 'Stuttgart', 'distance_km': 233,
             'cost': 95, 'date': '2024-02-12', 'status': 'parsed'},
            {'employee': 'Charlie Wilson', 'trip_type': 'business', 'mode': 'flight',
             'origin': 'FRA', 'destination': 'JFK', 'distance_km': 6196,
             'cost': 3200, 'date': '2024-02-20', 'status': 'parsed'},
            {'employee': 'Sarah Chen', 'trip_type': 'business', 'mode': 'hotel',
             'origin': 'New York', 'destination': 'New York', 'distance_km': 0,
             'cost': 1200, 'date': '2024-02-20', 'status': 'parsed'},
            {'employee': 'Mike Taylor', 'trip_type': 'business', 'mode': 'flight',
             'origin': 'SYD', 'destination': 'NRT', 'distance_km': 7823,
             'cost': 8500, 'date': '2024-03-01', 'status': 'suspicious'},
            {'employee': '', 'trip_type': '', 'mode': 'unknown',
             'origin': '', 'destination': '', 'distance_km': 0,
             'cost': 0, 'date': 'invalid', 'status': 'failed'},
        ]

        emission_factors = {'flight': Decimal('0.255'), 'train': Decimal('0.041'),
                            'car': Decimal('0.21'), 'hotel': Decimal('31.1')}

        for i, row in enumerate(travel_rows):
            raw = RawRecord.objects.create(
                batch=batch, row_number=i + 1, original_data=row,
            )

            mode = row['mode']
            distance = max(abs(row['distance_km']), 1)
            factor = emission_factors.get(mode, Decimal('0.255'))

            if mode == 'hotel':
                # Estimate 4 nights from cost
                nights = max(row['cost'] // 300, 1)
                emissions = factor * Decimal(str(nights))
                norm_val = Decimal(str(nights))
                norm_unit = 'room-nights'
            else:
                emissions = factor * Decimal(str(distance))
                norm_val = Decimal(str(distance))
                norm_unit = 'km'

            validation_errors = []
            suspicious_flag = False
            suspicious_reason = None
            if row['status'] == 'failed':
                validation_errors = [{'field': 'employee', 'rule': 'missing_field',
                                      'message': 'Employee name is required', 'severity': 'error'}]
            if row['status'] == 'suspicious':
                suspicious_flag = True
                suspicious_reason = 'Flight cost $8500 exceeds typical range for this route'

            record_date = date.today()
            try:
                record_date = date.fromisoformat(row['date'])
            except (ValueError, TypeError):
                pass

            nr = NormalizedRecord.objects.create(
                raw_record=raw, tenant=tenant, batch=batch,
                source_type='travel', scope='scope_3',
                category='Business Travel',
                record_date=record_date,
                original_unit=norm_unit,
                original_value=norm_val,
                normalized_unit=norm_unit,
                normalized_value=norm_val,
                emissions_kg_co2e=emissions,
                status=row['status'],
                validation_errors=validation_errors,
                suspicious_flag=suspicious_flag,
                suspicious_reason=suspicious_reason,
                approved_by=admin_user if row['status'] == 'approved' else None,
                approved_at=timezone.now() if row['status'] == 'approved' else None,
            )

            AuditLog.objects.create(
                normalized_record=nr, action='create',
                new_value=f'Parsed from row {i+1}', changed_by=analyst,
            )
