import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

from config import (
    SEEDS_PEQ,
    SEEDS_GRANDES,
    TIME_LIMIT,
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


def run_instance_with_limit(
    instance_path: str,
    instance_name: str,
    num_replications: int,
    seeds: list,
    vns_script: str,
    output_dir: str,
    max_iter: int,
    k_max: int,
    instance_time_limit: float | None,
):
    """
    Roda TODAS as replicações de UMA instância, em série, respeitando
    um limite de tempo total por instância.
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


def get_seed_pool(instance_name: str) -> list[int]:
    """
    Retorna o pool de seeds apropriado para a instância.
    TON / WEE usam SEEDS_GRANDES, o resto usa SEEDS_PEQ.
    """
    name = instance_name.lower()

    if "_ton" in name or "_wee" in name:
        return SEEDS_GRANDES

    return SEEDS_PEQ


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
    total_instances = len(instance_files)

    print(f"Iniciando experimentos: {total_instances} instâncias.")
    print(f"Limite de tempo por instância: {TIME_LIMIT if TIME_LIMIT is not None else 'sem limite'} s")
    print(f"Arquivo temporário: {TEMP_FILE}")
    print(f"Arquivo final: {SUMMARY_FILE}")

    all_results = []
    instance_times: dict[str, float] = {}

    # Cada futuro agora corresponde a UMA instância
    with ProcessPoolExecutor() as executor:
        futures = {}

        for instance_path in instance_files:
            instance_name = os.path.basename(instance_path)

            # escolhe o pool de seeds conforme a família da instância
            seed_pool = get_seed_pool(instance_name)

            future = executor.submit(
                run_instance_with_limit,
                instance_path,
                instance_name,
                len(seed_pool),   # número de replicações = qtd de seeds
                seed_pool,        # lista de seeds daquela instância
                VNS_SCRIPT,
                OUTPUT_DIR,
                VNS_MAX_ITER,
                VNS_K_MAX,
                TIME_LIMIT,       # limite de tempo POR instância
            )

            futures[future] = instance_name

        print("\nProgresso:")

        # i vai de 1 até total_instances
        for i, future in enumerate(as_completed(futures), start=1):
            instance_name = futures[future]
            instance_results, total_time = future.result()  # lista de linhas + tempo total
            all_results.extend(instance_results)
            instance_times[instance_name] = total_time

            pct = (i / total_instances) * 100
            print(
                f"  -> {i}/{total_instances} instâncias concluídas ({pct:.2f}%)",
                end="\r",
                flush=True
            )

    print(f"\n\nTodas as {total_instances} instâncias concluídas (ou interrompidas por tempo).")
    
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
