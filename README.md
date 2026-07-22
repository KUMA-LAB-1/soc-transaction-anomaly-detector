# 🛡️ Detector Inteligente de Anomalias em Transações Financeiras

![Python](https://img.shields.io/badge/Python-3.12-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-ML-orange)
![Status](https://img.shields.io/badge/Status-Concluído-success)
![LGPD](https://img.shields.io/badge/LGPD-Compliant-green)

Projeto desenvolvido durante o Bootcamp **Bradesco - GenAI, Dados & Cyber**.

O objetivo é construir uma plataforma capaz de identificar automaticamente comportamentos anômalos em transações financeiras utilizando Machine Learning, Ciência de Dados e conceitos de Cyber Security.

O sistema realiza desde a preparação dos dados até a geração automática de relatórios para um Centro de Operações de Segurança (SOC).

---

# 📌 Objetivos

Este projeto busca demonstrar a aplicação prática de:

- Ciência de Dados
- Machine Learning
- Engenharia de Features
- Banco de Dados
- Inteligência Artificial
- Segurança Cibernética
- Detecção de Fraudes
- Threat Intelligence

---

# 🏗 Arquitetura

```text
                    PostgreSQL
                         │
                         ▼
          Coleta das Transações Financeiras
                         │
                         ▼
            Preparação e Limpeza dos Dados
                         │
                         ▼
             Engenharia de Features
                         │
     ┌───────────────────┼────────────────────┐
     ▼                   ▼                    ▼
 Classificador      Detectores         Regressão
 Supervisionado   Não Supervisionados  Severidade
     │                   │                    │
     └──────────────┬────┘
                    ▼
          Comparação Automática
                    │
                    ▼
      Relatório Técnico do SOC (PDF)
                    │
                    ▼
          Correlação MITRE ATT&CK
```

---

# 📂 Estrutura do Projeto

```text
Projeto
│
├── sql/
│     ├── criação_banco.sql
│     ├── procedures.sql
│     └── população.sql
│
├── src/
│     ├── detector.py
│     ├── modelos.py
│     ├── engenharia_features.py
│     ├── relatorio_soc.py
│     └── utilitarios.py
│
├── graficos/
│
├── relatorios/
│
├── resultados/
│
├── README.md
│
└── requirements.txt
```

---

# 📊 Engenharia de Features

O projeto utiliza atributos derivados do comportamento histórico do cliente.

Principais features:

- Valor da transação
- Hora do evento
- Média histórica
- Desvio histórico
- Z-Score individual
- Quantidade de transações anteriores
- Dispositivo novo
- Alteração de limite Pix
- Mudança de localização
- Falhas recentes de login
- Tipo da transação

Essas variáveis simulam indicadores normalmente utilizados por mecanismos de prevenção à fraude.

---

# 🤖 Modelos Implementados

Foram implementados quatro detectores de anomalias para comparação de desempenho.

| Modelo | Tipo |
|---------|------|
| Isolation Forest | Não supervisionado |
| Local Outlier Factor | Não supervisionado |
| One-Class SVM | Não supervisionado |
| Elliptic Envelope | Não supervisionado |

Além dos detectores, foi treinado um classificador supervisionado para avaliação das features e geração das probabilidades de risco.

---

# 📈 Comparação dos Modelos

Critério utilizado para seleção:

1. Maior F1-Score
2. Maior Recall
3. Maior Precision
4. Menor tempo de execução

## Resultado

| Modelo | Precision | Recall | F1 |
|---------|----------|--------|------|
| Elliptic Envelope | **1.00** | **0.42** | **0.59** |
| Isolation Forest | 0.92 | 0.39 | 0.54 |
| One-Class SVM | 0.77 | 0.32 | 0.46 |
| Local Outlier Factor | 0.47 | 0.18 | 0.26 |

🏆 Modelo selecionado:

**Elliptic Envelope**

---

# 📉 Classificador Supervisionado

O classificador utilizado para triagem obteve:

- ROC-AUC ≈ **0.99**

Principais fatores utilizados na decisão:

- Z-Score do cliente
- Média histórica
- Falhas de login
- Alteração de limite
- Mudança de localização

O atributo **Z-Score do cliente** foi o mais relevante para o processo de classificação.

---

# 📊 Resultados Obtidos

Durante a execução foram identificadas:

- 315 transações anômalas
- geração automática de gráficos
- classificação por severidade
- relatório PDF
- histórico das execuções
- comparação automática entre modelos

---

# 📄 Relatório SOC

O sistema gera automaticamente um relatório contendo:

- Resumo Executivo
- Incidentes Detectados
- Probabilidade de fraude
- Score de severidade
- Correlação MITRE ATT&CK
- Informações pseudonimizadas (LGPD)

---

# 🛡️ Segurança

O projeto foi desenvolvido considerando conceitos de:

- Defesa em Profundidade
- MITRE ATT&CK
- LGPD
- Princípio do Menor Privilégio
- Auditoria
- Pseudonimização de clientes

---

# ⚙ Tecnologias Utilizadas

- Python
- PostgreSQL
- Pandas
- NumPy
- Scikit-Learn
- Matplotlib
- Seaborn
- ReportLab

---

# 🚀 Como executar

## Clone o projeto

```bash
git clone https://github.com/seuusuario/detector-anomalias.git
```

Instale as dependências

```bash
pip install -r requirements.txt
```

Configure o PostgreSQL.

Execute

```bash
python detector.py
```

---

# 📚 Conceitos Aplicados

✔ Machine Learning

✔ Data Science

✔ Feature Engineering

✔ Banco de Dados

✔ Cyber Security

✔ Fraud Detection

✔ SOC

✔ Threat Intelligence

✔ MITRE ATT&CK

✔ Engenharia de Software

✔ Visualização de Dados

---

# 📌 Limitações

Este projeto utiliza uma base de dados sintética construída para fins educacionais.

Embora os modelos tenham apresentado excelente desempenho no cenário proposto, a aplicação em ambiente produtivo exigiria:

- maior volume de dados;
- validação contínua;
- ajuste de hiperparâmetros;
- monitoramento contra drift dos dados;
- integração com SIEM/SOC.

---

# 🔮 Próximas Evoluções

- API REST
- Dashboard em Streamlit
- Docker
- DevSecOps
- GitHub Actions
- SHAP Explainability
- Autoencoders
- XGBoost
- Monitoramento contínuo
- Deploy em Cloud

---

# 👨‍💻 Autor

Desenvolvido por Wellington Hikaru Kumagai

Projeto desenvolvido durante o Bootcamp Bradesco - GenAI, Dados & Cyber.
