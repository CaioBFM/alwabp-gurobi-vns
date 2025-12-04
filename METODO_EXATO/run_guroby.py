from file_handler import processar_instancias

if __name__ == "__main__":
    print("PROCESSADOR DE INSTÂNCIAS ALWABP")
    print("=" * 60)
    print("Este script irá:")
    print("1. Ler todos os arquivos .txt da pasta 'instancias_teste_relatorio'")
    print("2. Resolver cada instância com Gurobi (limite: 20 minutos)")
    print("3. Salvar os resultados na pasta 'resultados_instancia'")
    print("=" * 60)
    
    # Processar todas as instâncias automaticamente
    processar_instancias()
    
    input("\nPressione Enter para sair...")