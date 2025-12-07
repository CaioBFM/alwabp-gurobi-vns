# config.py

# ----------------------
# Parâmetros do VNS
# ----------------------
VNS_MAX_ITER = 500      # número padrão de iterações
VNS_K_MAX = 3            # k_max padrão
DEFAULT_SEED = 42        # seed default se nenhuma for passada

# ----------------------
# Parâmetros do experimento
# ----------------------

# Geração automática de seeds a partir de uma base
BASE_SEED = 42
# SEEDS = [42, 101, 202, 303, 404, 505, 606, 707, 909, 1001, 1707, 1905, 1936]
SEEDS_PEQ = [0, 1, 7, 13, 17, 23, 31, 47, 42, 73, 202, 101, 606]
SEEDS_GRANDES = [97, 131, 197, 223, 281, 313, 487, 557, 613, 733, 1707, 1905, 1936]
# NUM_REPLICATIONS = len(SEEDS_PEQ)

# Limite de tempo de cada execução do VNS (em segundos)
# Use None para não ter limite
TIME_LIMIT = 600
