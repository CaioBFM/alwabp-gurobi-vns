import os
import subprocess
from typing import Optional


def run_single_replication(instance_path: str,
                           instance_name: str,
                           rep: int,
                           seed: int,
                           vns_script: str,
                           output_dir: str,
                           max_iter: Optional[int] = None,
                           k_max: Optional[int] = None) -> str:
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

    # Monta comando base
    base_cmd = f"python {vns_script} {output_filename} {seed}"
    if max_iter is not None:
        base_cmd += f" --max-iter {max_iter}"
    if k_max is not None:
        base_cmd += f" --kmax {k_max}"

    # Redireciona a instância via stdin
    command = f"{base_cmd} < {instance_path}"

    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
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
