import streamlit as st
import pandas as pd
from datetime import date, datetime
from database import get_db
from models import Base
from components import date_selector, professional_selector, schedule_grid
from commands import (
    create_professional, create_patient, create_insurance, create_appointment,
    update_appointment_status, mark_payment
)
from queries import (
    get_professionals, get_patients, get_insurances,
    get_appointments_by_date_and_professional, get_cash_flow
)
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import sys

# Carrega variáveis de ambiente
load_dotenv()

# Configuração inicial
st.set_page_config(page_title="Agenda Médica", layout="wide", page_icon="🩺")

# Configuração do banco de dados com verificação
required_env_vars = ['DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DB_NAME']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]

if missing_vars:
    st.error(f"Erro crítico: Variáveis de ambiente ausentes no arquivo .env: {', '.join(missing_vars)}")
    st.stop()

try:
    DATABASE_URL = (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20, connect_args={
        'sslmode': 'prefer',
        'client_encoding': 'utf8',
        'options': '-c client_encoding=utf8'        
    })
    #'sslrootcert': '/AIVEN/ca.pem'  # Importante para Aiven
    
    
    # Testa a conexão
    with engine.connect() as conn:
        conn.execute("SELECT 1")
        
except Exception as e:
    st.error(f"Falha ao conectar ao banco de dados: {str(e)}")
    st.stop()

# Inicialização do banco de dados
#engine = create_engine("postgresql://user:password@host:port/dbname")
Base.metadata.create_all(bind=engine)

# Cache para melhorar performance
@st.cache_data(ttl=300)
def load_professionals(db):
    return get_professionals(db)

@st.cache_data(ttl=300)
def load_patients(db, search=None):
    return get_patients(db, search)

@st.cache_data(ttl=300)
def load_insurances(db):
    return get_insurances(db)

def appointment_form(db, date, time, professional_id, appointment=None):
    with st.form(key="appointment_form"):
        patients = load_patients(db)
        patient_names = [p.name for p in patients]
        
        insurances = load_insurances(db)
        insurance_names = [i.name for i in insurances]
        insurance_names.insert(0, "Particular")
        
        status_options = ["agendado", "aguardando", "em_consulta", "encerrado"]
        payment_methods = ["Dinheiro", "Cartão Débito", "Cartão Crédito", "PIX", "Transferência"]
        
        if appointment:
            default_patient_index = patient_names.index(appointment.patient.name) if appointment.patient.name in patient_names else 0
            default_insurance_index = insurance_names.index(appointment.insurance.name) if appointment.insurance and appointment.insurance.name in insurance_names else 0
            default_status_index = status_options.index(appointment.status) if appointment.status in status_options else 0
            default_payment_method_index = payment_methods.index(appointment.payment_method) if appointment.payment_method in payment_methods else 0
            default_amount = appointment.amount or 0
            default_paid = appointment.paid
            default_notes = appointment.notes or ""
        else:
            default_patient_index = 0
            default_insurance_index = 0
            default_status_index = 0
            default_payment_method_index = 0
            default_amount = 0
            default_paid = False
            default_notes = ""
        
        col1, col2 = st.columns(2)
        with col1:
            selected_patient = st.selectbox("Paciente", patient_names, index=default_patient_index)
            selected_insurance = st.selectbox("Convênio", insurance_names, index=default_insurance_index)
            status = st.selectbox("Status", status_options, index=default_status_index)
        with col2:
            payment_method = st.selectbox("Forma de Pagamento", payment_methods, index=default_payment_method_index)
            amount = st.number_input("Valor (R$)", value=default_amount, min_value=0.0, step=50.0)
            paid = st.checkbox("Pago", value=default_paid)
        
        notes = st.text_area("Observações", value=default_notes)
        
        submitted = st.form_submit_button("Salvar Consulta")
        
        if submitted:
            patient_id = patients[patient_names.index(selected_patient)].id
            insurance_id = None if selected_insurance == "Particular" else insurances[insurance_names.index(selected_insurance)-1].id
            
            if appointment:
                # Atualizar consulta existente
                appointment.patient_id = patient_id
                appointment.insurance_id = insurance_id
                appointment.status = status
                appointment.payment_method = payment_method
                appointment.amount = amount if insurance_id is None else None
                appointment.paid = paid
                appointment.notes = notes
                db.commit()
                st.success("Consulta atualizada com sucesso!")
            else:
                # Criar nova consulta
                create_appointment(
                    db=db,
                    date=date,
                    time=time,
                    professional_id=professional_id,
                    patient_id=patient_id,
                    insurance_id=insurance_id,
                    status=status,
                    payment_method=payment_method,
                    amount=amount if insurance_id is None else None,
                    notes=notes
                )
                st.success("Consulta agendada com sucesso!")
            st.experimental_rerun()

def patient_registration(db):
    with st.form(key="patient_form"):
        name = st.text_input("Nome completo*")
        phone = st.text_input("Celular*")
        email = st.text_input("E-mail")
        birth_date = st.date_input("Data de Nascimento", max_value=date.today())
        notes = st.text_area("Observações")
        
        submitted = st.form_submit_button("Cadastrar Paciente")
        
        if submitted:
            if not name or not phone:
                st.error("Nome e celular são obrigatórios!")
            else:
                create_patient(
                    db=db,
                    name=name,
                    phone=phone,
                    email=email if email else None,
                    birth_date=birth_date,
                    notes=notes if notes else None
                )
                st.success("Paciente cadastrado com sucesso!")
                st.experimental_rerun()

def insurance_registration(db):
    with st.form(key="insurance_form"):
        name = st.text_input("Nome do Convênio*")
        
        submitted = st.form_submit_button("Cadastrar Convênio")
        
        if submitted:
            if not name:
                st.error("Nome do convênio é obrigatório!")
            else:
                create_insurance(db, name)
                st.success("Convênio cadastrado com sucesso!")
                st.experimental_rerun()

def professional_registration(db):
    with st.form(key="professional_form"):
        name = st.text_input("Nome do Profissional*")
        specialty = st.text_input("Especialidade*")
        
        submitted = st.form_submit_button("Cadastrar Profissional")
        
        if submitted:
            if not name or not specialty:
                st.error("Nome e especialidade são obrigatórios!")
            else:
                create_professional(db, name, specialty)
                st.success("Profissional cadastrado com sucesso!")
                st.experimental_rerun()

def cash_flow_report(db):
    st.subheader("Controle de Caixa")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Data Inicial", value=date.today().replace(day=1))
    with col2:
        end_date = st.date_input("Data Final", value=date.today())
    
    cash_flow = get_cash_flow(db, start_date, end_date)
    
    if cash_flow:
        data = []
        for item in cash_flow:
            data.append({
                "Data": item.date,
                "Descrição": item.description,
                "Valor (R$)": item.amount,
                "Pago": "✅" if item.paid else "❌",
                "Data Pagamento": item.payment_date
            })
        
        df = pd.DataFrame(data)
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "Valor (R$)": st.column_config.NumberColumn(format="R$ %.2f")
            }
        )
        
        total = sum(item.amount for item in cash_flow)
        paid = sum(item.amount for item in cash_flow if item.paid)
        pending = total - paid
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total", f"R$ {total:,.2f}")
        col2.metric("Recebido", f"R$ {paid:,.2f}")
        col3.metric("Pendente", f"R$ {pending:,.2f}", delta_color="inverse")
    else:
        st.info("Nenhum registro encontrado no período selecionado.")

def main():
    db = next(get_db())
    
    st.title("🩺 Agenda Médica")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Agenda", "Pacientes", "Convênios", "Profissionais", "Caixa"])
    
    with tab1:
        selected_date = date_selector()
        selected_professional = professional_selector(db)
        
        professional = next((p for p in load_professionals(db) if p.name == selected_professional), None)
        
        if professional:
            df, appointments_dict = schedule_grid(db, selected_date, professional.name)
            
            selected_time = st.selectbox("Selecione um horário", df["Horário"].tolist())
            
            if selected_time:
                if selected_time in appointments_dict:
                    appointment = appointments_dict[selected_time]
                    st.subheader(f"Consulta: {selected_time} - {appointment.patient.name}")
                    
                    appointment_form(
                        db=db,
                        date=selected_date,
                        time=selected_time,
                        professional_id=professional.id,
                        appointment=appointment
                    )
                    
                    if st.button("Cancelar Consulta", type="secondary"):
                        db.delete(appointment)
                        db.commit()
                        st.success("Consulta cancelada com sucesso!")
                        st.experimental_rerun()
                else:
                    st.subheader(f"Nova Consulta: {selected_time}")
                    appointment_form(
                        db=db,
                        date=selected_date,
                        time=selected_time,
                        professional_id=professional.id
                    )
    
    with tab2:
        st.subheader("Cadastro de Pacientes")
        
        search_term = st.text_input("Buscar Paciente")
        patients = load_patients(db, search_term if search_term else None)
        
        if patients:
            for patient in patients:
                with st.expander(f"{patient.name} - {patient.phone}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**E-mail:** {patient.email or 'Não informado'}")
                        st.write(f"**Data Nasc.:** {patient.birth_date.strftime('%d/%m/%Y') if patient.birth_date else 'Não informada'}")
                    with col2:
                        st.write(f"**Observações:** {patient.notes or 'Nenhuma'}")
        else:
            st.info("Nenhum paciente encontrado.")
        
        st.divider()
        patient_registration(db)
    
    with tab3:
        st.subheader("Cadastro de Convênios")
        insurances = load_insurances(db)
        
        if insurances:
            st.write("Convênios cadastrados:")
            cols = st.columns(4)
            for i, insurance in enumerate(insurances):
                cols[i % 4].write(f"- {insurance.name}")
        else:
            st.info("Nenhum convênio cadastrado.")
        
        st.divider()
        insurance_registration(db)
    
    with tab4:
        st.subheader("Cadastro de Profissionais")
        professionals = load_professionals(db)
        
        if professionals:
            st.write("Profissionais cadastrados:")
            cols = st.columns(3)
            for i, professional in enumerate(professionals):
                cols[i % 3].write(f"- {professional.name} ({professional.specialty})")
        else:
            st.info("Nenhum profissional cadastrado.")
        
        st.divider()
        professional_registration(db)
    
    with tab5:
        cash_flow_report(db)

if __name__ == "__main__":
    main()