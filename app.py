import time

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine, text

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

    st.caption(
        "Este login é simplificado para fins de demonstração acadêmica "
        "(Residência TIC / Atividade Integrada) e não implementa autenticação "
        "de produção. Use qualquer e-mail e a senha **SIGABEM** para entrar."
    )

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
# 3. CONEXÃO COM POSTGRESQL (NEON.TECH) — COM CACHE
# ---------------------------------------------------------
# st.cache_resource mantém UMA conexão viva entre reruns do Streamlit,
# em vez de abrir uma conexão nova a cada clique/rerun. Isso evita
# estourar o limite de conexões simultâneas do plano free do Neon
# durante uma apresentação ao vivo.
@st.cache_resource
def get_db_engine():
    conn_str = (
        f"postgresql+psycopg2://{st.secrets['DB_USER']}:{st.secrets['DB_PASSWORD']}"
        f"@{st.secrets['DB_HOST']}:{st.secrets['DB_PORT']}/{st.secrets['DB_NAME']}"
        f"?sslmode=require"
    )
    return create_engine(conn_str, pool_pre_ping=True, connect_args={"connect_timeout": 10})


# st.cache_data guarda o resultado da query por alguns segundos (ttl).
# Assim, vários widgets/reruns na mesma janela de tempo não disparam
# uma query nova a cada um — só depois que o ttl expira ou os dados mudam.
@st.cache_data(ttl=15)
def fetch_telemetria():
    try:
        engine = get_db_engine()
        query = "SELECT * FROM telemetria_trafego ORDER BY timestamp DESC LIMIT 200;"
        df = pd.read_sql(query, engine)
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)


def insert_telemetria(ponto, vel, lat, dens, alerta):
    try:
        engine = get_db_engine()
        query = text("""
            INSERT INTO telemetria_trafego
            (ponto_corredor, velocidade_media_kmh, latencia_5g_ms, densidade_veiculos, alerta_critico)
            VALUES (:ponto, :vel, :lat, :dens, :alerta);
        """)
        with engine.begin() as conn:
            conn.execute(query, {"ponto": ponto, "vel": vel, "lat": lat, "dens": dens, "alerta": alerta})
        return True, None
    except Exception as e:
        return False, str(e)

# ---------------------------------------------------------
# CONTROLE DA JORNADA — MALHAVIVA VR
# ---------------------------------------------------------

if "etapa" not in st.session_state:
    st.session_state.etapa = "monitoramento"

if "corredor_selecionado" not in st.session_state:
    st.session_state.corredor_selecionado = None

if "evento_investigacao" not in st.session_state:
    st.session_state.evento_investigacao = False

    def avancar_etapa(nova_etapa):
    st.session_state.etapa = nova_etapa
    st.rerun()
    
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
    st.markdown("**Modelo 3D — Estado Atual dos Corredores (dados reais do banco)**")

    # Posições fixas de layout para os 3 corredores monitorados (não temos
    # coordenadas GPS reais dos sensores — isso é apenas o posicionamento
    # espacial no gráfico, deixado claro no texto abaixo). O que É real
    # aqui é o eixo Z e a cor: vêm direto da telemetria mais recente no
    # banco, não de números inventados como antes.
    layout_posicoes = {
        "Av. Dom Aguirre (gNodeB_02)": (2, 8),
        "Av. Afonso Vergueiro (gNodeB_01)": (5, 3),
        "Av. Itavuvu (gNodeB_03)": (8, 6),
    }

    if not df_telemetria.empty:
        resumo = (
            df_telemetria
            .groupby("ponto_corredor")
            .agg(
                velocidade_media_kmh=("velocidade_media_kmh", "mean"),
                alerta_critico=("alerta_critico", "any"),
                latencia_5g_ms=("latencia_5g_ms", "mean"),
            )
            .reset_index()
        )
    else:
        resumo = pd.DataFrame(columns=["ponto_corredor", "velocidade_media_kmh", "alerta_critico", "latencia_5g_ms"])

    pontos_x, pontos_y, pontos_z, textos, cores = [], [], [], [], []
    for nome, (x, y) in layout_posicoes.items():
        linha = resumo[resumo["ponto_corredor"] == nome]
        if not linha.empty:
            z = float(linha["velocidade_media_kmh"].iloc[0])
            crit = bool(linha["alerta_critico"].iloc[0])
            lat_ms = float(linha["latencia_5g_ms"].iloc[0])
            texto = f"{nome}<br>{z:.1f} km/h • {lat_ms:.1f} ms"
        else:
            z = 0.0
            crit = False
            texto = f"{nome}<br>sem registros ainda"
        pontos_x.append(x)
        pontos_y.append(y)
        pontos_z.append(z)
        textos.append(texto)
        cores.append("#EF553B" if crit else "#00CC96")

    fig_3d = go.Figure(data=[
        go.Scatter3d(
            x=pontos_x, y=pontos_y, z=pontos_z,
            mode='markers+text',
            marker=dict(size=12, color=cores, opacity=0.9, symbol='diamond'),
            text=[t.split("<br>")[0] for t in textos],
            hovertext=textos,
            hoverinfo="text",
        )
    ])
    fig_3d.update_layout(
        scene=dict(xaxis_title='X (layout)', yaxis_title='Y (layout)', zaxis_title='Velocidade média (km/h)'),
        margin=dict(l=0, r=0, b=0, t=0),
        height=340
    )
    st.plotly_chart(fig_3d, use_container_width=True)
    st.caption(
        "Posição X/Y é apenas layout ilustrativo (sem coordenadas GPS no dataset atual). "
        "Altura, cor e valores no hover vêm da telemetria real mais recente do banco."
    )

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

st.markdown("---")

# ---------- SIMULAÇÃO (mantida, mas com linguagem mais limpa) ----------
st.markdown("### Painel de Simulação")

c1, c2, c3, c4 = st.columns(4)
with c1:
    ponto_sel = st.selectbox("Corredor", list(layout_posicoes.keys()))
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
        fetch_telemetria.clear()  # invalida o cache pra próxima leitura já vir atualizada
        time.sleep(0.8)
        st.rerun()
    else:
        st.error(f"Erro ao registrar: {err_msg}")

with st.expander("Ver histórico registrado"):
    if not df_telemetria.empty:
        st.dataframe(df_telemetria, use_container_width=True)
    else:
        st.write("Nenhum registro encontrado.")