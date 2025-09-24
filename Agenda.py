import streamlit as st
import pandas as pd
import datetime
import calendar
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
import json

# Configuração da página
st.set_page_config(
    page_title="Agenda de Ensaios", 
    page_icon="🎵", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Cores das bandas
CORES_BANDAS = {
    'D1': '#FF6B6B',  # Vermelho
    'D2': '#FFEAA7',  # Amarelo
    'D3': '#45B7D1',  # Azul
    'D4': '#DDA0DD',  # Roxo
    'S1': '#2E8B57',  # Verde escuro
    'S2': '#FF8C00',  # Laranja
    'POD': '#696969'   # Cinza escuro - NOVA BANDA PODCAST
}

# Nomes completos das bandas
NOMES_BANDAS = {
    'D1': 'Banda D1',
    'D2': 'Banda D2', 
    'D3': 'Banda D3',
    'D4': 'Banda D4',
    'S1': 'Banda S1',
    'S2': 'Banda S2',
    'POD': 'Podcast'   # NOVA BANDA PODCAST
}

# Meses em português
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

# ---------------- CONFIGURAÇÃO GOOGLE SHEETS ---------------- #

def setup_google_sheets():
    """Configura a conexão com o Google Sheets"""
    try:
        # Método 1: Tentar carregar como JSON string direto
        creds_info = {
            "type": st.secrets["gcp_service_account"]["type"],
            "project_id": st.secrets["gcp_service_account"]["project_id"],
            "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
            "private_key": st.secrets["gcp_service_account"]["private_key"],
            "client_email": st.secrets["gcp_service_account"]["client_email"],
            "client_id": st.secrets["gcp_service_account"]["client_id"],
            "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
            "token_uri": st.secrets["gcp_service_account"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"]
        }
        
        # Definir escopos
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Criar credenciais
        credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
        gc = gspread.authorize(credentials)
        
        # Abrir a planilha pelo ID
        spreadsheet_id = st.secrets["google_sheets"]["spreadsheet_id"]
        spreadsheet = gc.open_by_key(spreadsheet_id)
        
        # Selecionar a primeira worksheet
        worksheet = spreadsheet.sheet1
        
        # Verificar se a worksheet tem cabeçalhos, se não, criar
        try:
            existing_data = worksheet.get_all_records()
        except:
            # Se estiver vazia, adicionar cabeçalhos
            worksheet.append_row(['data', 'banda', 'horario'])
        
        return worksheet
        
    except Exception as e:
        st.error(f"Erro na configuração do Google Sheets: {str(e)}")
        # Tentar método alternativo com arquivo temporário
        try:
            return setup_google_sheets_alternative()
        except Exception as e2:
            st.error(f"Erro alternativo também falhou: {str(e2)}")
            return None

def setup_google_sheets_alternative():
    """Método alternativo para configuração"""
    try:
        # Criar um arquivo JSON temporário em memória
        import tempfile
        import os
        
        creds_info = {
            "type": st.secrets["gcp_service_account"]["type"],
            "project_id": st.secrets["gcp_service_account"]["project_id"],
            "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
            "private_key": st.secrets["gcp_service_account"]["private_key"],
            "client_email": st.secrets["gcp_service_account"]["client_email"],
            "client_id": st.secrets["gcp_service_account"]["client_id"],
            "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
            "token_uri": st.secrets["gcp_service_account"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"]
        }
        
        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(creds_info, temp_file)
            temp_file_path = temp_file.name
        
        # Usar o arquivo temporário
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        credentials = Credentials.from_service_account_file(temp_file_path, scopes=scopes)
        gc = gspread.authorize(credentials)
        
        # Abrir a planilha
        spreadsheet_id = st.secrets["google_sheets"]["spreadsheet_id"]
        spreadsheet = gc.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.sheet1
        
        # Limpar arquivo temporário
        os.unlink(temp_file_path)
        
        return worksheet
        
    except Exception as e:
        st.error(f"Erro no método alternativo: {str(e)}")
        return None

def carregar_dados_gsheets(worksheet):
    """Carrega os dados do Google Sheets"""
    try:
        # Obter todos os registros
        records = worksheet.get_all_records()
        
        if not records:
            return pd.DataFrame(columns=['data', 'banda', 'horario'])
        
        df = pd.DataFrame(records)
        # Converter a coluna de data
        df['data'] = pd.to_datetime(df['data'], errors='coerce').dt.date
        # Remover linhas com datas inválidas
        df = df.dropna(subset=['data'])
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame(columns=['data', 'banda', 'horario'])

def salvar_dados_gsheets(worksheet, df):
    """Salva os dados no Google Sheets"""
    try:
        # Limpar a worksheet completamente
        worksheet.clear()
        
        # Adicionar cabeçalhos
        headers = ['data', 'banda', 'horario']
        worksheet.append_row(headers)
        
        # Adicionar dados se não estiver vazio
        if not df.empty:
            # Converter para o formato correto
            df_to_save = df.copy()
            df_to_save['data'] = df_to_save['data'].astype(str)
            
            # Adicionar linhas em batch
            values = df_to_save.values.tolist()
            if values:
                worksheet.append_rows(values)
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar dados: {e}")
        return False

# ---------------- FUNÇÕES ---------------- #

def carregar_dados():
    """Carrega os dados do Google Sheets ou inicializa vazio"""
    if 'agenda' not in st.session_state:
        if 'worksheet' not in st.session_state:
            st.session_state.worksheet = setup_google_sheets()
        
        if st.session_state.worksheet:
            df = carregar_dados_gsheets(st.session_state.worksheet)
            st.session_state.agenda = df
        else:
            st.session_state.agenda = pd.DataFrame(columns=['data', 'banda', 'horario'])
    
    return st.session_state.agenda

def salvar_dados(df):
    """Salva os dados na session_state e no Google Sheets"""
    # Garantir que a coluna de data está no formato correto
    df_copy = df.copy()
    df_copy['data'] = pd.to_datetime(df_copy['data']).dt.date
    
    st.session_state.agenda = df_copy
    
    if 'worksheet' not in st.session_state:
        st.session_state.worksheet = setup_google_sheets()
    
    if st.session_state.worksheet:
        success = salvar_dados_gsheets(st.session_state.worksheet, df_copy)
        if success:
            st.success("✅ Dados salvos com sucesso no Google Sheets!")
        else:
            st.error("❌ Erro ao salvar dados no Google Sheets")
    else:
        st.error("❌ Não foi possível conectar ao Google Sheets")

def obter_agendamentos_do_dia(df, dia):
    """Retorna os agendamentos para um determinado dia"""
    if df.empty:
        return df
    return df[df['data'] == dia]

# ---------------- INTERFACE PRINCIPAL ---------------- #

st.title("🎵 Agenda de Ensaios - EM DESELVOLVIMENTO")
st.markdown("---")

# Verificar se os secrets estão configurados
if 'gcp_service_account' not in st.secrets:
    st.error("❌ Configuração do Google Sheets não encontrada. Verifique o arquivo secrets.toml")
    st.stop()

# Carregar dados
df_agenda = carregar_dados()

# Data atual
hoje = date.today()

# Sidebar
with st.sidebar:
    st.header("📅 Navegação")
    mes_atual = st.selectbox("Mês", range(1, 13), index=hoje.month-1, format_func=lambda m: MESES_PT[m])
    ano_atual = st.selectbox("Ano", range(2023, 2031), index=hoje.year-2023)
    
    st.markdown("---")
    st.header("📅 Novo Agendamento")
    
    with st.form("novo_agendamento", clear_on_submit=True):
        data_agendamento = st.date_input("Data do ensaio", min_value=hoje)
        banda_selecionada = st.selectbox(
            "Banda", list(NOMES_BANDAS.keys()),
            format_func=lambda x: f"{x} - {NOMES_BANDAS[x]}"
        )
        horario_agendamento = st.time_input("Horário de início", value=datetime.time(19, 0))

        submitted = st.form_submit_button("Agendar Ensaio")

        if submitted:
            data_agendamento = pd.to_datetime(data_agendamento).date()
            horario_str = horario_agendamento.strftime('%H:%M')

            # Verifica conflito (mesma data + horário)
            conflito = df_agenda[
                (df_agenda['data'] == data_agendamento) &
                (df_agenda['horario'] == horario_str)
            ]

            if not conflito.empty:
                st.error(
                    f"❌ Já existe ensaio em {data_agendamento.strftime('%d/%m/%Y')} às {horario_str}"
                )
            else:
                novo_agendamento = pd.DataFrame({
                    'data': [data_agendamento],
                    'banda': [banda_selecionada],
                    'horario': [horario_str]
                })
                df_agenda = pd.concat([df_agenda, novo_agendamento], ignore_index=True)
                salvar_dados(df_agenda)
                st.rerun()
    
    st.markdown("---")
    st.header("💾 Gerenciar Dados")
    
    if not df_agenda.empty:
        csv = df_agenda.to_csv(index=False)
        st.download_button(
            label="📥 Exportar Agenda (CSV)",
            data=csv,
            file_name=f"agenda_ensaios_{hoje.strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    # Upload de CSV para importar dados
    uploaded_file = st.file_uploader("📤 Importar CSV", type=['csv'])
    if uploaded_file is not None:
        try:
            novo_df = pd.read_csv(uploaded_file)
            novo_df['data'] = pd.to_datetime(novo_df['data']).dt.date
            st.session_state.agenda = novo_df
            salvar_dados(novo_df)
            st.success("✅ Dados importados com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erro ao importar arquivo: {e}")
    
    with st.expander("🔧 Debug"):
        st.write("Agendamentos atuais:")
        st.write(df_agenda)
        
        if st.button("🔄 Recarregar dados do Google Sheets"):
            if 'worksheet' in st.session_state:
                del st.session_state.worksheet
            if 'agenda' in st.session_state:
                del st.session_state.agenda
            st.rerun()
            
        if st.button("🗑️ Limpar todos os agendamentos"):
            st.session_state.agenda = pd.DataFrame(columns=['data', 'banda', 'horario'])
            salvar_dados(st.session_state.agenda)
            st.rerun()
    
    st.markdown("---")
    st.info("""
    **💡 Como usar:**
    1. Selecione data, banda e horário
    2. Clique em "Agendar Ensaio"
    3. O calendário será atualizado automaticamente
    4. Para excluir, use o botão 🗑 na lista do mês

    **📊 Dados salvos:** No Google Sheets (nuvem)
    **📤 Exportar:** Use o botão para baixar CSV
    """)

# ... (o restante do código do calendário permanece igual) ...

# ---------------- CALENDÁRIO ---------------- #

st.header(f"Calendário de {MESES_PT[mes_atual]} de {ano_atual}")

# CSS (mantido igual)
st.markdown("""
<style>
    .calendar-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 2px;
        width: 100%;
    }
    
    .calendar-header-cell {
        background-color: #f0f2f6;
        font-weight: bold;
        text-align: center;
        padding: 8px 2px;
        font-size: 12px;
        border: 1px solid #ddd;
        color: #333 !important;
        display: block !important;
    }
    
    .calendar-day-cell {
        border: 1px solid #ddd;
        padding: 4px;
        min-height: 80px;
        background-color: white;
        position: relative;
    }
    
    .calendar-day-number {
        font-weight: bold;
        font-size: 14px;
        text-align: center;
        margin-bottom: 3px;
        color: #333 !important;
        display: block !important;
    }
    
    .calendar-event {
        font-size: 9px;
        padding: 2px 3px;
        margin: 1px 0;
        border-radius: 2px;
        color: white;
        text-align: center;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .calendar-available {
        font-size: 8px;
        color: #666;
        text-align: center;
        margin-top: 5px;
    }
    
    .today-cell {
        background-color: #fff0f0 !important;
        border: 2px solid #ff4444 !important;
    }
    
    .today-cell .calendar-day-number {
        background-color: #ff4444;
        color: white !important;
        border-radius: 50%;
        width: 25px;
        height: 25px;
        line-height: 25px;
        margin: 0 auto 3px auto;
    }
    
    .normal-day .calendar-day-number {
        background-color: #f8f9fa;
        border-radius: 50%;
        width: 25px;
        height: 25px;
        line-height: 25px;
        margin: 0 auto 3px auto;
    }
    
    .empty-cell {
        background-color: #f8f9fa;
        border: 1px solid #ddd;
        min-height: 80px;
    }
    
    @media (max-width: 768px) {
        .calendar-grid { gap: 1px; }
        .calendar-header-cell { padding: 6px 1px; font-size: 10px !important; }
        .calendar-day-cell { min-height: 70px; padding: 3px; }
        .calendar-day-number { font-size: 12px; }
        .today-cell .calendar-day-number, .normal-day .calendar-day-number {
            width: 22px; height: 22px; line-height: 22px; font-size: 12px;
        }
        .calendar-event { font-size: 8px; padding: 1px 2px; }
        .calendar-available { font-size: 7px; }
        .empty-cell { min-height: 70px; }
    }
    
    @media (max-width: 480px) {
        .calendar-day-cell { min-height: 65px; padding: 2px; }
        .calendar-day-number { font-size: 11px; }
        .calendar-header-cell { font-size: 9px !important; padding: 4px 1px; }
        .today-cell .calendar-day-number, .normal-day .calendar-day-number {
            width: 20px; height: 20px; line-height: 20px; font-size: 11px;
        }
        .empty-cell { min-height: 65px; }
        .calendar-event { font-size: 7px; }
    }
    
    .calendar-header-cell, .calendar-day-number {
        visibility: visible !important; opacity: 1 !important;
    }
</style>
""", unsafe_allow_html=True)

# Gerar o calendário usando CSS Grid
cal = calendar.monthcalendar(ano_atual, mes_atual)
dias_semana = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']

# Iniciar o HTML do calendário
calendario_html = '<div class="calendar-grid">'

# Adicionar cabeçalho dos dias da semana
for dia in dias_semana:
    calendario_html += f'<div class="calendar-header-cell">{dia}</div>'

# Adicionar os dias do mês
for semana in cal:
    for dia in semana:
        if dia == 0:
            calendario_html += '<div class="empty-cell"></div>'
        else:
            data_dia = date(ano_atual, mes_atual, dia)
            agendamentos_dia = obter_agendamentos_do_dia(df_agenda, data_dia)
            
            if data_dia == hoje:
                classe_celula = "today-cell"
            else:
                classe_celula = "normal-day"
            
            calendario_html += f'<div class="calendar-day-cell {classe_celula}">'
            calendario_html += f'<div class="calendar-day-number">{dia}</div>'
            
            if not agendamentos_dia.empty:
                for _, ag in agendamentos_dia.iterrows():
                    cor = CORES_BANDAS[ag['banda']]
                    calendario_html += f'<div class="calendar-event" style="background:{cor};">{ag["banda"]}</div>'
            else:
                calendario_html += '<div class="calendar-available">Livre</div>'
            
            calendario_html += '</div>'

calendario_html += '</div>'

st.markdown(calendario_html, unsafe_allow_html=True)

# ... (o restante do código permanece igual) ...

