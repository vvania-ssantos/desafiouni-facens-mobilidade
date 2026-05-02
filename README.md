# 🚦 Desafio de Mobilidade Urbana - Sorocaba (Smart City)

Este projeto apresenta uma solução de **Engenharia de Dados** para o saneamento e análise de fluxos veiculares da cidade de Sorocaba, processando quase **1 milhão de registros** provenientes de sensores inteligentes.

## 🛠️ Stack Tecnológica
- **Linguagem:** Python 3.12
- **Ambiente:** Linux (WSL 2 / Ubuntu)
- **Banco de Dados:** PostgreSQL (Ingestão e Desduplicação)
- **Análise de Dados:** Pandas, NetworkX (Teoria dos Grafos)
- **Ferramentas:** VS Code, Google Colab

## 🚀 Destaques do Projeto
- **Pipeline de Limpeza:** Desenvolvimento do script `limpeza_facens.py` que realiza o saneamento de dados brutos, removendo duplicatas e tratando outliers de velocidade.
- **Modelagem de Grafos:** Transformação de dados tabulares em uma Matriz de Origem-Destino (O-D) para visualização da conectividade urbana.
- **Alta Performance:** Processamento eficiente de um dataset de 90MB em hardware com recursos limitados (8GB RAM).

## 📊 Resultados
O projeto validou a integridade de 17 sensores estratégicos, mapeando os principais eixos de fluxo da cidade. O grafo resultante permite identificar gargalos e padrões de tráfego em dias úteis e finais de semana.

---
**Desenvolvido por Vania dos Santos**  
*Engenheira de Computação | Transicionando para Análise de Dados*