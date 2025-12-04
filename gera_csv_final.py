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
    Gera o CSV final combinando dados do VNS e do Gurobi.
    """
    # Ler o summary_results.csv
    vns_data = []
    instance_names = set()
    
    with open(summary_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        fieldnames = reader.fieldnames
        
        # Coletar dados e nomes das instâncias
        for row in reader:
            vns_data.append(row)
            instance_name = row['Instance'].strip()
            instance_names.add(instance_name)
    
    # Processar resultados do Gurobi
    print(f"Processando resultados do Gurobi de {gurobi_dir}...")
    gurobi_data = process_gurobi_results(gurobi_dir, instance_names)
    print(f"Encontrados dados do Gurobi para {len(gurobi_data)} instâncias")
    
    # Preparar campo para CSV final
    new_fieldnames = list(fieldnames)
    # Inserir novas colunas após a coluna SO (Solução Ótima)
    # Encontrar índice da coluna SO
    if 'SO' in new_fieldnames:
        so_index = new_fieldnames.index('SO')
        # Inserir após SO
        new_fieldnames.insert(so_index + 1, 'SOL_GUROBI')
        new_fieldnames.insert(so_index + 2, 'TIME_GUROBI')
        new_fieldnames.insert(so_index + 3, 'GAP_GUROBI_OPT')
    else:
        # Se não encontrar SO, adicionar no final
        new_fieldnames.extend(['SOL_GUROBI', 'TIME_GUROBI', 'GAP_GUROBI_OPT'])
    
    # Escrever CSV final
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames, delimiter=';')
        writer.writeheader()
        
        for row in vns_data:
            instance_name = row['Instance'].strip()
            new_row = row.copy()
            
            # Adicionar dados do Gurobi se disponíveis
            if instance_name in gurobi_data:
                gurobi_info = gurobi_data[instance_name]
                new_row['SOL_GUROBI'] = gurobi_info['sol_gurobi'] if gurobi_info['sol_gurobi'] is not None else 'NA'
                new_row['TIME_GUROBI'] = gurobi_info['time_gurobi'] if gurobi_info['time_gurobi'] is not None else 'NA'
                new_row['GAP_GUROBI_OPT'] = gurobi_info['gap_gurobi'] if gurobi_info['gap_gurobi'] is not None else 'NA'
            else:
                new_row['SOL_GUROBI'] = 'NA'
                new_row['TIME_GUROBI'] = 'NA'
                new_row['GAP_GUROBI_OPT'] = 'NA'
            
            writer.writerow(new_row)
    
    print(f"CSV final gerado: {output_csv_path}")
    print(f"Total de instâncias processadas: {len(vns_data)}")

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
        optimal_matches = sum(1 for row in rows if row['SOL_GUROBI'] != 'NA' and row['SO'] != 'NA' 
                            and float(row['SOL_GUROBI']) == float(row['SO']))
        
        print(f"Total de instâncias: {total_instances}")
        print(f"Instâncias com solução Gurobi: {gurobi_solutions}")
        print(f"Instâncias onde Gurobi alcançou o ótimo: {optimal_matches}")
        
        if gurobi_solutions > 0:
            # Calcular estatísticas de tempo
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
        
        # Mostrar primeiras linhas como exemplo
        print(f"\nPrimeiras 5 linhas do arquivo gerado:")
        for i, row in enumerate(rows[:5]):
            print(f"  {i+1}. {row['Instance']}: VNS={row['SF']}, Gurobi={row['SOL_GUROBI']}, Ótimo={row['SO']}")

if __name__ == "__main__":
    main()