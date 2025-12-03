import sys
import math
import random
import time
from typing import List, Tuple, Dict, Any

# Valor usado para representar tarefa impossível/incapacidade
INF = float('inf')


class ALWABPInstance:
    """
    Representa uma instância do problema ALWABP.
    
    A instância contém:
    - n tarefas
    - k trabalhadores/estações
    - tempos t_{w,i}
    - precedências (i → j)
    
    Também constrói listas de predecessores e sucessores para acesso rápido.
    """

    def __init__(self, num_tasks: int, num_workers: int,
                 task_times: List[List[float]], precedences: List[Tuple[int, int]]):
        self.num_tasks = num_tasks
        self.num_workers = num_workers
        self.task_times = task_times
        self.precedences = precedences

        # Estruturas auxiliares
        self.predecessors = {i: [] for i in range(1, num_tasks + 1)}
        self.successors = {i: [] for i in range(1, num_tasks + 1)}

        for i, j in precedences:
            self.successors[i].append(j)
            self.predecessors[j].append(i)

    @classmethod
    def from_stdin(cls) -> 'ALWABPInstance':
        """
        Lê uma instância completa do ALWABP a partir do stdin.
        Formato:
            n
            t_1...t_k   (repetido n vezes)
            i j         (precedências)
            -1 -1       (fim)
        """
        # Número de tarefas
        try:
            line = sys.stdin.readline().strip()
            if not line:
                raise EOFError("Fim inesperado ao ler n.")
            num_tasks = int(line)
        except Exception as e:
            print(f"Erro ao ler n: {e}", file=sys.stderr)
            sys.exit(1)

        # Matriz de tempos (n linhas, k colunas)
        task_times_raw = []
        num_workers = 0

        for _ in range(num_tasks):
            try:
                line = sys.stdin.readline().strip()
                if not line:
                    raise EOFError("Fim inesperado ao ler tempos.")
                times = [float(x) for x in line.split()]
                task_times_raw.append(times)

                if num_workers == 0:
                    num_workers = len(times)
                elif len(times) != num_workers:
                    raise ValueError("Linhas com quantidade inconsistente de tempos.")
            except Exception as e:
                print(f"Erro na matriz de tempos: {e}", file=sys.stderr)
                sys.exit(1)

        # Transposição: task_times[w][i]
        task_times_transposed = [
            [task_times_raw[i][w] for i in range(num_tasks)]
            for w in range(num_workers)
        ] if num_tasks > 0 else []

        # Precedências
        precedences = []
        while True:
            line = sys.stdin.readline().strip()
            if not line:
                break
            parts = line.split()
            if not parts:
                continue
            try:
                i, j = map(int, parts)
                if i == -1 and j == -1:
                    break
                precedences.append((i, j))
            except Exception as e:
                # Linha inválida (exceto comentários)
                if line and not line.startswith("#"):
                    print(f"Erro ao ler precedência '{line}': {e}", file=sys.stderr)
                    sys.exit(1)
                elif not line:
                    break

        return cls(num_tasks, num_workers, task_times_transposed, precedences)


class ALWABPSolution:
    """
    Armazena uma solução do ALWABP:
    - Atribuição de tarefas às estações
    - Atribuição de trabalhadores às estações
    - Avaliação da solução (factibilidade e C_max)
    """

    def __init__(self, instance: ALWABPInstance,
                 task_station_assignment: List[int],
                 worker_station_assignment: List[int]):
        self.instance = instance
        self.task_station_assignment = task_station_assignment
        self.worker_station_assignment = worker_station_assignment

        self.is_feasible = False
        self.cycle_time = INF
        self.station_times = []

    def evaluate(self):
        """
        Avalia a solução:
        - Checa precedências
        - Checa incapacidade
        - Soma tempos por estação
        - Define C_max (cycle_time)
        """
        inst = self.instance
        n = inst.num_tasks
        m = inst.num_workers

        # Precedências
        for i1, j1 in inst.precedences:
            i = i1 - 1
            j = j1 - 1
            si = self.task_station_assignment[i]
            sj = self.task_station_assignment[j]

            if si == -1 or sj == -1 or si > sj:
                self.is_feasible = False
                self.cycle_time = INF
                self.station_times = [INF] * m
                return

        # Soma tempos por estação
        station_times = [0.0] * m
        tasks_in_station = {s: [] for s in range(m)}

        for i in range(n):
            tasks_in_station[self.task_station_assignment[i]].append(i)

        for s in range(m):
            w = self.worker_station_assignment[s]
            total = 0.0
            for i in tasks_in_station[s]:
                t = inst.task_times[w][i]
                if t >= INF:
                    self.is_feasible = False
                    self.cycle_time = INF
                    self.station_times = [INF] * m
                    return
                total += t
            station_times[s] = total

        self.is_feasible = True
        self.station_times = station_times
        self.cycle_time = max(station_times) if station_times else 0

    def __lt__(self, other: 'ALWABPSolution') -> bool:
        """Comparação entre soluções: factível > infactível; menor cycle_time é melhor."""
        if self.is_feasible != other.is_feasible:
            return self.is_feasible
        return self.cycle_time < other.cycle_time

    def to_output_format(self) -> str:
        """
        Retorna uma string formatada da solução:
        - C_max
        - Estação s: Trabalhador w -> tarefas
        """
        if not self.is_feasible:
            return f"{INF}\nSolução Infactível"

        out = f"{self.cycle_time:.6f}\n"
        m = self.instance.num_workers
        n = self.instance.num_tasks

        station_tasks = {s + 1: [] for s in range(m)}
        for i in range(n):
            s = self.task_station_assignment[i] + 1
            station_tasks[s].append(i + 1)

        for s in range(1, m + 1):
            w = self.worker_station_assignment[s - 1] + 1
            tasks = " ".join(map(str, sorted(station_tasks[s])))
            out += f"Estação {s}: Trabalhador {w} -> Tarefas: {tasks}\n"

        return out.strip()


# ------------------------------------------------------
# Funções auxiliares
# ------------------------------------------------------

def check_precedence_feasibility(instance: ALWABPInstance,
                                 task_station_assignment: List[int]) -> bool:
    """Valida precedências para uma atribuição de tarefas."""
    for i1, j1 in instance.precedences:
        i = i1 - 1
        j = j1 - 1
        si = task_station_assignment[i]
        sj = task_station_assignment[j]
        if si == -1 or sj == -1 or si > sj:
            return False
    return True


def generate_initial_solution(instance: ALWABPInstance) -> ALWABPSolution:
    """
    Gera solução inicial:
    - Permuta trabalhadores aleatoriamente
    - Atribui tarefas em ordem topológica, respeitando precedências e incapacidade
    """
    n = instance.num_tasks
    m = instance.num_workers

    # Trabalhadores embaralhados
    workers = list(range(m))
    random.shuffle(workers)
    worker_station_assignment = workers

    # Topological order
    in_degree = {i: len(instance.predecessors[i + 1]) for i in range(n)}
    queue = [i for i in range(n) if in_degree[i] == 0]
    topo = []

    while queue:
        i = queue.pop(0)
        topo.append(i)
        for j1 in instance.successors[i + 1]:
            j = j1 - 1
            in_degree[j] -= 1
            if in_degree[j] == 0:
                queue.append(j)

    if len(topo) != n:
        print("Erro: ciclo no grafo de precedência.", file=sys.stderr)
        return ALWABPSolution(instance, [-1] * n, worker_station_assignment)

    # Atribuição gulosa
    task_station_assignment = [-1] * n

    for i in topo:
        for s in range(m):
            w = worker_station_assignment[s]
            if instance.task_times[w][i] >= INF:
                continue

            ok = True
            for pred1 in instance.predecessors[i + 1]:
                pred = pred1 - 1
                if task_station_assignment[pred] > s:
                    ok = False
                    break
            if ok:
                task_station_assignment[i] = s
                break

        if task_station_assignment[i] == -1:
            print(f"Erro ao alocar tarefa {i+1}.", file=sys.stderr)
            return ALWABPSolution(instance, [-1] * n, worker_station_assignment)

    sol = ALWABPSolution(instance, task_station_assignment, worker_station_assignment)
    sol.evaluate()
    return sol


# ------------------------------------------------------
# VNS
# ------------------------------------------------------

def vns(instance: ALWABPInstance, max_iter: int, k_max: int) -> Tuple[ALWABPSolution, ALWABPSolution]:
    """
    Executa o VNS:
    - Gera solução inicial
    - Executa laços de shaking + VND
    - Retorna solução inicial e melhor solução
    """
    s_initial = generate_initial_solution(instance)
    s_best = s_initial
    s_current = s_initial

    iteration = 0
    while iteration < max_iter:
        k = 1
        while k <= k_max:
            s_prime = shaking(s_current, k)
            s_prime_prime = vnd(s_prime)

            if s_prime_prime < s_current:
                s_current = s_prime_prime
                if s_current < s_best:
                    s_best = s_current
                    k = 1
                else:
                    k += 1
            else:
                k += 1

        iteration += 1

    return s_initial, s_best


def shaking(solution: ALWABPSolution, k: int) -> ALWABPSolution:
    """
    Realiza shaking (perturbação):
    k=1 Swap de tarefas
    k=2 Reatribuição de tarefa
    k=3 Swap de trabalhadores
    """
    inst = solution.instance
    n = inst.num_tasks
    m = inst.num_workers

    new_t = list(solution.task_station_assignment)
    new_w = list(solution.worker_station_assignment)

    if k == 1:
        if n < 2: return solution
        i1, i2 = random.sample(range(n), 2)
        new_t[i1], new_t[i2] = new_t[i2], new_t[i1]

    elif k == 2:
        i = random.choice(range(n))
        s_old = new_t[i]
        opts = [s for s in range(m) if s != s_old]
        if not opts: return solution
        new_t[i] = random.choice(opts)

    elif k == 3:
        if m < 2: return solution
        s1, s2 = random.sample(range(m), 2)
        new_w[s1], new_w[s2] = new_w[s2], new_w[s1]

    else:
        return shaking(solution, 2)

    s_prime = ALWABPSolution(inst, new_t, new_w)
    s_prime.evaluate()
    return s_prime


def vnd(solution: ALWABPSolution) -> ALWABPSolution:
    """
    Executa VND:
    l=1: Task Reassignment
    l=2: Worker Swap
    (first improvement)
    """
    s_current = solution
    l = 1
    l_max = 2

    while l <= l_max:
        if l == 1:
            s_prime = local_search_task_reassignment(s_current)
        else:
            s_prime = local_search_worker_swap(s_current)

        if s_prime < s_current:
            s_current = s_prime
            l = 1
        else:
            l += 1

    return s_current


def local_search_task_reassignment(solution: ALWABPSolution) -> ALWABPSolution:
    """Busca local (first improvement) movendo tarefas entre estações."""
    inst = solution.instance
    n = inst.num_tasks
    m = inst.num_workers

    s_current = solution
    improved = True

    while improved:
        improved = False
        for i in range(n):
            s_old = s_current.task_station_assignment[i]
            for s_new in range(m):
                if s_new == s_old:
                    continue

                new_t = list(s_current.task_station_assignment)
                new_t[i] = s_new

                if not check_precedence_feasibility(inst, new_t):
                    continue

                s_neighbor = ALWABPSolution(inst, new_t, s_current.worker_station_assignment)
                s_neighbor.evaluate()

                if s_neighbor < s_current:
                    s_current = s_neighbor
                    improved = True
                    break
            if improved:
                break

    return s_current


def local_search_worker_swap(solution: ALWABPSolution) -> ALWABPSolution:
    """Busca local (first improvement) trocando trabalhadores entre estações."""
    inst = solution.instance
    m = inst.num_workers

    s_current = solution
    improved = True

    while improved:
        improved = False

        for s1 in range(m):
            for s2 in range(s1 + 1, m):
                new_w = list(s_current.worker_station_assignment)
                new_w[s1], new_w[s2] = new_w[s2], new_w[s1]

                s_neighbor = ALWABPSolution(inst, s_current.task_station_assignment, new_w)
                s_neighbor.evaluate()

                if s_neighbor < s_current:
                    s_current = s_neighbor
                    improved = True
                    break
            if improved:
                break

    return s_current


# ------------------------------------------------------
# Função Principal
# ------------------------------------------------------

def main():
    """
    Executa:
    1. Leitura da instância via stdin
    2. Configuração do VNS
    3. Execução do VNS
    4. Impressão do SI/SF/tempo
    5. Grava solução completa em arquivo
    """
    output_filename = sys.argv[1] if len(sys.argv) >= 2 else "best_solution.txt"

    # Instância (entradas vêm via redirecionamento "<")
    instance = ALWABPInstance.from_stdin()

    # Parâmetros do VNS
    MAX_ITER = 50
    K_MAX = 3

    # Semente da execução
    if len(sys.argv) > 2:
        try:
            random.seed(int(sys.argv[2]))
        except ValueError:
            random.seed(42)
    else:
        random.seed(42)

    # Rodar VNS
    start = time.time()
    s_initial, s_best = vns(instance, MAX_ITER, K_MAX)
    end = time.time()

    # Saída simplificada (para o script que processa seeds)
    si = s_initial.cycle_time if s_initial.is_feasible else INF
    sf = s_best.cycle_time if s_best.is_feasible else INF
    print(f"{si};{sf};{end-start:.4f}")

    # Salvar solução completa
    try:
        with open(output_filename, "w") as f:
            f.write(s_best.to_output_format())
    except Exception as e:
        print(f"Erro ao salvar solução: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
