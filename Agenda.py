import streamlit as st
import pandas as pd
import datetime
import calendar
from datetime import date, timedelta
import requests
import io

# Configuração da página
st.set_page_config(page_title="Agenda de Ensaios", page_icon="🎵", layout="wide")

# Cores das bandas
CORES_BANDAS = {
    'D1': '#FF6B6B',  # Vermelho
    'D2': '#4ECDC4',  # Azul claro
    'D3': '#45B7D1',  # Azul
    'D4': '#96CEB4',  # Verde
    'S1': '#FFEAA7',  # Amarelo
    'S2': '#DDA0DD'  # Roxo
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

# URL do arquivo CSV no GitHub (substitua pela sua URL)
GITHUB_CSV_URL = "https://raw.githubusercontent.com/seu-usuario/seu-repositorio/main/agenda_ensaios.csv"


def carregar_dados():
    """Carrega os dados do arquivo CSV do GitHub"""
    try:
        # Tenta carregar do GitHub
        response = requests.get(GITHUB_CSV_URL)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            # Converte a coluna de data para datetime
            df['data'] = pd.to_datetime(df['data']).dt.date
            return df
        else:
            # Se não encontrar, cria um DataFrame vazio
            return pd.DataFrame(columns=['data', 'banda', 'horario'])
    except:
        return pd.DataFrame(columns=['data', 'banda', 'horario'])


def salvar_dados(df):
    """Salva os dados no arquivo CSV do GitHub (simulação)"""
    # Em um ambiente real, você usaria a API do GitHub para fazer commit
    # Aqui vamos simular salvando localmente e instruindo sobre como fazer o upload
    df.to_csv('agenda_ensaios.csv', index=False)
    st.success(
        "Dados salvos localmente. Faça upload manual para o GitHub ou configure GitHub Actions para sincronização automática.")


def obter_primeiro_ultimo_dia_mes(data_referencia):
    """Retorna o primeiro e último dia do mês"""
    primeiro_dia = date(data_referencia.year, data_referencia.month, 1)
    ultimo_dia = date(data_referencia.year, data_referencia.month,
                      calendar.monthrange(data_referencia.year, data_referencia.month)[1])
    return primeiro_dia, ultimo_dia


def gerar_calendario(mes, ano):
    """Gera uma matriz representando o calendário do mês"""
    cal = calendar.monthcalendar(ano, mes)
    return cal


def obter_agendamentos_do_dia(df, dia):
    """Retorna os agendamentos para um determinado dia"""
    return df[df['data'] == dia]


def estilo_dia(dia, agendamentos, hoje):
    """Aplica estilo CSS para um dia do calendário"""
    if dia == 0:  # Dia vazio do calendário
        return "<div style='width:100%; height:100px; background-color:#f0f0f0; border:1px solid #ddd;'></div>"

    estilo = f"<div style='width:100%; height:100px; border:1px solid #ddd; padding:5px;"

    # Destacar dia atual
    if dia == hoje.day and mes_atual == hoje.month and ano_atual == hoje.year:
        estilo += "border:2px solid #ff4444;"

    # Verificar se há agendamentos para este dia
    agendamentos_dia = agendamentos[agendamentos['data'] == date(ano_atual, mes_atual, dia)]

    if not agendamentos_dia.empty:
        banda = agendamentos_dia.iloc[0]['banda']
        horario = agendamentos_dia.iloc[0]['horario']
        cor = CORES_BANDAS.get(banda, '#ffffff')
        estilo += f"background-color:{cor}; color:white; font-weight:bold;'"
        estilo += f">{dia}<br><small>{banda}</small><br><small>{horario}</small>"
    else:
        estilo += "background-color:white;'"
        estilo += f">{dia}"

    estilo += "</div>"
    return estilo


# Interface principal
st.title("🎵 Agenda de Ensaios de Bandas")
st.markdown("---")

# Carregar dados
df_agenda = carregar_dados()

# Data atual
hoje = date.today()
mes_atual = st.sidebar.selectbox("Mês", range(1, 13), index=hoje.month - 1)
ano_atual = st.sidebar.selectbox("Ano", range(2023, 2031), index=hoje.year - 2023)

# Sidebar para novo agendamento
st.sidebar.header("📅 Novo Agendamento")

with st.sidebar.form("novo_agendamento"):
    data_agendamento = st.date_input("Data do ensaio", min_value=hoje)
    banda_selecionada = st.selectbox("Banda", list(NOMES_BANDAS.keys()),
                                     format_func=lambda x: f"{x} - {NOMES_BANDAS[x]}")
    horario_agendamento = st.time_input("Horário de início", value=datetime.time(19, 0))

    submitted = st.form_submit_button("Agendar Ensaio")

    if submitted:
        # Verificar se já existe agendamento para esta data
        agendamento_existente = df_agenda[df_agenda['data'] == data_agendamento]

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
            st.sidebar.success("✅ Ensaio agendado com sucesso!")
            st.rerun()

# Exibir calendário
st.header(f"Calendário de {calendar.month_name[mes_atual]} de {ano_atual}")

# Gerar calendário
cal = gerar_calendario(mes_atual, ano_atual)

# Cabeçalho dos dias da semana
dias_semana = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
cols = st.columns(7)

for i, dia in enumerate(dias_semana):
    cols[i].markdown(f"**{dia}**")

# Exibir dias do calendário
for semana in cal:
    cols = st.columns(7)
    for i, dia in enumerate(semana):
        with cols[i]:
            if dia == 0:
                st.markdown("<div style='height:100px; background-color:#f8f9fa; border:1px solid #dee2e6;'></div>",
                            unsafe_allow_html=True)
            else:
                data_dia = date(ano_atual, mes_atual, dia)
                agendamentos_dia = obter_agendamentos_do_dia(df_agenda, data_dia)

                if not agendamentos_dia.empty:
                    banda = agendamentos_dia.iloc[0]['banda']
                    horario = agendamentos_dia.iloc[0]['horario']
                    cor = CORES_BANDAS[banda]

                    estilo = f"""
                    <div style='
                        background-color: {cor};
                        color: white;
                        padding: 10px;
                        border-radius: 5px;
                        height: 100px;
                        border: 2px solid {cor if data_dia != hoje else '#ff4444'};
                        font-weight: bold;
                    '>
                        <div style='font-size: 1.2em;'>{dia}</div>
                        <div style='font-size: 0.9em;'>{banda}</div>
                        <div style='font-size: 0.8em;'>{horario}</div>
                    </div>
                    """
                else:
                    estilo = f"""
                    <div style='
                        background-color: {'#ffebee' if data_dia == hoje else 'white'};
                        padding: 10px;
                        border-radius: 5px;
                        height: 100px;
                        border: 2px solid {'#ff4444' if data_dia == hoje else '#dee2e6'};
                    '>
                        <div style='font-size: 1.2em;'>{dia}</div>
                        <div style='color: #666; font-size: 0.8em;'>Disponível</div>
                    </div>
                    """

                st.markdown(estilo, unsafe_allow_html=True)

# Legenda das cores
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
        '>
            {banda} - {NOMES_BANDAS[banda]}
        </div>
        """, unsafe_allow_html=True)

# Lista de agendamentos do mês
st.markdown("---")
st.subheader("Agendamentos do Mês")

agendamentos_mes = df_agenda[
    (df_agenda['data'].apply(lambda x: x.month) == mes_atual) &
    (df_agenda['data'].apply(lambda x: x.year) == ano_atual)
    ].sort_values('data')

if not agendamentos_mes.empty:
    for _, agendamento in agendamentos_mes.iterrows():
        cor = CORES_BANDAS[agendamento['banda']]
        st.markdown(f"""
        <div style='
            background-color: {cor};
            color: white;
            padding: 15px;
            border-radius: 5px;
            margin: 5px 0;
        '>
            <strong>{agendamento['data'].strftime('%d/%m/%Y')}</strong> - 
            {agendamento['banda']} ({NOMES_BANDAS[agendamento['banda']]}) - 
            Horário: {agendamento['horario']}
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Nenhum ensaio agendado para este mês.")

# Instruções para sincronização com GitHub
st.sidebar.markdown("---")
st.sidebar.info("""
**💡 Sincronização com GitHub:**
1. Faça upload do arquivo `agenda_ensaios.csv` para seu repositório
2. Atualize a variável `GITHUB_CSV_URL` no código
3. Para sincronização automática, configure GitHub Actions
""")