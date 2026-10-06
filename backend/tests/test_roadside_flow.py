import sys
import unittest
from pathlib import Path
import datetime

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import main, models
from app.database import Base
from app.schemas import RoadsideCaseCreate, RoadsideCaseUpdate, StatusUpdate


class RoadsideFlowTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine, autoflush=False)()
        self.db.add_all([models.Customer(id=1, company_name='Fleet'), models.Customer(id=2, company_name='Other'),
            models.Vehicle(id='car', chassis_no='VIN1', plate='34 TEST', customer_id=1, brand='Toyota', vehicle_group='Sedan', is_active=True),
            models.Vehicle(id='other', chassis_no='VIN2', plate='06 OTHER', customer_id=2, is_active=True),
            models.Supplier(id=1, name='Roadside', type='yol_yardim'),
            models.Supplier(id=2, name='Other Roadside', type='yol_yardim'),
            models.Supplier(id=3, name='Repair', type='servis')])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def create(self, vehicle='car'):
        return main.create_roadside_case(RoadsideCaseCreate(vehicle_id=vehicle, incident='Akü bitti', latitude=41, longitude=29), self.db)

    def test_customer_service_end_to_end(self):
        case = self.create()
        request_id = case['request_id']
        self.assertEqual(len(main.get_requests(supplier_id=1, db=self.db)), 1)
        self.assertEqual(len(main.get_requests(supplier_id=3, db=self.db)), 0)
        main.update_request_status(request_id, StatusUpdate(status='Ekip Atandı', supplier_id=1, team_name='Team', team_phone='555'), self.db)
        self.assertEqual(main.get_roadside_case(case['id'], self.db)['team_name'], 'Team')
        self.assertEqual(main.get_requests(supplier_id=2, db=self.db), [])
        with self.assertRaises(HTTPException) as conflict:
            main.update_request_status(request_id, StatusUpdate(status='Yolda', supplier_id=2), self.db)
        self.assertEqual(conflict.exception.status_code, 409)
        main.update_request_status(request_id, StatusUpdate(status='Yolda', supplier_id=1, eta_minutes=12, distance_km=5.2), self.db)
        overview = main.get_roadside_overview(1, self.db)
        self.assertEqual(overview['summary']['active'], 1)
        self.assertEqual(overview['cases'][0]['progress'], 60)
        self.assertEqual(overview['cases'][0]['eta_minutes'], 12)
        self.assertEqual(overview['cases'][0]['vehicle_group'], 'Sedan')
        main.update_request_status(request_id, StatusUpdate(status='Çözüldü', supplier_id=1), self.db)
        self.assertEqual(main.get_roadside_overview(1, self.db)['summary']['resolved'], 1)
        self.assertEqual(self.db.get(models.Vehicle, 'car').status, 'Aktif')
        self.assertIsNotNone(self.db.get(models.Request, request_id).completed_at)
        self.assertEqual(len(main.get_roadside_events(case['id'], self.db)), 4)

    def test_customer_location_is_visible_to_service(self):
        case = self.create()
        main.update_roadside_case(case['id'], RoadsideCaseUpdate(latitude=40.5, longitude=28.5), self.db)
        request = main.get_requests(supplier_id=1, db=self.db)[0]
        self.assertEqual(request['details']['latitude'], 40.5)
        self.assertEqual(self.db.get(models.Vehicle, 'car').gps_longitude, 28.5)
        self.assertEqual(self.db.query(models.VehicleLocation).count(), 2)

    def test_summary_is_scoped_and_recent_filter_is_reversible(self):
        case = self.create()
        self.create('other')
        row = self.db.get(models.RoadsideCase, case['id'])
        row.created_at = (datetime.datetime.now() - datetime.timedelta(days=10)).strftime('%Y-%m-%d %H:%M')
        self.db.commit()
        data = main.get_roadside_overview(1, self.db)
        self.assertEqual(data['summary']['total'], 1)
        self.assertEqual(data['last_seven_days']['total'], 0)
        self.assertEqual(data['recent_case_ids'], [])

    def test_invalid_dispatch_data_does_not_mutate_case(self):
        case = self.create()
        with self.assertRaises(ValidationError):
            StatusUpdate(status='Yolda', eta_minutes=-1)
        with self.assertRaises(HTTPException):
            main.update_request_status(case['request_id'], StatusUpdate(status='Unknown', supplier_id=1), self.db)
        with self.assertRaises(HTTPException):
            main.update_request_status(case['request_id'], StatusUpdate(status='Ekip Atandı', supplier_id=3), self.db)
        self.assertEqual(self.db.get(models.Request, case['request_id']).status, 'Beklemede')

    def test_finishing_preserves_other_vehicle_operations(self):
        case = self.create()
        self.db.add(models.Request(vehicle_id='car', type='servis', status='İşlemde'))
        self.db.commit()
        main.update_request_status(case['request_id'], StatusUpdate(status='Çözüldü', supplier_id=1), self.db)
        self.assertEqual(self.db.get(models.Vehicle, 'car').status, 'Serviste')

if __name__ == '__main__':
    unittest.main()
