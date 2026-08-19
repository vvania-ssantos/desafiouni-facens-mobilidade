import time
import numpy as np
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------
# Configuração da Página (sempre no topo)
# ---------------------------------------------------------
st.set_page_config(
    page_title="SIGABEM — Digital Twin & 5G Control",
    page_icon="📡",
    layout="wide"
)

# ---------------------------------------------------------
# 1. CONTROLE DE ACESSO SIMPLIFICADO
# ---------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🚦 SIGABEM — Central de Controle de Mobilidade")
    st.subheader("Acesso de demonstração acadêmica • Sorocaba/SP")
    
    st.caption("Use qualquer e-mail e a senha **SIGABEM** para entrar no ambiente de demonstração.")
    
    with st.form("login_form"):
        email_input = st.text_input("E-mail:", placeholder="seu.email@exemplo.com")
        senha_input = st.text_input("Senha de acesso:", type="password", placeholder="Digite a senha")
        submit_button = st.form_submit_button("Acessar Painel")
        
        if submit_button:
            if senha_input.strip().upper() == "SIGABEM":
                st.session_state.authenticated = True
                st.session_state.user_email = email_input if email_input else "gestor@sigabem.gov.br"
                st.rerun()
            else:
                st.error("Senha incorreta. Use: **SIGABEM**")
    st.stop()

# ---------------------------------------------------------
# 2. MENU LATERAL - USUARIO & LOGOUT
# ---------------------------------------------------------
st.sidebar.write(f"👤 Logado como: **{st.session_state.user_email}**")
if st.sidebar.button("🚪 Sair"):
    st.session_state.authenticated = False
    st.rerun()

# ---------------------------------------------------------
# 3. CONEXÃO DIRETA COM POSTGRESQL (NEON.TECH)
# ---------------------------------------------------------
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=st.secrets["DB_HOST"],
            database=st.secrets["DB_NAME"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            port=st.secrets["DB_PORT"],
            sslmode="require",
            connect_timeout=10
        )
        return conn, None
    except Exception as e:
        return None, str(e)

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

def insert_telemetria(ponto, vel, lat, dens, alerta):
    conn, err = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO telemetria_trafego 
                (ponto_corredor, velocidade_media_kmh, latencia_5g_ms, densidade_veiculos, alerta_critico)
                VALUES (%s, %s, %s, %s, %s);
            """
            cursor.execute(query, (ponto, vel, lat, dens, alerta))
            conn.commit()
            cursor.close()
            conn.close()
            return True, None
        except Exception as e:
            if conn:
                conn.close()
            return False, str(e)
    return False, err

# ---------------------------------------------------------
# 4. DASHBOARD PRINCIPAL - MONITORAMENTO
# ---------------------------------------------------------
st.title("🚦 SIGABEM — Central de Controle de Mobilidade")
st.caption("Centro de Controle Urbano • Sorocaba/SP • Modo Simulação")

df_telemetria, db_error = fetch_telemetria()

if db_error:
    st.error(f"Erro de conexão com o banco de dados: `{db_error}`")

# ---------- STATUS RÁPIDO ----------
st.markdown("### Status Geral da Malha")

col1, col2, col3, col4 = st.columns(4)

latencia_media = round(df_telemetria['latencia_5g_ms'].mean(), 2) if not df_telemetria.empty else 1.5
velocidade_media = round(df_telemetria['velocidade_media_kmh'].mean(), 1) if not df_telemetria.empty else 0.0
tem_alerta = df_telemetria['alerta_critico'].any() if not df_telemetria.empty else False
qtd_registros = len(df_telemetria) if not df_telemetria.empty else 0

col1.metric("Estado da Malha", "Atenção" if tem_alerta else "Normal", delta="Monitoramento ativo")
col2.metric("Velocidade Média", f"{velocidade_media} km/h")
col3.metric("Latência (Simulada)", f"{latencia_media} ms")
col4.metric("Registros no Sistema", qtd_registros)

# ---------- ALERTA / EVENTO CRÍTICO (espaço preparado) ----------
if tem_alerta:
    st.error("⚠️ **EVENTO CRÍTICO DETECTADO** — Há corredor(es) com velocidade abaixo do esperado. Recomenda-se investigação.")
else:
    st.info("Nenhum evento crítico no momento. Monitoramento contínuo ativo.")

st.markdown("---")

# ---------- VISÃO PRINCIPAL ----------
st.markdown("### Visão da Malha Urbana")

col_left, col_right = st.columns([1.6, 1.4])

with col_left:
    st.markdown("**Modelo 3D da Área Monitorada**")

    # Lista de corredores com coordenadas fixas (simplificadas)
    corredores = [
        {"nome": "Av. Dom Aguirre (gNodeB_02)", "x": 2, "y": 8, "z": 20},
        {"nome": "Av. Afonso Vergueiro (gNodeB_01)", "x": 5, "y": 3, "z": 25},
        {"nome": "Av. Itavuvu (gNodeB_03)", "x": 8, "y": 6, "z": 30},
    ]

    fig_3d = go.Figure(data=[
        go.Scatter3d(
            x=[c["x"] for c in corredores],
            y=[c["y"] for c in corredores],
            z=[c["z"] for c in corredores],
            mode='markers+text',
            marker=dict(
                size=12,
                color=[c["z"] for c in corredores],
                colorscale='Plasma',
                opacity=0.85,
                symbol='diamond'
            ),
            text=[c["nome"] for c in corredores]
        )
    ])
    fig_3d.update_layout(
        scene=dict(xaxis_title='X', yaxis_title='Y', zaxis_title='Altura (m)'),
        margin=dict(l=0, r=0, b=0, t=0),
        height=340
    )
    st.plotly_chart(fig_3d, use_container_width=True)

with col_right:
    st.markdown("**Velocidade por Corredor**")
    if not df_telemetria.empty:
        fig_bar = px.bar(
            df_telemetria,
            x='ponto_corredor',
            y='velocidade_media_kmh',
            color='alerta_critico',
            color_discrete_map={True: '#EF553B', False: '#00CC96'},
            labels={'velocidade_media_kmh': 'Velocidade (km/h)', 'ponto_corredor': 'Corredor'}
        )
        fig_bar.update_layout(height=340, margin=dict(l=10, r=10, b=10, t=20), showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Nenhum dado disponível. Use o painel de simulação abaixo.")

# ---------- SIMULAÇÃO (mantida, mas com linguagem mais limpa) ----------
st.markdown("### Painel de Simulação")

c1, c2, c3, c4 = st.columns(4)
with c1:
    ponto_sel = st.selectbox("Corredor", ["Av. Dom Aguirre (gNodeB_02)", "Av. Afonso Vergueiro (gNodeB_01)", "Av. Itavuvu (gNodeB_03)"])
with c2:
    densidade = st.slider("Densidade de Veículos (veíc/km)", 20, 500, 180)
with c3:
    tempo_verde = st.slider("Tempo do Semáforo Verde (s)", 15, 120, 45)
with c4:
    perfil_5g = st.select_slider("Cenário de Conectividade (Simulação)", ["URLLC (Baixa Latência)", "eMBB (Alta Capacidade)", "mMTC (Alta Densidade)"])

if st.button("Simular e Registrar no Sistema"):
    vel_calculada = max(5.0, round(80.0 - (densidade * 0.15) + (tempo_verde * 0.2), 2))
    lat_calculada = round(1.5 if "URLLC" in perfil_5g else (6.5 if "eMBB" in perfil_5g else 15.0), 2)
    critico = bool(vel_calculada < 15.0 or lat_calculada > 10.0)
    
    sucesso, err_msg = insert_telemetria(ponto_sel, vel_calculada, lat_calculada, densidade, critico)
    if sucesso:
        st.toast(f"Simulação registrada • Velocidade: {vel_calculada} km/h", icon="✅")
        time.sleep(0.8)
        st.rerun()
    else:
        st.error(f"Erro ao registrar: {err_msg}")

with st.expander("Ver histórico registrado"):
    if not df_telemetria.empty:
        st.dataframe(df_telemetria, use_container_width=True)
    else:
        st.write("Nenhum registro encontrado.")