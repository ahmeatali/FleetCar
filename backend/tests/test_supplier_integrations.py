import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi import HTTPException
from test_supplier_workspace import SupplierWorkspaceTests

from app import models as m
from app.supplier_integrations import ArventoConfig, GpsPoint, ingest, normalize


class SupplierIntegrationTests(unittest.TestCase):
    setUp = SupplierWorkspaceTests.setUp
    tearDown = SupplierWorkspaceTests.tearDown

    # Reuse the isolated company/session fixture without inheriting its test methods.
    def point(self, **kwargs):
        return GpsPoint(
            device_id="device-1",
            occurred_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            latitude=41.01,
            longitude=29.01,
            mileage=11000,
            **kwargs,
        )

    def mapping(self, vid="car", device="device-1"):
        return self.client.put(
            "/api/supplier-workspace/integrations/arvento/mappings",
            {"vehicle_id": vid, "external_id": device},
        )

    def test_xml_column_mapping_units_and_entity_rejection(self):
        cfg = ArventoConfig(
            device_column="Node",
            time_column="At",
            latitude_column="Lat",
            longitude_column="Lon",
            mileage_column="Odometer",
            mileage_unit="m",
        )
        points = normalize(
            b"<DataSet><NewDataSet><Table><Node>device-1</Node><At>2026-01-01T12:00:00</At><Lat>41.0</Lat><Lon>29.0</Lon><Odometer>11000234</Odometer></Table></NewDataSet></DataSet>",
            cfg,
        )
        self.assertEqual(points[0].mileage, 11000)
        self.assertEqual(points[0].occurred_at.hour, 9)
        with self.assertRaises(ValueError):
            normalize(b'<!DOCTYPE x [<!ENTITY p "x">]><x>&p;</x>', cfg)
        with self.assertRaises(ValueError):
            normalize('<!DOCTYPE x [<!ENTITY p "x">]><x>&p;</x>'.encode("utf-16"), cfg)
        with self.assertRaises(ValueError):
            normalize(b"<DataSet/>", cfg)

    def test_ingestion_atomic_replay_and_mileage_history(self):
        self.assertEqual(self.mapping().status_code, 200)
        from app.supplier_operations import context

        ctx = context("Bearer " + self.token, self.db)
        point = self.point()
        self.assertEqual(ingest(self.db, ctx, [point])["processed"], 1)
        self.db.commit()
        self.assertEqual(self.db.get(m.Vehicle, "car").mileage, 11000)
        self.assertEqual(self.db.get(m.Vehicle, "car").gps_latitude, 41.01)
        self.assertEqual(
            self.db.get(m.Vehicle, "car").gps_last_seen_at, point.occurred_at.isoformat()
        )
        self.assertEqual(ingest(self.db, ctx, [point])["duplicate"], 1)
        self.db.commit()
        self.assertEqual(self.db.query(m.VehicleLocation).count(), 1)
        self.assertEqual(self.db.query(m.VehicleMileageRecord).count(), 1)
        modified = point.model_copy(update={"mileage": 12000})
        with self.assertRaises(HTTPException) as caught:
            ingest(self.db, ctx, [modified])
        self.db.rollback()
        self.assertEqual(caught.exception.status_code, 409)
        self.assertEqual(self.db.get(m.Vehicle, "car").mileage, 11000)

    def test_unmatched_retry_stale_and_decreasing_km(self):
        from app.supplier_operations import context

        ctx = context("Bearer " + self.token, self.db)
        point = self.point()
        self.assertEqual(ingest(self.db, ctx, [point])["pending"], 1)
        self.db.commit()
        eid = self.db.query(m.IntegrationEvent).first().id
        self.assertEqual(self.db.query(m.VehicleLocation).count(), 0)
        self.mapping()
        response = self.client.post(
            f"/api/supplier-workspace/integrations/arvento/events/{eid}/retry"
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.db.query(m.VehicleLocation).count(), 1)
        self.assertEqual(
            self.client.post(
                f"/api/supplier-workspace/integrations/arvento/events/{eid}/retry"
            ).status_code,
            409,
        )
        stale = point.model_copy(
            update={"occurred_at": point.occurred_at - timedelta(minutes=1), "mileage": 13000}
        )
        self.assertEqual(ingest(self.db, ctx, [stale])["stale"], 1)
        lower = point.model_copy(
            update={"occurred_at": point.occurred_at + timedelta(seconds=1), "mileage": 9000}
        )
        self.assertEqual(ingest(self.db, ctx, [lower])["pending"], 1)
        self.db.commit()
        self.assertEqual(self.db.get(m.Vehicle, "car").mileage, 11000)
        self.assertEqual(self.db.query(m.VehicleLocation).count(), 1)

    def test_tenant_roles_and_stable_device_identity(self):
        self.assertEqual(self.mapping("other").status_code, 404)
        self.assertEqual(self.mapping().status_code, 200)
        self.assertEqual(self.mapping("car2").status_code, 409)
        self.assertEqual(self.mapping("car", "device-2").status_code, 409)
        response = self.client.put(
            "/api/supplier-workspace/integrations/arvento/mappings",
            {"vehicle_id": "car2", "external_id": "new"},
            self.viewer_token,
        )
        self.assertEqual(response.status_code, 403)
        from app.supplier_operations import context

        ctx = context("Bearer " + self.token, self.db)
        ingest(self.db, ctx, [self.point()])
        self.db.commit()
        self.assertEqual(
            self.client.get(
                "/api/supplier-workspace/integrations/arvento", self.other_token
            ).json()["events"],
            [],
        )
        eid = self.db.query(m.IntegrationEvent).first().id
        self.assertEqual(
            self.client.post(
                f"/api/supplier-workspace/integrations/arvento/events/{eid}/retry",
                token=self.other_token,
            ).status_code,
            404,
        )

    def test_sync_validation_configuration_and_batch_rollback(self):
        cfg = {
            "device_column": "Node",
            "time_column": "At",
            "latitude_column": "Lat",
            "longitude_column": "Lon",
        }
        response = self.client.put("/api/supplier-workspace/integrations/arvento/config", cfg)
        self.assertEqual(response.status_code, 200, response.text)
        with patch.dict(os.environ, {}, clear=True):
            response = self.client.post("/api/supplier-workspace/integrations/arvento/sync")
        self.assertEqual(response.status_code, 503)
        self.mapping()
        when = (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()
        raw = f"<DataSet><Table><Node>device-1</Node><At>{when}</At><Lat>41</Lat><Lon>29</Lon></Table><Table><Node>device-1</Node><At>{when}</At><Lat>40</Lat><Lon>29</Lon></Table></DataSet>".encode()
        with patch("app.supplier_integrations.fetch_arvento", return_value=raw):
            response = self.client.post("/api/supplier-workspace/integrations/arvento/sync")
        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(self.db.query(m.VehicleLocation).count(), 0)
        self.assertEqual(self.db.query(m.IntegrationEvent).count(), 0)
        settings = self.client.get("/api/supplier-workspace/settings").json()
        self.assertEqual(
            self.client.put("/api/supplier-workspace/settings", settings).status_code, 200
        )
        self.assertEqual(
            self.client.get("/api/supplier-workspace/integrations/arvento").json()["config"][
                "device_column"
            ],
            "Node",
        )


# Only execute new integration cases; imported workflow cases already have their own module.
del SupplierWorkspaceTests
