"""
Ferramenta extra: testes de hipótese estatística.

Implementa dois testes:
  - teste_t: compara médias de uma coluna numérica entre dois grupos.
  - qui_quadrado: testa associação entre duas colunas categóricas.

Para registrar, adicione ao tools/__init__.py:
    from . import hypothesis_tools
"""

import pandas as pd
from scipy import stats
from .base import tool, state


# ============================================================
# teste_t
# ============================================================

@tool(
    description=(
        "Realiza um teste t de Student para comparar a média de uma coluna numérica "
        "entre dois grupos definidos por uma coluna categórica.\n\n"
        "Exemplo: comparar o ano médio de lançamento entre 'Movie' e 'TV Show'.\n\n"
        "Retorna: estatística t, p-valor e interpretação."
    ),
    parameters={
        "type": "object",
        "properties": {
            "coluna_numerica": {
                "type": "string",
                "description": "Coluna numérica a comparar entre os grupos.",
            },
            "coluna_grupo": {
                "type": "string",
                "description": "Coluna categórica que define os dois grupos.",
            },
            "grupo_a": {
                "type": "string",
                "description": "Valor do primeiro grupo (ex: 'Movie').",
            },
            "grupo_b": {
                "type": "string",
                "description": "Valor do segundo grupo (ex: 'TV Show').",
            },
        },
        "required": ["coluna_numerica", "coluna_grupo", "grupo_a", "grupo_b"],
    },
)
def teste_t(
    coluna_numerica: str,
    coluna_grupo: str,
    grupo_a: str,
    grupo_b: str,
) -> dict:
    """Teste t de Student entre dois grupos."""
    df = state.require_loaded()

    # Validações
    for col in (coluna_numerica, coluna_grupo):
        if col not in df.columns:
            return {"erro": f"Coluna '{col}' não existe."}

    if not pd.api.types.is_numeric_dtype(df[coluna_numerica]):
        return {"erro": f"Coluna '{coluna_numerica}' precisa ser numérica."}

    serie_a = df[df[coluna_grupo] == grupo_a][coluna_numerica].dropna()
    serie_b = df[df[coluna_grupo] == grupo_b][coluna_numerica].dropna()

    if len(serie_a) == 0:
        return {"erro": f"Grupo '{grupo_a}' não encontrado em '{coluna_grupo}'."}
    if len(serie_b) == 0:
        return {"erro": f"Grupo '{grupo_b}' não encontrado em '{coluna_grupo}'."}

    t_stat, p_valor = stats.ttest_ind(serie_a, serie_b, equal_var=False)

    alpha = 0.05
    significativo = p_valor < alpha
    interpretacao = (
        f"Diferença estatisticamente significativa (p < {alpha}): "
        f"as médias de '{grupo_a}' ({serie_a.mean():.2f}) e '{grupo_b}' "
        f"({serie_b.mean():.2f}) são diferentes."
        if significativo else
        f"Sem evidência de diferença significativa (p >= {alpha}): "
        f"as médias de '{grupo_a}' ({serie_a.mean():.2f}) e '{grupo_b}' "
        f"({serie_b.mean():.2f}) são estatisticamente semelhantes."
    )

    return {
        "teste": "t de Student (Welch)",
        "coluna_numerica": coluna_numerica,
        "coluna_grupo": coluna_grupo,
        "grupo_a": {"nome": grupo_a, "n": len(serie_a), "media": round(float(serie_a.mean()), 3)},
        "grupo_b": {"nome": grupo_b, "n": len(serie_b), "media": round(float(serie_b.mean()), 3)},
        "estatistica_t": round(float(t_stat), 4),
        "p_valor": round(float(p_valor), 6),
        "significativo": significativo,
        "interpretacao": interpretacao,
    }


# ============================================================
# qui_quadrado
# ============================================================

@tool(
    description=(
        "Realiza um teste qui-quadrado (χ²) de independência entre duas colunas "
        "categóricas. Verifica se existe associação estatística entre elas.\n\n"
        "Exemplo: verificar se 'type' (Movie/TV Show) e 'rating' são independentes.\n\n"
        "Retorna: estatística χ², p-valor, graus de liberdade e interpretação."
    ),
    parameters={
        "type": "object",
        "properties": {
            "coluna_a": {
                "type": "string",
                "description": "Primeira coluna categórica.",
            },
            "coluna_b": {
                "type": "string",
                "description": "Segunda coluna categórica.",
            },
            "top_n": {
                "type": "integer",
                "description": (
                    "Limita as categorias às top N mais frequentes de cada coluna "
                    "para evitar tabelas de contingência muito esparsas (default: 10)."
                ),
            },
        },
        "required": ["coluna_a", "coluna_b"],
    },
)
def qui_quadrado(coluna_a: str, coluna_b: str, top_n: int = 10) -> dict:
    """Teste qui-quadrado de independência entre duas colunas categóricas."""
    df = state.require_loaded()

    for col in (coluna_a, coluna_b):
        if col not in df.columns:
            return {"erro": f"Coluna '{col}' não existe."}

    # Filtra top N categorias para evitar tabela esparsa
    top_a = df[coluna_a].value_counts().head(top_n).index
    top_b = df[coluna_b].value_counts().head(top_n).index
    df_filtrado = df[df[coluna_a].isin(top_a) & df[coluna_b].isin(top_b)]

    tabela = pd.crosstab(df_filtrado[coluna_a], df_filtrado[coluna_b])

    if tabela.shape[0] < 2 or tabela.shape[1] < 2:
        return {"erro": "Tabela de contingência muito pequena para o teste."}

    chi2, p_valor, gl, _ = stats.chi2_contingency(tabela)

    alpha = 0.05
    significativo = p_valor < alpha
    interpretacao = (
        f"Associação estatisticamente significativa (p < {alpha}): "
        f"'{coluna_a}' e '{coluna_b}' NÃO são independentes."
        if significativo else
        f"Sem evidência de associação (p >= {alpha}): "
        f"'{coluna_a}' e '{coluna_b}' parecem independentes."
    )

    return {
        "teste": "Qui-quadrado de independência",
        "coluna_a": coluna_a,
        "coluna_b": coluna_b,
        "estatistica_chi2": round(float(chi2), 4),
        "p_valor": round(float(p_valor), 6),
        "graus_de_liberdade": int(gl),
        "significativo": significativo,
        "interpretacao": interpretacao,
        "linhas_analisadas": len(df_filtrado),
    }
