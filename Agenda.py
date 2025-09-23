# Agenda.py
import streamlit as st
import pandas as pd
import datetime
import calendar
import json
import os
from datetime import date

# IMPORTS para Google Sheets
try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError as e:
    st.error(f"Erro ao importar bibliotecas do Google: {e}")
    gspread = None
    Credentials = None

# --------- CONFIGURAÇÃO ----------
# Configuração via secrets do Streamlit
SHEET_ID = st.secrets.get("google", {}).get("sheet_id", "COLOQUE_SEU_ID_AQUI")
SHEET_NAME = st.secrets.get("google", {}).get("sheet_name", "Página1")

MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

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

# --------- FUNÇÕES ---------
def _check_libs():
    if gspread is None or Credentials is None:
        st.error(
            "📚 Bibliotecas necessárias não encontradas! "
            "Adicione ao requirements.txt:\n\n"
            "gspread==5.8.0\n"
            "google-auth==2.17.0\n"
            "streamlit\n"
            "pandas\n"
        )
        st.stop()

@st.cache_resource
def conectar_sheets():
    """Conecta ao Google Sheets usando credenciais de service account."""
    _check_libs()
    
    # Escopo necessário
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    try:
        # Tenta usar secrets do Streamlit
        if "google" in st.secrets and "credentials" in st.secrets["google"]:
            creds_info = st.secrets["google"]["credentials"]
            
            # Converte para dict se for string
            if isinstance(creds_info, str):
                creds_info = json.loads(creds_info)
                
            creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
            
        # Fallback para arquivo local (apenas para desenvolvimento)
        elif os.path.exists("credenciais.json"):
            with open("credenciais.json", "r") as f:
                creds_info = json.load(f)
            creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
            
        else:
            st.error(
                "🔐 Credenciais não encontradas!\n\n"
                "Para usar no Streamlit Cloud:\n"
                "1. Vá em Settings → Secrets\n"
                "2. Adicione:\n"
                "```\n"
                "[google]\n"
                "sheet_id = 'seu_id_da_planilha'\n"
                "sheet_name = 'Página1'\n"
                "credentials = '''{\n"
                "  \"type\": \"service_account\",\n"
                "  \"project_id\": \"...\",\n"
                "  \"private_key_id\": \"...\",\n"
                "  \"private_key\": \"...\",\n"
                "  \"client_email\": \"...\",\n"
                "  \"client_id\": \"...\",\n"
                "  \"auth_uri\": \"https://accounts.google.com/o/oauth2/auth\",\n"
                "  \"token_uri\": \"https://oauth2.googleapis.com/token\",\n"
                "  \"auth_provider_x509_cert_url\": \"https://www.googleapis.com/oauth2/v1/certs\"\n"
                "}'''\n"
                "```"
            )
            st.stop()
        
        # Conecta ao Google Sheets
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SHEET_ID)
        worksheet = spreadsheet.worksheet(SHEET_NAME)
        return worksheet
        
    except Exception as e:
        st.error(f"❌ Erro ao conectar com Google Sheets: {e}")
        st.stop()

def carregar_dados():
    """Carrega os registros do Google Sheets para DataFrame."""
    try:
        worksheet = conectar_sheets()
        records = worksheet.get_all_records()
        
        if not records:
            return pd.DataFrame(columns=["data", "banda", "horario"])
            
        df = pd.DataFrame(records)
        
        # Garante que as colunas necessárias existem
        for col in ["data", "banda", "horario"]:
            if col not in df.columns:
                df[col] = ""
        
        # Converte a coluna de data
        df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce").dt.date
        
        return df[["data", "banda", "horario"]]
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {e}")
        return pd.DataFrame(columns=["data", "banda", "horario"])

def salvar_dados(df):
    """Salva DataFrame no Google Sheets."""
    try:
        worksheet = conectar_sheets()
        
        # Prepara os dados para salvar
        df_to_save = df.copy()
        df_to_save["data"] = df_to_save["data"].apply(
            lambda d: d.strftime("%d/%m/%Y") if pd.notna(d) and d != "" else ""
        )
        
        # Converte para lista de listas
        data_to_save = [df_to_save.columns.tolist()] + df_to_save.values.tolist()
        
        # Limpa e atualiza a planilha
        worksheet.clear()
        worksheet.update(data_to_save, value_input_option='USER_ENTERED')
        
        st.success("✅ Agendamento salvo com sucesso!")
        
    except Exception as e:
        st.error(f"❌ Erro ao salvar dados: {e}")

def obter_agendamentos_do_dia(df, dia):
    """Retorna agendamentos para um dia específico."""
    if df.empty:
        return pd.DataFrame(columns=["data", "banda", "horario"])
    return df[df["data"] == dia]

# --------- INTERFACE DO USUÁRIO ---------
def main():
    st.set_page_config(
        page_title="Agenda de Ensaios", 
        page_icon="🎵", 
        layout="wide"
    )
    
    st.title("🎵 Agenda de Ensaios de Bandas")
    st.markdown("---")
    
    # Carrega os dados
    df_agenda = carregar_dados()
    
    # Sidebar com controles
    hoje = date.today()
    
    st.sidebar.header("📅 Configurações")
    mes_atual = st.sidebar.selectbox(
        "Mês", 
        list(MESES_PT.keys()), 
        index=hoje.month-1, 
        format_func=lambda m: MESES_PT[m]
    )
    ano_atual = st.sidebar.selectbox(
        "Ano", 
        list(range(2023, 2031)), 
        index=hoje.year-2023
    )
    
    # Formulário de novo agendamento
    st.sidebar.header("➕ Novo Agendamento")
    with st.sidebar.form("novo_agendamento", clear_on_submit=True):
        data_agendamento = st.date_input("Data do ensaio", min_value=hoje)
        banda_selecionada = st.selectbox(
            "Banda", 
            list(NOMES_BANDAS.keys()),
            format_func=lambda x: f"{x} - {NOMES_BANDAS[x]}"
        )
        horario_agendamento = st.time_input("Horário de início", value=datetime.time(19, 0))
        submitted = st.form_submit_button("🎵 Agendar Ensaio")
        
        if submitted:
            data_agendamento = data_agendamento  # Já é date object
            horario_str = horario_agendamento.strftime("%H:%M")
            
            # Verifica conflitos
            if not df_agenda.empty:
                conflito = df_agenda[
                    (df_agenda["data"] == data_agendamento) & 
                    (df_agenda["horario"] == horario_str)
                ]
                if not conflito.empty:
                    st.sidebar.error(
                        f"❌ Já existe ensaio agendado para "
                        f"{data_agendamento.strftime('%d/%m/%Y')} às {horario_str}"
                    )
                    return
            
            # Adiciona novo agendamento
            novo_registro = pd.DataFrame({
                "data": [data_agendamento],
                "banda": [banda_selecionada],
                "horario": [horario_str]
            })
            
            df_agenda = pd.concat([df_agenda, novo_registro], ignore_index=True)
            salvar_dados(df_agenda)
            st.rerun()
    
    # Exibe o calendário
    st.header(f"📅 Calendário de {MESES_PT[mes_atual]} de {ano_atual}")
    
    # Cria o calendário
    cal = calendar.monthcalendar(ano_atual, mes_atual)
    dias_semana = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
    
    # Cabeçalho dos dias da semana
    cols = st.columns(7)
    for i, dia in enumerate(dias_semana):
        cols[i].markdown(
            f"<div style='text-align:center; font-weight:bold; padding:10px;'>{dia}</div>", 
            unsafe_allow_html=True
        )
    
    # Dias do calendário
    for semana in cal:
        cols = st.columns(7)
        for i, dia in enumerate(semana):
            with cols[i]:
                if dia == 0:
                    # Dia vazio (fora do mês)
                    st.markdown("<div style='height:120px;'></div>", unsafe_allow_html=True)
                else:
                    data_dia = date(ano_atual, mes_atual, dia)
                    agendamentos = obter_agendamentos_do_dia(df_agenda, data_dia)
                    
                    # Estilo do dia
                    if not agendamentos.empty:
                        eventos_html = ""
                        for _, ag in agendamentos.iterrows():
                            cor = CORES_BANDAS.get(ag['banda'], "#666666")
                            eventos_html += f"""
                            <div style='font-size:0.7em; background:{cor}; color:white; 
                                     border-radius:3px; margin:1px; padding:2px;'>
                                {ag['banda']} {ag['horario']}
                            </div>
                            """
                        
                        estilo_dia = f"""
                        <div style='background-color: white; padding:5px; border-radius:8px; 
                                 height:120px; border:3px solid {"#ff4444" if data_dia == hoje else "#dee2e6"};
                                 text-align:center; overflow-y:auto;'>
                            <div style='font-size:1.2em; font-weight:bold; margin-bottom:5px;'>{dia}</div>
                            {eventos_html}
                        </div>
                        """
                    else:
                        estilo_dia = f"""
                        <div style='background-color: {"#fff0f0" if data_dia == hoje else "white"}; 
                                 padding:5px; border-radius:8px; height:120px; 
                                 border:2px solid {"#ff4444" if data_dia == hoje else "#dee2e6"};
                                 text-align:center; display:flex; flex-direction:column; 
                                 justify-content:center;'>
                            <div style='font-size:1.2em; font-weight:bold;'>{dia}</div>
                            <div style='color:#666; font-size:0.8em;'>Disponível</div>
                        </div>
                        """
                    
                    st.markdown(estilo_dia, unsafe_allow_html=True)
    
    # Lista de agendamentos do mês
    st.markdown("---")
    st.header("📋 Agendamentos do Mês")
    
    if not df_agenda.empty:
        # Filtra agendamentos do mês atual
        agendamentos_mes = df_agenda[
            (df_agenda['data'].apply(lambda x: x.month) == mes_atual) &
            (df_agenda['data'].apply(lambda x: x.year) == ano_atual)
        ].sort_values(by=["data", "horario"]).reset_index(drop=True)
        
        if not agendamentos_mes.empty:
            for idx, agendamento in agendamentos_mes.iterrows():
                cor = CORES_BANDAS.get(agendamento['banda'], "#666666")
                nome_banda = NOMES_BANDAS.get(agendamento['banda'], agendamento['banda'])
                
                col1, col2 = st.columns([9, 1])
                
                with col1:
                    st.markdown(f"""
                    <div style='background-color:{cor}; color:white; padding:15px; 
                             border-radius:8px; margin:10px 0; font-size:1.1em;'>
                        📅 <strong>{agendamento['data'].strftime('%d/%m/%Y')}</strong> | 
                        🎵 <strong>{nome_banda}</strong> | 
                        ⏰ <strong>{agendamento['horario']}</strong>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("🗑️", key=f"delete_{idx}", help="Excluir agendamento"):
                        # Remove o agendamento
                        df_agenda = df_agenda.drop(agendamentos_mes.index[idx]).reset_index(drop=True)
                        salvar_dados(df_agenda)
                        st.rerun()
        else:
            st.info("ℹ️ Nenhum ensaio agendado para este mês.")
    else:
        st.info("ℹ️ Nenhum ensaio agendado ainda.")
    
    # Informações de ajuda
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **💡 Como usar:**
    - Selecione mês/ano para navegar
    - Use o formulário para agendar ensaios
    - Clique em 🗑️ para excluir agendamentos
    - Dados salvos automaticamente no Google Sheets
    """)

# Executa a aplicação
if __name__ == "__main__":
    main()
