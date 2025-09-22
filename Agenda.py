import streamlit as st
import pandas as pd
import datetime
import calendar
from datetime import date

# Configuração da página para mobile
st.set_page_config(
    page_title="Agenda de Ensaios", 
    page_icon="🎵", 
    layout="wide",
    initial_sidebar_state="collapsed"  # Sidebar fechada por padrão no mobile
)

# Senha de acesso
SENHA_CORRETA = "firmeza"

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

def verificar_senha():
    """Verifica se o usuário está autenticado"""
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
    return st.session_state.autenticado

# ---------------- AUTENTICAÇÃO ---------------- #

def pagina_login():
    """Página de login"""
    st.title("🎵 Agenda de Ensaios ICCFV")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login"):
            st.subheader("🔐 Acesso Restrito")
            senha = st.text_input("Digite a senha:", type="password")
            enviar = st.form_submit_button("Entrar")
            
            if enviar:
                if senha == SENHA_CORRETA:
                    st.session_state.autenticado = True
                    st.success("✅ Acesso permitido!")
                    st.rerun()
                else:
                    st.error("❌ Senha incorreta!")
    
    # Informações públicas (visíveis sem login)
    st.markdown("---")
    st.subheader("📅 Calendário Público")
    
    # Carregar dados para visualização pública
    df_agenda = carregar_dados()
    hoje = date.today()
    
    col1, col2 = st.columns(2)
    with col1:
        mes_atual = st.selectbox("Mês", range(1, 13), index=hoje.month-1, format_func=lambda m: MESES_PT[m])
    with col2:
        ano_atual = st.selectbox("Ano", range(2023, 2031), index=hoje.year-2023)
    
    # Calendário simplificado para mobile
    st.subheader(f"Calendário de {MESES_PT[mes_atual]} de {ano_atual}")
    
    # Calendário adaptado para mobile
    cal = calendar.monthcalendar(ano_atual, mes_atual)
    
    # Cabeçalho dos dias da semana (abreviado para mobile)
    dias_semana_mobile = ['S', 'T', 'Q', 'Q', 'S', 'S', 'D']
    cols = st.columns(7)
    
    for i, dia in enumerate(dias_semana_mobile):
        cols[i].markdown(f"<div style='text-align: center; font-weight: bold; font-size: 0.8em;'>{dia}</div>", 
                        unsafe_allow_html=True)
    
    for semana in cal:
        cols = st.columns(7)
        for i, dia in enumerate(semana):
            with cols[i]:
                if dia == 0:
                    st.markdown("<div style='height:60px;'></div>", unsafe_allow_html=True)
                else:
                    data_dia = date(ano_atual, mes_atual, dia)
                    agendamentos_dia = obter_agendamentos_do_dia(df_agenda, data_dia)
                    
                    if not agendamentos_dia.empty:
                        # Mostrar apenas ponto colorido no mobile
                        cor_principal = CORES_BANDAS[agendamentos_dia.iloc[0]['banda']]
                        estilo = f"""
                        <div style='
                            background-color: white;
                            padding: 2px;
                            border-radius: 5px;
                            height: 60px;
                            border: 2px solid {"#ff4444" if data_dia == hoje else "#dee2e6"};
                            text-align: center;
                            position: relative;
                        '>
                            <div style='font-size: 1em;'>{dia}</div>
                            <div style='width: 12px; height: 12px; background-color: {cor_principal}; 
                                     border-radius: 50%; position: absolute; bottom: 3px; left: 50%; 
                                     transform: translateX(-50%);'></div>
                        </div>
                        """
                    else:
                        estilo = f"""
                        <div style='
                            background-color: {'#fff0f0' if data_dia == hoje else 'white'};
                            padding: 2px;
                            border-radius: 5px;
                            height: 60px;
                            border: 1px solid {'#ff4444' if data_dia == hoje else '#dee2e6'};
                            text-align: center;
                        '>
                            <div style='font-size: 1em;'>{dia}</div>
                        </div>
                        """
                    st.markdown(estilo, unsafe_allow_html=True)
    
    # Legenda simplificada
    st.markdown("---")
    st.subheader("🎨 Legenda")
    
    # Legenda em formato compacto para mobile
    cols = st.columns(3)
    bandas_list = list(CORES_BANDAS.items())
    
    for i in range(0, len(bandas_list), 3):
        for j in range(3):
            if i + j < len(bandas_list):
                banda, cor = bandas_list[i + j]
                with cols[j]:
                    st.markdown(f"""
                    <div style='
                        background-color: {cor};
                        color: white;
                        padding: 5px;
                        border-radius: 3px;
                        text-align: center;
                        font-size: 0.8em;
                        margin: 2px;
                    '>
                        {banda}
                    </div>
                    """, unsafe_allow_html=True)

# ---------------- PÁGINA PRINCIPAL (APÓS LOGIN) ---------------- #

def pagina_principal():
    """Página principal após autenticação"""
    
    # Botão de logout no topo
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🚪 Sair"):
            st.session_state.autenticado = False
            st.rerun()
    
    st.title("🎵 Agenda de Ensaios ICCFV")
    st.markdown("---")
    
    # Carregar dados
    df_agenda = carregar_dados()
    
    # Data atual
    hoje = date.today()
    
    # Sidebar para mobile (colapsável)
    with st.sidebar:
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
    
    # Layout principal responsivo
    col1, col2 = st.columns([1, 1])
    with col1:
        mes_atual = st.selectbox("Mês", range(1, 13), index=hoje.month-1, format_func=lambda m: MESES_PT[m])
    with col2:
        ano_atual = st.selectbox("Ano", range(2023, 2031), index=hoje.year-2023)
    
    # Calendário responsivo
    st.header(f"Calendário de {MESES_PT[mes_atual]} de {ano_atual}")
    
    cal = calendar.monthcalendar(ano_atual, mes_atual)
    dias_semana = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
    
    # Cabeçalho responsivo
    cols = st.columns(7)
    for i, dia in enumerate(dias_semana):
        cols[i].markdown(f"<div style='text-align: center; font-weight: bold; font-size: 0.9em;'>{dia}</div>", 
                        unsafe_allow_html=True)
    
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
                            eventos_html += f"<div style='font-size:0.7em; background:{cor}; color:white; border-radius:3px; margin:1px; padding:1px;'>{ag['banda']} {ag['horario']}</div>"
                        
                        estilo = f"""
                        <div style='
                            background-color: white;
                            padding: 3px;
                            border-radius: 5px;
                            height: 100px;
                            border: 2px solid {"#ff4444" if data_dia == hoje else "#dee2e6"};
                            font-weight: bold;
                            text-align: center;
                        '>
                            <div style='font-size: 1em; margin-bottom: 2px;'>{dia}</div>
                            {eventos_html}
                        </div>
                        """
                    else:
                        estilo = f"""
                        <div style='
                            background-color: {'#fff0f0' if data_dia == hoje else 'white'};
                            padding: 3px;
                            border-radius: 5px;
                            height: 100px;
                            border: 1px solid {'#ff4444' if data_dia == hoje else '#dee2e6'};
                            text-align: center;
                        '>
                            <div style='font-size: 1em; margin-bottom: 2px;'>{dia}</div>
                            <div style='color: #666; font-size: 0.7em;'>Disponível</div>
                        </div>
                        """
                    st.markdown(estilo, unsafe_allow_html=True)
    
    # Lista de agendamentos
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
                        font-size: 0.9em;
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
    
    # Legenda de cores
    st.markdown("---")
    st.subheader("🎨 Legenda de Cores das Bandas")
    
    cols = st.columns(len(CORES_BANDAS))
    for i, (banda, cor) in enumerate(CORES_BANDAS.items()):
        with cols[i]:
            st.markdown(f"""
            <div style='
                background-color: {cor};
                color: white;
                padding: 8px;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
                font-size: 0.8em;
                margin: 2px;
            '>
                {banda}
            </div>
            """, unsafe_allow_html=True)

# ---------------- APLICAÇÃO PRINCIPAL ---------------- #

def main():
    """Função principal da aplicação"""
    if verificar_senha():
        pagina_principal()
    else:
        pagina_login()

if __name__ == "__main__":
    main()
