import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# Carregando o 'troféu' de 90MB que você limpou
arquivo = 'dados_completos_limpos_Vania.csv'
df = pd.read_csv(arquivo, sep=';')

print(f"📊 Processando {len(df)} registros para o Grafo...")

# 1. Criando a lógica de Origem e Destino
# Ordenamos para garantir que a sequência temporal das placas esteja correta
df = df.sort_values(['placa', 'datatrafego'])
df['sensor_destino'] = df.groupby('placa')['nserie'].shift(-1)

# 2. Filtrando apenas deslocamentos reais (entre sensores diferentes)
conexoes = df[df['sensor_destino'].notna() & (df['nserie'] != df['sensor_destino'])]

# 3. Criando o Grafo Direcionado
G = nx.from_pandas_edgelist(conexoes, source='nserie', target='sensor_destino', create_using=nx.DiGraph())

# 4. Plotando o resultado
plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G, k=0.5)
nx.draw(G, pos, with_labels=True, node_color='lightgreen', node_size=1500, 
        edge_color='gray', arrowsize=15, font_weight='bold')

plt.title("Grafo de Fluxo Urbano - Sorocaba (Vania dos Santos)")
plt.savefig('grafo_mobilidade.png') # Salva uma imagem para você mandar no grupo!
plt.show()

print("✅ Grafo gerado e salvo como 'grafo_mobilidade.png'")

