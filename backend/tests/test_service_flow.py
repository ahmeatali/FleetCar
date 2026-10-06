import datetime
import sys
import unittest
from pathlib import Path
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import main, models
from app.database import Base
from app.schemas import RequestCreate, StatusUpdate, ServiceCheckIn, ServiceWorkOrder, ServiceInvoice


class ServiceFlowTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread':False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine, autoflush=False)()
        due = (datetime.date.today()+datetime.timedelta(days=10)).isoformat()
        self.db.add_all([models.Customer(id=1,company_name='Fleet'), models.Customer(id=2,company_name='Other'),
            models.Vehicle(id='car',chassis_no='VIN1',plate='34 TEST',customer_id=1,mileage=10000,is_active=True,vehicle_group='Sedan',next_service_due_date=due),
            models.Vehicle(id='other',chassis_no='VIN2',plate='06 OTHER',customer_id=2,is_active=True),
            models.Vehicle(id='inactive',chassis_no='VIN3',plate='34 OLD',customer_id=1,is_active=False,next_service_due_date=due),
            models.Supplier(id=1,name='Repair',type='servis'),models.Supplier(id=2,name='Another Repair',type='servis'),
            models.Supplier(id=3,name='Roadside',type='yol_yardim')])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def create(self,service_type='Periyodik Bakım',vehicle='car'):
        return main.create_request(RequestCreate(vehicle_id=vehicle,type='servis',description=service_type,details={'service_type':service_type}),self.db)

    def test_unassigned_service_claim_and_lifecycle_reaches_customer(self):
        request=self.create('Hasar / Kaza'); rid=request['id']
        self.assertTrue(request['details']['work_order_no'].startswith('HS-'))
        self.assertEqual(len(main.get_requests(supplier_id=1,db=self.db)),1)
        self.assertEqual(main.get_requests(supplier_id=3,db=self.db),[])
        main.update_request_status(rid,StatusUpdate(supplier_id=1,status='Onaylandı'),self.db)
        self.assertEqual(main.get_requests(supplier_id=2,db=self.db),[])
        main.service_checkin(rid,ServiceCheckIn(supplier_id=1,entry_mileage=12000,fuel_level='%50',driver_name='Driver'),self.db)
        main.service_work_order(rid,ServiceWorkOrder(supplier_id=1,diagnosis_notes='Tampon değişecek',parts_list=[{'part_name':'Tampon','quantity':1,'unit_price':2000}],labor_cost=1000,total_estimated_cost=3000),self.db)
        main.service_invoice(rid,ServiceInvoice(supplier_id=1,invoice_no='INV-1',invoice_date=datetime.date.today().isoformat(),invoice_amount=3500),self.db)
        main.update_request_status(rid,StatusUpdate(supplier_id=1,status='Tamamlandı'),self.db)
        data=main.get_service_overview(1,self.db)
        self.assertEqual(data['summary']['damage'],1)
        self.assertEqual(data['summary']['open_work_orders'],0)
        self.assertEqual(data['records'][0]['amount'],3500)
        self.assertEqual(data['records'][0]['supplier_name'],'Repair')
        self.assertEqual(data['records'][0]['details']['diagnosis_notes'],'Tampon değişecek')
        self.assertEqual(len(data['records'][0]['details']['service_history']),6)
        self.assertEqual(self.db.get(models.Vehicle,'car').mileage,12000)
        self.assertEqual(self.db.get(models.Vehicle,'car').status,'Aktif')

    def test_claim_conflict_and_wrong_provider_cannot_write(self):
        rid=self.create()['id']
        main.update_request_status(rid,StatusUpdate(supplier_id=1,status='Onaylandı'),self.db)
        with self.assertRaises(HTTPException) as conflict:
            main.service_work_order(rid,ServiceWorkOrder(supplier_id=2,diagnosis_notes='Wrong'),self.db)
        self.assertEqual(conflict.exception.status_code,409)
        with self.assertRaises(HTTPException):
            main.update_request_status(rid,StatusUpdate(supplier_id=3,status='Onaylandı'),self.db)
        self.assertNotIn('diagnosis_notes',self.db.get(models.Request,rid).details)

    def test_due_vehicles_exist_without_requests_and_exclude_inactive(self):
        data=main.get_service_overview(1,self.db)
        self.assertEqual(data['records'],[])
        self.assertEqual(data['summary']['due_vehicles'],1)
        self.assertEqual(data['due_vehicles'][0]['days_until_service'],10)
        self.assertEqual(data['due_vehicles'][0]['id'],'car')

    def test_customer_scope_classification_and_zero_invoice(self):
        rid=self.create()['id'];self.create('Ekspertiz');self.create('Hasar / Kaza');self.create(vehicle='other')
        main.service_work_order(rid,ServiceWorkOrder(total_estimated_cost=1000),self.db)
        main.service_invoice(rid,ServiceInvoice(invoice_no='Free',invoice_date='2026-10-07',invoice_amount=0),self.db)
        data=main.get_service_overview(1,self.db)
        self.assertEqual(data['summary']['tabs']['all'],3)
        self.assertEqual(data['summary']['service'],1)
        self.assertEqual(data['summary']['damage'],1)
        self.assertEqual(data['summary']['tabs']['expertise'],1)
        record=next(r for r in data['records'] if r['id']==rid)
        self.assertEqual(record['amount'],0)
        self.assertEqual(record['amount_source'],'Fatura')

    def test_reopening_clears_completion_and_sets_vehicle_status(self):
        rid=self.create()['id']
        main.update_request_status(rid,StatusUpdate(status='Tamamlandı',supplier_id=1),self.db)
        main.update_request_status(rid,StatusUpdate(status='Onarımda',supplier_id=1),self.db)
        self.assertIsNone(self.db.get(models.Request,rid).completed_at)
        self.assertEqual(self.db.get(models.Vehicle,'car').status,'Serviste')

if __name__=='__main__':
    unittest.main()
