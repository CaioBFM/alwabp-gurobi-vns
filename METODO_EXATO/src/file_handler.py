import os
from pathlib import Path
from alwabp_gurobi import ALWABPInstance, solve_alwabp_gurobi

# ============================================================
# Processa todas as instâncias
# ============================================================
def processar_instancias(input_dir="../instancias_teste_relatorio", output_dir="../resultados_instancia"):
    # Criar pastas se não existirem
    Path(output_dir).mkdir(exist_ok=True)
    
    if not os.path.exists(input_dir):
        print(f"Erro: A pasta '{input_dir}' não existe!")
        print(f"Crie a pasta '{input_dir}' e coloque os arquivos de instância nela.")
        return
    
    # Listar arquivos na pasta de entrada
    arquivos = []
    for arquivo in os.listdir(input_dir):
        arquivos.append(arquivo)
    
    if not arquivos:
        print(f"Nenhum arquivo .txt encontrado na pasta '{input_dir}'")
        return
    
    print(f"Encontrados {len(arquivos)} arquivos para processar:")
    for arquivo in arquivos:
        print(f"  - {arquivo}")
    
    # Processar cada arquivo
    total_processados = 0
    total_erros = 0
    
    for arquivo in arquivos:
        input_path = os.path.join(input_dir, arquivo)
        file_name = Path(arquivo).stem
        output_file = os.path.join(output_dir, f"resultado_{file_name}.txt")
        
        print(f"\n{'='*60}")
        print(f"Processando: {arquivo}")
        print(f"{'='*60}")
        
        try:
            # Carregar instância
            print(f"Carregando instância...")
            inst = ALWABPInstance.from_file(input_path)
            print(f"  Instância carregada: {inst.num_tasks} tarefas, {inst.num_workers} trabalhadores")
            
            # Resolver com limite de tempo de 20 minutos (1200 segundos)
            print(f"Resolvendo modelo (limite: 20 minutos)...")
            resultados = solve_alwabp_gurobi(inst, time_limit=1200)
            
            # Salvar resultados em arquivo
            with open(output_file, 'w', encoding='utf-8') as f:
                for linha in resultados:
                    f.write(linha + '\n')
            
            print(f"Resultado salvo em: {output_file}")
            
            # Mostrar resumo no console
            print("\nRESUMO DA SOLUÇÃO:")
            for linha in resultados:
                if "Tempo de ciclo" in linha or "Status:" in linha or "Valor objetivo" in linha or "Gap:" in linha:
                    print(f"  {linha}")
            
            total_processados += 1
            
        except FileNotFoundError:
            print(f"Erro: Arquivo '{input_path}' não encontrado.")
            total_erros += 1
        except Exception as e:
            print(f"Erro ao processar '{arquivo}': {e}")
            # Salvar erro em arquivo também
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"ERRO AO PROCESSAR INSTÂNCIA: {arquivo}\n")
                f.write(f"Erro: {str(e)}\n")
            total_erros += 1
    
    # Resumo final
    print(f"\n{'='*60}")
    print("PROCESSAMENTO CONCLUÍDO")
    print(f"{'='*60}")
    print(f"Total de arquivos processados: {total_processados}")
    print(f"Total de erros: {total_erros}")
    print(f"Resultados salvos na pasta: '{output_dir}'")
    print(f"\nArquivos de resultado:")
    for arquivo in os.listdir(output_dir):
        print(f"  - {arquivo}")