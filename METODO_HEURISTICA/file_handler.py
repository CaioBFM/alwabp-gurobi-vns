import os
import csv
import glob
from collections import defaultdict


def load_instance_files(instances_dir: str):
    """
    Carrega lista de arquivos de instância.
    """
    if not os.path.exists(instances_dir):
        raise FileNotFoundError(f"Diretório não encontrado: {instances_dir}")
    
    instance_files = sorted(glob.glob(os.path.join(instances_dir, "*")))
    return instance_files


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
            
    except FileNotFoundError:
        print(f"AVISO: Arquivo {csv_file} não encontrado.")
    except Exception as e:
        print(f"ERRO ao carregar {csv_file}: {e}")
        import traceback
        traceback.print_exc()
    
    return optimal_values


def write_temp_file(temp_file: str, results: list):
    """
    Escreve arquivo temporário com resultados brutos.
    """
    os.makedirs(os.path.dirname(temp_file), exist_ok=True)
    
    with open(temp_file, "w") as f:
        f.write("Instance;Replication;Seed;SI;SF;Time_s\n")
        for result_line in results:
            f.write(result_line + "\n")


def read_temp_file(temp_file: str):
    """
    Lê arquivo temporário e retorna dados agrupados por instância.
    """
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
    
    return instance_data


def write_summary_file(summary_file: str, instance_data: dict, optimal_values: dict):
    """
    Escreve arquivo consolidado (summary) com melhores resultados por instância.
    """
    os.makedirs(os.path.dirname(summary_file), exist_ok=True)
    
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