import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert
import os

# 1. CONFIGURAÇÃO DE CONEXÃO
DB_URL = 'postgresql://postgres:vania@localhost:5432/desafiouni_facens'
engine = create_engine(DB_URL)

# 2. FUNÇÃO "INSERT OR IGNORE" (Evita travar por duplicatas)
def insert_on_conflict_nothing(table, conn, keys, data_iter):
    data = [dict(zip(keys, row)) for row in data_iter]
    stmt = insert(table.table).values(data).on_conflict_do_nothing(
        index_elements=['nserie', 'datatrafego', 'placa']
    )
    conn.execute(stmt)

# 3. DEFINIÇÃO DO ARQUIVO ATUAL E PARÂMETROS
# -------------------------------------------------------------------------
arquivo = 'parte_114.csv'  # <--- Mude aqui para 'parte_38.csv' na próxima rodada
chunk_size = 50000

print(f"--- 🏁 Iniciando Carga Única: {arquivo} ---")

if not os.path.exists(arquivo):
    print(f"⚠️ Arquivo {arquivo} não encontrado!")
else:
    # Lendo em lotes para respeitar seus 8GB de RAM
    for i, chunk in enumerate(pd.read_csv(arquivo, sep=';', chunksize=chunk_size, encoding='utf-8')):
        
        # Seleção e Limpeza
        df = chunk[['NSerie', 'Datatrafego', 'Placa', 'Velocidade 1', 'Velocidade Regul']].copy()
        df.columns = ['nserie', 'datatrafego', 'placa', 'velocidade', 'velocidade_regul']
        
        df = df.dropna()
        df = df.drop_duplicates(subset=['nserie', 'datatrafego', 'placa'])
        
        # Transformação (Foco no Professor: Hora)
        df['datatrafego'] = pd.to_datetime(df['datatrafego'], dayfirst=True)
        df['hora'] = df['datatrafego'].dt.hour
        
        # Filtro de Sanidade
        df = df[(df['velocidade'] >= 0) & (df['velocidade'] <= 220)]
        
        # TENTATIVA DE INSERÇÃO COM RECURSO DE RECUPERAÇÃO NO BANCO
        try:
            df.to_sql(
                'leituras', 
                engine, 
                if_exists='append', 
                index=False, 
                method=insert_on_conflict_nothing
            )
            print(f"    ✅ Lote {i+1} processado com sucesso.")
        except Exception as e:
            print(f"    ⚠️ Conflito no lote {i+1}. Iniciando recuperação linha por linha...")
            for _, row in df.iterrows():
                try:
                    pd.DataFrame([row]).to_sql(
                        'leituras', engine, if_exists='append', index=False, method=insert_on_conflict_nothing
                    )
                except:
                    continue 
            print(f"    ✅ Lote {i+1} finalizado via recuperação.")

        # --- AJUSTE DE GRAVAÇÃO DO CSV (DENTRO DO LOOP) ---
        nome_arquivo_limpo = f"limpo_{arquivo}"
        
        # Se for o primeiro lote (i == 0), cria o arquivo ('w'). Nos próximos, apenas acrescenta ('a').
        modo = 'w' if i == 0 else 'a'
        header = True if i == 0 else False
        
        df.to_csv(nome_arquivo_limpo, index=False, sep=';', encoding='utf-8', mode=modo, header=header)

print(f"\n✨ Finalizado o processamento e geração do CSV: {arquivo}")