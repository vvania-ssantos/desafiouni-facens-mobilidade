import pandas as pd
import os

arquivos = ['parte_0.csv', 'parte_38.csv', 'parte_77.csv', 'parte_114.csv', 'parte_153.csv']

print("=== RELATÓRIO DE DISPONIBILIDADE LÓGICA (TELEMETRIA DE DADOS) ===")
print(f"{'Arquivo':<15} | {'Registros':<10} | {'Sensores Ativos':<15}")
print("-" * 50)

todos_sensores = set()
total_linhas = 0

for arq in arquivos:
    if os.path.exists(arq):
        df = pd.read_csv(arq, sep=';', usecols=['NSerie'], encoding='utf-8')
        n_linhas = len(df)
        total_linhas += n_linhas
        sensores_no_arquivo = df['NSerie'].unique()
        todos_sensores.update(sensores_no_arquivo)
        print(f"{arq:<15} | {n_linhas:<10} | {len(sensores_no_arquivo):<15}")

print("-" * 50)
print(f"TOTAL DE REGISTROS PROCESSADOS: {total_linhas}")
print(f"TOTAL DE SENSORES ÚNICOS DETECTADOS: {len(todos_sensores)}")
print(f"IDs DOS SENSORES: {sorted(list(todos_sensores))}")