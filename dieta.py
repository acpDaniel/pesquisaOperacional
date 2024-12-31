import pandas as pd
from gurobipy import Model, GRB, quicksum

# Carregar os dados da planilha
df = pd.read_excel("alimentosTeste.xlsx")

# Valor grande para M
M = 1000

# Parâmetros do problema
alimentos = df['alimento'].tolist() #alimentos da planilha
dias = 7  # número de dias
refeicoes = 3  # número de refeições por dia
grupos = list(range(1, 8)) #quantidade de grupos

# Nutrientes e limites
nutrientes = ["calorias", "carboidratos", "proteinas", "gorduras", "ferro", "magnesio", "vitamina_c", "zinco", "sodio"]
limites_nutrientes = {
    "calorias": (3000, 5000),
    "carboidratos": (450, 900),
    "proteinas": (120, 150),
    "gorduras": (70, 120),
    "ferro": (8, 18),
    "magnesio": (400, 420),
    "vitamina_c": (75, 90),
    "zinco": (11, 16),
    "sodio": (1500, 5000)
}

# Dados das colunas da planilha
calorias = df['calorias'].tolist()
carboidratos = df['carboidratos'].tolist()
proteinas = df['proteinas'].tolist()
gorduras = df['gorduras'].tolist()
ferro = df['ferro'].tolist()
magnesio = df['magnesio'].tolist()
vitamina_c = df['vitamina_c'].tolist()
zinco = df['zinco'].tolist()
sodio = df['sodio'].tolist()
preco = df['preco'].tolist()
max_porcoes = df['max_porcoes_dia'].tolist()
max_dias = df['max_dias'].tolist()
grupo = df['grupo'].tolist()

# Modelo
model = Model("problemaDaDieta")

# Variáveis de decisão
X = model.addVars(len(alimentos), range(dias), range(refeicoes), vtype=GRB.INTEGER, name="X")
Z = model.addVars(len(alimentos), range(dias), range(refeicoes), vtype=GRB.BINARY, name="Z")
Y = model.addVars(len(alimentos), range(dias), vtype=GRB.BINARY, name="Y")

# Função objetivo: minimizar o custo total
model.setObjective(quicksum(preco[i] * X[i,j,k] for i in range(len(alimentos)) for j in range(dias) for k in range(refeicoes)), GRB.MINIMIZE)

#Restrições

#Restrições de quantidades de nutrientes
for nutriente in nutrientes:
    min_val, max_val = limites_nutrientes[nutriente]
    for j in range(dias):
        model.addConstr(
            quicksum(df.loc[i, nutriente] * X[i, j, k] for i in range(len(alimentos)) for k in range(refeicoes)) >= min_val,
            f"{nutriente}_min_dia_{j}"
        )
        model.addConstr(
            quicksum(df.loc[i, nutriente] * X[i, j, k] for i in range(len(alimentos)) for k in range(refeicoes)) <= max_val,
            f"{nutriente}_max_dia_{j}"
        )

#Restrições porções minimas de grupos alimentares
#1-laticinios_acucar   2-frutas    3-horticolas    4-cereais_derivados_tuberculos  5-carne_peixe_ovos  6-leguminosas 7-oleos_gorduras
min_porcoes_grupo = {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0
    }

for j in range(dias):
    for g in grupos:
        model.addConstr(
            quicksum(X[i,j,k] for i in range(len(alimentos)) if grupo[i] == g for k in range(refeicoes)) >= min_porcoes_grupo[g],
            f"min_porcoes_grupo_{g}_dia_{j}"
        )

# Restrições de máximo de porções por alimento i por dia
for i in range(len(alimentos)):
    for j in range(dias):
        model.addConstr(
            quicksum(X[i,j,k] for k in range(refeicoes)) <= Y[i,j] * max_porcoes[i],
            f"max_porcoes_alimento_{i}_dia_{j}"
        )

# Restrição de quantidade máxima de dias que um alimento pode ser consumido em uma semana
for i in range(len(alimentos)):
    model.addConstr(
        quicksum(Y[i,j] for j in range(dias)) <= max_dias[i],
        f"max_dias_alimento_{i}"
    )

# Restrição de que um alimento i pode ser usado em no máximo 2 refeições diárias
for i in range(len(alimentos)):
    for j in range(dias):
        model.addConstr(
            quicksum(Z[i,j,k] for k in range(refeicoes)) <= 1 * Y[i,j],
            f"max_refeicoes_alimento_{i}_dia_{j}"
        )

# Restrição de limite total de 50 porções de alimento por dia
for j in range(dias):
    model.addConstr(
        quicksum(X[i,j,k] for i in range(len(alimentos)) for k in range(refeicoes)) <= 50,
        f"limite_total_porcoes_dia_{j}"
    )

# Garantir que em cada refeição pelo menos uma porção de alimento foi consumida
for j in range(dias):
    for k in range(refeicoes):
        model.addConstr(
            quicksum(X[i, j, k] for i in range(len(alimentos))) >= 1,
            f"min_1_porção_consumida_dia_{j}_refeicao_{k}"
        )

# Amarrar Y_{i,j} e X_{i,j,k}
for i in range(len(alimentos)):
    for j in range(dias):
        model.addConstr(
            quicksum(X[i, j, k] for k in range(refeicoes)) >= Y[i, j],
            f"amarrar_Y_X_{i}_dia_{j}"
        )               

# # Garantir que pelo menos um alimento foi consumido em cada refeição de cada dia
# for j in range(dias):  # Para cada dia
#     for k in range(refeicoes):  # Para cada refeição
#         model.addConstr(
#             quicksum(Z[i, j, k] for i in range(len(alimentos))) >= 1,
#             f"min_1_alimento_consumido_dia_{j}_refeicao_{k}"
#         )    

# # Amarrar Z_{i,j,k} e Y_{i,j}
# for i in range(len(alimentos)):
#     for j in range(dias):
#         model.addConstr(
#             quicksum(Z[i, j, k] for k in range(refeicoes)) <= M * Y[i, j],
#             f"amarrar_Z_Y_{i}_dia_{j}"
#         )

# Amarrar Z_{i,j,k} e X_{i,j,k}
for i in range(len(alimentos)):
    for j in range(dias):
        for k in range(refeicoes):
            model.addConstr(
                Z[i, j, k] >= X[i, j, k] / M,
                f"amarrar_Z_X_{i}_dia_{j}_ref_{k}"
            )    


# Amarrar Z_{i,j,k} e X_{i,j,k} para garantir que Z[i,j,k] = 0 se X[i,j,k] = 0
for i in range(len(alimentos)):
    for j in range(dias):
        for k in range(refeicoes):
            # Se Z[i,j,k] = 0, então X[i,j,k] = 0
            model.addConstr(X[i, j, k] <= M * Z[i, j, k], f"Z_limita_X_{i}_dia_{j}_ref_{k}")                     

#Flag para ver mais logs
#model.setParam("OutputFlag", 1)

#GAP aceitavel no resultado, se comentar aqui vai demorar muito tempo para a planilha completa
#model.setParam("MIPGap", 0.04)

# Resolver o modelo
model.optimize()

# Escrever os resultados em um arquivo (limpando o conteúdo antes de escrever novamente)
with open("resultado.txt", "w") as arquivo:
    # Verificar o status da solução
    if model.status == GRB.OPTIMAL:
        arquivo.write("Solução ótima encontrada!\n")
        arquivo.write(f"Valor da função objetivo (custo total): {model.objVal}\n")
        
        # Variáveis de decisão organizadas por dia e refeição
        arquivo.write("\nPorções consumidas por refeição (organizado por dia e refeição):\n")
        for j in range(dias):
            for k in range(refeicoes):
                arquivo.write(f"\nDia {j}, Refeição {k}:\n")
                for i in range(len(alimentos)):
                    if X[i, j, k].x > 0:  # Mostrar apenas variáveis com valores positivos
                        arquivo.write(f"  Alimento {alimentos[i]}: {X[i, j, k].x} porções\n")
        
        # Dias em que os alimentos foram consumidos
        arquivo.write("\nDias em que os alimentos foram consumidos (Y[i,j]):\n")
        for j in range(dias):
            arquivo.write(f"\nDia {j}:\n")
            for i in range(len(alimentos)):
                if Y[i, j].x > 0:
                    arquivo.write(f"  Alimento {alimentos[i]}\n")
        
        # Refeições em que os alimentos foram consumidos
        arquivo.write("\nRefeições em que os alimentos foram consumidos (Z[i,j,k]):\n")
        for j in range(dias):
            for k in range(refeicoes):
                arquivo.write(f"\nDia {j}, Refeição {k}:\n")
                for i in range(len(alimentos)):
                    if Z[i, j, k].x > 0:
                        arquivo.write(f"  Alimento {alimentos[i]}\n")
    else:
        arquivo.write(f"Modelo não encontrado ou solução não ótima. Status: {model.status}\n")
