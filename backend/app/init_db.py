"""
FleetCar — SQLite Seed Data
Tabloları oluşturur ve yoksa başlangıç verilerini ekler (idempotent).
"""
from .database import engine, SessionLocal
from . import models


def create_tables():
    models.Base.metadata.create_all(bind=engine)


def seed():
    """Veritabanı tabloları oluşturulur. Test verileri eklenmez."""
    pass
