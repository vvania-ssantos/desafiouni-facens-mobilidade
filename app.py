import time
import numpy as np
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configuração da Página
st.set_page_config(
    page_title="SIGABEM — Digital Twin & 5G Control",
    page_icon="📡",
    layout="wide"
)

# 1. CONTROLE DE ACESSO VIA GOOGLE OAUTH
if not st.experimental_user.is_logged_in:
    st.title("🚦 SIGABEM — Acesso Restrito")
    st.subheader("Gêmeo Digital & Central de Controle de Mobilidade Urbana")
    st.write("Por favor, faça login com sua conta do Google para acessar a Central de Controle.")
    if st.button("🔑 Entrar com Google"):
        st.login()
    st.stop()

# 2. MENU LATERAL - DADOS DO USUÁRIO
user = st.experimental_user
st.sidebar.write(f"👤 Logado como: **{user.name}**")
st.sidebar.caption(f"E-mail: {user.email}")
if st.sidebar.button("Sair"):
    st.logout()

# 3. CONEXÃO COM POSTGRESQL (NEON)
def get_db_connection():
    try:
        conn = psycopg2.connect(
            st.secrets["POSTGRES_URL"],
            connect_timeout=5
        )
        return conn, None
    except Exception as e:
        return None, str(e)

# 4. FUNÇÃO PARA BUSCAR TELEMETRIA
def fetch_telemetria():
    conn, err = get_db_connection()
    if conn:
        try:
            query = "SELECT * FROM telemetria_trafego ORDER BY timestamp DESC LIMIT 100;"
            df = pd.read_sql(query, conn)
            conn.close()
            return df, None
        except Exception as e:
            if conn:
                conn.close()
            return pd.DataFrame(), str(e)
    return pd.DataFrame(), err

# 5. PAINEL PRINCIPAL DO SIGABEM
st.title("🚦 SIGABEM — Gêmeo Digital & Infraestrutura 5G")
st.caption("Central de Controle Urbano • Telemetria 5G URLLC • Simulação de Tráfego • Sorocaba/SP")

df_telemetria, db_error = fetch_telemetria()

if db_error:
    st.error(f"❌ **Erro de Conexão com o PostgreSQL (Neon):** `{db_error}`")
else:
    st.success("✅ **Conexão com PostgreSQL (Neon) estabelecida com sucesso!**")