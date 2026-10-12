import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import asyncio
import json
from urllib.parse import urlencode, urlsplit
from types import SimpleNamespace
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import main, models, init_db
from app.database import Base, get_db
from app.schemas import VehicleExpenseCreate


class ASGIClient:
    """Exercise actual HTTP routes without an optional HTTP client dependency."""
    def __init__(self, app):
        self.app = app

    def request(self, method, url, params=None, json_body=None):
        parts = urlsplit(url)
        query = parts.query + ('&' if parts.query else '') + urlencode(params or {})
        payload = json.dumps(json_body).encode() if json_body is not None else b''
        messages = []
        async def receive():
            return {'type': 'http.request', 'body': payload, 'more_body': False}
        async def send(message):
            messages.append(message)
        scope = {'type': 'http', 'asgi': {'version': '3.0'}, 'http_version': '1.1', 'method': method,
                 'scheme': 'http', 'path': parts.path, 'raw_path': parts.path.encode(),
                 'query_string': query.encode(), 'headers': [(b'content-type', b'application/json')],
                 'server': ('test', 80), 'client': ('test', 1), 'root_path': ''}
        asyncio.run(self.app(scope, receive, send))
        status = next(m['status'] for m in messages if m['type'] == 'http.response.start')
        body = b''.join(m.get('body', b'') for m in messages if m['type'] == 'http.response.body').decode()
        return SimpleNamespace(status_code=status, text=body, json=lambda: json.loads(body))

    def get(self, url, params=None):
        return self.request('GET', url, params)

    def post(self, url, json=None):
        return self.request('POST', url, json_body=json)

    def close(self):
        pass


class FuelFlowTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine, autoflush=False)()
        self.db.add_all([
            models.Customer(id=1, company_name='Fleet'), models.Customer(id=2, company_name='Other'),
            models.Vehicle(id='car', chassis_no='VIN1', plate='34 TEST', customer_id=1, brand='Toyota',
                           model='Corolla', fuel='Dizel', mileage=10000, vehicle_group='Sedan', is_active=True),
            models.Vehicle(id='second', chassis_no='VIN2', plate='06 TEST', customer_id=1, brand='Renault',
                           model='Clio', fuel='Benzin', mileage=1000, vehicle_group='Hatchback', is_active=True),
            models.Vehicle(id='other', chassis_no='VIN3', plate='35 OTHER', customer_id=2, fuel='LPG', mileage=0, is_active=True)
        ])
        self.db.commit()
        main.app.dependency_overrides[get_db] = lambda: self.db
        self.client = ASGIClient(main.app)

    def tearDown(self):
        main.app.dependency_overrides.clear()
        self.client.close()
        self.db.close()
        self.engine.dispose()

    def purchase(self, day, vehicle='car', liters=50, amount=2500, mileage=10000, full=False, **extra):
        return main.create_vehicle_expense(VehicleExpenseCreate(vehicle_id=vehicle, kind='Yakıt', amount=amount,
            date=day, liters=liters, mileage=mileage, full_tank=full, **extra), self.db)

    def overview(self, **filters):
        response = self.client.get('/api/fuel-overview', params={'customer_id': 1, 'start_date': '2026-04-01', 'end_date': '2026-04-30', **filters})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_real_fields_detail_and_customer_scope(self):
        r = self.purchase('2026-04-05T12:15:00+03:00', station='Shell - Maslak', receipt_no='F-12', latitude=41.1, longitude=29.1)
        self.purchase('2026-04-06', vehicle='other', amount=9000)
        data = self.overview()
        self.assertEqual(data['summary']['amount'], 2500)
        self.assertEqual(data['records'][0]['receipt_no'], 'F-12')
        self.assertEqual(data['map_markers'][0]['latitude'], 41.1)
        self.assertEqual(data['records'][0]['unit_price'], 50)
        self.assertEqual({v['id'] for v in data['options']['vehicles']}, {'car', 'second'})
        response = self.client.get(f"/api/vehicle-expenses/{r['id']}", params={'customer_id': 1})
        self.assertEqual(response.json()['station'], 'Shell - Maslak')
        self.assertEqual(self.client.get(f"/api/vehicle-expenses/{r['id']}", params={'customer_id': 2}).status_code, 404)
        self.assertEqual(self.client.post('/api/vehicle-expenses?customer_id=2', json={
            'vehicle_id': 'car', 'kind': 'Yakıt', 'amount': 2000, 'date': '2026-04-02', 'mileage': 10000
        }).status_code, 404)

    def test_consumption_excludes_baseline_and_includes_partial_fills(self):
        self.purchase('2026-03-30', liters=45, mileage=10000, full=True)
        self.purchase('2026-04-10', liters=20, mileage=10200)
        self.purchase('2026-04-20', liters=30, mileage=10500, full=True)
        data = self.overview()
        self.assertAlmostEqual(data['summary']['consumption'], 10)
        self.assertEqual(data['summary']['measured_distance_km'], 500)
        self.assertEqual(data['summary']['liters'], 50)
        self.assertEqual(data['ranking'][0]['consumption'], 10)

    def test_unknown_liters_and_odometer_rollback_do_not_fabricate_consumption(self):
        self.purchase('2026-03-30', mileage=10000, full=True)
        self.purchase('2026-04-05', liters=None, mileage=10100)
        self.purchase('2026-04-20', mileage=10500, full=True)
        data = self.overview()
        self.assertIsNone(data['summary']['consumption'])
        self.assertEqual(data['summary']['missing_liters'], 1)
        self.purchase('2026-04-22', liters=20, mileage=200, full=True)
        self.assertIsNone(self.overview()['records'][0]['consumption'])

    def test_weighted_consumption_and_unit_price(self):
        self.purchase('2026-03-30', vehicle='car', mileage=10000, full=True)
        self.purchase('2026-03-30', vehicle='second', mileage=1000, full=True)
        self.purchase('2026-04-10', vehicle='car', liters=60, amount=3000, mileage=10600, full=True)
        self.purchase('2026-04-10', vehicle='second', liters=20, amount=1200, mileage=1200, full=True)
        data = self.overview()
        self.assertAlmostEqual(data['summary']['consumption'], 10)
        self.assertAlmostEqual(data['summary']['unit_price'], 52.5)
        self.assertEqual(sum(b['amount'] for b in data['chart']), 4200)
        self.assertEqual(sum(b['liters'] or 0 for b in data['breakdown']), 80)

    def test_filters_and_calendar_month_comparison(self):
        self.purchase('2026-03-01', amount=1000, liters=20, station='Shell')
        self.purchase('2026-04-01', amount=2000, liters=40, station='Shell')
        self.purchase('2026-04-30T23:59:00+03:00', amount=1000, liters=20, station='Shell')
        self.purchase('2026-05-01', amount=8000, station='Shell')
        self.purchase('2026-04-10', vehicle='second', station='Other')
        data = self.overview(vehicle_group='Sedan', fuel_type='Dizel', station='Shell', search='toyota')
        self.assertEqual(data['summary']['count'], 2)
        self.assertEqual(data['summary']['amount'], 3000)
        self.assertEqual(data['changes']['amount'], 200)
        self.assertEqual(data['period']['previous_start'], '2026-03-01')
        self.assertEqual(data['period']['previous_end'], '2026-03-31')
        self.assertEqual(self.overview(vehicle_id='second')['summary']['count'], 1)

    def test_station_insights_and_empty_state(self):
        self.purchase('2026-04-01', station='Expensive', liters=10, amount=600)
        self.purchase('2026-04-02', station='Cheap', liters=20, amount=1000)
        self.purchase('2026-04-03', station='Cheap', liters=10, amount=400)
        data = self.overview()
        self.assertEqual(data['insights']['top_station']['station'], 'Cheap')
        self.assertAlmostEqual(data['insights']['cheapest_station']['unit_price'], 1400 / 30)
        empty = self.overview(station='Missing')
        self.assertEqual(empty['records'], [])
        self.assertEqual(empty['summary']['amount'], 0)
        self.assertIsNone(empty['summary']['consumption'])
        self.assertIsNone(empty['summary']['unit_price'])
        self.assertEqual(empty['map_markers'], [])

    def test_legacy_records_and_nonfuel_expenses(self):
        self.purchase('2026-04-01', liters=None)
        self.db.add(models.VehicleExpense(vehicle_id='car', kind='Otopark', date='2026-04-02', amount=10000, mileage=10000))
        self.db.commit()
        data = self.overview()
        self.assertEqual(data['summary']['amount'], 2500)
        self.assertIsNone(data['summary']['liters'])
        self.assertEqual(data['records'][0]['fuel_type'], 'Dizel')
        self.assertEqual(data['records'][0]['station'], 'Belirtilmedi')
        self.assertFalse(data['records'][0]['full_tank'])
        self.assertEqual(data['map_markers'], [])

    def test_validation_and_mileage_history(self):
        base = {'vehicle_id': 'car', 'kind': 'Yakıt', 'amount': 2500, 'date': '2026-04-01', 'mileage': 12000, 'liters': 50}
        for invalid in ({'date': 'not a date'}, {'latitude': 41}, {'latitude': 91, 'longitude': 29}, {'amount': -1}, {'liters': 0}, {'mileage': -1}):
            self.assertEqual(self.client.post('/api/vehicle-expenses?customer_id=1', json={**base, **invalid}).status_code, 422)
        self.assertEqual(self.client.post('/api/vehicle-expenses?customer_id=1', json=base).status_code, 200)
        self.assertEqual(self.db.get(models.Vehicle, 'car').mileage, 12000)
        self.assertEqual(self.db.query(models.VehicleMileageRecord).count(), 1)
        for filters in ({'start_date': 'invalid'}, {'start_date': '2026-05-01', 'end_date': '2026-04-01'}):
            self.assertEqual(self.client.get('/api/fuel-overview', params={'customer_id': 1, **filters}).status_code, 422)

    def test_existing_database_migration_preserves_records(self):
        engine = create_engine('sqlite://', poolclass=StaticPool)
        with engine.begin() as conn:
            conn.execute(text('CREATE TABLE vehicle_expenses (id INTEGER PRIMARY KEY, vehicle_id VARCHAR, kind VARCHAR, amount FLOAT, date VARCHAR, liters FLOAT, mileage INTEGER, note TEXT)'))
            conn.execute(text("INSERT INTO vehicle_expenses VALUES (1, 'car', 'Yakıt', 2500, '2026-04-01', 50, 10000, NULL)"))
        with patch.object(init_db, 'engine', engine):
            init_db.create_tables()
            init_db.create_tables()
        with engine.connect() as conn:
            record = conn.execute(text('SELECT amount, full_tank, station FROM vehicle_expenses')).one()
            self.assertEqual(tuple(record), (2500, 0, None))
        engine.dispose()


if __name__ == '__main__':
    unittest.main()
