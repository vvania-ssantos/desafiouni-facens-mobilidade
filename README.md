# 🚦 Desafio de Mobilidade Urbana — Sorocaba (Gêmeo Digital & 5G)

> **Solução de Engenharia e Análise de Dados para Gestão e Simulação Preditiva de Tráfego Urbano**
> *Desenvolvido para a Residência TIC / Atividade Integrada UniFacens*

---

## 📌 Visão Geral do Projeto

Este projeto apresenta um ecossistema completo de **Engenharia de Dados e Gêmeos Digitais** focado na mobilidade urbana da cidade de Sorocaba/SP. A solução abrange desde o saneamento e ingestão de quase **1 milhão de registros** provenientes de sensores inteligentes até a criação de um **painel interativo de Gêmeo Digital (SIGABEM)** integrado à telemetria de redes **5G Standalone (URLLC)** e **PostgreSQL**.

---

## 🛠️ Pilha Tecnológica

- **Linguagem:** Python 3.12
- **Ambiente:** Linux (Ubuntu no WSL 2) & VS Code
- **Banco de Dados:** PostgreSQL (Ingestão, Desduplicação e Persistência de Telemetria)
- **Análise & Modelagem:** Pandas, NumPy, NetworkX (Teoria dos Grafos)
- **Gêmeo Digital & Visualização:** Streamlit, Plotly 3D (Sub-6 / gNodeB)
- **Redes & Conectividade:** Simulação de *Network Slicing* (URLLC/eMBB) e Edge Computing (MEC)

---

## 🚀 Destaques da Arquitetura

### 1. Pipeline de Ingestão e Saneamento de Dados (`limpeza_facens.py`)
- **Tratamento de Dados Brutos:** Processamento de dataset de 90MB com quase 1 milhão de registros em ambiente com limitação de hardware (8GB RAM).
- **Higienização:** Desduplicação de registros, tratamento de nulos e filtragem de *outliers* de velocidade.
- **Modelagem em Grafos:** Construção da Matriz Origem-Destino (OD) para mapear a conectividade e os eixos de fluxo dos 17 sensores estratégicos de Sorocaba.

### 2. Gêmeo Digital e Telemetria 5G (`app.py` / `SIGABEM`)
- **Painel de Controle Urbano:** Visualização 3D simulada dos blocos viários e antenas 5G (*gNodeB*).
- **Monitoramento da Rede 5G:** Acompanhamento em tempo real da latência em milissegundos, comparando o ganho da fatia **5G URLLC** frente ao 4G tradicional.
- **Simulador Preditivo (*What-If*):** Injeção dinâmica de parâmetros (densidade de veículos e tempos de semáforo) com alertas automáticos de retenção no banco PostgreSQL.

---

## 📊 Resultados Alcançados

- **Saneamento e Integridade:** Validação dos dados brutos dos 17 sensores viários de Sorocaba, permitindo mapear gargalos e padrões de tráfego entre dias úteis e finais de semana.
- **Persistência Relacional:** Ingestão estruturada no PostgreSQL com geração de histórico de telemetria.
- **Simulação de Baixa Latência:** Demostração prática da aplicação de fatiamento de rede (*Network Slicing*) para priorização de tráfego em situações de retenção crítica.

---

## 🛠️ Como Executar o Projeto Localmente

### Pré-requisitos
- Python 3.12
- PostgreSQL ativo
- Ambiente Linux (WSL 2)

### Passo a Passo no Terminal

```bash
# 1. Clonar o repositório
git clone [https://github.com/vvania-ssantos/desafiouni-facens-mobilidade.git](https://github.com/vvania-ssantos/desafiouni-facens-mobilidade.git)
cd desafiouni-facens-mobilidade

# 2. Ativar o ambiente virtual Python
source .venv/bin/activate

# 3. Instalar as dependências
pip install -r requirements.txt

# 4. Criar a estrutura da tabela no PostgreSQL
psql -U postgres -d sigabem_db -f schema.sql

# 5. Executar o Gêmeo Digital SIGABEM
streamlit run app.py

👩‍💻 Autora
Vania dos Santos

Engenheira de Computação | Pós-graduada em Governança e Gestão de TI

Foco de Atuação: Análise de Dados, Engenharia de Dados e Ciência de Dados

GitHub: @vvania-ssantos
