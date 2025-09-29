import streamlit as st
import pandas as pd
import datetime
import calendar
from datetime import date, timedelta
import pytz
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
    'POD': 'Podcast'
}

# Meses em português
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

# ---------------- CONFIGURAÇÃO DO GOOGLE SHEETS ---------------- #

def get_google_credentials():
    try:
        creds_json = st.secrets["google_sheets"]["credentials"]
        creds_dict = json.loads(creds_json)
    except Exception as e:
        st.error("Erro ao carregar credenciais do Google Sheets. Verifique o arquivo secrets.toml.")
        st.stop()
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    return Credentials.from_service_account_info(creds_dict, scopes=scopes)

GOOGLE_SHEET_ID = st.secrets["google_sheets"]["sheet_id"]
WORKSHEET_NAME = "agenda"

def carregar_dados_google():
    try:
        creds = get_google_credentials()
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID).worksheet(WORKSHEET_NAME)
        data = sheet.get_all_records()
        if data:
            df = pd.DataFrame(data)
            df['data'] = pd.to_datetime(df['data']).dt.date
        else:
            df = pd.DataFrame(columns=['data', 'banda', 'horario'])
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados do Google Sheets: {e}")
        return pd.DataFrame(columns=['data', 'banda', 'horario'])

def salvar_dados_google(df):
    try:
        creds = get_google_credentials()
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID).worksheet(WORKSHEET_NAME)
        sheet.clear()
        sheet.append_row(['data', 'banda', 'horario'])
        for _, row in df.iterrows():
            sheet.append_row([row['data'].strftime('%Y-%m-%d'), row['banda'], row['horario']])
    except Exception as e:
        st.error(f"Erro ao salvar no Google Sheets: {e}")

# ---------------- FUNÇÕES ---------------- #

def obter_data_brasil():
    fuso_brasil = pytz.timezone('America/Sao_Paulo')
    data_utc = datetime.datetime.now(pytz.utc)
    data_brasil = data_utc.astimezone(fuso_brasil)
    return data_brasil.date()

def carregar_dados():
    if 'agenda' not in st.session_state:
        st.session_state.agenda = carregar_dados_google()
    return st.session_state.agenda

def salvar_dados(df):
    df['data'] = pd.to_datetime(df['data']).dt.date
    st.session_state.agenda = df
    salvar_dados_google(df)

def obter_agendamentos_do_dia(df, dia):
    if df.empty:
        return df
    return df[df['data'] == dia]

def formatar_data_brasil(data):
    return data.strftime('%d/%m/%Y')

def gerar_calendario(ano, mes, df_agenda, hoje):
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia = date(ano, mes, calendar.monthrange(ano, mes)[1])
    primeiro_dia_semana = primeiro_dia.weekday()
    dias_semana = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
    
    calendario_html = '<div class="calendar-grid">'
    
    for dia in dias_semana:
        calendario_html += f'<div class="calendar-header-cell">{dia}</div>'
    
    for i in range(primeiro_dia_semana):
        calendario_html += '<div class="empty-cell"></div>'
    
    for dia in range(1, ultimo_dia.day + 1):
        data_dia = date(ano, mes, dia)
        agendamentos_dia = obter_agendamentos_do_dia(df_agenda, data_dia)
        
        classe_celula = "today-cell" if data_dia == hoje else "normal-day"
        
        calendario_html += f'<div class="calendar-day-cell {classe_celula}">'
        calendario_html += f'<div class="calendar-day-number">{dia}</div>'
        
        if not agendamentos_dia.empty:
            for _, ag in agendamentos_dia.iterrows():
                cor = CORES_BANDAS[ag['banda']]
                calendario_html += f'<div class="calendar-event" style="background:{cor};">{ag["banda"]} {ag["horario"]}</div>'
        else:
            calendario_html += '<div class="calendar-available">Livre</div>'
        
        calendario_html += '</div>'
    
    ultimo_dia_semana = ultimo_dia.weekday()
    dias_restantes = 6 - ultimo_dia_semana
    for i in range(dias_restantes):
        calendario_html += '<div class="empty-cell"></div>'
    
    calendario_html += '</div>'
    return calendario_html

# ---------------- INTERFACE PRINCIPAL ---------------- #

st.title("🎵 Agenda de Ensaios ICCFV")
st.markdown("---")

df_agenda = carregar_dados()
hoje = obter_data_brasil()

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
            horario_str = horario_agendamento.strftime('%H:%M')

            conflito = df_agenda[
                (df_agenda['data'] == data_agendamento) &
                (df_agenda['horario'] == horario_str)
            ]

            if not conflito.empty:
                st.error(
                    f"❌ Já existe ensaio em {formatar_data_brasil(data_agendamento)} às {horario_str}"
                )
            else:
                novo_agendamento = pd.DataFrame({
                    'data': [data_agendamento],
                    'banda': [banda_selecionada],
                    'horario': [horario_str]
                })
                df_agenda = pd.concat([df_agenda, novo_agendamento], ignore_index=True)
                salvar_dados(df_agenda)
                st.success("✅ Agendamento salvo com sucesso!")
                st.rerun()

    st.markdown("---")
    st.info("""
    **💡 Como usar:**
    1. Selecione data, banda e horário
    2. Clique em "Agendar Ensaio"
    3. O calendário será atualizado automaticamente
    4. Para excluir, use o botão 🗑 na lista do mês

    **📊 Dados salvos:** Na Google Sheet configurada
    """)

# ---------------- CALENDÁRIO ---------------- #

st.header(f"Calendário de {MESES_PT[mes_atual]} de {ano_atual}")

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
        color: black;  /* ALTERADO DE WHITE PARA BLACK */
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
        .today-cell .calendar-day-number,
        .normal-day .calendar-day-number {
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
        .today-cell .calendar-day-number,
        .normal-day .calendar-day-number {
            width: 20px; height: 20px; line-height: 20px; font-size: 11px;
        }
        .empty-cell { min-height: 65px; }
        .calendar-event { font-size: 7px; }
    }
</style>
""", unsafe_allow_html=True)

calendario_html = gerar_calendario(ano_atual, mes_atual, df_agenda, hoje)
st.markdown(calendario_html, unsafe_allow_html=True)

# ---------------- LISTA DE AGENDAMENTOS ---------------- #

st.markdown("---")
# Tamanho original do h3 no Streamlit ≈ 1.17em (~18.72px)
# Antes: 40% → agora: 40% * 1.3 = 52%
st.markdown('<h3 style="font-size: 99%;">📋 Agendamentos do Mês</h3>', unsafe_allow_html=True)

if not df_agenda.empty:
    agendamentos_mes = df_agenda[
        (df_agenda['data'].apply(lambda x: x.month) == mes_atual) &
        (df_agenda['data'].apply(lambda x: x.year) == ano_atual)
    ].sort_values(by=["data", "horario"])

    if not agendamentos_mes.empty:
        for idx, agendamento in agendamentos_mes.iterrows():
            cor = CORES_BANDAS[agendamento['banda']]
            col1, col2 = st.columns([8, 1])
            with col1:
                st.markdown(f"""
                <div style='
                    background-color: {cor};
                    color: white;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 5px 0;
                    font-weight: bold;
                    font-size: 14px;
                '>
                    📅 {formatar_data_brasil(agendamento['data'])} - 
                    🎵 {agendamento['banda']} - 
                    ⏰ {agendamento['horario']}
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("🗑", key=f"del_{idx}"):
                    df_agenda = df_agenda.drop(idx).reset_index(drop=True)
                    salvar_dados(df_agenda)
                    st.rerun()
    else:
        st.info("Nenhum ensaio agendado para este mês.")
else:
    st.info("Nenhum ensaio agendado ainda.")

# ---------------- LEGENDA DE CORES ---------------- #

st.markdown("---")
st.markdown('<h3 style="font-size: 99%;">🎨 Legenda de Cores das Bandas</h3>', unsafe_allow_html=True)

# Ordem fixa desejada
ORDEM_LEGENDA = ['D1', 'D2', 'D3', 'D4', 'S1', 'S2', 'POD']

# Renderização em blocos de 3 por linha para manter ordem visual correta
for i in range(0, len(ORDEM_LEGENDA), 3):
    cols = st.columns(3)
    for j in range(3):
        if i + j < len(ORDEM_LEGENDA):
            banda = ORDEM_LEGENDA[i + j]
            cor = CORES_BANDAS[banda]
            with cols[j]:
                st.markdown(f"""
                <div style='
                    background-color: {cor};
                    color: white;
                    padding: 8px;
                    border-radius: 5px;
                    text-align: center;
                    font-weight: bold;
                    margin: 3px 0;
                    font-size: 12px;
                '>
                    {banda} - {NOMES_BANDAS[banda]}
                </div>
                """, unsafe_allow_html=True)

# ---------------- INSTRUÇÕES ADICIONAIS ---------------- #

st.markdown("---")
with st.expander("📱 Dicas para uso em celular"):
    st.markdown("""
    **Para melhor visualização no celular:**
    
    • **Gire a tela horizontalmente** para ver o calendário completo  
    • **Toque nos dias** para ver mais detalhes  
    • **Use o menu lateral** para adicionar novos agendamentos  
    • **Deslize horizontalmente** se o calendário não couber na tela  
    
    **Atalhos:**  
    • 🗑 - Excluir agendamento  
    • 📅 - Novo agendamento na sidebar  
    • 🎙 - Agendamentos de Podcast (nova funcionalidade)
    """)
