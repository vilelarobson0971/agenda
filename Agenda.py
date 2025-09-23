import streamlit as st
import pandas as pd
import datetime
import calendar
from datetime import date
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ---------------- CONFIGURAÇÃO GOOGLE SHEETS ---------------- #
SHEET_ID = "COLOQUE_SEU_ID_AQUI"  # <-- troque pelo ID da sua planilha
SHEET_NAME = "Página1"            # nome da aba da planilha

# Autenticação com o arquivo JSON (credenciais da service account)
@st.cache_resource
def conectar_sheets():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json", scope)
    cliente = gspread.authorize(creds)
    planilha = cliente.open_by_key(SHEET_ID)
    aba = planilha.worksheet(SHEET_NAME)
    return aba

def carregar_dados():
    aba = conectar_sheets()
    dados = aba.get_all_records()
    if not dados:
        return pd.DataFrame(columns=["data", "banda", "horario"])
    df = pd.DataFrame(dados)
    df["data"] = pd.to_datetime(df["data"]).dt.date
    return df

def salvar_dados(df):
    aba = conectar_sheets()
    aba.clear()
    aba.update([df.columns.values.tolist()] + df.astype(str).values.tolist())
    st.success("✅ Agendamento salvo no Google Sheets com sucesso!")

# ---------------- CONFIGURAÇÃO DA PÁGINA ---------------- #
st.set_page_config(page_title="Agenda de Ensaios", page_icon="🎵", layout="wide")

CORES_BANDAS = {
    'D1': '#FF6B6B',
    'D2': '#4ECDC4',
    'D3': '#45B7D1',
    'D4': '#96CEB4',
    'S1': '#FFEAA7',
    'S2': '#DDA0DD'
}

NOMES_BANDAS = {
    'D1': 'Banda D1',
    'D2': 'Banda D2', 
    'D3': 'Banda D3',
    'D4': 'Banda D4',
    'S1': 'Banda S1',
    'S2': 'Banda S2'
}

# ---------------- INTERFACE PRINCIPAL ---------------- #
st.title("🎵 Agenda de Ensaios de Bandas")
st.markdown("---")

df_agenda = carregar_dados()

hoje = date.today()
mes_atual = st.sidebar.selectbox("Mês", range(1, 13), index=hoje.month-1)
ano_atual = st.sidebar.selectbox("Ano", range(2023, 2031), index=hoje.year-2023)

# Novo agendamento
st.sidebar.header("📅 Novo Agendamento")

with st.sidebar.form("novo_agendamento", clear_on_submit=True):
    data_agendamento = st.date_input("Data do ensaio", min_value=hoje)
    banda_selecionada = st.selectbox("Banda", list(NOMES_BANDAS.keys()), 
                                   format_func=lambda x: f"{x} - {NOMES_BANDAS[x]}")
    horario_agendamento = st.time_input("Horário de início", value=datetime.time(19, 0))
    
    submitted = st.form_submit_button("Agendar Ensaio")
    
    if submitted:
        if not df_agenda.empty:
            agendamento_existente = df_agenda[df_agenda['data'] == data_agendamento]
        else:
            agendamento_existente = pd.DataFrame()
        
        if not agendamento_existente.empty:
            st.sidebar.error(f"❌ Já existe um agendamento para {data_agendamento.strftime('%d/%m/%Y')}")
        else:
            novo_agendamento = pd.DataFrame({
                'data': [data_agendamento],
                'banda': [banda_selecionada],
                'horario': [horario_agendamento.strftime('%H:%M')]
            })
            
            df_agenda = pd.concat([df_agenda, novo_agendamento], ignore_index=True)
            salvar_dados(df_agenda)
            st.rerun()

# ---------------- RESTANTE DO CÓDIGO (calendário, legendas, lista etc.) ---------------- #
