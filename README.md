# Agente de Análise Exploratória de Dados em Linguagem Natural

Trabalho Final — Tecnologia em Ciência de Dados (5º semestre) — Fatec Ourinhos

Grupo: Bruna Oliveira

---

## Visão geral

O projeto implementa um **agente conversacional** que recebe perguntas em português sobre
um arquivo CSV e responde executando, autonomamente, operações de análise exploratória
(EDA) por meio de *function calling*.

O dataset utilizado é o **Netflix Titles** (`netflix_titles.csv`), com informações sobre
filmes e séries disponíveis na plataforma Netflix.

```
Usuário → Orquestrador → LLM (decide) → Tool (executa) → Observa → ... → Resposta
                              ↑___________________________________________│
                                        loop até resposta final
```

---

## Estrutura de pastas

```
PLN-NETFLIX/
├── agent/                  # Loop do agente e integração com o LLM
│   ├── __init__.py
│   ├── agent.py            # Classe principal Agent (suporte Anthropic e DeepSeek)
│   └── llm_client.py       # Cliente da API (Anthropic / DeepSeek)
│
├── tools/                  # Implementação das ferramentas (pandas)
│   ├── __init__.py
│   ├── base.py             # Decorador @tool e base comum
│   ├── inspect_tools.py    # listar_colunas, descrever_dados, contar_valores
│   ├── filter_tools.py     # filtrar, agrupar_e_agregar
│   ├── stats_tools.py      # correlacao, detectar_outliers (IQR e z-score)
│   ├── plot_tools.py       # gerar_grafico
│   └── hypothesis_tools.py # [BÔNUS] teste_t, qui_quadrado
│
├── evaluation/             # Sistema de avaliação (benchmark)
│   ├── __init__.py
│   ├── benchmark.py        # Carrega benchmark.json e executa
│   ├── metrics.py          # Cálculo de acurácia, latência, custo, etc.
│   └── benchmark.json      # 32 perguntas (10 factuais, 15 analíticas, 5 ambíguas, 2 bônus)
│
├── data/
│   ├── netflix_titles.csv  # Dataset principal (Netflix)
│   └── exemplo.csv         # Dataset de exemplo
│
├── outputs/                # Gráficos gerados pelo agente
├── logs/                   # Logs de execução do benchmark
├── tests/
│   ├── __init__.py
│   └── test_tools.py       # Testes unitários das tools (pytest)
│
├── cli.py                  # Interface de linha de comando (entry point)
├── config.py               # Configurações centralizadas
├── preencher_gabaritos.py  # Script para preencher gabaritos do benchmark
├── requirements.txt        # Dependências
└── README.md
```

---

## Tools implementadas

### Obrigatórias
| Tool | Arquivo | Descrição |
|---|---|---|
| `listar_colunas` | inspect_tools.py | Lista colunas e tipos do dataset |
| `descrever_dados` | inspect_tools.py | Estatísticas descritivas (df.describe) |
| `contar_valores` | inspect_tools.py | Distribuição de valores (value_counts) |
| `filtrar` | filter_tools.py | Filtra com expressão pandas .query() |
| `agrupar_e_agregar` | filter_tools.py | Groupby + agg (mean, sum, count...) |
| `correlacao` | stats_tools.py | Correlação Pearson ou Spearman |
| `detectar_outliers` | stats_tools.py | Outliers por IQR ou z-score |
| `gerar_grafico` | plot_tools.py | Gera PNG (hist, boxplot, scatter, barplot, linha) |

### Bônus
| Tool | Arquivo | Descrição |
|---|---|---|
| `teste_t` | hypothesis_tools.py | Teste t de Student (Welch) entre dois grupos |
| `qui_quadrado` | hypothesis_tools.py | Teste qui-quadrado entre duas colunas categóricas |

---

## Instalação

### 1. Pré-requisitos

- Python 3.10 ou superior
- Conta na Anthropic (Claude) ou DeepSeek

### 2. Setup no PyCharm

1. **File → Open** e selecione a pasta do projeto.
2. PyCharm vai detectar `requirements.txt` e oferecer criar um virtualenv — aceite.
3. Após criar o venv, instale as dependências:
   ```
   pip install -r requirements.txt
   ```
4. Copie `.env.example` para `.env` e preencha sua API key:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   # ou
   DEEPSEEK_API_KEY=sk-...
   ```
5. **Marque a pasta raiz como Sources Root**: clique direito na pasta → *Mark Directory as → Sources Root*.

---

## Como usar

### Modo interativo (CLI)

```bash
python cli.py
```

Exemplo de sessão com o dataset Netflix:

```
> Quais são as colunas do dataset?
[O agente chama listar_colunas() e lista as 12 colunas]

> Quantos filmes existem no dataset?
[O agente chama filtrar() ou contar_valores() e responde: 6.131 filmes]

> Qual país produziu mais conteúdo?
[O agente chama contar_valores(coluna='country') e responde: United States]

> Existe diferença significativa entre o ano de lançamento de filmes e séries?
[O agente chama teste_t() e apresenta o resultado do teste estatístico]
```

Comandos especiais disponíveis na CLI:

| Comando | Descrição |
|---|---|
| `/sair` | Encerra a sessão |
| `/trajetoria` | Mostra a trajetória da última pergunta |
| `/custo` | Mostra tokens e tempo acumulados |
| `/ajuda` | Lista de comandos |

### Rodar o benchmark completo

```bash
python -m evaluation.benchmark
```

Gera um relatório em `logs/benchmark_<timestamp>.json` com todas as métricas.

### Preencher gabaritos automaticamente

```bash
python preencher_gabaritos.py
```

Recalcula os gabaritos do `benchmark.json` a partir do CSV atual.

---

## Benchmark

O benchmark contém **32 perguntas** distribuídas em 3 categorias:

| Categoria | Quantidade | Descrição |
|---|---|---|
| Factual | 10 | Perguntas diretas sobre o dataset (contagens, valores únicos) |
| Analítica | 17 | Perguntas que exigem múltiplas tools (filtros, agrupamentos, testes) |
| Ambígua | 5 | Perguntas subjetivas ou inválidas — agente deve recusar |

---

## Política de uso de LLMs

Podemos usar ChatGPT/Claude/Copilot para programar.
Não podemos entregar código que não compreendamos.
Durante a apresentação, qualquer integrante pode ser questionado sobre qualquer linha.
