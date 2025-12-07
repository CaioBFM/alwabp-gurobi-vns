# Trabalho Prático Final – GCC118 / PCC540

**ALWABP – Método Exato (Gurobi) e Metaheurística VNS**

Este repositório contém a implementação completa do trabalho prático final da disciplina, abordando o **Problema de Balanceamento de Linha de Montagem com Designação de Trabalhadores (ALWABP)** por meio de:

- **Método exato**, via formulação em MILP e resolução com **Gurobi**;
- **Método heurístico**, baseado na metaheurística **Variable Neighborhood Search (VNS)**;
- **Pipeline de experimentos**, consolidando resultados de ambas as abordagens em um **único CSV final** para análise.

> Este README é focado na **documentação do código** (estrutura, execução, arquivos gerados).  
> Toda a parte teórica mais detalhada (formulação MILP, análise completa, bibliografia, etc.) está no `RelatorioTrabalhoPM.pdf`.

---

## 1. Visão Geral do Projeto

O projeto está dividido em três blocos principais:

1. **Método Exato (`METODO_EXATO/`)**

   - Lê as instâncias do problema ALWABP.
   - Resolve cada instância com o **Gurobi** (modelo MILP).
   - Gera arquivos `.txt` com o resumo dos resultados por instância.

2. **Método Heurístico (`METODO_HEURISTICA/`)**

   - Implementa a metaheurística **VNS** para o ALWABP.
   - Executa múltiplas replicações por instância, com seeds diferentes e limite de tempo por instância.
   - Consolida os resultados em um arquivo `summary_results.csv`.

3. **Geração do CSV Final (raiz do projeto)**
   - Script `gera_csv_final.py` que:
     - Lê os resultados da heurística (`summary_results.csv`).
     - Lê os resultados do Gurobi (`resultado_*.txt`).
     - Gera o arquivo **`csv_final.csv`** combinando, para cada instância, os dados do exato e da heurística.

---

## 2. Estrutura do Repositório

A estrutura resumida do projeto é:

```bash
alwabp-gurobi-vns/
│
├── METODO_EXATO/
│   ├── instancias_teste_relatorio/     # Instâncias utilizadas com o Gurobi
│   ├── resultados_instancia/           # Saída de resultados do Gurobi
│   └── src/
│       ├── alwabp_gurobi.py            # Modelo MILP e chamada do solver
│       ├── file_handler.py             # Funções auxiliares de leitura/gravação
│       └── run_gurobi.py               # Script principal para rodar todas as instâncias
│
├── METODO_HEURISTICA/
│   ├── src/
│   │   ├── alwabp_vns.py               # Implementação da VNS para o ALWABP
│   │   ├── config.py                   # Parâmetros globais da heurística (seeds, limites, etc.)
│   │   ├── file_handler.py             # Funções auxiliares (operações de arquivos: instâncias, summary, etc.)
│   │   ├── gerar_csv_vns.py            # (opcional) Geração/ajuste de CSVs intermediários
│   │   ├── run_all_vns_parallel.py     # Roda VNS em todas as instâncias (execução paralela por instância)
│   │   └── run_vns.py                  # Wrapper para rodar uma instância/replicação (subprocess)
│   │
│   ├── testes_relatorio/
│   │   ├── instancias_teste_relatorio/ # Instâncias usadas pela heurística
│   │   ├── vns_resultados_teste_relatorio/  # Arquivos de solução por instância/replicação
│   │   └── summary_results.csv         # Consolidação dos resultados da VNS por instância
│   │
│   ├── instances.csv                   # Arquivo com valores ótimos/upper bounds por instância
│   └── resultado_vns.csv               # (opcional) Outras saídas consolidadas da heurística
│
├── gera_csv_final.py                   # Combina VNS + Gurobi em um único csv_final.csv
├── csv_final.csv                       # Arquivo final para análise comparativa (heurística x exato)
└── README.md
```

---

## 3. Dependências e Ambiente

### 3.1. Requisitos básicos

- **Python 3.10+**
- Bibliotecas Python padrão (já utilizadas no código):  
  `os`, `csv`, `time`, `concurrent.futures`, `subprocess`, `re`, etc.

### 3.2. Solver Gurobi

Para executar o método exato:

- Gurobi instalado e configurado no sistema;
- Licença acadêmica ou válida ativa;
- Biblioteca `gurobipy` instalada no ambiente Python.

---

## 4. Método Heurístico – VNS (METODO_HEURISTICA)

### 4.1. Arquivo de configuração (`config.py`)

Os principais parâmetros da heurística são definidos em `METODO_HEURISTICA/src/config.py`, por exemplo:

<!-- - `NUM_REPLICATIONS`
  Número máximo de replicações por instância (execuções independentes). -->

- `SEEDS_PEQUENAS`  
  Lista de sementes para instâncias pequenas. A instância é rodada várias vezes, uma seed por replicação.

- `SEEDS_GRANDES`  
  Lista de sementes para instâncias grandes. A instância é rodada várias vezes, uma seed por replicação.

- `TIME_LIMIT`  
  **Limite de tempo total por instância** (em segundos).

  - O tempo é medido desde o início da primeira replicação dessa instância.
  - Antes de iniciar cada nova replicação, é verificado se o tempo decorrido já ultrapassou o limite.
  - Se o limite é atingido, a instância é interrompida (sem novas replicações).

- `VNS_MAX_ITER`  
  Número máximo de iterações do laço principal do VNS.

- `VNS_K_MAX`  
  Número máximo de estruturas de vizinhança exploradas no VNS.

Esses valores podem ser ajustados diretamente no arquivo para facilitar experimentos diferentes.

### 4.2. Execução da heurística em todas as instâncias

A partir da pasta `METODO_HEURISTICA/src`:

```bash
cd METODO_HEURISTICA/src
python run_all_vns_parallel.py
```

Esse script:

1. Lê as instâncias em `../testes_relatorio/instancias_teste_relatorio/`;
2. Para cada instância:
   - Escolhe qual seed usar (grande ou pequena) e guarda valores em `NUM_REPLICATIONS` e `SEEDS`;
   - Executa até `NUM_REPLICATIONS` replicações, cada uma com uma seed da lista;
   - Respeita o `TIME_LIMIT` total daquela instância;
   - Salva as soluções detalhadas (por replicação) em  
     `../testes_relatorio/vns_resultados_teste_relatorio/`;
3. Gera e grava o arquivo consolidado `../testes_relatorio/summary_results.csv`, com **uma linha por instância**, contendo:
   - `Instance`
   - `Best_Seed` (seed que produziu o melhor SF)
   - `SI` (solução inicial da heurística)
   - `SF` (melhor solução final)
   - `SO` (ótimo/upper bound da instância, lido de `instances.csv`)
   - `Total_Time_s` (tempo total da heurística para aquela instância)
   - `Improvement_%` = \(100 \times (SI - SF) / SI\)
   - `Gap_to_Optimal_%` = \(100 \times (SF - SO) / SO\)

> Observação importante:  
> Embora as instâncias sejam executadas em paralelo (cada uma em um processo diferente),  
> o tempo armazenado para cada instância (`Total_Time_s`) é sempre **medido por instância**, somando apenas suas replicações.

---

## 5. Método Exato – Gurobi (METODO_EXATO)

### 5.1. Instâncias e saídas

Na pasta `METODO_EXATO`:

- `instancias_teste_relatorio/`  
  Contém os arquivos de instância do ALWABP que serão resolvidos pelo Gurobi.

- `resultados_instancia/`  
  Recebe os arquivos de saída do solver no formato:  
  `resultado_<nome_da_instancia>.txt`

Cada arquivo `resultado_*.txt` contém, entre outras informações:

- Valor objetivo encontrado (`Valor objetivo: ...`);
- Tempo de execução (`Tempo de execução: ...`);
- Gap reportado pelo solver (`Gap: ... %`), quando aplicável.

### 5.2. Execução do solver para todas as instâncias

A partir de `METODO_EXATO/src`:

```bash
cd METODO_EXATO/src
python run_gurobi.py
```

Esse script:

1. Lê todas as instâncias em `../instancias_teste_relatorio/`;
2. Para cada instância:
   - Monta e resolve o modelo MILP no Gurobi;
   - Respeita o limite de tempo configurado no código (por instância);
   - Salva o arquivo `resultado_<instancia>.txt` em `../resultados_instancia/`.

---

## 6. Geração do CSV Final (`csv_final.csv`)

Após rodar:

- a heurística (VNS) e gerar `METODO_HEURISTICA/testes_relatorio/summary_results.csv`,
- o exato (Gurobi) e gerar `METODO_EXATO/resultados_instancia/resultado_*.txt`,

podemos consolidar tudo em um **único arquivo CSV final** na raiz do projeto.

### 6.1. Script `gera_csv_final.py`

Na raiz do projeto (`PM_TRABALHO/`):

```bash
python gera_csv_final.py
```

Esse script:

1. Lê:
   - `METODO_HEURISTICA/testes_relatorio/summary_results.csv` (resultados da VNS);
   - `METODO_EXATO/resultados_instancia/resultado_*.txt` (resultados do Gurobi).
2. Extrai dos arquivos do Gurobi:
   - `sol_gurobi` → valor objetivo encontrado;
   - `time_gurobi` → tempo de execução;
   - `gap_gurobi` → % de gap reportado.
3. Gera o arquivo **`csv_final.csv`** na raiz, com colunas na seguinte ordem:

```text
Instance;
Best_Seed;
SI;
SF;
SO;
SOL_GUROBI;
TIME_GUROBI;
GAP_GUROBI_OPT;
Total_Time_s;
Improvement_% ;
Gap_to_Optimal_%
```

onde:

- **Instance**: nome da instância (ex.: `11_hes`, `52_wee`);
- **Best_Seed**: semente da melhor replicação da VNS;
- **SI**: solução inicial da heurística;
- **SF**: melhor solução final da heurística;
- **SO**: solução ótima/UB de referência;
- **SOL_GUROBI**: solução obtida pelo Gurobi;
- **TIME_GUROBI**: tempo do Gurobi para aquela instância;
- **GAP_GUROBI_OPT**: gap percentual usado para o solver (quando extraído);
- **Total_Time_s**: tempo total da heurística VNS (por instância);
- **Improvement\_%**: melhoria percentual da heurística em relação à solução inicial;
- **Gap_to_Optimal\_%**: gap percentual da solução heurística em relação ao ótimo/UB.

Ao final, o script ainda imprime no terminal algumas estatísticas:

- Quantas instâncias têm solução do Gurobi;
- Em quantas ele atingiu exatamente o valor ótimo (`SOL_GUROBI == SO`);
- Estatísticas de tempo do solver e da heurística (média, mínimo, máximo, total).

---

## 7. Observações Finais

- A parametrização da heurística (número de iterações, vizinhanças, seeds e limite de tempo) está centralizada em `METODO_HEURISTICA/src/config.py`, facilitando a realização de diferentes cenários de teste.
- A comparação entre heurística e método exato é feita **por instância**, em termos de:
  - Valor da melhor solução (SF x SO x SOL_GUROBI);
  - Melhor seed;
  - Tempo computacional de cada abordagem;
  - Melhorias e gaps percentuais.

Esse README serve como guia prático para compreender a organização do projeto e reproduzir todos os experimentos necessários para o relatório e análise de resultados.

---

## 8. Autores

- Caio Bueno Finocchio Martins – [@caiobfm](https://github.com/caiobfm)
- Tobias Maugus Bueno Cougo – [@tobiasmaugus](https://github.com/tobiasmaugus)
