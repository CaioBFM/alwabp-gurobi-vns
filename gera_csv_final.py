import os
import csv
import re
from pathlib import Path

def extract_gurobi_data(txt_file_path):
    """
    Extrai dados do arquivo de resultado do Gurobi.
    
    Retorna: (valor_objetivo, tempo_execucao, gap) ou (None, None, None) se não encontrar.
    """
    try:
        with open(txt_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        valor_objetivo = None
        tempo_execucao = None
        gap = None
        
        # Extrair Valor Objetivo
        valor_match = re.search(r'Valor objetivo:\s*([0-9]+(?:\.[0-9]+)?)', content)
        if valor_match:
            valor_objetivo = float(valor_match.group(1))
        
        # Extrair Tempo de Execução
        tempo_match = re.search(r'Tempo de execução:\s*([0-9]+(?:\.[0-9]+)?)', content)
        if tempo_match:
            tempo_execucao = float(tempo_match.group(1))
        
        # Extrair Gap
        gap_match = re.search(r'Gap:\s*([0-9]+(?:\.[0-9]+)?)%', content)
        if gap_match:
            gap = float(gap_match.group(1))
        
        return valor_objetivo, tempo_execucao, gap
    
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {txt_file_path}")
        return None, None, None
    except Exception as e:
        print(f"Erro ao processar {txt_file_path}: {e}")
        return None, None, None

def process_gurobi_results(gurobi_dir, instance_names):
    """
    Processa todos os arquivos .txt do diretório do Gurobi.
    
    Retorna um dicionário: {nome_instancia: (valor_objetivo, tempo_execucao, gap)}
    """
    gurobi_data = {}
    
    # Listar todos os arquivos .txt no diretório
    for txt_file in os.listdir(gurobi_dir):
        if txt_file.endswith('.txt') and txt_file.startswith('resultado_'):
            # Extrair nome da instância (remover "resultado_" e ".txt")
            instance_name = txt_file[10:-4]  # Remove "resultado_" (10 chars) e ".txt" (4 chars)
            
            # Verificar se esta instância está na lista que temos
            if instance_name in instance_names:
                txt_path = os.path.join(gurobi_dir, txt_file)
                valor, tempo, gap = extract_gurobi_data(txt_path)
                
                if valor is not None:
                    gurobi_data[instance_name] = {
                        'sol_gurobi': valor,
                        'time_gurobi': tempo,
                        'gap_gurobi': gap
                    }
                else:
                    print(f"AVISO: Não foi possível extrair dados de {txt_file}")
                    gurobi_data[instance_name] = {
                        'sol_gurobi': None,
                        'time_gurobi': None,
                        'gap_gurobi': None
                    }
    
    return gurobi_data

def generate_final_csv(summary_csv_path, gurobi_dir, output_csv_path):
    """
    Gera o CSV final combinando dados do VNS (heurística) e do Gurobi.
    A ordem final das colunas é:
    Instance;Best_Seed;SI;SF;SO;SOL_GUROBI;TIME_GUROBI;GAP_GUROBI_OPT;Total_Time_s;Improvement_% ;Gap_to_Optimal_%
    """
    vns_data = []
    instance_names = set()
    
    # Ler summary_results.csv gerado pela heurística
    with open(summary_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            vns_data.append(row)
            instance_names.add(row['Instance'].strip())
    
    # Processar resultados do Gurobi
    gurobi_data = process_gurobi_results(gurobi_dir, instance_names)
    
    # Definir explicitamente a ordem das colunas no CSV final
    final_fieldnames = [
        'Instance',         # Nome da instância
        'Best_Seed',        # Semente que gerou o melhor SF na heurística
        'SI',               # Solução inicial (heurística)
        'SF',               # Melhor solução final (heurística)
        'SO',               # Valor ótimo ou upper bound
        'SOL_GUROBI',       # Valor objetivo obtido pelo Gurobi
        'TIME_GUROBI',      # Tempo de execução do Gurobi
        'GAP_GUROBI_OPT',   # Gap percentual do Gurobi em relação ao ótimo
        'Total_Time_s',     # Tempo total gasto na heurística para essa instância
        'Improvement_%',    # Melhoria da heurística (SI → SF)
        'Gap_to_Optimal_%'  # Gap da melhor heurística em relação ao ótimo
    ]
    
    # Escrever o CSV final com a nova ordem de colunas
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=final_fieldnames, delimiter=';')
        writer.writeheader()
        
        for row in vns_data:
            instance_name = row['Instance'].strip()
            
            # Montar linha na ordem correta e preencher valores ausentes com 'NA'
            new_row = {
                'Instance': instance_name,
                'Best_Seed': row.get('Best_Seed', 'NA'),
                'SI': row.get('SI', 'NA'),
                'SF': row.get('SF', 'NA'),
                'SO': row.get('SO', 'NA'),
                'SOL_GUROBI': 'NA',
                'TIME_GUROBI': 'NA',
                'GAP_GUROBI_OPT': 'NA',
                'Total_Time_s': row.get('Total_Time_s', 'NA'),
                'Improvement_%': row.get('Improvement_%', 'NA'),
                'Gap_to_Optimal_%': row.get('Gap_to_Optimal_%', 'NA')
            }
            
            # Sobrescrever valores do Gurobi se existirem
            if instance_name in gurobi_data:
                gdata = gurobi_data[instance_name]
                if gdata['sol_gurobi'] is not None:
                    new_row['SOL_GUROBI'] = gdata['sol_gurobi']
                if gdata['time_gurobi'] is not None:
                    new_row['TIME_GUROBI'] = gdata['time_gurobi']
                if gdata['gap_gurobi'] is not None:
                    new_row['GAP_GUROBI_OPT'] = gdata['gap_gurobi']
            
            writer.writerow(new_row)
    
    print(f"CSV final gerado: {output_csv_path}")


def main():
    # Configurar caminhos
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Caminho para o summary_results.csv (ajuste conforme necessário)
    summary_csv_path = os.path.join(base_dir, 'METODO_HEURISTICA', 'testes_relatorio', 'summary_results.csv')
    
    # Caminho para os resultados do Gurobi
    gurobi_dir = os.path.join(base_dir, 'METODO_EXATO', 'resultados_instancia')
    
    # Caminho de saída
    output_csv_path = os.path.join(base_dir, 'csv_final.csv')
    
    # Verificar se os diretórios existem
    if not os.path.exists(summary_csv_path):
        print(f"ERRO: Arquivo não encontrado: {summary_csv_path}")
        return
    
    if not os.path.exists(gurobi_dir):
        print(f"ERRO: Diretório não encontrado: {gurobi_dir}")
        return
    
    # Gerar CSV final
    generate_final_csv(summary_csv_path, gurobi_dir, output_csv_path)
    
    # Mostrar estatísticas
    print("\n" + "="*60)
    print("RESUMO DA GERAÇÃO DO CSV FINAL")
    print("="*60)
    
    # Contar dados disponíveis
    with open(output_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        rows = list(reader)
        
        total_instances = len(rows)
        gurobi_solutions = sum(1 for row in rows if row['SOL_GUROBI'] != 'NA')
        optimal_matches = sum(
            1
            for row in rows
            if row['SOL_GUROBI'] != 'NA'
            and row['SO'] != 'NA'
            and float(row['SOL_GUROBI']) == float(row['SO'])
        )
        
        print(f"Total de instâncias: {total_instances}")
        print(f"Instâncias com solução Gurobi: {gurobi_solutions}")
        print(f"Instâncias onde Gurobi alcançou o ótimo: {optimal_matches}")
        
        # Estatísticas de tempo do Gurobi
        if gurobi_solutions > 0:
            times = []
            for row in rows:
                if row['TIME_GUROBI'] != 'NA':
                    try:
                        times.append(float(row['TIME_GUROBI']))
                    except ValueError:
                        pass
            
            if times:
                print(f"\nEstatísticas de tempo do Gurobi:")
                print(f"  Tempo médio: {sum(times)/len(times):.2f} segundos")
                print(f"  Tempo mínimo: {min(times):.2f} segundos")
                print(f"  Tempo máximo: {max(times):.2f} segundos")
                print(f"  Tempo total: {sum(times):.2f} segundos")

        # Estatísticas da heurística (VNS)
        vns_times = []
        heur_optimal_matches = 0

        for row in rows:
            sf = row.get('SF', 'NA')
            so = row.get('SO', 'NA')

            # Contar quantas vezes a heurística atingiu o ótimo (SF == SO)
            if sf != 'NA' and so != 'NA':
                try:
                    if float(sf) == float(so):
                        heur_optimal_matches += 1
                except ValueError:
                    pass

            # Coletar tempos da heurística (Total_Time_s)
            t_vns = row.get('Total_Time_s', 'NA')
            if t_vns != 'NA':
                try:
                    vns_times.append(float(t_vns))
                except ValueError:
                    pass

        print(f"\nEstatísticas da heurística (VNS):")
        print(f"  Ótimos encontrados: {heur_optimal_matches}")
        if vns_times:
            avg_vns = sum(vns_times) / len(vns_times)
            print(f"  Tempo médio: {avg_vns:.2f} segundos")
            print(f"  Tempo mínimo: {min(vns_times):.2f} segundos")
            print(f"  Tempo máximo: {max(vns_times):.2f} segundos")
            print(f"  Tempo total: {sum(vns_times):.2f} segundos")
        
        # Mostrar primeiras linhas como exemplo
        print(f"\nPrimeiras 5 linhas do arquivo gerado:")
        for i, row in enumerate(rows[:5]):
            print(f"  {i+1}. {row['Instance']}: VNS={row['SF']}, Gurobi={row['SOL_GUROBI']}, Ótimo={row['SO']}")


if __name__ == "__main__":
    main()