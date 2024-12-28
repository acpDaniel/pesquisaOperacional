import pandas as pd
from gurobipy import Model, GRB, quicksum

# Carregar os dados da planilha
df = pd.read_excel("alimentosTeste.xlsx")

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
    "sodio": (3000, 7000)
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
#1-laticinios   2-frutas    3-horticolas    4-cereais_derivados_tuberculos  5-carne_peixe_ovos  6-leguminosas 7-oleos_gorduras
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
            quicksum(Z[i,j,k] for k in range(refeicoes)) <= 2 * Y[i,j],
            f"max_refeicoes_alimento_{i}_dia_{j}"
        )

# Restrição de limite total de 50 porções de alimento por dia
for j in range(dias):
    model.addConstr(
        quicksum(X[i,j,k] for i in range(len(alimentos)) for k in range(refeicoes)) <= 50,
        f"limite_total_porcoes_dia_{j}"
    )

# Resolver o modelo
model.optimize()

# Verificar o status da solução
if model.status == GRB.OPTIMAL:
    print("Solução ótima encontrada!")
    for i in range(len(alimentos)):
        for j in range(dias):
            for k in range(refeicoes):
                if X[i,j,k].x > 0: #printa apenas as variáveis X que são diferentes de zero
                    print(f"Alimento: {alimentos[i]}, Dia: {j+1}, Refeição: {k+1}, Porções: {X[i,j,k].x}")
    print(f"\nCusto total da dieta: {model.objVal}")
else:
    print("Não foi possível encontrar uma solução ótima.")