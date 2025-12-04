import os
from concurrent.futures import ProcessPoolExecutor, as_completed

from file_handler import (load_instance_files, load_optimal_values, 
                          write_temp_file, read_temp_file, write_summary_file)
from run_vns import prepare_tasks, run_single_replication


# Configurações gerais
NUM_REPLICATIONS = 16
SEEDS = [42, 101, 202, 303, 404, 505, 606, 707, 808, 909, 1001, 1707, 1905, 1936, 1969, 1618]

INSTANCES_DIR = "testes_relatorio/instancias_teste_relatorio"
VNS_SCRIPT = "alwabp_vns.py"
OUTPUT_DIR = "testes_relatorio/vns_resultados_teste_relatorio"
INSTANCES_CSV = "instances.csv"  # Arquivo com os valores ótimos/UB

SUMMARY_FILE = os.path.join(OUTPUT_DIR, "../summary_results.csv")
TEMP_FILE = os.path.join(OUTPUT_DIR, "../temp_results.csv")


def run_experiment_parallel():
    """
    Executa todas as instâncias em paralelo com múltiplas replicações.
    """
    # Carregar valores ótimos
    print(f"Carregando valores ótimos de {INSTANCES_CSV}...")
    optimal_values = load_optimal_values(INSTANCES_CSV)
    
    # Listar instâncias
    print(f"Carregando instâncias de {INSTANCES_DIR}...")
    instance_files = load_instance_files(INSTANCES_DIR)

    print(f"Iniciando experimentos: {len(instance_files)} instâncias × {NUM_REPLICATIONS} replicações")
    print(f"Arquivo temporário: {TEMP_FILE}")
    print(f"Arquivo final: {SUMMARY_FILE}")

    # Preparar tarefas
    tasks = prepare_tasks(
        instance_files, NUM_REPLICATIONS, SEEDS, VNS_SCRIPT, OUTPUT_DIR
    )

    # Execução paralela
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(run_single_replication, *task) for task in tasks]

        results = []
        print("\nProgresso:")

        # Processa conforme as tarefas concluem
        for i, future in enumerate(as_completed(futures)):
            result_line = future.result()
            results.append(result_line)

            # Atualiza percentual concluído
            pct = (i + 1) / len(tasks) * 100
            print(f"  -> {i+1}/{len(tasks)} ({pct:.2f}%)", end="\r", flush=True)

    print("\n\nTodas as replicações concluídas.")
    
    # Salvar resultados temporários
    print(f"Salvando resultados temporários em {TEMP_FILE}...")
    write_temp_file(TEMP_FILE, results)
    
    # Consolidar resultados
    print("Consolidando resultados por instância...")
    instance_data = read_temp_file(TEMP_FILE)
    write_summary_file(SUMMARY_FILE, instance_data, optimal_values)
    
    print(f"Arquivo final salvo em: {SUMMARY_FILE}")
    
    # Remover arquivo temporário (opcional)
    try:
        os.remove(TEMP_FILE)
        print(f"Arquivo temporário {TEMP_FILE} removido.")
    except OSError:
        pass


if __name__ == "__main__":
    run_experiment_parallel()