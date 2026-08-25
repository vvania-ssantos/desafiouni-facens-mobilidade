import time

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
@st.cache_resource
def get_db_engine():
    conn_str = (
        f"postgresql+psycopg2://{st.secrets['DB_USER']}:{st.secrets['DB_PASSWORD']}"
        f"@{st.secrets['DB_HOST']}:{st.secrets['DB_PORT']}/{st.secrets['DB_NAME']}"
        f"?sslmode=require"
    )
    return create_engine(conn_str, pool_pre_ping=True, connect_args={"connect_timeout": 10})


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


def calcular_simulacao(densidade, tempo_verde, perfil_5g):
    vel_calculada = max(5.0, round(80.0 - (densidade * 0.15) + (tempo_verde * 0.2), 2))
    lat_calculada = round(1.5 if "URLLC" in perfil_5g else (6.5 if "eMBB" in perfil_5g else 15.0), 2)
    critico = bool(vel_calculada < 15.0 or lat_calculada > 10.0)
    return vel_calculada, lat_calculada, critico

LAYOUT_POSICOES = {
    "Av. Dom Aguirre (gNodeB_02)": (2, 8),
    "Av. Afonso Vergueiro (gNodeB_01)": (5, 3),
    "Av. Itavuvu (gNodeB_03)": (8, 6),
}


def construir_figura_3d(df_telemetria, altura=340):
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
    for nome, (x, y) in LAYOUT_POSICOES.items():
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

    fig = go.Figure(data=[
        go.Scatter3d(
            x=pontos_x, y=pontos_y, z=pontos_z,
            mode='markers+text',
            marker=dict(size=12, color=cores, opacity=0.9, symbol='diamond'),
            text=[t.split("<br>")[0] for t in textos],
            hovertext=textos,
            hoverinfo="text",
        )
    ])
    fig.update_layout(
        scene=dict(
            xaxis_title='X (layout)', yaxis_title='Y (layout)', zaxis_title='Velocidade média (km/h)',
            # Câmera fixa num ângulo isométrico legível — sem isso, o Plotly abre
            # com um ângulo padrão que costuma ficar ruim em telas pequenas até
            # o usuário arrastar manualmente para ajustar.
            camera=dict(eye=dict(x=1.4, y=1.4, z=1.1)),
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        height=altura
    )
    return fig


def exibir_grafico_3d(fig, key):
    """Renderiza o gráfico 3D sem barra de ferramentas (que fica minúscula e
    difícil de tocar em telas pequenas). A altura real já vem definida na
    própria figura (parâmetro `altura` de construir_figura_3d) — não dá para
    reduzi-la depois via CSS de página, porque o Plotly desenha o gráfico no
    tamanho configurado internamente; tentar encolher só o contêiner por
    fora deixa o gráfico cortado/espremido em vez de menor de verdade."""
    st.plotly_chart(
        fig,
        width='stretch',
        key=key,
        config={"displayModeBar": False, "responsive": True},
    )

ETAPAS = [
    ("monitoramento",     "👁",  "Monitoramento"),
    ("evento_critico",    "⚠️",  "Evento"),
    ("ativacao_vr",       "🥽",  "VR"),
    ("investigacao",      "🔎",  "Investigação"),
    ("analise_temporal",  "📈",  "Análise"),
    ("simulacao",         "🧪",  "Simulação"),
    ("decisao",           "✅",  "Decisão"),
]

CAUSAS_PROVAVEIS = [
    "Alta densidade de veículos",
    "Falha de sincronismo semafórico",
    "Degradação de sinal 5G",
    "Obra / interferência externa",
    "Outro",
]

if "etapa" not in st.session_state:
    st.session_state.etapa = "monitoramento"
if "corredor_selecionado" not in st.session_state:
    st.session_state.corredor_selecionado = None
if "causa_provavel" not in st.session_state:
    st.session_state.causa_provavel = None
if "observacao_investigacao" not in st.session_state:
    st.session_state.observacao_investigacao = ""
if "simulacao_resultado" not in st.session_state:
    st.session_state.simulacao_resultado = None
if "decisao_registrada" not in st.session_state:
    st.session_state.decisao_registrada = False


def avancar_etapa(nova_etapa: str):
    st.session_state.etapa = nova_etapa
    st.rerun()


def barra_jornada():
    chaves = [e[0] for e in ETAPAS]
    idx_atual = chaves.index(st.session_state.etapa)
    cols = st.columns(len(ETAPAS))
    for i, (chave, icone, label) in enumerate(ETAPAS):
        with cols[i]:
            if i < idx_atual:
                estilo = "opacity:0.45"
            elif i == idx_atual:
                estilo = "font-weight:700;border-bottom:3px solid #2ecc71"
            else:
                estilo = "opacity:0.25"
            st.markdown(
                f"<div style='text-align:center;{estilo}'>{icone}<br><small>{label}</small></div>",
                unsafe_allow_html=True,
            )

st.title("🚦 SIGABEM — Central de Controle de Mobilidade")
st.caption("Centro de Controle Urbano • Sorocaba/SP • Modo Simulação")
barra_jornada()

df_telemetria, db_error = fetch_telemetria()

if db_error:
    st.error(f"Erro de conexão com o banco de dados: `{db_error}`")

if st.session_state.etapa == "evento_critico":
    st.markdown("## 🥽 MalhaViva VR")
    st.caption("Modo de visualização especializada")
    st.write("Um evento crítico foi detectado na malha urbana.")
    st.markdown(f"**Corredor em atenção:** {st.session_state.corredor_selecionado}")
    st.markdown("**Objetivo da investigação:** Localizar e analisar o ponto de congestionamento.")
    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("🥽 INICIAR MALHAVIVA VR"):
            avancar_etapa("ativacao_vr")
    with col_b:
        if st.button("← Voltar ao Monitoramento"):
            avancar_etapa("monitoramento")
    st.stop()

if st.session_state.etapa == "ativacao_vr":
    st.markdown("## 🥽 MalhaViva VR — Modo Imersivo")
    st.caption(f"Corredor em investigação: **{st.session_state.corredor_selecionado}**")

    fig_vr = construir_figura_3d(df_telemetria, altura=420)
    exibir_grafico_3d(fig_vr, key="grafico_vr_imersivo")
    st.caption(
        "Posição X/Y é apenas layout ilustrativo (sem coordenadas GPS no dataset atual). "
        "Altura, cor e valores no hover vêm da telemetria real mais recente do banco."
    )

    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("🔎 Investigar Anomalia"):
            avancar_etapa("investigacao")
    with col_b:
        if st.button("← Voltar ao Monitoramento"):
            avancar_etapa("monitoramento")
    st.stop()

if st.session_state.etapa == "investigacao":
    st.markdown("## 🔎 Investigação do Corredor")
    st.caption(f"Corredor sob investigação: **{st.session_state.corredor_selecionado}**")

    if not df_telemetria.empty and st.session_state.corredor_selecionado:
        linha_corredor = df_telemetria[
            df_telemetria["ponto_corredor"] == st.session_state.corredor_selecionado
        ]
    else:
        linha_corredor = pd.DataFrame()

    st.markdown("### Diagnóstico Atual")
    col1, col2, col3 = st.columns(3)

    if not linha_corredor.empty:
        vel_corredor = round(linha_corredor["velocidade_media_kmh"].mean(), 1)
        lat_corredor = round(linha_corredor["latencia_5g_ms"].mean(), 2)
        dens_corredor = round(linha_corredor["densidade_veiculos"].mean(), 0)
    else:
        vel_corredor, lat_corredor, dens_corredor = 0.0, 0.0, 0

    col1.metric("Velocidade Média", f"{vel_corredor} km/h")
    col2.metric("Latência 5G", f"{lat_corredor} ms")
    col3.metric("Densidade de Veículos", f"{int(dens_corredor)} veíc/km")

    st.markdown("---")

    st.markdown("### Comparativo com os Demais Corredores")
    if not df_telemetria.empty:
        resumo_comparativo = (
            df_telemetria
            .groupby("ponto_corredor")
            .agg(velocidade_media_kmh=("velocidade_media_kmh", "mean"))
            .reset_index()
        )
        resumo_comparativo["destaque"] = resumo_comparativo["ponto_corredor"] == st.session_state.corredor_selecionado

        fig_comparativo = px.bar(
            resumo_comparativo,
            x="ponto_corredor",
            y="velocidade_media_kmh",
            color="destaque",
            color_discrete_map={True: "#EF553B", False: "#4A5568"},
            labels={"velocidade_media_kmh": "Velocidade (km/h)", "ponto_corredor": "Corredor"},
        )
        fig_comparativo.update_layout(height=320, margin=dict(l=10, r=10, b=10, t=20), showlegend=False)
        st.plotly_chart(fig_comparativo, width='stretch', key="grafico_comparativo_investigacao")
    else:
        st.info("Sem dados suficientes para comparação no momento.")

    st.markdown("---")

    st.markdown("### Registrar Causa Provável")
    st.session_state.causa_provavel = st.selectbox(
        "Qual a causa provável da anomalia?",
        CAUSAS_PROVAVEIS,
        index=CAUSAS_PROVAVEIS.index(st.session_state.causa_provavel)
        if st.session_state.causa_provavel in CAUSAS_PROVAVEIS else 0,
    )
    st.session_state.observacao_investigacao = st.text_area(
        "Observações adicionais (opcional):",
        value=st.session_state.observacao_investigacao,
        placeholder="Ex.: pico de veículos coincidindo com evento local, sensor com leitura instável, etc.",
    )

    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("✅ Confirmar Investigação e Avançar"):
            avancar_etapa("analise_temporal")
    with col_b:
        if st.button("← Voltar à Ativação VR"):
            avancar_etapa("ativacao_vr")
    st.stop()

if st.session_state.etapa == "analise_temporal":
    st.markdown("## 📈 Análise Temporal")
    st.caption(f"Corredor em análise: **{st.session_state.corredor_selecionado}**")
    if st.session_state.causa_provavel:
        st.markdown(f"**Causa provável registrada:** {st.session_state.causa_provavel}")

    if not df_telemetria.empty and st.session_state.corredor_selecionado:
        historico = df_telemetria[
            df_telemetria["ponto_corredor"] == st.session_state.corredor_selecionado
        ].copy()
        historico = historico.sort_values("timestamp", ascending=True)
    else:
        historico = pd.DataFrame()

    if len(historico) < 2:
        st.info(
            "Ainda há poucos registros para este corredor para traçar uma linha do tempo. "
            "Use o Painel de Simulação para gerar mais leituras e enriquecer esta análise."
        )
    else:
        fig_temporal = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.06,
            subplot_titles=("Velocidade (km/h)", "Latência 5G (ms)", "Densidade de Veículos (veíc/km)"),
        )
        fig_temporal.add_trace(
            go.Scatter(
                x=historico["timestamp"], y=historico["velocidade_media_kmh"],
                mode="lines+markers", line=dict(color="#00CC96"), name="Velocidade",
            ),
            row=1, col=1,
        )
        fig_temporal.add_trace(
            go.Scatter(
                x=historico["timestamp"], y=historico["latencia_5g_ms"],
                mode="lines+markers", line=dict(color="#636EFA"), name="Latência",
            ),
            row=2, col=1,
        )
        fig_temporal.add_trace(
            go.Scatter(
                x=historico["timestamp"], y=historico["densidade_veiculos"],
                mode="lines+markers", line=dict(color="#EF553B"), name="Densidade",
            ),
            row=3, col=1,
        )
        fig_temporal.update_layout(height=650, showlegend=False, margin=dict(l=10, r=10, b=10, t=40))
        st.plotly_chart(fig_temporal, width='stretch', key="grafico_temporal")
        st.caption(
            "As três métricas compartilham o eixo do tempo — útil para ver se a queda de "
            "velocidade coincide com o aumento de densidade ou de latência."
        )

    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("🧪 Ir para Simulação"):
            avancar_etapa("simulacao")
    with col_b:
        if st.button("← Voltar à Investigação"):
            avancar_etapa("investigacao")
    st.stop()

if st.session_state.etapa == "simulacao":
    st.markdown("## 🧪 Simulação — Atual vs. Cenário Proposto")
    st.caption(f"Corredor em simulação: **{st.session_state.corredor_selecionado}**")
    st.info(
        "Esta tela apenas simula o efeito dos parâmetros — nenhum dado é gravado no banco aqui. "
        "A gravação definitiva acontece na etapa de Decisão."
    )

    if not df_telemetria.empty and st.session_state.corredor_selecionado:
        linha_atual = df_telemetria[
            df_telemetria["ponto_corredor"] == st.session_state.corredor_selecionado
        ]
    else:
        linha_atual = pd.DataFrame()

    if not linha_atual.empty:
        vel_atual = round(linha_atual["velocidade_media_kmh"].mean(), 1)
        lat_atual = round(linha_atual["latencia_5g_ms"].mean(), 2)
        dens_atual = round(linha_atual["densidade_veiculos"].mean(), 0)
    else:
        vel_atual, lat_atual, dens_atual = 0.0, 0.0, 0

    st.markdown("### Ajustar Parâmetros do Cenário Proposto")
    c1, c2, c3 = st.columns(3)
    with c1:
        densidade_sim = st.slider(
            "Densidade de Veículos (veíc/km)", 20, 500, int(dens_atual) if dens_atual else 180,
            key="sim_densidade",
        )
    with c2:
        tempo_verde_sim = st.slider("Tempo do Semáforo Verde (s)", 15, 120, 45, key="sim_tempo_verde")
    with c3:
        perfil_5g_sim = st.select_slider(
            "Cenário de Conectividade (5G)",
            ["URLLC (Baixa Latência)", "eMBB (Alta Capacidade)", "mMTC (Alta Densidade)"],
            key="sim_perfil_5g",
        )

    vel_simulada, lat_simulada, critico_simulado = calcular_simulacao(
        densidade_sim, tempo_verde_sim, perfil_5g_sim
    )
    st.session_state.simulacao_resultado = {
        "ponto_corredor": st.session_state.corredor_selecionado,
        "velocidade_media_kmh": vel_simulada,
        "latencia_5g_ms": lat_simulada,
        "densidade_veiculos": densidade_sim,
        "alerta_critico": critico_simulado,
    }

    st.markdown("---")
    st.markdown("### Comparativo: Atual vs. Simulado")

    col_atual, col_simulado = st.columns(2)
    with col_atual:
        st.markdown("**📍 Estado Atual**")
        st.metric("Velocidade", f"{vel_atual} km/h")
        st.metric("Latência 5G", f"{lat_atual} ms")
        st.metric("Densidade", f"{int(dens_atual)} veíc/km")
    with col_simulado:
        st.markdown("**🧪 Cenário Proposto**")
        st.metric("Velocidade", f"{vel_simulada} km/h", delta=round(vel_simulada - vel_atual, 1))
        st.metric("Latência 5G", f"{lat_simulada} ms", delta=round(lat_simulada - lat_atual, 2), delta_color="inverse")
        st.metric("Densidade", f"{int(densidade_sim)} veíc/km", delta=int(densidade_sim - dens_atual))

    if critico_simulado:
        st.error("⚠️ O cenário proposto ainda resultaria em estado crítico.")
    else:
        st.success("✅ O cenário proposto resolveria o estado crítico do corredor.")

    fig_sim_bar = go.Figure(data=[
        go.Bar(name="Atual", x=["Velocidade (km/h)"], y=[vel_atual], marker_color="#4A5568"),
        go.Bar(name="Simulado", x=["Velocidade (km/h)"], y=[vel_simulada], marker_color="#00CC96"),
    ])
    fig_sim_bar.update_layout(height=300, margin=dict(l=10, r=10, b=10, t=20), barmode="group")
    st.plotly_chart(fig_sim_bar, width='stretch', key="grafico_simulacao_comparativa")

    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("✅ Ir para Decisão"):
            avancar_etapa("decisao")
    with col_b:
        if st.button("← Voltar à Análise Temporal"):
            avancar_etapa("analise_temporal")
    st.stop()

if st.session_state.etapa == "decisao":
    st.markdown("## ✅ Decisão Operacional")
    st.caption(f"Corredor em decisão: **{st.session_state.corredor_selecionado}**")

    resultado = st.session_state.simulacao_resultado

    if not resultado:
        st.warning("Nenhum resultado de simulação disponível. Volte à simulação para gerar um cenário.")
        if st.button("← Voltar à Simulação"):
            avancar_etapa("simulacao")
        st.stop()

    st.markdown("### 1. Resumo do Problema")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**Corredor investigado:** {st.session_state.corredor_selecionado}")
        st.markdown(
            f"**Causa provável:** "
            f"{st.session_state.causa_provavel or 'Não registrada'}"
        )

    with col2:
        st.markdown("**Observação registrada:**")
        st.write(
            st.session_state.observacao_investigacao
            if st.session_state.observacao_investigacao
            else "Nenhuma observação registrada."
        )

    st.markdown("---")

    st.markdown("### 2. Estado Atual × Cenário Escolhido")

    if not df_telemetria.empty and st.session_state.corredor_selecionado:
        linha_atual_decisao = df_telemetria[
            df_telemetria["ponto_corredor"] == st.session_state.corredor_selecionado
        ]
    else:
        linha_atual_decisao = pd.DataFrame()

    if not linha_atual_decisao.empty:
        vel_atual_decisao = round(
            linha_atual_decisao["velocidade_media_kmh"].mean(), 1
        )
        lat_atual_decisao = round(
            linha_atual_decisao["latencia_5g_ms"].mean(), 2
        )
        dens_atual_decisao = round(
            linha_atual_decisao["densidade_veiculos"].mean(), 0
        )
    else:
        vel_atual_decisao, lat_atual_decisao, dens_atual_decisao = 0.0, 0.0, 0

    col_atual, col_cenario = st.columns(2)

    with col_atual:
        st.markdown("**📍 Estado Atual**")
        st.metric("Velocidade", f"{vel_atual_decisao} km/h")
        st.metric("Latência 5G", f"{lat_atual_decisao} ms")
        st.metric("Densidade", f"{int(dens_atual_decisao)} veíc/km")

    with col_cenario:
        st.markdown("**🧪 Cenário Escolhido**")
        st.metric(
            "Velocidade",
            f"{resultado['velocidade_media_kmh']} km/h",
            delta=round(
                resultado["velocidade_media_kmh"] - vel_atual_decisao, 1
            ),
        )
        st.metric(
            "Latência 5G",
            f"{resultado['latencia_5g_ms']} ms",
            delta=round(
                resultado["latencia_5g_ms"] - lat_atual_decisao, 2
            ),
            delta_color="inverse",
        )
        st.metric(
            "Densidade",
            f"{int(resultado['densidade_veiculos'])} veíc/km",
            delta=int(resultado["densidade_veiculos"] - dens_atual_decisao),
        )

    st.markdown("---")

    st.markdown("### 3. Resultado da Simulação")

    if resultado["alerta_critico"]:
        st.warning("⚠️ **Cenário ainda crítico** — a simulação não eliminou a condição crítica.")
    else:
        st.success("✅ **Cenário recomendado** — a simulação indica resolução da condição crítica.")

    st.markdown("---")

    st.markdown("### 4. Decisão Operacional")

    if st.session_state.decisao_registrada:
        st.success(
            "✅ **Cenário aprovado e registrado no banco de dados como nova telemetria.**"
        )
        st.caption(
            "O registro utiliza a estrutura de telemetria já existente, "
            "sem alterar a estrutura do banco."
        )
    else:
        st.info(
            "Ao aprovar, o cenário escolhido será registrado no banco utilizando "
            "a tabela de telemetria existente."
        )

        col_a, col_b = st.columns([1, 1])

        with col_a:
            if st.button(
                "✅ APROVAR CENÁRIO",
                width='stretch',
                disabled=st.session_state.decisao_registrada,
            ):
                sucesso, err_msg = insert_telemetria(
                    resultado["ponto_corredor"],
                    resultado["velocidade_media_kmh"],
                    resultado["latencia_5g_ms"],
                    resultado["densidade_veiculos"],
                    resultado["alerta_critico"],
                )

                if sucesso:
                    st.session_state.decisao_registrada = True
                    fetch_telemetria.clear()
                    st.success(
                        "✅ Cenário aprovado e registrado com sucesso no banco de dados."
                    )
                else:
                    st.error(f"Erro ao registrar a decisão: {err_msg}")

        with col_b:
            if st.button(
                "↩️ REJEITAR / VOLTAR À SIMULAÇÃO",
                width='stretch',
            ):
                st.session_state.decisao_registrada = False
                avancar_etapa("simulacao")

    st.stop()

st.markdown("### Status Geral da Malha")

col1, col2, col3, col4 = st.columns(4)

latencia_media = round(df_telemetria['latencia_5g_ms'].mean(), 2) if not df_telemetria.empty else 1.5
velocidade_media = round(df_telemetria['velocidade_media_kmh'].mean(), 1) if not df_telemetria.empty else 0.0
tem_alerta = df_telemetria['alerta_critico'].any() if not df_telemetria.empty else False
qtd_registros = len(df_telemetria) if not df_telemetria.empty else 0

col1.metric("Estado da Malha", "Atenção" if tem_alerta else "Normal", delta="Monitoramento ativo")
col2.metric("Velocidade Média", f"{velocidade_media} km/h")
col3.metric("Latência (Simulada)", f"{latencia_media} ms")
if tem_alerta:
    st.error("⚠️ **EVENTO CRÍTICO DETECTADO** — Há corredor(es) com velocidade abaixo do esperado. Recomenda-se investigação.")
    if st.session_state.etapa == "monitoramento":
        corredor_critico = df_telemetria[df_telemetria["alerta_critico"] == True]["ponto_corredor"].iloc[0]
        if st.button("🔎 Investigar Evento Crítico"):
            # Reinicia o estado da investigação anterior, para que uma segunda
            # rodada de demonstração (outro corredor) não herde causa provável,
            # observação, resultado de simulação ou decisão já registrada.
            st.session_state.corredor_selecionado = corredor_critico
            st.session_state.causa_provavel = None
            st.session_state.observacao_investigacao = ""
            st.session_state.simulacao_resultado = None
            st.session_state.decisao_registrada = False
            avancar_etapa("evento_critico")
else:
    st.info("Nenhum evento crítico no momento. Monitoramento contínuo ativo.")

st.markdown("---")

st.markdown("### Visão da Malha Urbana")

col_left, col_right = st.columns([1.6, 1.4])

with col_left:
    st.markdown("**Modelo 3D — Estado Atual dos Corredores (dados reais do banco)**")
    fig_3d = construir_figura_3d(df_telemetria)
    exibir_grafico_3d(fig_3d, key="grafico_3d_dashboard")
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
        st.plotly_chart(fig_bar, width='stretch', key="grafico_barras_dashboard")
    else:
        st.info("Nenhum dado disponível. Use o painel de simulação abaixo.")

st.markdown("---")

st.markdown("### Painel de Simulação")

c1, c2, c3, c4 = st.columns(4)
with c1:
    ponto_sel = st.selectbox("Corredor", list(LAYOUT_POSICOES.keys()))
with c2:
    densidade = st.slider("Densidade de Veículos (veíc/km)", 20, 500, 180)
with c3:
    tempo_verde = st.slider("Tempo do Semáforo Verde (s)", 15, 120, 45)
with c4:
    perfil_5g = st.select_slider("Cenário de Conectividade (Simulação)", ["URLLC (Baixa Latência)", "eMBB (Alta Capacidade)", "mMTC (Alta Densidade)"])

if st.button("Simular e Registrar no Sistema"):
    vel_calculada, lat_calculada, critico = calcular_simulacao(densidade, tempo_verde, perfil_5g)

    sucesso, err_msg = insert_telemetria(ponto_sel, vel_calculada, lat_calculada, densidade, critico)
    if sucesso:
        st.toast(f"Simulação registrada • Velocidade: {vel_calculada} km/h", icon="✅")
        fetch_telemetria.clear()
        time.sleep(0.8)
        st.rerun()
    else:
        st.error(f"Erro ao registrar: {err_msg}")

with st.expander("Ver histórico registrado"):
    if not df_telemetria.empty:
        st.dataframe(df_telemetria, width='stretch')
    else:
        st.write("Nenhum registro encontrado.")
