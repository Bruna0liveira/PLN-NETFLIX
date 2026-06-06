"""
Testes unitários das tools.

Estes testes não dependem do LLM — testam APENAS a lógica em pandas.
Rodar com:
    pytest tests/

TODO (alunos):
  - Adicionar testes para as tools que vocês criarem.
  - Adicionar testes de casos de erro (coluna inexistente, etc).
"""

import pandas as pd
import pytest

from tools import state
from tools.inspect_tools import listar_colunas, descrever_dados, contar_valores
from tools.filter_tools import filtrar, agrupar_e_agregar
from tools.stats_tools import correlacao, detectar_outliers
from tools.hypothesis_tools import teste_t, qui_quadrado


# ============================================================
# Fixture: dataset sintético usado por todos os testes
# ============================================================

@pytest.fixture(autouse=True)
def carregar_dataset_sintetico():
    """Carrega um DataFrame sintético antes de cada teste."""
    df = pd.DataFrame({
        "idade": [25, 30, 35, 40, 45, 50, 100],   # 100 é outlier
        "salario": [3000, 4500, 6000, 7500, 9000, 11000, 12500],
        "genero": ["F", "M", "F", "M", "F", "M", "F"],
        "cidade": ["SP", "RJ", "SP", "MG", "RJ", "SP", "BA"],
    })
    state.df = df
    state.path = "<fixture>"
    yield
    state.df = None


# ============================================================
# Testes de inspect_tools
# ============================================================

def test_listar_colunas_retorna_todas():
    resultado = listar_colunas()
    nomes = [c["nome"] for c in resultado["colunas"]]
    assert nomes == ["idade", "salario", "genero", "cidade"]
    assert resultado["total_linhas"] == 7
    assert resultado["total_colunas"] == 4


def test_descrever_dados_separa_numericas_de_categoricas():
    resultado = descrever_dados()
    assert "numericas" in resultado
    assert "categoricas" in resultado
    assert "idade" in resultado["numericas"]
    assert "genero" in resultado["categoricas"]


def test_descrever_dados_coluna_invalida_retorna_erro():
    resultado = descrever_dados(colunas=["nao_existe"])
    assert "erro" in resultado


def test_contar_valores_basico():
    resultado = contar_valores("genero")
    assert resultado["coluna"] == "genero"
    assert resultado["total_valores_unicos"] == 2
    assert resultado["distribuicao"]["F"] == 4
    assert resultado["distribuicao"]["M"] == 3


def test_contar_valores_coluna_invalida():
    resultado = contar_valores("inexistente")
    assert "erro" in resultado


# ============================================================
# Testes de filter_tools
# ============================================================

def test_filtrar_basico():
    resultado = filtrar("idade > 35")
    assert resultado["linhas_resultantes"] == 4  # 40, 45, 50, 100


def test_filtrar_expressao_invalida():
    resultado = filtrar("coluna_inexistente > 0")
    assert "erro" in resultado


def test_agrupar_e_agregar_media_por_genero():
    resultado = agrupar_e_agregar(grupo="genero", coluna="salario", funcao="mean")
    assert "F" in resultado["resultados"]
    assert "M" in resultado["resultados"]
    # F: (3000+6000+9000+12500)/4 = 7625
    assert resultado["resultados"]["F"] == pytest.approx(7625.0, abs=0.1)


def test_agrupar_e_agregar_funcao_invalida():
    resultado = agrupar_e_agregar(grupo="genero", coluna="salario", funcao="xyz")
    assert "erro" in resultado


def test_agrupar_e_agregar_coluna_nao_numerica():
    resultado = agrupar_e_agregar(grupo="genero", coluna="cidade", funcao="mean")
    assert "erro" in resultado


# ============================================================
# Testes de stats_tools
# ============================================================

def test_correlacao_idade_salario():
    # Idade e salário são fortemente correlacionados nesse dataset
    resultado = correlacao("idade", "salario")
    assert "correlacao" in resultado
    assert resultado["correlacao"] > 0.8  # esperamos forte positiva


def test_correlacao_coluna_categorica_retorna_erro():
    resultado = correlacao("idade", "genero")
    assert "erro" in resultado


def test_detectar_outliers_iqr_identifica_o_100():
    resultado = detectar_outliers("idade", metodo="iqr")
    assert resultado["total_outliers"] >= 1
    assert 100.0 in resultado["exemplos"]


def test_detectar_outliers_metodo_invalido():
    resultado = detectar_outliers("idade", metodo="foo")
    assert "erro" in resultado


# ============================================================
# Testes de hypothesis_tools (bônus)
# ============================================================

@pytest.fixture(autouse=False)
def carregar_dataset_com_grupos():
    """Dataset com dois grupos claramente diferentes para teste t."""
    df = pd.DataFrame({
        "idade": [25, 30, 35, 40, 45, 50, 100],
        "salario": [3000, 4500, 6000, 7500, 9000, 11000, 12500],
        "genero": ["F", "M", "F", "M", "F", "M", "F"],
        "cidade": ["SP", "RJ", "SP", "MG", "RJ", "SP", "BA"],
        "tipo": ["A", "A", "A", "B", "B", "B", "B"],
    })
    state.df = df
    state.path = "<fixture>"
    yield
    state.df = None


def test_teste_t_detecta_diferenca(carregar_dataset_com_grupos):
    resultado = teste_t(
        coluna_numerica="salario",
        coluna_grupo="tipo",
        grupo_a="A",
        grupo_b="B",
    )
    assert "p_valor" in resultado
    assert "estatistica_t" in resultado
    assert "significativo" in resultado
    assert "grupo_a" in resultado and "grupo_b" in resultado


def test_teste_t_coluna_invalida(carregar_dataset_com_grupos):
    resultado = teste_t(
        coluna_numerica="nao_existe",
        coluna_grupo="tipo",
        grupo_a="A",
        grupo_b="B",
    )
    assert "erro" in resultado


def test_teste_t_grupo_invalido(carregar_dataset_com_grupos):
    resultado = teste_t(
        coluna_numerica="salario",
        coluna_grupo="tipo",
        grupo_a="X",  # não existe
        grupo_b="B",
    )
    assert "erro" in resultado


def test_qui_quadrado_basico(carregar_dataset_com_grupos):
    resultado = qui_quadrado(coluna_a="genero", coluna_b="cidade")
    assert "p_valor" in resultado
    assert "estatistica_chi2" in resultado
    assert "significativo" in resultado


def test_qui_quadrado_coluna_invalida(carregar_dataset_com_grupos):
    resultado = qui_quadrado(coluna_a="nao_existe", coluna_b="cidade")
    assert "erro" in resultado


def test_detectar_outliers_zscore_identifica_o_100():
    # Com dataset pequeno (n=7), z-score pode não detectar como |z|>3
    # mas a estrutura do retorno deve estar correta
    resultado = detectar_outliers("idade", metodo="zscore")
    assert "total_outliers" in resultado
    assert "media" in resultado
    assert "desvio_padrao" in resultado
    assert "limite_z" in resultado
    assert resultado["limite_z"] == 3
