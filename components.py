import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd

def date_selector(default_date=None):
    if default_date is None:
        default_date = datetime.now().date()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("◀️"):
            default_date -= timedelta(days=1)
    with col2:
        selected_date = st.date_input("Data", value=default_date, label_visibility="collapsed")
    with col3:
        if st.button("▶️"):
            selected_date += timedelta(days=1)
    
    return selected_date

def professional_selector(db, selected_professional=None):
    from .queries import get_professionals
    professionals = get_professionals(db)
    professional_names = [p.name for p in professionals]
    
    if selected_professional and selected_professional in professional_names:
        default_index = professional_names.index(selected_professional)
    else:
        default_index = 0
    
    selected = st.selectbox(
        "Profissional",
        professional_names,
        index=default_index,
        key="professional_selector"
    )
    return selected

def schedule_grid(db, date, professional_name):
    from .queries import get_appointments_by_date_and_professional
    
    appointments = get_appointments_by_date_and_professional(db, date, professional_name)
    appointments_dict = {app.time: app for app in appointments}
    
    # Criar grade de horários
    time_slots = [
        "08:00", "08:30", "09:00", "09:30", "10:00", "10:30",
        "11:00", "11:30", "12:00", "13:30", "14:00", "14:30",
        "15:00", "15:30", "16:00", "16:30", "17:00", "17:30"
    ]
    
    data = []
    for time in time_slots:
        if time in appointments_dict:
            app = appointments_dict[time]
            data.append({
                "Horário": time,
                "Paciente": app.patient.name,
                "Convênio": app.insurance.name if app.insurance else "Particular",
                "Status": app.status,
                "Pago": "✅" if app.paid else "❌"
            })
        else:
            data.append({
                "Horário": time,
                "Paciente": "Disponível",
                "Convênio": "",
                "Status": "",
                "Pago": ""
            })
    
    df = pd.DataFrame(data)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Horário": st.column_config.TextColumn("Horário", width="small"),
            "Paciente": st.column_config.TextColumn("Paciente"),
            "Convênio": st.column_config.TextColumn("Convênio", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Pago": st.column_config.TextColumn("Pago", width="small")
        }
    )
    
    return df, appointments_dict