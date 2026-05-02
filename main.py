import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# 1. Carregar as configurações do .env
load_dotenv()

print("--- Iniciando o Desafio Mobilidade Facens ---")

# 2. Construir a URL de conexão (Padrão Engenharia)
user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')
db = os.getenv('DB_NAME')

DATABASE_URL = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"

# 3. Criar o motor (Engine)
engine = create_engine(DATABASE_URL)

def inicializar_banco():
    # SQL para criar as tabelas do desafio
    create_tables = """
    CREATE TABLE IF NOT EXISTS sensores (
        NSerie INTEGER PRIMARY KEY,
        Endereco TEXT,
        Sentido TEXT,
        Latitude NUMERIC(12,8),
        Longitude NUMERIC(12,8)
    );

    CREATE TABLE IF NOT EXISTS leituras (
        id BIGSERIAL PRIMARY KEY,
        NSerie INTEGER REFERENCES sensores(NSerie),
        Datatrafego TIMESTAMP,
        Placa TEXT,
        Velocidade REAL,
        Velocidade_Regul REAL,
        UNIQUE(NSerie, Datatrafego, Placa)
    );
    """
    
    print(f"Tentando conectar ao banco '{db}' no WSL...")
    
    try:
        with engine.connect() as conn:
            # Executa o comando SQL
            conn.execute(text(create_tables))
            # No SQLAlchemy 2.0, precisamos dar o commit explicitamente
            conn.commit()
            print("✅ Sucesso: Banco de Dados e Tabelas criados/verificados!")
    except Exception as e:
        print(f"❌ Erro de Conexão ou SQL: {e}")
        print("\nDICA: Verifique se o serviço do Postgres está rodando com: sudo service postgresql start")

if __name__ == "__main__":
    inicializar_banco()
    print("--- Script finalizado ---")