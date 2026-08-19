🚦 Desafio de Mobilidade Urbana — Sorocaba (Gêmeo Digital & 5G)

Solução de Engenharia e Análise de Dados para Gestão e Simulação Preditiva de Tráfego Urbano Desenvolvido para a Residência TIC / Atividade Integrada — UniFacens

🔗 App ao vivo: SIGABEM — Digital Twin & 5G Control (login de demonstração acadêmica: qualquer e-mail + senha SIGABEM)

📌 Visão Geral do Projeto

Este projeto tem duas camadas, e é importante deixar isso claro logo de início:

Camada analítica (offline / batch) — pipeline de engenharia de dados que processou o dataset completo de mobilidade urbana de Sorocaba/SP (~1 milhão de registros brutos, 17 sensores viários), incluindo limpeza, desduplicação e modelagem em grafos (matriz Origem-Destino).
Camada operacional (painel em tempo real) — o gêmeo digital SIGABEM, construído em Streamlit, que demonstra o fluxo completo de monitoramento, alerta e simulação what-if integrado ao PostgreSQL. O painel foi validado com um subconjunto de teste na região dos arredores da UniFacens, não com a malha completa da cidade — a ingestão em escala real é feita pela camada analítica, não pelo painel ao vivo.

Essa separação é intencional: em sistemas de mobilidade e IoT reais, é comum ter um pipeline de processamento em lote (que lida com o volume grande de dados históricos) desacoplado da camada operacional em tempo real (que precisa responder rápido, com um subconjunto de dados ativos).

🛠️ Pilha Tecnológica
Linguagem: Python 3.12
Ambiente: Linux (Ubuntu no WSL 2) & VS Code
Banco de Dados: PostgreSQL (Neon.tech), com pooling de conexões
Análise & Modelagem: Pandas, NumPy, NetworkX (Teoria dos Grafos)
Gêmeo Digital & Visualização: Streamlit, Plotly 3D
Persistência: SQLAlchemy + st.secrets para credenciais (fora do controle de versão)

🚀 Destaques da Arquitetura
1. Pipeline de Ingestão e Saneamento de Dados (limpeza_facens.py)
Tratamento de Dados Brutos: processamento de dataset de 90MB com quase 1 milhão de registros, em ambiente com limitação de hardware (8GB RAM).
Higienização: desduplicação de registros, tratamento de nulos e filtragem de outliers de velocidade.
Modelagem em Grafos (analise_grafos.py): construção da Matriz Origem-Destino (OD) para mapear a conectividade entre os 17 sensores estratégicos de Sorocaba.

2. Gêmeo Digital e Telemetria — Painel SIGABEM (app.py)
Painel de Controle Urbano: visualização 3D do estado dos corredores monitorados — altura, cor e valores no gráfico refletem a telemetria mais recente registrada no banco (não são valores estáticos ou aleatórios).
Monitoramento: métricas de velocidade média, latência simulada da rede e alertas automáticos quando um corredor opera abaixo do esperado.

Simulador What-If: injeção de parâmetros (densidade de veículos, tempo de semáforo, cenário de conectividade 5G) com persistência direta no PostgreSQL.
Performance: conexão com o banco via connection pooling (Neon -pooler endpoint) e cache de sessão (st.cache_resource / st.cache_data), para suportar múltiplas interações simultâneas sem estourar o limite de conexões do plano gratuito.

📊 Resultados Alcançados
Saneamento e Integridade: validação do dataset bruto dos 17 sensores viários de Sorocaba, permitindo mapear gargalos e padrões de tráfego entre dias úteis e finais de semana — na camada analítica.
Persistência Relacional: ingestão estruturada no PostgreSQL, com histórico de telemetria consultável pelo painel.
Validação do Painel: fluxo completo de monitoramento → alerta → simulação → persistência testado e funcional, com dados reais de teste da região da UniFacens.

⚠️ Limitações Conhecidas (transparência acadêmica)
O login do painel é simplificado para fins de demonstração (senha fixa), não é autenticação de produção.
As posições X/Y dos corredores no mapa 3D são um layout ilustrativo — o dataset atual não contém coordenadas GPS por sensor. Os valores que são reais (altura do marcador, cor, velocidade e latência) vêm da telemetria do banco.
O volume de dados no painel operacional é um subconjunto de teste, não a ingestão completa do dataset de ~1 milhão de registros (essa está na camada analítica, ver seção acima).

🛠️ Como Executar o Projeto Localmente
Pré-requisitos
Python 3.12
PostgreSQL ativo (ou conta Neon.tech)
Ambiente Linux (WSL 2 recomendado)
Passo a Passo
bash
# 1. Clonar o repositório
git clone https://github.com/vvania-ssantos/desafiouni-facens-mobilidade.git
cd desafiouni-facens-mobilidade

# 2. Criar e ativar o ambiente virtual
python3 -m venv .venv --upgrade-deps
source .venv/bin/activate

# 3. Instalar as dependências
pip install -r requirements.txt

# 4. Configurar credenciais do banco (NÃO commitar este arquivo)
mkdir -p .streamlit
nano .streamlit/secrets.toml
# Preencher com DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT

# 5. Criar a estrutura da tabela no PostgreSQL
psql -U postgres -d sigabem_db -f schema.sql

# 6. Executar o Gêmeo Digital SIGABEM
streamlit run app.py
👩‍💻 Autora

Vania dos Santos Engenheira de Computação | Pós-graduada em Governança e Gestão de TI Foco de Atuação: Análise de Dados, Engenharia de Dados e Ciência de Dados

GitHub: @vvania-ssantos
LinkedIn: vaniadossantos

