import sys
import os
from pathlib import Path
from gurobipy import *

# ============================================================
# Carrega instância no formato que você enviou
# ============================================================
class ALWABPInstance:
    def __init__(self, n, k, task_times, precedences):
        self.num_tasks = n
        self.num_workers = k
        self.task_times = task_times      # task_times[w][i]
        self.precedences = precedences    # pares (i,j)

    @classmethod
    def from_file(cls, file_path):
        with open(file_path, 'r') as f:
            line = f.readline().strip()
            if not line:
                raise ValueError("Erro ao ler n")
            n = int(line)

            # matriz t_iw (n linhas, k colunas)
            raw = []
            k = 0
            for _ in range(n):
                line = f.readline().strip()
                times = []
                for x in line.split():
                    if x.lower() == 'inf':
                        times.append(1e12)  # Usar um valor muito grande para Inf
                    else:
                        times.append(float(x))
                raw.append(times)
                if k == 0:
                    k = len(times)
                elif len(times) != k:
                    raise ValueError("Quantidade inconsistente de tempos")

            # transposição: task_times[w][i]
            task_times = [[raw[i][w] for i in range(n)] for w in range(k)]

            # precedências (converter para índices 0-based)
            prec = []
            while True:
                line = f.readline().strip()
                if not line:
                    break
                i, j = map(int, line.split())
                if i == -1 and j == -1:
                    break
                # Converter de 1-based para 0-based
                prec.append((i-1, j-1))

        return cls(n, k, task_times, prec)

# ============================================================
# Construção e solução do modelo de Gurobi
# ============================================================
def solve_alwabp_gurobi(inst: ALWABPInstance, time_limit=1200):
    n = inst.num_tasks
    k = inst.num_workers
    m = k   # número de estações = número de trabalhadores
    TW = inst.task_times
    prec = inst.precedences

    model = Model("ALWABP")
    model.Params.OutputFlag = 0  # Reduzir output no console
    model.Params.TimeLimit = time_limit  # 20 minutos = 1200 segundos
    model.Params.LogToConsole = 0  # Desativar log do Gurobi no console
    
    S = range(m)
    W = range(k)
    I = range(n)

    # ------------------------------------------------------------
    # Variáveis
    # ------------------------------------------------------------
    x = model.addVars(n, m, vtype=GRB.BINARY, name="x")
    y = model.addVars(k, m, vtype=GRB.BINARY, name="y")
    z = model.addVars(k, n, m, vtype=GRB.BINARY, name="z")
    c = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name="cycle")

    # ------------------------------------------------------------
    # 1. Cada tarefa em exatamente uma estação
    # ------------------------------------------------------------
    for i in I:
        model.addConstr(sum(x[i,s] for s in S) == 1)

    # ------------------------------------------------------------
    # 2. Cada trabalhador em exatamente uma estação
    # ------------------------------------------------------------
    for w in W:
        model.addConstr(sum(y[w,s] for s in S) == 1)

    # ------------------------------------------------------------
    # 3. Cada estação tem exatamente 1 trabalhador
    # ------------------------------------------------------------
    for s in S:
        model.addConstr(sum(y[w,s] for w in W) == 1)

    # ------------------------------------------------------------
    # 4. Precedências
    # ------------------------------------------------------------
    for (i,j) in prec:
        if 0 <= i < n and 0 <= j < n:  # Verificação de segurança
            lhs = sum((s+1)*x[i,s] for s in S)
            rhs = sum((s+1)*x[j,s] for s in S)
            model.addConstr(lhs <= rhs)

    # ------------------------------------------------------------
    # 5. Linearização z[w,i,s] = x[i,s] * y[w,s]
    # ------------------------------------------------------------
    for w in W:
        for i in I:
            for s in S:
                model.addConstr(z[w,i,s] <= x[i,s])
                model.addConstr(z[w,i,s] <= y[w,s])
                model.addConstr(z[w,i,s] >= x[i,s] + y[w,s] - 1)

    # ------------------------------------------------------------
    # 6. Restrição de tempo por estação
    # ------------------------------------------------------------
    for s in S:
        model.addConstr(sum(TW[w][i] * z[w,i,s] for w in W for i in I) <= c)

    # ------------------------------------------------------------
    # 7. Incapacidades (twi = ∞)
    # ------------------------------------------------------------
    for w in W:
        for i in I:
            if TW[w][i] >= 1e12:  # interpreta como "incapaz"
                for s in S:
                    model.addConstr(z[w,i,s] == 0)

    # ------------------------------------------------------------
    # Objetivo: minimizar ciclo
    # ------------------------------------------------------------
    model.setObjective(c, GRB.MINIMIZE)

    # ------------------------------------------------------------
    # Resolve
    # ------------------------------------------------------------
    model.optimize()
    
    # ============================================================
    # Coleta resultados
    # ============================================================
    resultados = []
    
    # Informações básicas da instância
    resultados.append("=" * 60)
    resultados.append(f"INSTÂNCIA: {inst.num_tasks} tarefas, {inst.num_workers} trabalhadores")
    resultados.append("=" * 60)
    resultados.append("SOLUÇÃO ALWABP via GUROBI")
    resultados.append("-" * 60)
    
    if model.status == GRB.OPTIMAL:
        resultados.append(f"Status: Solução ótima encontrada")
    elif model.status == GRB.TIME_LIMIT:
        resultados.append(f"Status: Time limit atingido (20 minutos)")
        if model.SolCount > 0:
            resultados.append(f"Melhor solução encontrada até o momento")
    elif model.status in [GRB.INFEASIBLE, GRB.INF_OR_UNBD]:
        resultados.append("Status: Modelo infactível")
        return resultados
    elif model.status == GRB.UNBOUNDED:
        resultados.append("Status: Modelo ilimitado")
        return resultados
    else:
        resultados.append(f"Status do solver: {model.status}")
    
    if model.SolCount > 0:
        # Tempo de ciclo (valor objetivo)
        resultados.append(f"Tempo de ciclo: {c.X}")
        resultados.append(f"Valor objetivo: {model.ObjVal}")
        resultados.append(f"Gap: {model.MIPGap:.4%}")
        resultados.append(f"Tempo de execução: {model.Runtime:.2f} segundos")
        resultados.append(f"Limite de tempo: {time_limit} segundos")
        
        # Trabalhador por estação
        resultados.append("\nTrabalhador por estação:")
        worker_by_station = {}
        for s in S:
            for w in W:
                if y[w,s].X > 0.5:
                    resultados.append(f" Estaçao {s+1}: trabalhador {w+1}")
                    worker_by_station[s] = w
                    break
        
        # Tarefas por estação (mostrar como 1-based para o usuário)
        resultados.append("\nTarefas por estação:")
        for s in S:
            tasks_s = [i+1 for i in I if x[i,s].X > 0.5]
            resultados.append(f" Estaçao {s+1} (trabalhador {worker_by_station[s]+1}): {tasks_s}")
            
            # Calcular tempo de trabalho por estação
            station_time = 0
            w = worker_by_station[s]
            for i in I:
                if x[i,s].X > 0.5:
                    station_time += TW[w][i]
            resultados.append(f"  Tempo total na estação: {station_time}")
            
        # Informações de balanceamento
        station_times = []
        for s in S:
            w = worker_by_station[s]
            station_time = 0
            for i in I:
                if x[i,s].X > 0.5:
                    station_time += TW[w][i]
            station_times.append(station_time)
        
        if station_times:
            max_time = max(station_times)
            min_time = min(station_times)
            avg_time = sum(station_times) / len(station_times)
            balanceamento = (max_time - avg_time) / avg_time * 100
            
            resultados.append("\nANÁLISE DE BALANCEAMENTO:")
            resultados.append(f"  Tempo máximo na estação: {max_time}")
            resultados.append(f"  Tempo mínimo na estação: {min_time}")
            resultados.append(f"  Tempo médio nas estações: {avg_time:.2f}")
            resultados.append(f"  Desbalanceamento: {balanceamento:.2f}%")
    else:
        resultados.append("Nenhuma solução viável encontrada.")
    
    resultados.append("=" * 60)
    return resultados