import os
import subprocess
import glob
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict

"""
Execução paralela do algoritmo VNS com múltiplas replicações.

Objetivo:
---------
Executar o VNS para cada instância em uma pasta, repetindo várias vezes
com diferentes seeds, salvando a saída individual e um CSV consolidado.

Resumo:
-------
- run_single_replication(): executa 1 instância + seed + rep.
- run_experiment_parallel(): organiza as tarefas e roda tudo em paralelo.
"""

# Configurações gerais
NUM_REPLICATIONS = 5
SEEDS = [42, 101, 202, 303, 404]

INSTANCES_DIR = "testes_relatorio/instancias_teste_relatorio"
VNS_SCRIPT = "alwabp_vns.py"
OUTPUT_DIR = "testes_relatorio/vns_resultados_teste_relatorio"

SUMMARY_FILE = os.path.join(OUTPUT_DIR, "../summary_results.csv")


def run_single_replication(instance_path: str, instance_name: str, rep: int, seed: int) -> str:
    """
    Executa 1 replicação do VNS para uma instância.

    - Roda o script VNS via subprocess.
    - Redireciona a instância com '< instance_path'.
    - Captura SI;SF;tempo da saída padrão.
    - Retorna a linha formatada para o CSV.

    Retorno:
        "instancia;rep;seed;SI;SF;tempo"
    """

    # Garante pasta de saída (cada processo pode rodar isolado)
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Arquivo onde a solução completa será salva
    output_filename = os.path.join(
        OUTPUT_DIR, f"{instance_name}_rep{rep+1}_seed{seed}.txt"
    )

    # Comando de execução do VNS
    command = f"python {VNS_SCRIPT} {output_filename} {seed} < {instance_path}"

    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )

        summary_line = result.stdout.strip()
        return f"{instance_name};{rep+1};{seed};{summary_line}"

    except subprocess.CalledProcessError as e:
        msg = e.stderr.strip()
        print(f"\n{instance_name} - Rep {rep+1} Seed {seed}: ERRO — {msg}")
        return f"{instance_name};{rep+1};{seed};ERROR;ERROR;ERROR"

    except Exception as e:
        print(f"\n{instance_name} - Rep {rep+1} Seed {seed}: ERRO — {e}")
        return f"{instance_name};{rep+1};{seed};ERROR;ERROR;ERROR"


def run_experiment_parallel():
    """
    Executa todas as instâncias em paralelo com múltiplas replicações.

    Etapas:
    -------
    1. Localiza todas as instâncias em INSTANCES_DIR.
    2. Cria uma tarefa (instance × rep × seed) para cada combinação.
    3. Executa tudo simultaneamente com ProcessPoolExecutor.
    4. Escreve a linha de cada execução no CSV final.
    5. Exibe progresso no terminal.
    """

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Lista de instâncias
    instance_files = sorted(glob.glob(os.path.join(INSTANCES_DIR, "*")))

    print(f"Iniciando experimentos: {len(instance_files)} instâncias × {NUM_REPLICATIONS} replicações")
    print(f"Saída consolidada: {SUMMARY_FILE}")

    tasks = []

    # Cria todas as tarefas
    for instance_path in instance_files:
        instance_name = os.path.basename(instance_path)
        for rep in range(NUM_REPLICATIONS):
            seed = SEEDS[rep]
            tasks.append((instance_path, instance_name, rep, seed))

    # Execução paralela
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(run_single_replication, *task) for task in tasks]

        # CSV final
        with open(SUMMARY_FILE, "w") as f:
            f.write("Instance;Replication;Seed;SI;SF;Time_s\n")

        print("\nProgresso:")

        # Processa conforme as tarefas concluem
        for i, future in enumerate(as_completed(futures)):
            result_line = future.result()

            with open(SUMMARY_FILE, "a") as f:
                f.write(result_line + "\n")

            # Atualiza percentual concluído
            pct = (i + 1) / len(tasks) * 100
            print(f"  -> {i+1}/{len(tasks)} ({pct:.2f}%)", end="\r", flush=True)

    print("\n\nExecução concluída.")
    print("Arquivo final:", SUMMARY_FILE)


if __name__ == "__main__":
    run_experiment_parallel()
