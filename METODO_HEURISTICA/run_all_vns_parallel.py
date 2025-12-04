import os
import subprocess
import glob
import csv
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import defaultdict

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
- consolidate_results(): consolida resultados por instância.
"""

# Configurações gerais
NUM_REPLICATIONS = 11
SEEDS = [42, 101, 202, 303, 404, 505, 606, 707, 808, 909, 1001]

INSTANCES_DIR = "testes_relatorio/instancias_teste_relatorio"
VNS_SCRIPT = "alwabp_vns.py"
OUTPUT_DIR = "testes_relatorio/vns_resultados_teste_relatorio"
INSTANCES_CSV = "instances.csv"  # Arquivo com os valores ótimos/UB

SUMMARY_FILE = os.path.join(OUTPUT_DIR, "../summary_results.csv")
TEMP_FILE = os.path.join(OUTPUT_DIR, "../temp_results.csv")

def load_optimal_values(csv_file: str) -> dict:
    """
    Carrega os valores ótimos/UB do arquivo CSV.
    
    O arquivo instances.csv tem formato:
    "name","num","tasks","workers","deps","tdeps","ninc","timef","pinc","LB","UB"
    
    Exemplo: "heskia",1 -> corresponde ao arquivo "1_hes.txt"
    """
    optimal_values = {}
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Mapeamento de nomes completos para abreviações usadas nos arquivos
            name_mapping = {
                "heskia": "hes",
                "roszieg": "ros", 
                "wee-mag": "wee",
                "tonge": "ton"
            }
            
            for row in reader:
                # Obter tipo e número da instância
                instance_type = row['name'].strip()
                instance_num = row['num'].strip()
                
                # Obter valor ótimo (UB)
                try:
                    ub_value = float(row['UB'].strip())
                except (ValueError, KeyError):
                    print(f"AVISO: Não foi possível ler UB para {instance_type}_{instance_num}")
                    continue
                
                # Mapear para o nome do arquivo
                if instance_type in name_mapping:
                    # Formato: numero_abreviacao (ex: 1_hes)
                    instance_key = f"{instance_num}_{name_mapping[instance_type]}"
                    optimal_values[instance_key] = ub_value
                else:
                    # Se não estiver no mapeamento, usar os primeiros 3 caracteres
                    instance_key = f"{instance_num}_{instance_type[:3]}"
                    optimal_values[instance_key] = ub_value
            
            print(f"Carregados {len(optimal_values)} valores ótimos de {csv_file}")
            
            # Mostrar alguns exemplos para verificação
            print("\nExemplos de valores ótimos carregados:")
            for i, (key, val) in enumerate(list(optimal_values.items())[:10]):
                print(f"  {key}: {val}")
            if len(optimal_values) > 10:
                print(f"  ... e mais {len(optimal_values) - 10} entradas")
            
    except FileNotFoundError:
        print(f"AVISO: Arquivo {csv_file} não encontrado.")
    except Exception as e:
        print(f"ERRO ao carregar {csv_file}: {e}")
        import traceback
        traceback.print_exc()
    
    return optimal_values

def run_single_replication(instance_path: str, instance_name: str, rep: int, seed: int) -> str:
    """
    Executa 1 replicação do VNS para uma instância.

    Retorna:
        "instancia;rep;seed;SI;SF;tempo"
    """

    # Garante pasta de saída
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


def consolidate_results(temp_file: str, summary_file: str, optimal_values: dict):
    """
    Consolida resultados por instância, selecionando a melhor seed.
    """
    # Ler o arquivo temporário
    instance_data = defaultdict(list)
    
    try:
        with open(temp_file, 'r') as f:
            next(f)  # Pular cabeçalho
            for line in f:
                parts = line.strip().split(';')
                if len(parts) >= 6:
                    instance_name = parts[0]
                    instance_data[instance_name].append(parts)
    except FileNotFoundError:
        print(f"ERRO: Arquivo temporário {temp_file} não encontrado.")
        return
    
    # Escrever arquivo consolidado
    with open(summary_file, "w") as f:
        f.write("Instance;Best_Seed;SI;SF;SO;Total_Time_s;Improvement_%;Gap_to_Optimal_%\n")
        
        for instance_name in sorted(instance_data.keys()):
            rows = instance_data[instance_name]
            
            # Filtrar apenas linhas com valores numéricos válidos
            valid_rows = []
            for row in rows:
                if len(row) >= 6 and row[3] != 'ERROR' and row[4] != 'ERROR' and row[5] != 'ERROR':
                    try:
                        si = float(row[3])
                        sf = float(row[4])
                        time_val = float(row[5])
                        seed = int(row[2])
                        valid_rows.append((seed, si, sf, time_val))
                    except ValueError:
                        continue
            
            if not valid_rows:
                f.write(f"{instance_name};NA;NA;NA;NA;NA;NA;NA\n")
                continue
            
            # Calcular tempo total (soma de todas as seeds)
            total_time = sum(row[3] for row in valid_rows)
            
            # Encontrar a melhor seed (menor SF)
            best_row = min(valid_rows, key=lambda x: x[2])  # Índice 2 = SF
            best_seed, best_si, best_sf, _ = best_row
            
            # Obter valor ótimo (SO)
            instance_key = instance_name
            if instance_name.endswith('.txt'):
                instance_key = instance_name[:-4]
            
            optimal_value = optimal_values.get(instance_key)
            
            # Calcular melhoria percentual
            if best_si > 0:
                improvement_pct = ((best_si - best_sf) / best_si) * 100
            else:
                improvement_pct = 0.0
            
            # Calcular gap em relação ao ótimo
            if optimal_value and optimal_value > 0:
                gap_to_optimal_pct = ((best_sf - optimal_value) / best_sf) * 100
                f.write(f"{instance_name};{best_seed};{best_si};{best_sf};{optimal_value};{total_time:.2f};{improvement_pct:.2f};{gap_to_optimal_pct:.2f}\n")
            else:
                f.write(f"{instance_name};{best_seed};{best_si};{best_sf};NA;{total_time:.2f};{improvement_pct:.2f};NA\n")

def run_experiment_parallel():
    """
    Executa todas as instâncias em paralelo com múltiplas replicações.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Carregar valores ótimos
    print(f"Carregando valores ótimos de {INSTANCES_CSV}...")
    optimal_values = load_optimal_values(INSTANCES_CSV)
    
    # Lista de instâncias
    instance_files = sorted(glob.glob(os.path.join(INSTANCES_DIR, "*")))

    print(f"Iniciando experimentos: {len(instance_files)} instâncias × {NUM_REPLICATIONS} replicações")
    print(f"Arquivo temporário: {TEMP_FILE}")
    print(f"Arquivo final: {SUMMARY_FILE}")

    tasks = []

    # Criar todas as tarefas
    for instance_path in instance_files:
        instance_name = os.path.basename(instance_path)
        for rep in range(NUM_REPLICATIONS):
            seed = SEEDS[rep]
            tasks.append((instance_path, instance_name, rep, seed))

    # Execução paralela - primeiro grava em arquivo temporário
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(run_single_replication, *task) for task in tasks]

        # CSV temporário
        with open(TEMP_FILE, "w") as f:
            f.write("Instance;Replication;Seed;SI;SF;Time_s\n")

        print("\nProgresso:")

        # Processa conforme as tarefas concluem
        for i, future in enumerate(as_completed(futures)):
            result_line = future.result()

            with open(TEMP_FILE, "a") as f:
                f.write(result_line + "\n")

            # Atualiza percentual concluído
            pct = (i + 1) / len(tasks) * 100
            print(f"  -> {i+1}/{len(tasks)} ({pct:.2f}%)", end="\r", flush=True)

    print("\n\nTodas as replicações concluídas.")
    
    # Consolidar resultados
    print("Consolidando resultados por instância...")
    consolidate_results(TEMP_FILE, SUMMARY_FILE, optimal_values)
    
    print(f"Arquivo final salvo em: {SUMMARY_FILE}")
    
    # Remover arquivo temporário
    try:
        os.remove(TEMP_FILE)
        print(f"Arquivo temporário {TEMP_FILE} removido.")
    except OSError:
        pass


if __name__ == "__main__":
    run_experiment_parallel()