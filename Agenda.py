import streamlit as st
import pandas as pd
import datetime
import calendar
from datetime import date

# Configuração da página
st.set_page_config(page_title="Agenda de Ensaios", page_icon="🎵", layout="wide")

# Cores das bandas
CORES_BANDAS = {
    'D1': '#FF6B6B',  # Vermelho
    'D2': '#4ECDC4',  # Azul claro
    'D3': '#45B7D1',  # Azul
    'D4': '#96CEB4',  # Verde
    'S1': '#FFEAA7',  # Amarelo
    'S2': '#DDA0DD'   # Roxo
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
    st.success("✅ Agendamento salvo com sucesso!")


def obter_agendamentos_do_dia(df, dia):
    """Retorna os agendamentos para um determinado dia"""
    if df.empty:
        return df
    return df[df['data'] == dia]


# ---------------- INTERFACE PRINCIPAL ---------------- #

st.title("🎵 Agenda de Ensaios de Bandas")
st.markdown("---")

# Carregar dados
df_agenda = carregar_dados()

# Data atual
hoje = date.today()
mes_atual = st.sidebar.selectbox("Mês", range(1, 13), index=hoje.month-1)
ano_atual = st.sidebar.selectbox("Ano", range(2023, 2031), index=hoje.year-2023)

# ---------------- NOVO AGENDAMENTO ---------------- #

st.sidebar.header("📅 Novo Agendamento")

with st.sidebar.form("novo_agendamento", clear_on_submit=True):
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
            st.sidebar.error(
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

# ---------------- CALENDÁRIO ---------------- #

st.header(f"Calendário de {calendar.month_name[mes_atual]} de {ano_atual}")

cal = calendar.monthcalendar(ano_atual, mes_atual)
dias_semana = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']

cols = st.columns(7)
for i, dia in enumerate(dias_semana):
    cols[i].markdown(f"<div style='text-align: center; font-weight: bold;'>{dia}</div>", unsafe_allow_html=True)

for semana in cal:
    cols = st.columns(7)
    for i, dia in enumerate(semana):
        with cols[i]:
            if dia == 0:
                st.markdown(
                    "<div style='height:100px; background-color:#f8f9fa; border:1px solid #dee2e6; border-radius:5px;'></div>",
                    unsafe_allow_html=True
                )
            else:
                data_dia = date(ano_atual, mes_atual, dia)
                agendamentos_dia = obter_agendamentos_do_dia(df_agenda, data_dia)

                if not agendamentos_dia.empty:
                    eventos_html = ""
                    for _, ag in agendamentos_dia.iterrows():
                        cor = CORES_BANDAS[ag['banda']]
                        eventos_html += f"<div style='font-size:0.8em; background:{cor}; color:white; border-radius:3px; margin:2px; padding:2px;'>{ag['banda']} {ag['horario']}</div>"

                    estilo = f"""
                    <div style='
                        background-color: white;
                        padding: 4px;
                        border-radius: 5px;
                        height: 100px;
                        border: 3px solid {"#ff4444" if data_dia == hoje else "#dee2e6"};
                        font-weight: bold;
                        text-align: center;
                    '>
                        <div style='font-size: 1.1em; margin-bottom: 3px;'>{dia}</div>
                        {eventos_html}
                    </div>
                    """
                else:
                    estilo = f"""
                    <div style='
                        background-color: {'#fff0f0' if data_dia == hoje else 'white'};
                        padding: 4px;
                        border-radius: 5px;
                        height: 100px;
                        border: 2px solid {'#ff4444' if data_dia == hoje else '#dee2e6'};
                        text-align: center;
                    '>
                        <div style='font-size: 1.1em; margin-bottom: 3px;'>{dia}</div>
                        <div style='color: #666; font-size: 0.8em;'>Disponível</div>
                    </div>
                    """
                st.markdown(estilo, unsafe_allow_html=True)

# ---------------- LEGENDA ---------------- #

st.markdown("---")
st.subheader("Legenda das Bandas")
cols_legenda = st.columns(6)
for i, (banda, cor) in enumerate(CORES_BANDAS.items()):
    with cols_legenda[i]:
        st.markdown(f"""
        <div style='
            background-color: {cor};
            color: white;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            font-weight: bold;
            margin: 5px;
        '>
            {banda}<br>
            <small>{NOMES_BANDAS[banda]}</small>
        </div>
        """, unsafe_allow_html=True)

# ---------------- LISTA DE AGENDAMENTOS ---------------- #

st.markdown("---")
st.subheader("📋 Agendamentos do Mês")

if not df_agenda.empty:
    agendamentos_mes = df_agenda[
        (df_agenda['data'].apply(lambda x: x.month) == mes_atual) &
        (df_agenda['data'].apply(lambda x: x.year) == ano_atual)
    ].sort_values(by=["data", "horario"])

    if not agendamentos_mes.empty:
        for _, agendamento in agendamentos_mes.iterrows():
            cor = CORES_BANDAS[agendamento['banda']]
            st.markdown(f"""
            <div style='
                background-color: {cor};
                color: white;
                padding: 12px;
                border-radius: 5px;
                margin: 5px 0;
                font-weight: bold;
            '>
                📅 {agendamento['data'].strftime('%d/%m/%Y')} - 
                🎵 {agendamento['banda']} - 
                ⏰ {agendamento['horario']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhum ensaio agendado para este mês.")
else:
    st.info("Nenhum ensaio agendado ainda.")

# ---------------- EXPORTAR / IMPORTAR ---------------- #

st.sidebar.markdown("---")
st.sidebar.header("💾 Gerenciar Dados")

if not df_agenda.empty:
    csv = df_agenda.to_csv(index=False)
    st.sidebar.download_button(
        label="📥 Exportar Agenda (CSV)",
        data=csv,
        file_name=f"agenda_ensaios_{hoje.strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

uploaded_file = st.sidebar.file_uploader("📤 Importar CSV", type=['csv'])
if uploaded_file is not None:
    try:
        novo_df = pd.read_csv(uploaded_file)
        novo_df['data'] = pd.to_datetime(novo_df['data']).dt.date
        st.session_state.agenda = novo_df
        novo_df.to_csv("agenda.csv", index=False)
        st.sidebar.success("Dados importados com sucesso!")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Erro ao importar arquivo: {e}")

# ---------------- DEBUG / RESET ---------------- #

with st.sidebar.expander("🔧 Debug"):
    st.write("Agendamentos atuais:")
    st.write(df_agenda)
    if st.button("Limpar todos os agendamentos"):
        st.session_state.agenda = pd.DataFrame(columns=['data', 'banda', 'horario'])
        st.session_state.agenda.to_csv("agenda.csv", index=False)
        st.rerun()

# ---------------- INSTRUÇÕES ---------------- #

st.sidebar.markdown("---")
st.sidebar.info("""
**💡 Como usar:**
1. Selecione data, banda e horário
2. Clique em "Agendar Ensaio"
3. O calendário será atualizado automaticamente

**📊 Dados salvos:** Em `agenda.csv` no diretório do app
**📤 Exportar:** Use o botão para baixar CSV
""")
