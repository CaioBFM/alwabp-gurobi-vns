import os
import subprocess


def run_single_replication(instance_path: str, instance_name: str, rep: int, seed: int, 
                           vns_script: str, output_dir: str) -> str:
    """
    Executa 1 replicação do VNS para uma instância.

    Retorna:
        "instancia;rep;seed;SI;SF;tempo"
    """
    # Garante pasta de saída
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Arquivo onde a solução completa será salva
    output_filename = os.path.join(
        output_dir, f"{instance_name}_rep{rep+1}_seed{seed}.txt"
    )

    # Comando de execução do VNS
    command = f"python {vns_script} {output_filename} {seed} < {instance_path}"

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


def prepare_tasks(instance_files: list, num_replications: int, seeds: list, 
                  vns_script: str, output_dir: str):
    """
    Prepara todas as tarefas para execução paralela.
    """
    tasks = []
    for instance_path in instance_files:
        instance_name = os.path.basename(instance_path)
        for rep in range(num_replications):
            seed = seeds[rep]
            tasks.append((instance_path, instance_name, rep, seed, vns_script, output_dir))
    return tasks