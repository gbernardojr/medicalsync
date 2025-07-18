from sqlalchemy.orm import Session
from models import Professional, Patient, Insurance, Appointment, CashFlow
from datetime import date

def get_professionals(db: Session):
    return db.query(Professional).filter(Professional.active == True).order_by(Professional.name).all()

def get_patients(db: Session, search: str = None):
    query = db.query(Patient)
    if search:
        query = query.filter(Patient.name.ilike(f"%{search}%"))
    return query.order_by(Patient.name).all()

def get_insurances(db: Session):
    return db.query(Insurance).filter(Insurance.active == True).order_by(Insurance.name).all()

def get_appointments_by_date_and_professional(db: Session, date: date, professional_name: str):
    return (
        db.query(Appointment)
        .join(Appointment.professional)
        .filter(Appointment.date == date)
        .filter(Professional.name == professional_name)
        .order_by(Appointment.time)
        .all()
    )

def get_cash_flow(db: Session, start_date: date, end_date: date):
    return (
        db.query(CashFlow)
        .filter(CashFlow.date >= start_date)
        .filter(CashFlow.date <= end_date)
        .order_by(CashFlow.date)
        .all()
    )