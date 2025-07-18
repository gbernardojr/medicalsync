from sqlalchemy.orm import Session
from models import Professional, Patient, Insurance, Appointment, CashFlow
from datetime import date

def create_professional(db: Session, name: str, specialty: str):
    professional = Professional(name=name, specialty=specialty)
    db.add(professional)
    db.commit()
    db.refresh(professional)
    return professional

def create_patient(db: Session, name: str, phone: str, email: str = None, birth_date: date = None, notes: str = None):
    patient = Patient(
        name=name,
        phone=phone,
        email=email,
        birth_date=birth_date,
        notes=notes
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient

def create_insurance(db: Session, name: str):
    insurance = Insurance(name=name)
    db.add(insurance)
    db.commit()
    db.refresh(insurance)
    return insurance

def create_appointment(
    db: Session,
    date: date,
    time: str,
    professional_id: int,
    patient_id: int,
    insurance_id: int = None,
    status: str = "agendado",
    payment_method: str = None,
    amount: float = None,
    notes: str = None
):
    appointment = Appointment(
        date=date,
        time=time,
        professional_id=professional_id,
        patient_id=patient_id,
        insurance_id=insurance_id,
        status=status,
        payment_method=payment_method,
        amount=amount,
        notes=notes
    )
    db.add(appointment)
    
    # Se for particular, cria registro no caixa
    if insurance_id is None and amount:
        cash_flow = CashFlow(
            date=date,
            description=f"Consulta {patient_id} - {time}",
            amount=amount,
            paid=False,
            appointment_id=appointment.id,
            type="entrada"
        )
        db.add(cash_flow)
    
    db.commit()
    db.refresh(appointment)
    return appointment

def update_appointment_status(db: Session, appointment_id: int, status: str):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if appointment:
        appointment.status = status
        db.commit()
        db.refresh(appointment)
    return appointment

def mark_payment(db: Session, appointment_id: int, paid: bool):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if appointment:
        appointment.paid = paid
        if paid and not appointment.insurance_id:
            # Atualiza o caixa
            cash_flow = (
                db.query(CashFlow)
                .filter(CashFlow.appointment_id == appointment_id)
                .first()
            )
            if cash_flow:
                cash_flow.paid = True
                cash_flow.payment_date = date.today()
        db.commit()
        db.refresh(appointment)
    return appointment