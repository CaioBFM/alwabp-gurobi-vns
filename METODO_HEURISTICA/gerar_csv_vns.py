import os
import pandas as pd

"""
Consolida resultados do VNS:
- Lê arquivos <num>_<inst>_repX_seedY.txt
- Extrai valores das seeds
- Cruza com instances.csv (LB)
- Gera resultado_vns.csv com melhor valor e erro
"""

# Caminhos
PASTA_VNS = "testes_relatorio/vns_resultados_teste_relatorio"
ARQUIVO_INSTANCIAS = "instances.csv"
SAIDA_CSV = "resultado_vns.csv"

# Mapeamento simplificado → nome completo
MAP_INSTANCIAS = {
    "hes": "heskia",
    "ros": "roszieg",
    "wee": "wee-mag",
    "ton": "tonge"
}

# Seeds esperadas
SEEDS = [42, 101, 202, 303, 404, 505, 606, 707, 808, 909, 1001, 1707, 1905, 1936, 1969, 1618]

def main():
    # Lê o CSV de instâncias
    df_inst = pd.read_csv(ARQUIVO_INSTANCIAS)
    df_inst = df_inst.rename(columns=str.strip)

    resultados = {}

    for arquivo in os.listdir(PASTA_VNS):
        if not arquivo.endswith(".txt"):
            continue

        # Exemplo: 1_hes_rep1_seed42.txt
        nome = os.path.splitext(arquivo)[0]
        partes = nome.split("_")

        num = int(partes[0])  
        inst_simplificada = partes[1]
        seed = int(partes[-1].replace("seed", ""))

        if inst_simplificada not in MAP_INSTANCIAS:
            print(f"⚠️ Instância desconhecida: {inst_simplificada}")
            continue

        inst_completa = MAP_INSTANCIAS[inst_simplificada]

        caminho = os.path.join(PASTA_VNS, arquivo)
        with open(caminho, "r") as f:
            primeira_linha = f.readline().strip()

        try:
            valor = float(primeira_linha)
        except ValueError:
            print(f"⚠️ Erro ao converter valor em {arquivo}: {primeira_linha}")
            continue

        chave = (inst_completa, num)
        if chave not in resultados:
            resultados[chave] = {}

        resultados[chave][f"seed_{seed}"] = valor

    linhas = []
    for (inst_completa, num), valores in resultados.items():
        linha = {"instancia": inst_completa, "num": num}

        valor_otimo = df_inst.loc[
            (df_inst["name"] == inst_completa) & (df_inst["num"] == num), "LB"
        ].values
        valor_otimo = float(valor_otimo[0]) if len(valor_otimo) > 0 else None
        linha["valor_otimo"] = valor_otimo

        for s in SEEDS:
            linha[f"seed_{s}"] = valores.get(f"seed_{s}", None)

        seed_vals = [v for v in [linha[f"seed_{s}"] for s in SEEDS] if v is not None]
        melhor_valor = min(seed_vals) if seed_vals else None
        linha["melhor_valor"] = melhor_valor

        if melhor_valor is not None and valor_otimo is not None:
            linha["erro"] = melhor_valor - valor_otimo
        else:
            linha["erro"] = None

        linhas.append(linha)

    df_saida = pd.DataFrame(linhas)
    df_saida = df_saida[
        ["instancia", "num", "valor_otimo"]
        + [f"seed_{s}" for s in SEEDS]
        + ["melhor_valor", "erro"]
    ]

    df_saida.to_csv(SAIDA_CSV, index=False)
    print(f"✅ Arquivo gerado com sucesso: {SAIDA_CSV}")

if __name__ == "__main__":
    main()
