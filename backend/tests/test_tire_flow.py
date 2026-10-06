import datetime
import sys
import unittest
from pathlib import Path
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import main,models
from app.database import Base
from app.schemas import TireRecordCreate,RequestCreate,StatusUpdate,TireOperationCreate


class TireFlowTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db=sessionmaker(bind=self.engine,autoflush=False)()
        self.db.add_all([models.Customer(id=1,company_name='Fleet'),models.Customer(id=2,company_name='Other'),
            models.Vehicle(id='car',chassis_no='VIN1',plate='34 TEST',customer_id=1,vehicle_group='Sedan',is_active=True,mileage=10000),
            models.Vehicle(id='other',chassis_no='VIN2',plate='06 OTHER',customer_id=2,is_active=True,mileage=10000),
            models.Supplier(id=1,name='Tires',type='lastik'),models.Supplier(id=2,name='Other Tires',type='lastik'),
            models.Supplier(id=3,name='Repair',type='servis')])
        self.db.commit()
        old=(datetime.date.today()-datetime.timedelta(days=200)).isoformat()
        self.tire=main.create_tire_record(TireRecordCreate(vehicle_id='car',brand='Michelin',size='205/55 R16',changed_at=old,status='İyi',remaining_km=15000),self.db)

    def tearDown(self):
        self.db.close();self.engine.dispose()

    def request(self,operation='Rotasyon'):
        return main.create_request(RequestCreate(vehicle_id='car',type='lastik',description='Test lastik talebi',details={'tire_id':self.tire['id'],'tire_operation':operation}),self.db)

    def complete(self,request,type='Rotasyon',**extra):
        return main.complete_tire_request(request['id'],TireOperationCreate(vehicle_id='car',tire_id=self.tire['id'],supplier_id=1,type=type,date=datetime.date.today().isoformat(),**extra),self.db)

    def test_rotation_request_service_completion_resets_due_and_is_idempotent(self):
        self.assertEqual(main.get_tire_overview(1,self.db)['summary']['rotation_due'],1)
        request=self.request()
        self.assertEqual(self.db.query(models.TireOperation).count(),0)
        self.assertEqual(len(main.get_requests(supplier_id=1,db=self.db)),1)
        main.update_request_status(request['id'],StatusUpdate(supplier_id=1,status='Onaylandı'),self.db)
        operation=self.complete(request,mileage=12000)
        repeated=self.complete(request,mileage=12000)
        self.assertEqual(operation['id'],repeated['id'])
        data=main.get_tire_overview(1,self.db)
        self.assertEqual(data['summary']['rotation_due'],0)
        self.assertEqual(len(data['operations']),1)
        self.assertIsNone(data['tires'][0]['pending_request'])
        self.assertEqual(self.db.get(models.Request,request['id']).status,'Tamamlandı')
        self.assertEqual(self.db.get(models.Vehicle,'car').mileage,12000)
        self.assertEqual(self.db.get(models.Vehicle,'car').status,'Aktif')

    def test_duplicate_plan_and_direct_status_completion_are_rejected(self):
        request=self.request()
        with self.assertRaises(HTTPException) as duplicate:self.request()
        self.assertEqual(duplicate.exception.status_code,409)
        with self.assertRaises(HTTPException):main.update_request_status(request['id'],StatusUpdate(supplier_id=1,status='Tamamlandı'),self.db)
        self.assertEqual(self.db.query(models.TireOperation).count(),0)
        self.assertEqual(main.get_tire_overview(1,self.db)['tires'][0]['pending_request']['id'],request['id'])

    def test_replacement_updates_inventory_only_when_service_completes(self):
        tire=self.db.get(models.TireRecord,self.tire['id']);tire.status='Değişim Gerekli';self.db.commit()
        request=self.request('Lastik değişimi')
        self.assertEqual(main.get_tire_overview(1,self.db)['summary']['change_pending'],1)
        main.update_request_status(request['id'],StatusUpdate(supplier_id=1,status='Onaylandı'),self.db)
        self.complete(request,type='Lastik değişimi',remaining_km=40000,tread_depth_mm=8)
        data=main.get_tire_overview(1,self.db)
        self.assertEqual(data['summary']['change_pending'],0)
        self.assertEqual(data['tires'][0]['remaining_km'],40000)
        self.assertEqual(data['tires'][0]['tread_depth_mm'],8)
        self.assertEqual(data['tires'][0]['status'],'İyi')

    def test_scope_provider_and_future_date_validation(self):
        main.create_tire_record(TireRecordCreate(vehicle_id='other',brand='Other',size='225/45 R18'),self.db)
        data=main.get_tire_overview(1,self.db)
        self.assertEqual(data['summary']['total'],1)
        self.assertEqual(data['status_counts'][0]['percent'],100)
        request=self.request()
        main.update_request_status(request['id'],StatusUpdate(supplier_id=1,status='Onaylandı'),self.db)
        with self.assertRaises(HTTPException):
            main.complete_tire_request(request['id'],TireOperationCreate(vehicle_id='car',tire_id=self.tire['id'],supplier_id=2,type='Rotasyon'),self.db)
        with self.assertRaises(HTTPException):self.complete(request,type='Unknown')
        future=(datetime.date.today()+datetime.timedelta(days=1)).isoformat()
        with self.assertRaises(HTTPException):
            main.complete_tire_request(request['id'],TireOperationCreate(vehicle_id='car',tire_id=self.tire['id'],supplier_id=1,type='Rotasyon',date=future),self.db)
        self.assertEqual(self.db.query(models.TireOperation).count(),0)

    def test_new_replacement_date_takes_priority_over_old_rotation(self):
        old=(datetime.date.today()-datetime.timedelta(days=200)).isoformat()
        main.create_tire_operation(TireOperationCreate(vehicle_id='car',tire_id=self.tire['id'],type='Rotasyon',date=old),self.db)
        main.create_tire_operation(TireOperationCreate(vehicle_id='car',tire_id=self.tire['id'],type='Lastik değişimi',date=datetime.date.today().isoformat()),self.db)
        self.assertEqual(main.get_tire_overview(1,self.db)['summary']['rotation_due'],0)

if __name__=='__main__':unittest.main()
