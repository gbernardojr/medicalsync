from sqlalchemy import Column, Integer, String, Date, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Professional(Base):
    __tablename__ = "professionals"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    specialty = Column(String)
    active = Column(Boolean, default=True)
    
    appointments = relationship("Appointment", back_populates="professional")

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    phone = Column(String)
    email = Column(String, nullable=True)
    birth_date = Column(Date, nullable=True)
    notes = Column(String, nullable=True)
    
    appointments = relationship("Appointment", back_populates="patient")

class Insurance(Base):
    __tablename__ = "insurances"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    active = Column(Boolean, default=True)

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    time = Column(String, index=True)
    professional_id = Column(Integer, ForeignKey("professionals.id"))
    patient_id = Column(Integer, ForeignKey("patients.id"))
    insurance_id = Column(Integer, ForeignKey("insurances.id"), nullable=True)
    status = Column(String, default="agendado")  # agendado, aguardando, em_consulta, encerrado
    payment_method = Column(String, nullable=True)
    paid = Column(Boolean, default=False)
    amount = Column(Float, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, server_default='now()')
    
    professional = relationship("Professional", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")
    insurance = relationship("Insurance")

class CashFlow(Base):
    __tablename__ = "cash_flow"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    description = Column(String)
    amount = Column(Float)
    payment_date = Column(Date, nullable=True)
    paid = Column(Boolean, default=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    type = Column(String)  # entrada, saida