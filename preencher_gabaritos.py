"""
Preenche os resposta_esperada null no benchmark.json
usando o netflix_titles.csv.

Como usar:
    python preencher_gabaritos.py

Coloque o netflix_titles.csv na mesma pasta ou ajuste o caminho abaixo.
"""

import json
import pandas as pd
from pathlib import Path

# ============================================================
# Ajuste esses caminhos se necessário
# ============================================================
CSV_PATH = "data/netflix_titles.csv"          # caminho do CSV
BENCHMARK_IN = "evaluation/benchmark.json"   # benchmark original
BENCHMARK_OUT = "evaluation/benchmark.json"  # sobrescreve o mesmo arquivo
# ============================================================

print(f"Carregando {CSV_PATH}...")
df = pd.read_csv(CSV_PATH)
print(f"✓ {len(df)} linhas × {len(df.columns)} colunas\n")

# Calcula todos os gabaritos
gabaritos = {
    "fat-001": int(len(df)),
    "fat-002": df.columns.tolist(),
    "fat-003": int(df[df["type"] == "Movie"].shape[0]),
    "fat-004": int(df[df["type"] == "TV Show"].shape[0]),
    "fat-005": str(df["rating"].mode()[0]),
    "fat-006": int(df["release_year"].min()),
    "fat-007": int(df["release_year"].max()),
    "fat-008": int(df["director"].isna().sum()),
    "fat-009": int(df["country"].nunique()),
    "fat-010": str(df["country"].value_counts().index[0]),

    "ana-001": {str(k): int(v) for k, v in df["type"].value_counts().to_dict().items()},
    "ana-002": df["country"].value_counts().head(5).index.tolist(),
    "ana-003": int(df[df["release_year"] >= 2019].shape[0]),
    "ana-004": round(float(df[df["type"] == "Movie"]["release_year"].mean()), 2),
    "ana-005": df["listed_in"].value_counts().head(5).index.tolist(),
    "ana-006": str(df[df["type"] == "Movie"]["rating"].mode()[0]),
    "ana-007": str(df[df["type"] == "TV Show"]["rating"].mode()[0]),
    "ana-008": int(df[df["country"] == "United States"].shape[0]),
    "ana-009": int(df["release_year"].value_counts().index[0]),
    "ana-010": int(df[df["rating"] == "TV-MA"].shape[0]),
    "ana-011": round(float(df[df["type"] == "Movie"].shape[0] / len(df) * 100), 2),
    "ana-012": df["rating"].value_counts().head(3).index.tolist(),
    "ana-013": int(df[df["release_year"] < 2000].shape[0]),
    "ana-014": str(df[df["type"] == "TV Show"]["country"].value_counts().index[0]),
    "ana-015": round(float(df["release_year"].std()), 2),

    # Ambíguas já têm gabarito "recusa" — não mexemos
}

# Lê o benchmark original
with open(BENCHMARK_IN, "r", encoding="utf-8") as f:
    benchmark = json.load(f)

# Preenche os nulls
preenchidos = 0
for pergunta in benchmark["perguntas"]:
    pid = pergunta["id"]
    if pid in gabaritos and pergunta["resposta_esperada"] is None:
        pergunta["resposta_esperada"] = gabaritos[pid]
        print(f"  ✓ {pid}: {gabaritos[pid]}")
        preenchidos += 1

# Salva
with open(BENCHMARK_OUT, "w", encoding="utf-8") as f:
    json.dump(benchmark, f, ensure_ascii=False, indent=4)

print(f"\n✓ {preenchidos} gabaritos preenchidos → {BENCHMARK_OUT}")
