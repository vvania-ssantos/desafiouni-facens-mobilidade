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

# ---------------------------------------------------------
# 1. CONTROLE DE ACESSO VIA GOOGLE OAUTH (SEGURO)
# ---------------------------------------------------------
try:
    is_logged_in = st.experimental_user.is_logged_in
except AttributeError:
    is_logged_in = hasattr(st, "user") and bool(getattr(st.user, "email", None))

if not is_logged_in:
    st.title("🚦 SIGABEM — Acesso Restrito")
    st.subheader("Gêmeo Digital & Central de Controle de Mobilidade Urbana")
    st.write("Por favor, faça login com sua conta do Google para acessar a Central de Controle.")
    if st.button("🔑 Entrar com Google"):
        st.login("google")
    st.stop()

# ---------------------------------------------------------
# 2. MENU LATERAL - DADOS DO USUÁRIO & SAIR
# ---------------------------------------------------------
user = st.experimental_user if hasattr(st, "experimental_user") else st.user
user_email = getattr(user, "email", "Usuário Autenticado")
user_name = getattr(user, "name", user_email)

st.sidebar.write(f"👤 Logado como: **{user_name}**")
st.sidebar.caption(f"E-mail: {user_email}")

if st.sidebar.button("Sair"):
    st.logout()

# ---------------------------------------------------------
# 3. FUNÇÕES DE BANCO DE DADOS (POSTGRESQL / NEON.TECH)
# ---------------------------------------------------------
def get_db_connection():
    try:
        conn = psycopg2.connect(
            st.secrets["POSTGRES_URL"],
            connect_timeout=5
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
# 4. DASHBOARD PRINCIPAL - SIGABEM
# ---------------------------------------------------------
st.title("🚦 SIGABEM — Gêmeo Digital & Infraestrutura 5G")
st.caption("Central de Controle Urbano • Telemetria 5G URLLC • Simulação de Tráfego • Sorocaba/SP")

df_telemetria, db_error = fetch_telemetria()

if db_error:
    st.error(f"❌ **Erro de Conexão com o PostgreSQL (Neon):** `{db_error}`")

tem_alerta = df_telemetria['alerta_critico'].any() if not df_telemetria.empty else False

# PAINEL DE TELEMETRIA 5G
st.markdown("### 📡 Status da Rede 5G Standalone (SA) & Edge Computing")
m1, m2, m3, m4 = st.columns(4)

latencia_media_5g = round(df_telemetria['latencia_5g_ms'].mean(), 2) if not df_telemetria.empty else 0.0

m1.metric(label="📶 Tecnologia de Conexão", value="5G Standalone (gNodeB)", delta="3.5 GHz Sub-6")
m2.metric(label="⚡ Latência Média da Rede", value=f"{latencia_media_5g} ms", delta="URLLC Ativo" if latencia_media_5g < 5 else "Risco de Jitter")
m3.metric(label="📊 Slice de Rede (Network Slicing)", value="URLLC / eMBB", delta="Prioridade Crítica")
m4.metric(label="🖥️ Processamento na Borda (MEC)", value="Ativo - Sorocaba Node", delta="100% Sincronizado")

if tem_alerta:
    st.error("🚨 **CRITICAL ALERT 5G:** Congestionamento severo detectado no PostgreSQL! Acionando priorização de tráfego via corte de rede (Network Slice URLLC).")
else:
    st.success("✅ **REDE 5G OPERACIONAL:** Latência ultra-baixa confirmada para o Gêmeo Digital.")

st.markdown("---")

# VISUALIZAÇÕES EM COLUNAS
col_left, col_mid, col_right = st.columns([1.5, 2, 1.5])

with col_left:
    st.markdown("**🏢 Modelo 3D Urbano & Antenas 5G (gNodeB)**")
    np.random.seed(42)
    n_b = 15
    bx = np.random.uniform(0, 10, n_b)
    by = np.random.uniform(0, 10, n_b)
    bz = np.random.uniform(10, 60, n_b)
    
    fig_3d = go.Figure(data=[
        go.Scatter3d(
            x=bx, y=by, z=bz,
            mode='markers+text',
            marker=dict(size=12, color=bz, colorscale='Plasma', opacity=0.85, symbol='diamond'),
            text=["Antena 5G" if i % 4 == 0 else f"Edifício {i}" for i in range(n_b)]
        )
    ])
    fig_3d.update_layout(scene=dict(xaxis_title='X', yaxis_title='Y', zaxis_title='Altura (m)'), margin=dict(l=0, r=0, b=0, t=0), height=300)
    st.plotly_chart(fig_3d, use_container_width=True)

with col_mid:
    st.markdown("**🚥 Velocidade x Congestionamento nos Corredores**")
    if not df_telemetria.empty:
        fig_line = px.bar(
            df_telemetria, x='ponto_corredor', y='velocidade_media_kmh', color='alerta_critico',
            color_discrete_map={True: '#EF553B', False: '#00CC96'},
            labels={'velocidade_media_kmh': 'Velocidade Média (km/h)', 'ponto_corredor': 'Célula 5G / Corredor'}
        )
        fig_line.update_layout(height=300, margin=dict(l=10, r=10, b=10, t=20))
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Nenhum registro no Neon. Use o painel abaixo para simular e gravar dados.")

with col_right:
    st.markdown("**📈 Latência Comparativa: 5G URLLC vs 4G Legacy (ms)**")
    if not df_telemetria.empty:
        df_comparativo = pd.DataFrame({
            'Corredor': df_telemetria['ponto_corredor'],
            'Latência 5G (ms)': df_telemetria['latencia_5g_ms'],
            'Latência 4G Teórica (ms)': [l * 4.5 for l in df_telemetria['latencia_5g_ms']]
        })
        fig_comp = px.bar(
            df_comparativo, x='Corredor', y=['Latência 5G (ms)', 'Latência 4G Teórica (ms)'],
            barmode='group', labels={'value': 'Latência (ms)', 'variable': 'Tecnologia'}
        )
        fig_comp.update_layout(height=300, margin=dict(l=10, r=10, b=10, t=20))
        st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.info("Aguardando inserções para exibir gráficos de latência...")

st.markdown("---")

# PAINEL DE SIMULAÇÃO DE TRÁFEGO
st.markdown("**🎛️ Painel de Simulação de Tráfego e Parâmetros da Rede 5G**")

c1, c2, c3, c4 = st.columns(4)
with c1:
    ponto_sel = st.selectbox("Corredor / Antena 5G (gNodeB)", ["Av. Dom Aguirre (gNodeB_02)", "Av. Afonso Vergueiro (gNodeB_01)", "Av. Itavuvu (gNodeB_03)"])
with c2:
    densidade = st.slider("Densidade de Veículos (veíc/km)", 20, 500, 180)
with c3:
    tempo_verde = st.slider("Tempo do Semáforo Verde (s)", 15, 120, 45)
with c4:
    perfil_5g = st.select_slider("Fatia de Rede 5G (Network Slice)", ["URLLC (Ultra-Low Latency)", "eMBB (High Throughput)", "mMTC (IoT Density)"])

if st.button("🚀 Simular e Persistir no PostgreSQL (Neon)"):
    vel_calculada = max(5.0, round(80.0 - (densidade * 0.15) + (tempo_verde * 0.2), 2))
    lat_calculada = round(1.5 if perfil_5g == "URLLC (Ultra-Low Latency)" else (6.5 if perfil_5g == "eMBB (High Throughput)" else 15.0), 2)
    critico = bool(vel_calculada < 15.0 or lat_calculada > 10.0)
    
    sucesso, err_msg = insert_telemetria(ponto_sel, vel_calculada, lat_calculada, densidade, critico)
    if sucesso:
        st.toast(f"Gravado no Neon! Velocidade: {vel_calculada} km/h", icon="📡")
        time.sleep(0.8)
        st.rerun()
    else:
        st.error(f"Erro ao gravar no PostgreSQL: {err_msg}")

with st.expander("📄 Ver Histórico Real Persistido no Neon.tech"):
    if not df_telemetria.empty:
        st.dataframe(df_telemetria, use_container_width=True)
    else:
        st.write("Nenhum registro encontrado no banco de dados Neon.")