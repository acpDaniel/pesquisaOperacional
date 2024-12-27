from gurobipy import Model, GRB, quicksum
import pandas as pd

# Carregar os dados do Excel
data = pd.read_excel("alimentosTeste.xlsx")

# Conjuntos
alimentos = data['alimento'].tolist()
dias = range(7)  # Supondo 7 dias na semana
refeicoes = range(3)  # 3 refeições por dia

# Parâmetros
calorias = data['calorias'].tolist()
carboidratos = data['carboidratos'].tolist()
proteinas = data['proteinas'].tolist()
gorduras = data['gorduras'].tolist()
ferro = data['ferro'].tolist()
magnesio = data['magnesio'].tolist()
vitamina_c = data['vitamina_c'].tolist()
zinco = data['zinco'].tolist()
sodio = data['sodio'].tolist()
preco = data['preco'].tolist()
max_porcoes = data['max_porcoes_dia'].tolist()
max_dias = data['max_dias'].tolist()

# Restrições nutricionais
nutrientes_min = [3000, 450, 120, 70, 8, 400, 75, 11, 3000]  # Calorias, carb, prot, gord, ferro, mag, vitC, zinco, sodio
nutrientes_max = [5000, 900, 150, 120, 18, 420, 90, 11, 7000]

# Modelo
model = Model("Problema da dieta")

# Variáveis
X = model.addVars(len(alimentos), len(dias), len(refeicoes), vtype=GRB.INTEGER, name="X")
Z = model.addVars(len(alimentos), len(dias), len(refeicoes), vtype=GRB.BINARY, name="Z")
Y = model.addVars(len(alimentos), len(dias), vtype=GRB.BINARY, name="Y")

# Função objetivo: minimizar o custo total
print("Definindo a função objetivo...")
model.setObjective(
    quicksum(preco[i] * X[i, j, k] for i in range(len(alimentos)) for j in dias for k in refeicoes),
    GRB.MINIMIZE
)

# Restrições nutricionais por dia
print("Adicionando restrições nutricionais por dia...")
for j in dias:
    for n, (nutr_min, nutr_max) in enumerate(zip(nutrientes_min, nutrientes_max)):
        # Parte do lado esquerdo da restrição (LHS)
        lhs_min = quicksum(
            X[i, j, k] * [calorias, carboidratos, proteinas, gorduras, ferro, magnesio, vitamina_c, zinco, sodio][n][i]
            for i in range(len(alimentos)) for k in refeicoes
        )
        # Print da restrição mínima
        print(f"Dia {j + 1}, Nutriente {n} (min): {lhs_min} >= {nutr_min}")
        model.addConstr(lhs_min >= nutr_min, name=f"Nut_Min_{n}_Dia_{j}")
        
        # Parte do lado esquerdo para a restrição máxima
        lhs_max = quicksum(
            X[i, j, k] * [calorias, carboidratos, proteinas, gorduras, ferro, magnesio, vitamina_c, zinco, sodio][n][i]
            for i in range(len(alimentos)) for k in refeicoes
        )
        # Print da restrição máxima
        print(f"Dia {j + 1}, Nutriente {n} (max): {lhs_max} <= {nutr_max}")
        model.addConstr(lhs_max <= nutr_max, name=f"Nut_Max_{n}_Dia_{j}")

# Restrição: máximo de porções por alimento por refeição e dia
print("Adicionando restrição de porções por alimento por refeição e dia...")
for i in range(len(alimentos)):
    for j in dias:
        for k in refeicoes:
            # Restrição por refeição
            print(f"X[{i},{j},{k}] <= {max_porcoes[i]} * Z[{i},{j},{k}]")
            model.addConstr(X[i, j, k] <= max_porcoes[i] * Z[i, j, k], name=f"Max_Porcoes_{i}_{j}_{k}")
        # Restrição total por dia
        print(f"Sum(X[{i},{j},k]) for k in refeicoes <= {max_porcoes[i]} * Y[{i},{j}]")
        model.addConstr(
            quicksum(X[i, j, k] for k in refeicoes) <= max_porcoes[i] * Y[i, j],
            name=f"Max_Porcoes_Total_{i}_{j}"
        )

# Restrição: limite máximo de dias que um alimento pode ser consumido
print("Adicionando restrição de consumo máximo por dias...")
for i in range(len(alimentos)):
    # Restrição de limite de dias
    print(f"Sum(Y[{i},j]) for j in dias <= {max_dias[i]}")
    model.addConstr(quicksum(Y[i, j] for j in dias) <= max_dias[i], name=f"Max_Dias_{i}")

# Restrição: consumo máximo de 2 refeições diárias por alimento
print("Adicionando restrição de máximo de 2 refeições por dia por alimento...")
for i in range(len(alimentos)):
    for j in dias:
        # Restrição por dia
        print(f"Sum(Z[{i},{j},k]) for k in refeicoes <= 2 * Y[{i},{j}]")
        model.addConstr(
            quicksum(Z[i, j, k] for k in refeicoes) <= 2 * Y[i, j],
            name=f"Max_Refeicoes_{i}_{j}"
        )

# Restrição: limite total de porções diárias
print("Adicionando restrição de limite total de porções diárias...")
for j in dias:
    # Restrição total de porções por dia
    print(f"Sum(X[i,{j},k]) for i in alimentos, k in refeicoes <= 50")
    model.addConstr(
        quicksum(X[i, j, k] for i in range(len(alimentos)) for k in refeicoes) <= 50,
        name=f"Max_Porcoes_Dia_{j}"
    )


# Resolver o modelo
print("Otimizando o modelo...")
model.optimize()

# Imprimir solução
if model.status == GRB.OPTIMAL:
    print("Solução ótima encontrada:")
    for i in range(len(alimentos)):
        for j in dias:
            for k in refeicoes:
                if X[i, j, k].x > 0:
                    print(f"Alimento: {alimentos[i]}, Dia: {j + 1}, Refeição: {k + 1}, Porções: {X[i, j, k].x}")
else:
    print("Nenhuma solução ótima foi encontrada.")
