# MVP — Poder de Compra do Salário Mínimo Brasileiro (1994–2026)

**Aluno:** Marcelo Monnerat Castello  
**Matrícula:** 4052026000091  
**Curso:** PUC Rio — Pós-Graduação em Ciência de Dados

**Link do Colab:** https://colab.research.google.com/github/MonneratRJ/mvp-inflacao/blob/master/notebooks/analysis.ipynb

---

## Visão Geral

Este MVP analisa a evolução do poder de compra do salário mínimo brasileiro ao longo de 32 anos (jun/1994–mar/2026), cruzando três fontes de dados:

- **DIEESE** — salário mínimo nominal e salário mínimo necessário (custo de vida básico familiar)
- **FIPE** — Índice de Preços ao Consumidor (IPC) segmentado por setor (habitação, alimentação, saúde, transporte, educação, vestuário, despesas pessoais)
- **IBGE/SIDRA** — renda média mensal real (Tabela 6388, PNAD Contínua, disponível a partir de 2012)

Três hipóteses são investigadas:

1. O salário mínimo nominal nunca alcançou o salário mínimo necessário
2. Setores inelásticos (habitação, saúde, educação) cresceram desproporcionalmente
3. A razão entre salário necessário e nominal cresceu ao longo das três décadas

---

## Estrutura do Projeto

```
mvp-inflacao/
├── data/
│   ├── processed/          # CSVs prontos para uso no notebook
│   │   ├── fipe_ipc_199406.csv
│   │   ├── salario_minimo_dieese.csv
│   │   └── tabela_6388_monthly.csv
│   └── raw/                # Arquivos originais baixados das fontes
├── notebooks/
│   └── analysis.ipynb      # ← Notebook principal da análise
├── src/                    # Scripts de coleta e pré-processamento das fontes
│   ├── process_fipe_ipc.py
│   ├── process_tabela_6388.py
│   └── scrape_dieese_salario_minimo.py
└── README.md
```

---

## Como Executar

### Pré-requisitos

```bash
pip install pandas numpy matplotlib seaborn scikit-learn
```

> Python 3.9 ou superior recomendado.

### Executando o notebook

1. Abra o arquivo `notebooks/analysis.ipynb` no Jupyter Notebook, JupyterLab ou VS Code.
2. **Execute as células sequencialmente, uma a uma** — o notebook possui dependências entre células (variáveis reutilizadas entre seções). Executar em ordem incorreta ou usar "Run All" pode causar erros.
3. Os dados processados já estão disponíveis em `data/processed/`. Não é necessário rodar os scripts em `src/` para reproduzir a análise.

> **Atenção:** A célula de carregamento de dados usa caminhos relativos (`../data/processed/`). O notebook deve ser executado a partir do diretório `notebooks/`, que é o comportamento padrão do Jupyter.

---

## Fontes dos Dados

- **DIEESE — Salário Mínimo Necessário**  
  https://www.dieese.org.br/analisecestabasica/salarioMinimo.html

- **FIPE — IPC Mensal**  
  https://www.fipe.org.br/pt-br/indices/ipc/#indice-mensal

- **IBGE/SIDRA — Tabela 6388**  
  https://sidra.ibge.gov.br/tabela/6388
