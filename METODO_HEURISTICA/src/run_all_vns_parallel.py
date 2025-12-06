import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

from config import (
    NUM_REPLICATIONS,
    SEEDS,
    TIME_LIMIT,      # limite de tempo POR INSTÂNCIA
    VNS_MAX_ITER,
    VNS_K_MAX,
)
from file_handler import (
    load_instance_files,
    load_optimal_values,
    write_temp_file,
    read_temp_file,
    write_summary_file,
)
from run_vns import run_single_replication


# Configurações de caminhos (também fáceis de mudar)
INSTANCES_DIR = "../testes_relatorio/instancias_teste_relatorio"
VNS_SCRIPT = "alwabp_vns.py"
OUTPUT_DIR = "../testes_relatorio/vns_resultados_teste_relatorio"
INSTANCES_CSV = "../instances.csv"  # Arquivo com os valores ótimos/UB

SUMMARY_FILE = os.path.join(OUTPUT_DIR, "../summary_results.csv")
TEMP_FILE = os.path.join(OUTPUT_DIR, "../temp_results.csv")


def run_instance_with_limit(instance_path: str,
                            instance_name: str,
                            num_replications: int,
                            seeds: list,
                            vns_script: str,
                            output_dir: str,
                            max_iter: int,
                            k_max: int,
                            instance_time_limit: float | None):
    """
    Roda TODAS as replicações de UMA instância, em série, respeitando
    um limite de tempo total por instância.

    - Mede o tempo desde o início da primeira replicação até o fim da última
      (ou até estourar o limite).
    - Se atingir o tempo-limite, interrompe novas replicações.
    - Retorna (lista_de_resultados, tempo_total_da_instancia).
    """
    start_time = time.time()
    results = []

    for rep in range(num_replications):
        elapsed = time.time() - start_time
        if instance_time_limit is not None and elapsed >= instance_time_limit:
            print(
                f"\n{instance_name}: limite de tempo por instância atingido "
                f"({elapsed:.2f}s >= {instance_time_limit:.2f}s). "
                "Interrompendo replicações."
            )
            break

        seed = seeds[rep]
        line = run_single_replication(
            instance_path=instance_path,
            instance_name=instance_name,
            rep=rep,
            seed=seed,
            vns_script=vns_script,
            output_dir=output_dir,
            max_iter=max_iter,
            k_max=k_max,
        )
        results.append(line)

    total_time = time.time() - start_time
    print(f"\n{instance_name}: tempo total de execução {total_time:.2f}s.")

    return results, total_time


def run_experiment_parallel():
    """
    Executa todas as instâncias em paralelo, mas as replicações de cada
    instância são executadas em série dentro de um mesmo processo,
    respeitando um limite de tempo total por instância.
    """
    # Carregar valores ótimos
    print(f"Carregando valores ótimos de {INSTANCES_CSV}...")
    optimal_values = load_optimal_values(INSTANCES_CSV)
    
    # Listar instâncias
    print(f"Carregando instâncias de {INSTANCES_DIR}...")
    instance_files = load_instance_files(INSTANCES_DIR)

    print(f"Iniciando experimentos: {len(instance_files)} instâncias × {NUM_REPLICATIONS} replicações (máx.)")
    print(f"Limite de tempo por instância: {TIME_LIMIT if TIME_LIMIT is not None else 'sem limite'} s")
    print(f"Arquivo temporário: {TEMP_FILE}")
    print(f"Arquivo final: {SUMMARY_FILE}")

    all_results = []
    instance_times: dict[str, float] = {}

    # Cada futuro agora corresponde a UMA instância
    with ProcessPoolExecutor() as executor:
        futures = {
            executor.submit(
                run_instance_with_limit,
                instance_path,
                os.path.basename(instance_path),
                NUM_REPLICATIONS,
                SEEDS,
                VNS_SCRIPT,
                OUTPUT_DIR,
                VNS_MAX_ITER,
                VNS_K_MAX,
                TIME_LIMIT,        # limite de tempo POR instância
            ): os.path.basename(instance_path)
            for instance_path in instance_files
        }

        print("\nProgresso:")

        for i, future in enumerate(as_completed(futures)):
            instance_name = futures[future]
            instance_results, total_time = future.result()  # lista de linhas + tempo total
            all_results.extend(instance_results)
            instance_times[instance_name] = total_time

            pct = (i + 1) / len(instance_files) * 100
            print(f"  -> {i+1}/{len(instance_files)} instâncias ({pct:.2f}%)", end="\r", flush=True)

    print("\n\nTodas as instâncias concluídas (ou interrompidas por tempo).")
    
    # Salvar resultados temporários
    print(f"Salvando resultados temporários em {TEMP_FILE}...")
    write_temp_file(TEMP_FILE, all_results)
    
    # Consolidar resultados
    print("Consolidando resultados por instância...")
    instance_data = read_temp_file(TEMP_FILE)
    write_summary_file(SUMMARY_FILE, instance_data, optimal_values, instance_times)
    
    print(f"Arquivo final salvo em: {SUMMARY_FILE}")
    
    # Remover arquivo temporário (opcional)
    try:
        os.remove(TEMP_FILE)
        print(f"Arquivo temporário {TEMP_FILE} removido.")
    except OSError:
        pass


if __name__ == "__main__":
    run_experiment_parallel()
