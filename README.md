# 🛡️ KUMA-LAB | SOC Transaction Anomaly Detector

**Evidence-grounded SOC investigation assistant for transaction anomaly analysis.**

[![CI](https://github.com/KUMA-LAB-1/soc-transaction-anomaly-detector/actions/workflows/ci.yml/badge.svg)](https://github.com/KUMA-LAB-1/soc-transaction-anomaly-detector/actions/workflows/ci.yml)

Projeto independente de **Cybersecurity, Detection Engineering, Machine Learning e investigação SOC**, desenvolvido dentro do **KUMA-LAB**.

A primeira versão nasceu durante um bootcamp de GenAI, Dados e Cybersecurity. Desde então, o projeto evoluiu de forma independente para se tornar um laboratório técnico incremental de engenharia de detecção, dados sintéticos, geração de evidências e apoio à investigação.

> **Status de versionamento**
>
> - Última release formal registrada: **v2.0.0**
> - Linha ativa de desenvolvimento: **V3**
> - Estado da V3: núcleo defensivo validado por testes automatizados e CI; linha V3 ainda em fechamento
> - PDF público versionado: relatório analítico atualizado em **08/09/2026**, já com correções de reporting realizadas na linha **V3**; os demais artefatos multimodelo permanecem históricos da **v2.0.0**
> - Camada conversacional com LLM: **integrada e avaliada formalmente** por contrato provider-neutral, adapter Gemini e interface Streamlit; experimento generativo controlado concluído e versionado
>
> O projeto continua sendo uma **prova de conceito baseada em dados sintéticos**. Não deve ser interpretado como sistema de detecção de fraude pronto para produção nem como mecanismo de confirmação automática de incidentes.

### 🧭 Leitura rápida

- [Arquitetura V3](#️-arquitetura-v3)
- [KUMA GUARD](#-kuma-guard---guarded-soc-assistant)
- [Evaluation Matrix](#-evaluation-matrix)
- [DevSecOps e segurança](#️-devsecops-e-segurança)
- [Estado da documentação](#-estado-da-documentação-e-fonte-de-verdade)
- [Artefatos públicos e reporting](#-artefatos-públicos-e-reporting)
- [Como executar](#️-como-executar)
- [Evolução do projeto](#️-evolução-do-projeto)

---

## 📌 O que este projeto faz

O projeto combina análise transacional, detecção de anomalias e investigação orientada por evidências para explorar como um SOC pode transformar sinais técnicos em contexto investigativo sem confundir suspeita com confirmação.

Entre as capacidades implementadas estão:

- preparação e validação de dados transacionais;
- engenharia de features comportamentais;
- geração sintética reproduzível com truth conhecida;
- cenários sintéticos, severidade, intensidade, população e diagnósticos estatísticos;
- classificação supervisionada para triagem;
- múltiplos detectores de anomalia;
- avaliação experimental e comparação de detectores;
- regressão de severidade;
- holdout e validação cruzada temporal;
- geração de alertas SOC estruturados;
- persistência opcional de alertas em JSONL ou SQLite;
- `EvidenceContext` para projetar evidências de um alerta sem reinterpretá-las;
- correlação MITRE ATT&CK com proveniência explícita da seleção;
- **KUMA GUARD - Guarded SOC Assistant**;
- contratos provider-neutral para integração com LLM;
- construção de contexto conversacional grounded a partir do `GuardedSocAssessment`;
- adapter Gemini via API REST;
- interface conversacional Streamlit para demonstração interativa;
- avaliação generativa formal com casos sintéticos, métricas automáticas, revisão humana e artefatos auditáveis;
- **Evaluation Matrix** independente para avaliar claims sem suporte e falsas confirmações;
- teste E2E do contrato defensivo da V3;
- geração de métricas, gráficos, CSV e JSON;
- geração de relatório PDF analítico de execução pelo pipeline;
- controles DevSecOps de qualidade, segurança, supply chain e container.

A implementação atual utiliza PostgreSQL/Supabase como infraestrutura principal de dados.

---

## 🧭 Princípio central: evidência antes de conclusão

O núcleo defensivo da V3 foi construído para preservar uma separação explícita entre fatos, lacunas de evidência, hipóteses e confirmação.

```text
evidência observada
        │
        ▼
      fato
        │
        ├───────────────┐
        │               │
        ▼               ▼
pode suportar       evidência ausente
uma hipótese             │
        │                ▼
        │        recommended check
        ▼
    hipótese
        │
        ▼
NÃO confirma incidente automaticamente
```

Em outras palavras:

- observado pode virar fato;
- ausente gera investigação;
- hipótese precisa de suporte explícito;
- score alto não confirma incidente;
- anomalia não confirma incidente;
- hipótese plausível não confirma incidente.

Esse contrato é o "truth firewall" do KUMA GUARD.

---

## 🏗️ Arquitetura V3

A V3 possui dois eixos complementares: o pipeline analítico e o eixo defensivo de investigação.

```text
Dados / geração sintética
          │
          ▼
Validação e preparação
          │
          ▼
Engenharia de features
          │
          ├── Classificação de triagem
          ├── Detectores de anomalia
          └── Regressão de severidade
          │
          ▼
Avaliação + validação temporal
          │
          ▼
Contrato de alerta SOC
          │
          ├──────────────► Persistência opcional
          │                 JSONL / SQLite
          │
          ▼
EvidenceContext
          │
          ▼
KUMA GUARD
GuardedSocAssessment
          │
          ├──────────────► Evaluation Matrix
          │                  │
          │                  ▼
          │              Auditoria de claims
          │              e confirmação
          │
          ▼
Conversation Context
          │
          ▼
LlmAdapter
          │
          ├──────────────► Gemini REST
          │
          ▼
Streamlit
          │
          ▼
Grounded Response

Trilha separada de enriquecimento contextual:
MITRE ATT&CK → seleção + provenance → reporting/contexto
```

O MITRE ATT&CK funciona como contexto de Threat Intelligence e mantém sua proveniência separada do `EvidenceContext`. O contexto de evidência projeta o alerta sem transformar enriquecimento externo em fato observado.

---

## 🧩 Componentes principais

| Componente | Responsabilidade |
| --- | --- |
| `src/security_detector.py` | Orquestra o pipeline analítico principal |
| `src/data/` | Acesso, validação e preparação estrutural dos dados |
| `src/features/` | Engenharia de features comportamentais |
| `src/models/` | Classificação, anomaly detection, regressão, benchmarks e validação |
| `src/synthetic/` | Geração sintética, truth, cenários, população, severidade, diagnósticos e benchmarks |
| `src/alerts/` | Contrato, geração, serialização, consulta e persistência de alertas |
| `src/evidence_context.py` | Projeção de um `Alert` em contexto de evidência sem reinterpretar seus dados |
| `src/threat_intel/` | Correlação e enriquecimento MITRE ATT&CK |
| `src/soc_assistant/assessment.py` | KUMA GUARD: fatos, hipóteses suportadas, evidência ausente e checks recomendados |
| `src/soc_assistant/evaluation.py` | Evaluation Matrix independente do runtime do assistente |
| `src/genai/` | Contratos de LLM, construção de contexto, orquestração conversacional, runtime e providers |
| `streamlit_app.py` | Interface conversacional demonstrável do KUMA GUARD |
| `src/reporting/` | Métricas, gráficos e relatório PDF analítico de execução |
| `.github/workflows/ci.yml` | Quality gates, testes, segurança, SBOM e container security |

---

## 🐻 KUMA GUARD - Guarded SOC Assistant

O **KUMA GUARD** recebe um `EvidenceContext` e constrói um `GuardedSocAssessment` com cinco dimensões explícitas:

- fatos observados;
- evidências ausentes;
- hipóteses suportadas;
- verificações recomendadas;
- estado de confirmação do incidente.

Por padrão:

```python
incident_confirmed = False
```

A camada conversacional usa esse assessment estruturado como autoridade factual. O LLM recebe contexto derivado do estado defensivo e atua como camada de linguagem e interação; ele não altera o estado de confirmação nem transforma hipótese, anomalia ou score em incidente confirmado.

A interface Streamlit mantém histórico visual da sessão. No estágio atual, cada nova pergunta continua sendo grounded no `GuardedSocAssessment` atual, sem tratar mensagens anteriores do chat como nova evidência factual.

Uma hipótese só pode ser adicionada quando declara quais fatos observados a suportam. Suporte vazio ou referência a fato não observado é rejeitado.

Exemplo conceitual:

```text
failed_logins = observado
new_device    = observado

        │
        ▼

possible_account_compromise
suportada por:
- failed_logins
- new_device

        │
        ▼

continua sendo hipótese
```

---

## 🧪 Evaluation Matrix

A Evaluation Matrix funciona como um avaliador independente do resultado do KUMA GUARD.

O núcleo atual mede:

- quantidade de hipóteses;
- hipóteses sem suporte observável;
- `unsupported_claim_rate`;
- falsas confirmações quando existe truth externa;
- `false_confirmation_rate`;
- agregação de múltiplas avaliações;
- execução de cenários de avaliação.

Quando a truth de confirmação não existe, o evaluator preserva a ausência de informação:

```text
false_confirmation_rate = None
```

Ele não converte "truth ausente" em uma falsa certeza numérica.

---

## 🎯 MITRE ATT&CK e provenance

A correlação MITRE utiliza sinais como:

- múltiplas falhas de login;
- dispositivo novo;
- alteração de limite;
- mudança de localização;
- tipo de transação como fallback.

O enriquecimento MITRE retorna também **por que** um candidato foi selecionado e **de onde** o conhecimento foi resolvido.

Entre os campos de provenance estão:

- `selection_basis`: base utilizada para selecionar o candidato;
- `knowledge_source`: fonte que resolveu o conhecimento;
- `fallback_reason`: motivo pelo qual um fallback foi necessário.

Quando uma família MITRE não é resolvida pelo catálogo local, o sistema preserva o candidato como **não resolvido**, em vez de inventar uma técnica terminal.

O mapeamento MITRE é contexto investigativo. Ele não representa confirmação automática de ataque.

---

## ⏱️ Validação temporal

A V3 possui infraestrutura de validação temporal para os modelos, com:

- holdout temporal;
- folds temporais com janela de treino expansiva;
- suporte a `gap`;
- tratamento de timestamps empatados nas fronteiras;
- avaliação em período posterior ao treino após fit no passado;
- integração com features históricas causais.

No fluxo operacional atual do `SecurityDetector`:

- **classificação** solicita validação temporal explicitamente;
- **regressão** solicita validação temporal explicitamente;
- a API de **detecção de anomalias** suporta avaliação temporal, mas o fluxo operacional ainda usa o modo `in_sample` padrão nessa etapa.

Conceitualmente:

```text
passado
   │
   ▼
treino
   │
   ▼
fronteira temporal
   │
   ▼
futuro
   │
   ▼
avaliação
```

Essa infraestrutura corrige uma limitação presente em versões anteriores e reduz risco de leakage temporal onde a estratégia temporal é aplicada.

---

## 🧬 Dados sintéticos

Os datasets utilizados são **sintéticos** e destinados a experimentação, testes e validação arquitetural.

A V3 possui uma camada dedicada em `src/synthetic/` para controlar e diagnosticar aspectos como:

- população;
- cenários;
- intensidade;
- severidade;
- efeitos de cenário;
- observáveis;
- flags comportamentais;
- política de labels;
- estratégia de seeds;
- composição;
- truth;
- qualidade estatística;
- comparação entre datasets;
- benchmark e estabilidade.

Nos modelos não supervisionados, a truth sintética não é usada como target de treinamento. Ela é consumida posteriormente para avaliação retrospectiva e experimentação controlada.

---

## 🤖 Modelos analíticos

### Classificação supervisionada

O classificador operacional de triagem utiliza `DecisionTreeClassifier`. No fluxo do `SecurityDetector`, sua avaliação solicita validação temporal explicitamente.

A zona experimental de benchmark permanece separada do caminho operacional e compara candidatos como `DecisionTree`, `LogisticRegression` e `RandomForest` sob contratos comuns. Resultado de benchmark **não promove automaticamente** um challenger para uso operacional.

### Detecção de anomalias

O projeto trabalha com múltiplos detectores:

| Modelo | Papel experimental |
| --- | --- |
| Isolation Forest | Isolamento de observações incomuns por particionamento |
| Local Outlier Factor | Desvio em relação à densidade local |
| One-Class SVM | Fronteira de comportamento normal |
| Elliptic Envelope | Região robusta baseada em covariância |

O pipeline separa `melhor_detector_benchmark` de `detector_operacional`: benchmark mede desempenho retrospectivo; a escolha operacional permanece explícita.

### Regressão de severidade

A regressão operacional utiliza `LinearRegression` e limita o score produzido à faixa `[0, 100]`. No `SecurityDetector`, a avaliação usa validação temporal explícita.

O contrato atual inclui sinais comportamentais como `dispositivo_novo_flag`, `alteracao_limite_flag` e `mudanca_localizacao_flag`, mantendo compatibilidade com datasets legados quando esses campos não existem.

A regressão permanece experimental e deve ser interpretada dentro das limitações dos dados sintéticos.

---

## 🛡️ DevSecOps e segurança

O pipeline de CI aplica controles em diferentes superfícies.

```text
Código
  ├── Ruff
  ├── Pytest
  ├── Coverage
  └── Bandit

Dependências
  ├── uv.lock
  ├── pip-audit
  ├── CycloneDX SBOM
  └── Dependabot

Repositório
  └── Gitleaks

Container
  ├── multi-stage build
  ├── runtime non-root
  ├── exclusão de secrets
  └── Trivy
```

Também são aplicados:

- GitHub Actions fixadas por commit SHA;
- `GITHUB_TOKEN` com menor privilégio;
- timeouts explícitos;
- concurrency;
- security gate para vulnerabilidades HIGH/CRITICAL corrigíveis no container;
- separação entre runtime e ferramentas de desenvolvimento;
- credenciais fora do código;
- hardening PostgreSQL/Supabase;
- RLS e least privilege;
- separação entre runtime SOC, Threat Intelligence e auditoria.

### Último checkpoint técnico validado da linha V3

Em **21/09/2026**, durante o fechamento local do bloco de avaliação generativa formal da V3:

- **1513 testes** aprovados;
- **98,66%** de coverage total;
- Ruff lint aprovado;
- Ruff format check aprovado;
- diff-check aprovado.

Esse checkpoint pertence à branch de avaliação generativa antes de sua integração à `main`. A validação de CI do Pull Request continua sendo necessária antes do merge.

---

## 🔗 E2E defensivo da V3

O contrato de integração da linha V3 atravessa:

```text
Alert
  │
  ▼
EvidenceContext
  │
  ▼
KUMA GUARD
  │
  ▼
SupportedHypothesis
  │
  ▼
Evaluation Matrix
```

O teste E2E valida que:

- os fatos vêm das evidências observadas;
- evidências ausentes geram checks recomendados;
- hipóteses carregam suporte explícito;
- o incidente não é confirmado automaticamente;
- o evaluator independente não detecta claim sem suporte no cenário válido;
- a truth externa permite avaliar falsa confirmação.

Arquivo:

```text
tests/integration/test_kuma_guard_e2e.py
```

---

## 📂 Estrutura do repositório

Visão de alto nível:

```text
.
├── .github/
│   └── workflows/
├── database/
│   ├── queries/
│   ├── schema/
│   └── seeds/
├── docs/
│   ├── architecture/
│   └── devsecops/
├── reports/
│   └── resultado_multimodelo/
├── src/
│   ├── alerts/
│   ├── data/
│   ├── features/
│   ├── genai/
│   ├── models/
│   ├── reporting/
│   ├── soc_assistant/
│   ├── synthetic/
│   ├── threat_intel/
│   ├── evidence_context.py
│   ├── ingest_mitre.py
│   └── security_detector.py
├── tests/
│   ├── integration/
│   └── unit/
├── Dockerfile
├── CHANGELOG.md
├── streamlit_app.py
├── pyproject.toml
├── README.md
└── uv.lock
```

---

## 📚 Estado da documentação e fonte de verdade

Nem todo artefato do repositório representa a mesma geração do projeto. Para evitar mistura entre a V3 ativa e snapshots históricos, a leitura pública deve seguir esta hierarquia:

| Superfície | Papel atual | Estado |
| --- | --- | --- |
| `README.md` | visão pública, escopo, capacidades e status da linha ativa | **V3 atual** |
| `docs/architecture/` | documentação técnica detalhada da arquitetura | documentação existente; parcialmente desatualizada em relação à V3 atual |
| `docs/devsecops/` | documentação dos controles de qualidade e segurança | documentação técnica complementar; código e CI continuam sendo a referência executável |
| `docs/bootcamp/` | documentação e evidências da camada GenAI desenvolvida no contexto do bootcamp | inclui agente, base de conhecimento, prompts e avaliação generativa formal |
| `reports/resultado_multimodelo/` | artefatos públicos de reporting | PDF analítico atualizado em 08/09/2026 com correções de reporting da V3; CSV, JSON e gráficos permanecem históricos da v2.0.0 |
| `src/reporting/pdf_report.py` | gerador atual de relatório analítico de execução | origem do formato do PDF analítico atual; não é sistema de case management nem trilha operacional completa |

A regra de documentação da linha V3 é simples: **não promover um artefato histórico a “V3” apenas porque o código ao redor evoluiu**. Quando houver divergência entre documentação, código e comportamento executável, código, testes e CI atuais são a referência técnica principal.

---

## 📚 Documentação técnica

### Arquitetura

- [Visão geral](docs/architecture/overview.md)
- [Pipeline](docs/architecture/pipeline.md)
- [Modelos e validação](docs/architecture/ml-models.md)

### DevSecOps

- [Visão geral](docs/devsecops/overview.md)
- [Pipeline de CI](docs/devsecops/ci-pipeline.md)
- [Controles de segurança](docs/devsecops/security-controls.md)
- [Software supply chain](docs/devsecops/supply-chain.md)
- [Container security](docs/devsecops/container-security.md)

### GenAI / Bootcamp

- [Documentação do agente](docs/bootcamp/01-documentacao-agente.md)
- [Base de conhecimento](docs/bootcamp/02-base-conhecimento.md)
- [Prompts](docs/bootcamp/03-prompts.md)
- [Avaliação generativa formal](docs/bootcamp/04-avaliacao-generativa.md)

Os documentos de arquitetura existentes ainda não refletem integralmente todas as mudanças da linha V3; por isso, devem ser lidos em conjunto com o código, testes e este README.

---

## 📦 Artefatos públicos e reporting

A pasta `reports/resultado_multimodelo/` reúne artefatos públicos de momentos distintos do projeto. O PDF analítico foi atualizado em **08/09/2026**, enquanto CSV, JSON, gráficos e histórico de métricas permanecem preservados como artefatos da **v2.0.0**.

Isso inclui:

- [Relatório SOC - execução analítica pública atualizada em 08/09/2026](reports/resultado_multimodelo/Relatorio_Incidente_SOC.pdf)
- [Comparação dos detectores em CSV](reports/resultado_multimodelo/comparacao_detectores.csv)
- [Comparação dos detectores em JSON](reports/resultado_multimodelo/comparacao_detectores.json)
- gráficos analíticos da execução v2.0.0;
- histórico de métricas daquele snapshot.

> **Importante:** o PDF público atual foi atualizado a partir da execução de **08/09/2026** e já incorpora correções realizadas na linha **V3** no gerador de PDF, incluindo o ajuste de conteúdo em tabelas para manter identificadores/pseudônimos dentro das células em vez de ultrapassar suas bordas. Ele continua sendo um **relatório analítico de execução** e, isoladamente, não representa toda a arquitetura nem o contrato defensivo integral da V3.

### Gerador atual

O pipeline atual utiliza `src/reporting/pdf_report.py` para produzir um relatório analítico de execução com métricas, alertas, severidade e contexto MITRE.

Por padrão, uma execução pode escrever:

```text
reports/Relatorio_Incidente_SOC.pdf
```

Esse arquivo representa **aquela execução do pipeline**. Uma nova execução local não é automaticamente promovida para `reports/resultado_multimodelo/` e o PDF não deve ser tratado como estado vivo de uma investigação.

No estado atual do projeto, ainda não existe um workflow completo de case management ou reporting operacional para SOC que defina, por exemplo, lifecycle de investigação, revisões, handoff entre analistas ou histórico documental imutável.

O PDF deve ser entendido como **uma representação analítica derivada dos dados e resultados disponíveis**, não como banco operacional ou fonte primária de verdade.

### Snapshot visual v2.0.0

![Comparação histórica dos detectores](reports/resultado_multimodelo/comparacao_detectores.png)

![Importância histórica das features](reports/resultado_multimodelo/importancia_features_classificador.png)

---

## ⚙️ Como executar

### 1. Clonar

```bash
git clone https://github.com/KUMA-LAB-1/soc-transaction-anomaly-detector.git
cd soc-transaction-anomaly-detector
```

### 2. Sincronizar o runtime

Requer Python **3.12** e `uv`.

```bash
uv sync --locked
```

### 3. Ambiente de desenvolvimento em paridade com o CI

```bash
uv sync --locked --group lint --group test --group security
```

### 4. Configurar o ambiente

Copie `.env.example` para `.env` e configure as conexões necessárias.

Principais variáveis:

- `SOC_DATABASE_URL`: runtime do pipeline SOC;
- `MITRE_DATABASE_URL`: ingestão de Threat Intelligence;
- `SOC_PIPELINE_USER`: identidade lógica de auditoria;
- `ALERT_STORAGE`: backend opcional para persistência dos alertas;
- `GEMINI_API_KEY`: credencial local para a demo conversacional;
- `GEMINI_MODEL`: modelo Gemini utilizado pelo adapter, com `gemini-3.8-flash` como padrão atual.

O arquivo `.env` não deve ser versionado. A interface Streamlit atual lê a configuração GenAI do ambiente do processo; o `.env.example` serve como referência segura e não deve conter credenciais reais.

### 5. Preparar PostgreSQL/Supabase

Execute os scripts em `database/schema/` na ordem numérica e carregue os seeds necessários em `database/seeds/`.

As consultas em `database/queries/forensic_investigation.sql` são destinadas a investigação privilegiada e não fazem parte do fluxo normal de inicialização.

### 6. Ingestão MITRE ATT&CK

```bash
uv run python src/ingest_mitre.py
```

### 7. Executar o pipeline principal

```bash
uv run python -m src.security_detector
```

> O pipeline pode gerar `reports/Relatorio_Incidente_SOC.pdf`. Esse arquivo é um **relatório analítico da execução atual** e não é automaticamente promovido para o artefato público versionado em `reports/resultado_multimodelo/`. Ele também não representa um sistema completo de case management.

### 8. Executar a interface conversacional

A demo usa um cenário sintético canônico. Sem `GEMINI_API_KEY`, a interface continua abrindo em modo seguro e informa que a configuração está ausente. Para conversar com o provider Gemini, exponha a chave apenas no ambiente local.

No PowerShell:

```powershell
$env:GEMINI_API_KEY = "<SUA_CHAVE_LOCAL>"
$env:GEMINI_MODEL = "gemini-3.8-flash"

uv run streamlit run streamlit_app.py
```

A chave não deve ser adicionada ao Git nem registrada em arquivos públicos.

### 9. Executar a suíte global

```bash
uv run pytest
```

### 10. Quality gates locais

```bash
uv run ruff check .
uv run ruff format --check .
git diff --check
```

---

## ⚠️ Limitações atuais

Este projeto continua sendo uma prova de conceito.

Principais limitações:

- datasets e incidentes são sintéticos;
- resultados experimentais não podem ser generalizados diretamente para produção;
- o pipeline não está conectado a um SOC real;
- ainda não existem conectores operacionais de SIEM, EDR ou XDR;
- KUMA GUARD não confirma incidentes automaticamente;
- a interface conversacional atual é uma demo Streamlit baseada em cenário sintético e integração Gemini;
- o histórico do chat é visual; ainda não existe memória conversacional semântica incorporada ao estado factual da investigação;
- a avaliação generativa formal foi executada em cinco cenários sintéticos controlados; seus resultados não devem ser generalizados para todos os cenários SOC, modelos ou providers;
- a regressão de severidade permanece experimental;
- ainda não existe monitoramento operacional de data drift ou concept drift;
- o backend atual utiliza PostgreSQL/Supabase;
- o PDF público disponível é um relatório analítico de execução atualizado em 08/09/2026, já incorpora correções de reporting da V3, mas não representa sozinho o contrato completo da V3;
- o gerador atual de PDF produz relatório analítico de execução, mas ainda não existe case management/reporting operacional completo.

---

## 🗺️ Evolução do projeto

### ✅ v1.0.0 - Análise de Dados e Segurança

- preparação e validação de dados;
- engenharia de features;
- modelos analíticos;
- PostgreSQL/Supabase;
- MITRE ATT&CK;
- relatório PDF;
- pseudonimização e auditoria.

### ✅ v2.0.0 - DevSecOps e arquitetura modular

- modularização;
- testes automatizados;
- CI/CD;
- Ruff;
- Bandit;
- pip-audit;
- Gitleaks;
- CycloneDX SBOM;
- Docker;
- Trivy;
- RLS e least privilege;
- persistência estruturada de alertas;
- documentação de arquitetura e DevSecOps.

### 🚧 V3 - Linha ativa

Já implementado e validado:

- Core Integrity Checkpoint;
- Evidence Context Foundation;
- MITRE Provenance Foundation;
- KUMA GUARD - Guarded SOC Assistant MVP;
- Evaluation Matrix V3;
- E2E do contrato defensivo;
- contrato provider-neutral para LLM;
- builder de contexto grounded e `ConversationService`;
- adapter Gemini via API REST;
- interface conversacional Streamlit com testes de integração;
- avaliação generativa formal com cinco cenários sintéticos, métricas automáticas, revisão humana e artefatos auditáveis.

A V3 ainda não foi publicada como nova release formal. O estado público atual deve ser interpretado pelos contratos, testes, CI e limitações documentadas neste README.

---

## 🔎 Rastreabilidade da evolução V3

Alguns checkpoints principais da linha V3 foram integrados por Pull Requests separados:

- [PR #56 - Evidence Context Foundation](https://github.com/KUMA-LAB-1/soc-transaction-anomaly-detector/pull/56)
- [PR #57 - MITRE Provenance Foundation](https://github.com/KUMA-LAB-1/soc-transaction-anomaly-detector/pull/57)
- [PR #58 - KUMA GUARD MVP](https://github.com/KUMA-LAB-1/soc-transaction-anomaly-detector/pull/58)
- [PR #59 - Evaluation Matrix V3](https://github.com/KUMA-LAB-1/soc-transaction-anomaly-detector/pull/59)
- [PR #65 - E2E do contrato defensivo](https://github.com/KUMA-LAB-1/soc-transaction-anomaly-detector/pull/65)
- [PR #69 - Contrato provider-neutral para LLM](https://github.com/KUMA-LAB-1/soc-transaction-anomaly-detector/pull/69)
- [PR #70 - Fundação conversacional GenAI](https://github.com/KUMA-LAB-1/soc-transaction-anomaly-detector/pull/70)

A estratégia de evolução privilegia mudanças pequenas, contratos explícitos, testes, revisão e validação antes de expandir o escopo.

---

## 👨‍💻 Autor

**Wellington Hikaru Kumagai**

Projeto independente do **KUMA-LAB**.

A primeira versão nasceu durante um bootcamp de GenAI, Dados e Cybersecurity. Desde então, o projeto evoluiu de forma independente dentro do KUMA-LAB.
