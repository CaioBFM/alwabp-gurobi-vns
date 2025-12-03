# Trabalho Prático Final - GCC118/PCC540: ALWABP com VNS

## Sumário

- [1. Introdução](#1-introdução)
- [2. Formulação MILP](#2-formulação-do-problema-como-programa-linear-inteiro-misto-milp)
- [3. Algoritmo Proposto: VNS](#3-algoritmo-proposto-variable-neighborhood-search-vns)
- [4. Resultados Obtidos](#4-resultados-obtidos-com-análise)
- [5. Como Executar o Programa](#5-como-executar-o-programa)
- [6. Conclusão](#6-conclusão)
- [7. Bibliografia](#7-bibliografia)

---

## 1. Introdução

O presente trabalho visa a resolução do **Problema de Balanceamento de Linhas de Produção e Designação de Trabalhadores (ALWABP)**, um problema de otimização combinatória que busca minimizar o tempo de ciclo de uma linha de montagem ao mesmo tempo em que considera a alocação de trabalhadores com diferentes tempos de execução e restrições de incapacidade. Para tal, foi utilizada a metaheurística **Variable Neighborhood Search (VNS)**.

O ALWABP, introduzido por Miralles et al. (2007), é um problema complexo que generaliza o problema clássico de balanceamento de linha de montagem ao incorporar a heterogeneidade dos trabalhadores. A solução requer a definição de:

1.  Uma atribuição de tarefas a estações.
2.  Uma atribuição de trabalhadores a estações.

O objetivo é minimizar o tempo de ciclo (C_max), que é o tempo máximo de processamento entre todas as estações.

## 2. Formulação do Problema como Programa Linear Inteiro Misto (MILP)

A formulação a seguir representa o ALWABP como um modelo de Programação Linear Inteira Mista (MILP), conforme solicitado.

# Formulação do Problema ALWABP como Programa Linear Inteiro Misto (MILP)

O problema ALWABP (Assembly Line Worker Assignment and Balancing Problem) consiste em designar tarefas a estações de trabalho e alocar trabalhadores a essas estações, minimizando o tempo de ciclo da linha de montagem, sujeito a restrições de precedência, capacidade do trabalhador e tempo de ciclo.

## Conjuntos e Parâmetros

| Símbolo         | Descrição                                                                                         |
| :-------------- | :------------------------------------------------------------------------------------------------ |
| N = {1, ..., n} | Conjunto de tarefas.                                                                              |
| W = {1, ..., k} | Conjunto de trabalhadores.                                                                        |
| S = {1, ..., m} | Conjunto de estações de trabalho. Assume-se m=k (uma estação por trabalhador).                    |
| P               | Conjunto de pares de precedência (i, j) em N x N, onde i deve preceder j.                         |
| t_wi            | Tempo de execução da tarefa i por trabalhador w.                                                  |
| I_w             | Conjunto de tarefas que o trabalhador w é incapaz de executar (t_wi = infinito \forall i em I_w). |
| M               | Uma constante grande (Big M).                                                                     |

## Variáveis de Decisão

| Símbolo | Tipo          | Descrição                                                                                                                              |
| :------ | :------------ | :------------------------------------------------------------------------------------------------------------------------------------- |
| C_max   | Real positivo | Tempo de ciclo da linha de produção (a ser minimizado).                                                                                |
| y_si    | Binária       | 1 se a tarefa i é designada à estação s. 0 caso contrário.                                                                             |
| z_ws    | Binária       | 1 se o trabalhador w é alocado à estação s. 0 caso contrário.                                                                          |
| u_wis   | Binária       | Variável auxiliar para linearizar o produto y_si \* z_ws. 1 se a tarefa i é atribuída à estação s e o trabalhador w está na estação s. |

## Função Objetivo

Minimizar o tempo de ciclo da linha de produção:

```math
min C_{max}
```

## Restrições

### 1. Designação de Tarefas e Trabalhadores

Cada tarefa deve ser designada a exatamente uma estação:

```math
∑_{s ∈ S} y_{si} = 1   \forall i ∈ N   (R1)
```

Cada trabalhador deve ser alocado a exatamente uma estação:

```math
∑_{s ∈ S} z_{ws} = 1   \forall w ∈ W   (R2)
```

Cada estação deve ter exatamente um trabalhador alocado:

```math
∑_{w ∈ W} z_{ws} = 1   \forall s ∈ S   (R3)
```

### 2. Linearização e Restrição de Incapacidade

Linearização do produto y_si \* z_ws através da variável u_wis:

```math
u_{wis} ≤ y_{si}   \forall i ∈ N, w ∈ W, s ∈ S   (R4.1)
u_{wis} ≤ z_{ws}   \forall i ∈ N, w ∈ W, s ∈ S   (R4.2)
u_{wis} ≥ y_{si} + z_{ws} - 1   \forall i ∈ N, w ∈ W, s ∈ S   (R4.3)
```

Restrição de Incapacidade: Se o trabalhador w é incapaz de executar a tarefa i (ou seja, t_wi = infinito), então u_wis deve ser zer \foralls os s:

```math
u_{wis} = 0   \forall i ∈ I_w, w ∈ W, s ∈ S   (R5)
```

_Nota: Esta restrição pode ser simplificada se a matriz t_wi for tratada no modelo, mas a formulação explícita é mais clara._

### 3. Restrições de Tempo de Ciclo

O tempo total de trabalho em cada estação s deve ser menor ou igual ao tempo de ciclo C_max:

```math
∑_{i ∈ N} ∑_{w ∈ W} t_{wi} u_{wis} ≤ C_max   \forall s ∈ S   (R6)
```

### 4. Restrições de Precedência

Se a tarefa i precede a tarefa j ((i, j) ∈ P), então a estação que executa i deve ser anterior ou igual à estação que executa j:

```math
∑_{s ∈ S} s * y_{si} ≤ ∑_{s ∈ S} s * y_{sj}   \forall (i, j) ∈ P   (R7)
```

### 5. Domínio das Variáveis

```math
y_{si} ∈ {0, 1}, z_{ws} ∈ {0, 1}, u_{wis} ∈ {0, 1}, C_max ≥ 0   (R8)
```

## 3. Algoritmo Proposto: Variable Neighborhood Search (VNS)

A metaheurística escolhida para resolver o ALWABP é o **Variable Neighborhood Search (VNS)**. O VNS é baseado na ideia de mudança sistemática de vizinhanças (neighborhoods) para a busca local e global.

### 3.1. Representação da Solução

Uma solução S é definida por dois vetores principais:

1.  **Atribuição de Tarefas a Estações (Y):** Um vetor onde Y[i] é a estação à qual a tarefa i é atribuída.
2.  **Atribuição de Trabalhadores a Estações (Z):** Um vetor onde Z[s] é o trabalhador alocado à estação s.

### 3.2. Função de Avaliação

A função objetivo é o tempo de ciclo (C_max), calculado como o tempo máximo de processamento entre todas as estações. A avaliação também verifica a factibilidade da solução:

1.  \*_Factibilidade de Precedência:_ \forall par de precedência (i, j), a estação de i deve ser menor ou igual à estação de j.
2.  **Factibilidade de Incapacidade:** Nenhuma tarefa i pode ser atribuída a uma estação s cujo trabalhador alocado Z[s] é incapaz de executá-la (tempo de execução t\_{Z[s], i} = infinito).

Soluções infactíveis são penalizadas com um C_max = infinito.

### 3.3. Geração da Solução Inicial

A solução inicial é gerada por uma heurística gulosa:

1.  **Alocação de Trabalhadores:** Uma permutação aleatória dos trabalhadores é atribuída às estações.
2.  **Alocação de Tarefas:** As tarefas são percorridas em ordem topológica (respeitando precedências) e atribuídas à primeira estação factível que satisfaça as restrições de incapacidade e precedência.

### 3.4. Estrutura de Vizinhanças (N_k)

O VNS utiliza uma sequência de K_max=3 vizinhanças:

| k   | Vizinhança (N_k)  | Descrição                                                   |
| :-- | :---------------- | :---------------------------------------------------------- |
| 1   | Task Swap         | Troca as estações de duas tarefas aleatórias.               |
| 2   | Task Reassignment | Move uma tarefa aleatória para uma estação diferente.       |
| 3   | Worker Swap       | Troca os trabalhadores alocados a duas estações aleatórias. |

### 3.5. Busca Local (Variable Neighborhood Descent - VND)

O VND é aplicado após a perturbação (Shaking) e utiliza uma sequência de vizinhanças de busca local (L_max=2):

| l   | Vizinhança de Busca Local | Estratégia                                                                                      |
| :-- | :------------------------ | :---------------------------------------------------------------------------------------------- |
| 1   | Task Reassignment         | Busca o primeiro movimento de reatribuição de tarefa que melhora a solução (First Improvement). |
| 2   | Worker Swap               | Busca o primeiro movimento de troca de trabalhadores que melhora a solução (First Improvement). |

O VND reinicia a busca na vizinhança l=1 sempre que uma melhoria é encontrada.

### 3.6. Critério de Parada

O critério de parada é o número máximo de iterações (MAX_ITER) do ciclo principal do VNS.

## 4. Resultados Obtidos com Análise

**(ESTA SEÇÃO DEVE SER PREENCHIDA PELO USUÁRIO APÓS A EXECUÇÃO DO SCRIPT `run_all_vns.py`)**

Esta seção deve apresentar e analisar os resultados computacionais obtidos pela execução da metaheurística VNS, conforme as regras do trabalho.

### 4.1. Configuração Experimental

- **Hardware:** (Preencher)
- **Software:** Python 3.x
- **Parâmetros do VNS:** MAX_ITER=50, K_max=3.
- **Replicações:** 5 replicações por instância com sementes diferentes.

### 4.2. Tabela de Resultados

A tabela de resultados deve seguir o formato exigido, apresentando a média das 5 replicações:

| Instância | SI (Média)  | SF (Média)  | Desvio % (SI-SF)/SI | Desvio % (SF-Ótimo) | Tempo VNS (s) | Tempo Solver (s) |
| :-------- | :---------- | :---------- | :------------------ | :------------------ | :------------ | :--------------- |
| 1_hes     | (Preencher) | (Preencher) | (Preencher)         | (Preencher)         | (Preencher)   | (Preencher)      |
| ...       | ...         | ...         | ...                 | ...                 | ...           | ...              |

### 4.3. Análise dos Resultados

**(Preencher com a análise)**

## 5. Como Executar o Programa

Siga o passo a passo abaixo para executar corretamente o VNS e gerar os resultados.

### 5.1. Requisitos

- Python **3.10+**

Instalação das dependências:

```bash
pip install bibliotecas_necessarias
```

### 5.2. Estrutura esperada das pastas

```bash
PM_TRABALHO/
│
├── teste_todas_instancias/
│ ├── alwabp/ # scripts/arquivos para teste em todas as instâncias
│ ├── vns_results/
│ └── comparacao_seeds_final.csv
│
└── testes_relatorio/
├── instacias_teste_relatorio/ # instâncias usadas especificamente no relatório
├── vns_resultados_teste_relatorio/ # resultados das execuções do relatório
│ └── summary_results.csv
│
├── alwabp_vns.py # implementação principal do VNS para o relatório
├── gerar_csv_vns.py
├── instances.csv
├── resultado_vns.csv
├── run_all_vns_parallel.py
└── README.md

```

### 5.3. Executar instâncias

```bash
python run_all_vns.py
```

Esse script:

- lê todas as instâncias dentro de `instacias_teste_relatorio/`;
- executa o VNS diversas vezes com seeds diferentes;
- salva os resultados na pasta `vns_resultados_teste_relatorio/`.

### 5.4. Gerar o CSV final consolidado

Após rodar tudo:

```bash
python gerar_csv_vns.py

```

Ele gera e atualiza arquivos como:

- `summary_results.csv`;
- `resultado_vns.csv`.

## 6. Conclusão

**(Preencher com a conclusão)**

## 7. Bibliografia

**(Preencher com as referências, incluindo a referência original do ALWABP)**

- Miralles, C., Garcia-Sabater, J. P., Andres, C., & Cardos, M. (2007). Advantages of assembly lines in sheltered work centres for disabled. A case study. International Journal of Production Economics, 110(1-2), 187-197.
- (Outras referências)
