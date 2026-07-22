# 🛡️ SOC Transaction Anomaly Detector

Projeto de análise de dados e detecção de anomalias em transações financeiras desenvolvido durante o Bootcamp **Bradesco - GenAI, Dados & Cyber**.

Esta versão corresponde à entrega do módulo:

> **Análise de Dados com Python: da preparação à aplicação em segurança**

O sistema integra Python, PostgreSQL, Machine Learning e conceitos de Segurança Cibernética para identificar transações com comportamento fora do padrão, comparar diferentes detectores e gerar um relatório técnico voltado para análise em um SOC.

---

## 📌 Objetivo

O objetivo do projeto é construir um pipeline capaz de:

- carregar transações armazenadas em PostgreSQL;
- validar, limpar e preparar os dados;
- criar variáveis comportamentais;
- detectar padrões anômalos;
- comparar algoritmos de Machine Learning;
- estimar a severidade dos eventos;
- correlacionar sinais de segurança com o MITRE ATT&CK;
- gerar gráficos, métricas e relatório executivo.

---

## 🧪 Natureza dos dados

A base utilizada neste projeto é composta por **dados sintéticos**, criados exclusivamente para fins educacionais e experimentais.

O banco foi populado com:

- transações consideradas normais;
- transações classificadas como suspeitas;
- eventos de autenticação;
- falhas recentes de login;
- uso de dispositivo novo;
- alterações de limite;
- mudanças de localização.

Nos modelos não supervisionados, o status da transação não participa do treinamento. Ele é utilizado apenas posteriormente para auditoria e comparação dos resultados.

---

## 🏗️ Arquitetura

```text
PostgreSQL / Supabase
        │
        ▼
View de investigação do SOC
        │
        ▼
Validação e preparação dos dados
        │
        ▼
Engenharia de features
        │
        ├── Classificador de triagem
        ├── Detectores de anomalia
        └── Regressão de severidade
                │
                ▼
Comparação de métricas
                │
                ▼
Seleção do melhor detector
                │
                ▼
Correlação MITRE ATT&CK
                │
                ▼
Gráficos, JSON, CSV e relatório PDF
```

---

## 📂 Estrutura do repositório

```text
.
├── src/
│   ├── security_detector.py
│   ├── db_connector.py
│   └── ingest_mitre.py
│
├── database/
│   ├── schema/
│   ├── queries/
│   └── seeds/
│
├── reports/
│   └── resultado_multimodelo/
│
├── docs/
├── README.md
├── CHANGELOG.md
├── requirements.txt
├── .gitignore
└── .env.example
```

---

## 🔎 Engenharia de features

O pipeline utiliza atributos originais e derivados do comportamento histórico dos clientes:

- valor da transação;
- horário do evento;
- dia da semana;
- média histórica por cliente;
- desvio-padrão histórico;
- Z-Score do valor da transação;
- quantidade de transações anteriores;
- falhas recentes de login;
- uso de dispositivo novo;
- alteração de limite;
- mudança de localização;
- tipo da transação.

O Z-Score mede quanto o valor atual se afasta do comportamento histórico do cliente.

---

## 🤖 Modelos implementados

### Classificador supervisionado

Foi utilizado um `DecisionTreeClassifier` para reproduzir decisões históricas de triagem.

O objetivo desse classificador não é descobrir ataques inéditos, mas avaliar quais features mais contribuíram para a classificação das transações já rotuladas.

### Detectores não supervisionados

Foram comparados quatro modelos:

| Modelo | Característica principal |
|---|---|
| Isolation Forest | Isola observações incomuns por particionamento aleatório |
| Local Outlier Factor | Identifica desvios em relação à densidade local |
| One-Class SVM | Aprende uma fronteira para representar o comportamento normal |
| Elliptic Envelope | Modela a distribuição dos dados por uma região elíptica robusta |

### Regressão de severidade

Foi utilizada uma regressão linear para estimar um score de risco entre 0 e 100.

Essa parte é experimental e deverá ser reavaliada com uma base maior e modelos mais adequados para níveis ordinais de risco.

---

## 📊 Resultados experimentais

Os detectores utilizaram o mesmo conjunto de features e foram avaliados com o mesmo conjunto de dados.

| Modelo | Anomalias | Precision | Recall | F1-score | ROC-AUC | Tempo |
|---|---:|---:|---:|---:|---:|---:|
| Elliptic Envelope | 315 | **1,000** | **0,420** | **0,592** | **0,9995** | 0,116 s |
| Isolation Forest | 315 | 0,917 | 0,385 | 0,543 | 0,9808 | 0,279 s |
| One-Class SVM | 315 | 0,771 | 0,324 | 0,456 | 0,7185 | **0,059 s** |
| Local Outlier Factor | 296 | 0,466 | 0,184 | 0,264 | 0,5654 | 0,090 s |

### Modelo selecionado

O modelo selecionado automaticamente foi:

> **Elliptic Envelope**

O critério utilizado foi:

1. maior F1-score;
2. maior recall;
3. maior precision;
4. menor tempo de execução.

O Elliptic Envelope apresentou o maior F1-score e precision igual a 1,0 no conjunto sintético utilizado.

---

## 📈 Comparação visual

![Comparação dos detectores](reports/resultado_multimodelo/comparacao_detectores.png)

---

## 🌲 Isolation Forest

![Isolation Forest](reports/resultado_multimodelo/anomalias_isolation_forest.png)

---

## 📐 Elliptic Envelope

![Elliptic Envelope](reports/resultado_multimodelo/anomalias_elliptic_envelope.png)

---

## 🧭 Local Outlier Factor

![Local Outlier Factor](reports/resultado_multimodelo/anomalias_local_outlier_factor.png)

---

## 🧠 One-Class SVM

![One-Class SVM](reports/resultado_multimodelo/anomalias_one_class_svm.png)

---

## 🔬 Importância das features

O classificador de triagem atingiu ROC-AUC próximo de `0,99`.

![Importância das features](reports/resultado_multimodelo/importancia_features_classificador.png)

A feature `zscore_valor_cliente` concentrou aproximadamente 92,3% da importância do classificador.

Esse resultado indica que a separação entre transações normais e suspeitas no conjunto sintético está fortemente relacionada ao desvio do valor em relação ao histórico do cliente.

Embora o resultado seja positivo para a prova de conceito, ele também representa uma limitação: o modelo pode estar excessivamente dependente de uma única variável.

---

## 🛡️ Segurança e privacidade

O projeto aplica medidas como:

- conexão SSL obrigatória com o banco;
- credenciais armazenadas fora do código;
- pseudonimização dos clientes;
- auditoria de acesso;
- políticas de segurança no PostgreSQL;
- correlação entre transações e eventos de segurança;
- minimização da exposição de dados nos relatórios.

Os dados utilizados são sintéticos e não representam clientes ou operações reais.

---

## 🎯 MITRE ATT&CK

O pipeline utiliza dados do MITRE ATT&CK armazenados no PostgreSQL.

A correlação considera sinais como:

- múltiplas falhas de login;
- dispositivo novo;
- alteração de limite;
- mudança de localização;
- possível comprometimento de conta.

O mapeamento é utilizado como apoio à investigação e não representa confirmação automática de ataque.

---

## ⚙️ Como executar

### 1. Clonar o repositório

```bash
git clone https://github.com/SEU_USUARIO/soc-transaction-anomaly-detector.git
cd soc-transaction-anomaly-detector
```

### 2. Criar o ambiente virtual

No Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

No Linux ou macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar a conexão

Copie:

```text
.env.example
```

para:

```text
docs/.env
```

Depois preencha a variável:

```env
DATABASE_URL=postgresql://postgres.HOST:SENHA@aws-1-us-west-2.pooler.supabase.com:6543/postgres?sslmode=require
```

### 5. Preparar o banco

Execute os scripts SQL na ordem indicada pelos números:

```text
01_schema.sql
06_security_policies.sql
07_view_seguranca.sql
08_hardening_e_correlacao.sql
```

Depois execute o script de população da base.

### 6. Importar o MITRE ATT&CK

```bash
python src/ingest_mitre.py
```

### 7. Executar o detector

```bash
python src/security_detector.py
```

Os resultados serão gerados na pasta `reports`.

---

## 📄 Relatório

O pipeline gera automaticamente um relatório contendo:

- resumo executivo;
- transações sinalizadas;
- pseudônimos dos clientes;
- score de risco;
- probabilidade de suspeita;
- comparação dos modelos;
- métricas de validação;
- correlação com MITRE ATT&CK.

Arquivo gerado:

```text
reports/resultado_multimodelo/Relatorio_Incidente_SOC.pdf
```

---

## ⚠️ Limitações

Este projeto é uma prova de conceito baseada em dados sintéticos.

As principais limitações são:

- as anomalias foram simuladas;
- a base ainda não representa toda a diversidade de fraudes reais;
- os resultados não podem ser generalizados para ambiente produtivo;
- o parâmetro `contamination=0.15` influencia a quantidade de alertas;
- o classificador apresentou forte dependência do Z-Score;
- a regressão de severidade necessita de validação adicional;
- não foi realizada validação temporal;
- não há monitoramento de data drift ou concept drift.

---

## 🧾 Conclusão

A comparação mostrou que o Elliptic Envelope apresentou o melhor equilíbrio entre precision e recall na base sintética utilizada.

O Isolation Forest também apresentou bom desempenho e demonstrou maior flexibilidade para distribuições menos restritivas.

O resultado do Elliptic Envelope deve ser interpretado dentro do cenário experimental, pois esse modelo pressupõe que os dados normais possam ser representados por uma distribuição aproximadamente elíptica.

Por isso, a seleção atual representa o melhor resultado para esta base, não uma conclusão universal sobre detecção de fraudes.

---

## 🗺️ Roadmap

### ✅ v1.0.0 — Análise de Dados e Segurança

- preparação dos dados;
- engenharia de features;
- comparação entre detectores;
- geração de métricas e gráficos;
- PostgreSQL;
- relatório PDF;
- MITRE ATT&CK;
- pseudonimização e auditoria.

### ⏳ v2.0.0 — DevSecOps

- testes automatizados;
- análise estática;
- auditoria de dependências;
- Docker;
- GitHub Actions;
- scan de segurança;
- pipeline CI/CD.

### 🔮 v3.0.0 — Projeto final

- API REST;
- dashboard;
- autenticação;
- monitoramento;
- deploy.

---

## 👨‍💻 Autor

**Wellington Hikaru Kumagai**

Projeto desenvolvido durante o Bootcamp Bradesco - GenAI, Dados & Cyber.
