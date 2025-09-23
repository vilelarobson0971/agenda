# Agenda.py
import streamlit as st
import pandas as pd
import datetime
import calendar
import json
import os
from datetime import date

# IMPORTS opcionais (tratados para dar mensagem amigável se faltar no ambiente)
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
except Exception:
    gspread = None
    ServiceAccountCredentials = None

# --------- CONFIGURAÇÃO (AJUSTE AQUI) ----------
# Se preferir, coloque o ID da planilha em st.secrets["google"]["sheet_id"]
SHEET_ID = st.secrets.get("google", {}).get("sheet_id", "COLOQUE_SEU_ID_AQUI")
SHEET_NAME = st.secrets.get("google", {}).get("sheet_name", "Página1")  # ou "Sheet1"

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
    if gspread is None or ServiceAccountCredentials is None:
        st.error(
            "Bibliotecas necessárias não encontradas: adicione `gspread` e `oauth2client` ao requirements.txt "
            "e redeploy no Streamlit Cloud. Ex.: gspread==5.7.2\noauth2client==4.1.3"
        )
        st.stop()

@st.cache_resource
def conectar_sheets():
    """Conecta ao Google Sheets usando st.secrets (preferível) ou credenciais locais (fallback)."""
    _check_libs()
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # 1) Preferência: credenciais via st.secrets (campo google.credentials com JSON)
    if "google" in st.secrets and "credentials" in st.secrets["google"]:
        try:
            # Se já é um dicionário, usa diretamente
            if isinstance(st.secrets["google"]["credentials"], dict):
                creds_dict = st.secrets["google"]["credentials"]
            else:
                # Se é string, tenta converter de JSON
                creds_dict = json.loads(st.secrets["google"]["credentials"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        except Exception as e:
            st.error(f"Erro ao ler credenciais do st.secrets: {e}")
            st.stop()
    else:
        # 2) Fallback: tentar arquivo local 'credenciais.json'
        path = "credenciais.json"
        if os.path.exists(path):
            try:
                creds = ServiceAccountCredentials.from_json_keyfile_name(path, scope)
            except Exception as e:
                st.error(f"Erro ao carregar '{path}': {e}")
                st.stop()
        else:
            st.error(
                "Credenciais não encontradas. Cole o JSON em st.secrets['google']['credentials'] ou "
                "faça upload de 'credenciais.json' no diretório do app."
            )
            st.stop()

    try:
        cliente = gspread.authorize(creds)
        planilha = cliente.open_by_key(SHEET_ID)
        aba = planilha.worksheet(SHEET_NAME)
        return aba
    except Exception as e:
        st.error(f"Erro ao conectar com Google Sheets: {e}")
        st.stop()

def carregar_dados():
    """Carrega os registros do Google Sheets para DataFrame."""
    try:
        aba = conectar_sheets()
        dados = aba.get_all_records()
        if not dados:
            return pd.DataFrame(columns=["data", "banda", "horario"])
        df = pd.DataFrame(dados)
        
        # Verifica se as colunas necessárias existem
        expected = ["data", "banda", "horario"]
        for col in expected:
            if col not in df.columns:
                df[col] = ""

        # Converte data (assume dd/mm/YYYY armazenado)
        df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce").dt.date
        return df[expected]
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame(columns=["data", "banda", "horario"])

def salvar_dados(df):
    """Salva DataFrame no Google Sheets (substitui todo o conteúdo)."""
    try:
        aba = conectar_sheets()
        # Formatamos a data para dd/mm/YYYY na planilha
        df_to_save = df.copy()
        df_to_save["data"] = df_to_save["data"].apply(lambda d: d.strftime("%d/%m/%Y") if pd.notna(d) and d != "" else "")
        
        # Prepara os dados para salvar
        dados_para_salvar = [df_to_save.columns.values.tolist()] + df_to_save.astype(str).values.tolist()
        
        # Limpa a planilha e salva novos dados
        aba.clear()
        aba.update(dados_para_salvar)
        st.success("✅ Agendamento salvo no Google Sheets com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar dados: {e}")

def obter_agendamentos_do_dia(df, dia):
    """Retorna agendamentos para um dia específico."""
    if df.empty:
        return pd.DataFrame(columns=["data", "banda", "horario"])
    return df[df["data"] == dia]

# --------- UI ---------
st.set_page_config(page_title="Agenda de Ensaios", page_icon="🎵", layout="wide")
st.title("🎵 Agenda de Ensaios de Bandas")
st.markdown("---")

# Carrega agenda
df_agenda = carregar_dados()

hoje = date.today()
mes_atual = st.sidebar.selectbox("Mês", list(range(1, 13)), index=hoje.month-1, format_func=lambda m: MESES_PT[m])
ano_atual = st.sidebar.selectbox("Ano", list(range(2023, 2031)), index=hoje.year-2023)

# Novo agendamento
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
        horario_str = horario_agendamento.strftime("%H:%M")

        # Conflito: mesma data + mesmo horário
        if not df_agenda.empty:
            conflito = df_agenda[
                (df_agenda["data"] == data_agendamento) &
                (df_agenda["horario"] == horario_str)
            ]
            if not conflito.empty:
                st.sidebar.error(f"❌ Já existe ensaio em {data_agendamento.strftime('%d/%m/%Y')} às {horario_str}")
            else:
                novo = pd.DataFrame({
                    "data": [data_agendamento],
                    "banda": [banda_selecionada],
                    "horario": [horario_str]
                })
                df_agenda = pd.concat([df_agenda, novo], ignore_index=True)
                salvar_dados(df_agenda)
                st.rerun()
        else:
            # Primeiro agendamento
            novo = pd.DataFrame({
                "data": [data_agendamento],
                "banda": [banda_selecionada],
                "horario": [horario_str]
            })
            df_agenda = novo
            salvar_dados(df_agenda)
            st.rerun()

# Calendário
st.header(f"Calendário de {MESES_PT[mes_atual]} de {ano_atual}")
cal = calendar.monthcalendar(ano_atual, mes_atual)
dias_semana = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']

cols = st.columns(7)
for i, dia in enumerate(dias_semana):
    cols[i].markdown(f"<div style='text-align:center;font-weight:bold'>{dia}</div>", unsafe_allow_html=True)

for semana in cal:
    cols = st.columns(7)
    for i, d in enumerate(semana):
        with cols[i]:
            if d == 0:
                st.markdown("<div style='height:100px;background-color:#f8f9fa;border:1px solid #dee2e6;border-radius:5px;'></div>", unsafe_allow_html=True)
            else:
                data_dia = date(ano_atual, mes_atual, d)
                ags = obter_agendamentos_do_dia(df_agenda, data_dia)
                if not ags.empty:
                    eventos = ""
                    for _, ag in ags.iterrows():
                        cor = CORES_BANDAS.get(ag['banda'], "#666")
                        eventos += f"<div style='font-size:0.8em;background:{cor};color:white;border-radius:3px;margin:2px;padding:2px;'>{ag['banda']} {ag['horario']}</div>"
                    estilo = f"""
                    <div style='background-color:white;padding:4px;border-radius:5px;height:100px;border:3px solid {"#ff4444" if data_dia==hoje else "#dee2e6"};text-align:center;'>
                        <div style='font-size:1.1em;margin-bottom:3px;'>{d}</div>
                        {eventos}
                    </div>
                    """
                else:
                    estilo = f"""
                    <div style='background-color: {'#fff0f0' if data_dia==hoje else 'white'};padding:4px;border-radius:5px;height:100px;border:2px solid {'#ff4444' if data_dia==hoje else '#dee2e6'};text-align:center;'>
                        <div style='font-size:1.1em;margin-bottom:3px;'>{d}</div>
                        <div style='color:#666;font-size:0.8em;'>Disponível</div>
                    </div>
                    """
                st.markdown(estilo, unsafe_allow_html=True)

# Lista do mês com opção de excluir
st.markdown("---")
st.subheader("📋 Agendamentos do Mês")

if not df_agenda.empty:
    # Filtra agendamentos do mês selecionado
    agendamentos_mes = df_agenda[
        (df_agenda['data'].apply(lambda x: x.month) == mes_atual) &
        (df_agenda['data'].apply(lambda x: x.year) == ano_atual)
    ].sort_values(by=["data", "horario"]).reset_index(drop=True)
    
    # Adiciona índice original para exclusão
    agendamentos_mes['index_original'] = agendamentos_mes.index

    if not agendamentos_mes.empty:
        for idx, row in agendamentos_mes.iterrows():
            cor = CORES_BANDAS.get(row['banda'], "#666")
            c1, c2 = st.columns([9, 1])
            with c1:
                st.markdown(f"""
                <div style='background-color:{cor};color:white;padding:12px;border-radius:5px;margin:5px 0;font-weight:bold;'>
                    📅 {row['data'].strftime('%d/%m/%Y')} - 🎵 {row['banda']} - ⏰ {row['horario']}
                </div>
                """, unsafe_allow_html=True)
            with c2:
                if st.button("🗑", key=f"del_{idx}"):
                    # Remove o agendamento do DataFrame principal
                    index_para_remover = agendamentos_mes.loc[idx, 'index_original']
                    df_agenda = df_agenda.drop(index_para_remover).reset_index(drop=True)
                    salvar_dados(df_agenda)
                    st.rerun()
    else:
        st.info("Nenhum ensaio agendado para este mês.")
else:
    st.info("Nenhum ensaio agendado ainda.")

# Rodapé / instruções
st.sidebar.markdown("---")
st.sidebar.info("""
**Como funciona**
- As entradas são salvas direto no Google Sheets.
- Se estiver usando Streamlit Cloud, coloque o JSON nas Secrets: [google] credentials = \"\"\"{...json...}\"\"\"
- Certifique-se de ter adicionado gspread e oauth2client no requirements.txt e redeploy.
""")

# Debug (opcional - remova em produção)
with st.sidebar.expander("🔧 Debug"):
    st.write(f"Total de agendamentos: {len(df_agenda)}")
    if not df_agenda.empty:
        st.write("Últimos agendamentos:")
        st.dataframe(df_agenda.tail(3))
