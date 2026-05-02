import pandas as pd
import os

arquivos = ['parte_0.csv', 'parte_38.csv', 'parte_77.csv', 'parte_114.csv', 'parte_153.csv']
print(f"{'Arquivo':<15} | {'Linhas':<10} | {'Sensores Únicos':<15} | {'Duplicatas'}")
print("-" * 60)

todos_sensores = set()

for arq in arquivos:
    if os.path.exists(arq):
        # Lemos apenas as colunas necessárias para economizar memória
        df = pd.read_csv(arq, sep=';', usecols=['NSerie', 'Datatrafego', 'Placa'], encoding='utf-8')
        
        n_linhas = len(df)
        sensores_no_arquivo = df['NSerie'].unique()
        todos_sensores.update(sensores_no_arquivo)
        
        # Checa se existem linhas 100% iguais (mesmo sensor, hora e placa)
        duplicados = df.duplicated().sum()
        
        print(f"{arq:<15} | {n_linhas:<10} | {len(sensores_no_arquivo):<15} | {duplicados}")
    else:
        print(f"❌ {arq} não encontrado.")

print("-" * 60)
print(f"✅ Total de sensores diferentes encontrados no projeto: {len(todos_sensores)}")
print(f"IDs detectados: {sorted(list(todos_sensores))}")