-- SIGABEM — Gêmeo Digital & Mobilidade Urbana (Sorocaba/SP)
-- SCRIPT DE ESTRUTURA DO BANCO DE DADOS (PostgreSQL)
-- =========================================================

-- Criação da tabela de telemetria do corredor e rede 5G (se não existir)
CREATE TABLE IF NOT EXISTS telemetria_trafego (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ponto_corredor VARCHAR(100) NOT NULL,
    velocidade_media_kmh NUMERIC(5,2) NOT NULL,
    latencia_5g_ms NUMERIC(5,2) NOT NULL,
    densidade_veiculos INT NOT NULL,
    alerta_critico BOOLEAN DEFAULT FALSE
);

-- Inserção de dados iniciais para teste de telemetria
INSERT INTO telemetria_trafego (ponto_corredor, velocidade_media_kmh, latencia_5g_ms, densidade_veiculos, alerta_critico)
VALUES 
('Av. Afonso Vergueiro (gNodeB_01)', 42.50, 1.80, 120, FALSE),
('Av. Dom Aguirre (gNodeB_02)', 12.00, 14.80, 380, TRUE),
('Av. Itavuvu (gNodeB_03)', 28.30, 3.20, 210, FALSE);