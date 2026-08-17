-- =============================================================
-- PIPELINE DE ETL: SANEAMENTO E CONSOLIDAÇÃO DE DADOS URBANOS
-- Responsável: Vania Santos
-- Ambiente: PostgreSQL 15 via WSL2 (Ubuntu)
-- =============================================================

-- 1. CRIAÇÃO DA ESTRUTURA DE INGESTÃO
-- Criamos uma tabela temporária para receber o volume bruto de dados
CREATE TABLE public.trafego_bruto (
    nserie VARCHAR(50),
    datatrafego TIMESTAMP,
    placa VARCHAR(20),
    velocidade INT,
    faixa INT
);

-- 2. INGESTÃO DE ALTA PERFORMANCE (BULK INSERT)
-- Utilizamos o comando COPY para processar os registros com máxima eficiência
-- Exemplo de comando executado via terminal PSQL:
-- \copy public.trafego_bruto FROM 'caminho/para/parte_0.csv' WITH (FORMAT csv, DELIMITER ';', HEADER true, ENCODING 'utf8');

-- 3. SANEAMENTO E REMOÇÃO DE DUPLICATAS (INTEGRIDADE LÓGICA)
-- Criamos a tabela final selecionando apenas registros únicos baseados na 
-- tríade: Sensor (nserie) + Tempo (datatrafego) + Veículo (placa)
CREATE TABLE public.dados_limpos AS
SELECT DISTINCT ON (nserie, datatrafego, placa)
    nserie,
    datatrafego,
    placa,
    velocidade,
    faixa
FROM public.trafego_bruto
ORDER BY nserie, datatrafego, placa;

-- 4. EXPORTAÇÃO PARA O ARQUIVO MESTRE
-- Comando utilizado para gerar o dataset consolidado usado no Colab/GitHub
-- \copy public.dados_limpos TO 'dados_completos_limpos_Vania.csv' WITH (FORMAT csv, DELIMITER ';', HEADER true);