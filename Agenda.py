import streamlit as st
import pandas as pd
import datetime
import calendar
from datetime import date

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
    'S2': '#FF8C00'   # Laranja
}

# Nomes completos das bandas
NOMES_BANDAS = {
    'D1': 'Banda D1',
    'D2': 'Banda D2', 
    'D3': 'Banda D3',
    'D4': 'Banda D4',
    'S1': 'Banda S1',
    'S2': 'Banda S2'
}

# Meses em português
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

# ---------------- FUNÇÕES ---------------- #

def carregar_dados():
    """Carrega os dados do arquivo CSV ou inicializa vazio"""
    if 'agenda' not in st.session_state:
        try:
            df = pd.read_csv("agenda.csv")
            df['data'] = pd.to_datetime(df['data']).dt.date
            st.session_state.agenda = df
        except FileNotFoundError:
            st.session_state.agenda = pd.DataFrame(columns=['data', 'banda', 'horario'])
    return st.session_state.agenda

def salvar_dados(df):
    """Salva os dados na session_state e em CSV"""
    df['data'] = pd.to_datetime(df['data']).dt.date
    st.session_state.agenda = df
    df.to_csv("agenda.csv", index=False)

def obter_agendamentos_do_dia(df, dia):
    """Retorna os agendamentos para um determinado dia"""
    if df.empty:
        return df
    return df[df['data'] == dia]

# ---------------- INTERFACE PRINCIPAL ---------------- #

st.title("🎵 Agenda de Ensaios ICCFV")
st.markdown("---")

# Carregar dados
df_agenda = carregar_dados()

# Data atual
hoje = date.today()

# Sidebar
with st.sidebar:
    st.header("📅 Navegação")
    mes_atual = st.selectbox("Mês", range(1, 13), index=hoje.month-1, format_func=lambda m: MESES_PT[m])
    ano_atual = st.sidebar.selectbox("Ano", range(2023, 2031), index=hoje.year-2023)
    
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
                st.success("✅ Agendamento salvo com sucesso!")
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

    uploaded_file = st.file_uploader("📤 Importar CSV", type=['csv'])
    if uploaded_file is not None:
        try:
            novo_df = pd.read_csv(uploaded_file)
            novo_df['data'] = pd.to_datetime(novo_df['data']).dt.date
            st.session_state.agenda = novo_df
            novo_df.to_csv("agenda.csv", index=False)
            st.success("Dados importados com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao importar arquivo: {e}")
    
    with st.expander("🔧 Debug"):
        st.write("Agendamentos atuais:")
        st.write(df_agenda)
        if st.button("Limpar todos os agendamentos"):
            st.session_state.agenda = pd.DataFrame(columns=['data', 'banda', 'horario'])
            st.session_state.agenda.to_csv("agenda.csv", index=False)
            st.rerun()
    
    st.markdown("---")
    st.info("""
    **💡 Como usar:**
    1. Selecione data, banda e horário
    2. Clique em "Agendar Ensaio"
    3. O calendário será atualizado automaticamente
    4. Para excluir, use o botão 🗑 na lista do mês

    **📊 Dados salvos:** Em `agenda.csv` no diretório do app
    **📤 Exportar:** Use o botão para baixar CSV
    """)

# ---------------- CALENDÁRIO CORRIGIDO PARA MOBILE ---------------- #

st.header(f"Calendário de {MESES_PT[mes_atual]} de {ano_atual}")

# CSS personalizado para corrigir problemas de mobile
st.markdown("""
<style>
    /* Estilos gerais para o calendário */
    .calendar-container {
        width: 100%;
        overflow-x: auto;
    }
    
    .calendar-table {
        width: 100%;
        min-width: 300px;
        border-collapse: collapse;
    }
    
    .calendar-header {
        background-color: #f0f2f6;
        font-weight: bold;
        text-align: center;
        padding: 10px 5px;
        border: 1px solid #ddd;
    }
    
    .calendar-day {
        border: 1px solid #ddd;
        padding: 5px;
        vertical-align: top;
        min-height: 80px;
        height: 80px;
        position: relative;
    }
    
    .calendar-day-number {
        font-weight: bold;
        font-size: 14px;
        margin-bottom: 3px;
        text-align: center;
        background-color: #f8f9fa;
        border-radius: 50%;
        width: 25px;
        height: 25px;
        line-height: 25px;
        margin: 0 auto 5px auto;
    }
    
    .calendar-event {
        font-size: 10px;
        padding: 2px 4px;
        margin: 1px 0;
        border-radius: 3px;
        color: white;
        text-align: center;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .calendar-available {
        font-size: 9px;
        color: #666;
        text-align: center;
        margin-top: 5px;
    }
    
    .today {
        background-color: #fff0f0 !important;
        border: 2px solid #ff4444 !important;
    }
    
    .today .calendar-day-number {
        background-color: #ff4444;
        color: white;
    }
    
    /* Media queries para responsividade */
    @media (max-width: 768px) {
        .calendar-day {
            min-height: 70px;
            height: 70px;
            padding: 3px;
        }
        
        .calendar-day-number {
            font-size: 12px;
            width: 22px;
            height: 22px;
            line-height: 22px;
        }
        
        .calendar-event {
            font-size: 9px;
            padding: 1px 2px;
        }
        
        .calendar-available {
            font-size: 8px;
        }
        
        .calendar-header {
            padding: 8px 3px;
            font-size: 12px;
        }
    }
    
    @media (max-width: 480px) {
        .calendar-day {
            min-height: 60px;
            height: 60px;
            padding: 2px;
        }
        
        .calendar-day-number {
            font-size: 11px;
            width: 20px;
            height: 20px;
            line-height: 20px;
        }
        
        .calendar-event {
            font-size: 8px;
            padding: 1px;
        }
        
        .calendar-header {
            padding: 6px 2px;
            font-size: 11px;
        }
    }
</style>
""", unsafe_allow_html=True)

# Gerar o calendário
cal = calendar.monthcalendar(ano_atual, mes_atual)
dias_semana = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']

# Criar o calendário usando HTML table para melhor compatibilidade mobile
calendario_html = """
<div class="calendar-container">
    <table class="calendar-table">
        <thead>
            <tr>
"""

# Cabeçalho dos dias da semana
for dia in dias_semana:
    calendario_html += f'<th class="calendar-header">{dia}</th>'

calendario_html += """
            </tr>
        </thead>
        <tbody>
"""

# Dias do mês
for semana in cal:
    calendario_html += "<tr>"
    
    for i, dia in enumerate(semana):
        if dia == 0:
            calendario_html += '<td class="calendar-day" style="background-color:#f8f9fa;"></td>'
        else:
            data_dia = date(ano_atual, mes_atual, dia)
            agendamentos_dia = obter_agendamentos_do_dia(df_agenda, data_dia)
            
            # Classe para o dia atual
            classe_today = "today" if data_dia == hoje else ""
            
            calendario_html += f'<td class="calendar-day {classe_today}">'
            calendario_html += f'<div class="calendar-day-number">{dia}</div>'
            
            if not agendamentos_dia.empty:
                for _, ag in agendamentos_dia.iterrows():
                    cor = CORES_BANDAS[ag['banda']]
                    calendario_html += f'<div class="calendar-event" style="background:{cor};">{ag["banda"]} {ag["horario"]}</div>'
            else:
                calendario_html += '<div class="calendar-available">Disponível</div>'
            
            calendario_html += '</td>'
    
    calendario_html += "</tr>"

calendario_html += """
        </tbody>
    </table>
</div>
"""

st.markdown(calendario_html, unsafe_allow_html=True)

# ---------------- LISTA DE AGENDAMENTOS ---------------- #

st.markdown("---")
st.subheader("📋 Agendamentos do Mês")

if not df_agenda.empty:
    agendamentos_mes = df_agenda[
        (df_agenda['data'].apply(lambda x: x.month) == mes_atual) &
        (df_agenda['data'].apply(lambda x: x.year) == ano_atual)
    ].sort_values(by=["data", "horario"])

    if not agendamentos_mes.empty:
        for idx, agendamento in agendamentos_mes.iterrows():
            cor = CORES_BANDAS[agendamento['banda']]
            
            # Layout responsivo para a lista
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
                    📅 {agendamento['data'].strftime('%d/%m/%Y')} - 
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
st.subheader("🎨 Legenda de Cores das Bandas")

# Layout responsivo para a legenda (3 colunas em desktop, 2 em mobile)
cols = st.columns(3)

for i, (banda, cor) in enumerate(CORES_BANDAS.items()):
    with cols[i % 3]:
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
