# 🛡️ KUMA-LAB | SOC Transaction Anomaly Detector

**Evidence-grounded SOC investigation assistant for transaction anomaly analysis.**

[![CI](https://github.com/KUMA-LAB-1/soc-transaction-anomaly-detector/actions/workflows/ci.yml/badge.svg)](https://github.com/KUMA-LAB-1/soc-transaction-anomaly-detector/actions/workflows/ci.yml)

Projeto independente de **Cybersecurity, Detection Engineering, Machine Learning e investigação SOC**, desenvolvido dentro do **KUMA-LAB**.

A primeira versão nasceu durante um bootcamp de GenAI, Dados e Cybersecurity. Desde então, o projeto evoluiu de forma independente para se tornar um laboratório técnico incremental de engenharia de detecção, dados sintéticos, geração de evidências e apoio à investigação.

> **Status de versionamento**
>
> - Última release formal registrada: **v2.0.0**
> - Linha ativa de desenvolvimento: **V3**
> - Estado da V3: núcleo defensivo certificado; documentação, arquitetura pública e pitch técnico em fechamento
> - README público: alinhado à linha V3
> - PDF público versionado: ainda é o snapshot histórico da **v2.0.0**
>
> O projeto continua sendo uma **prova de conceito baseada em dados sintéticos**. Não deve ser interpretado como sistema de detecção de fraude pronto para produção nem como mecanismo de confirmação automática de incidentes.

### 🧭 Leitura rápida

- [Arquitetura V3](#️-arquitetura-v3)
- [KUMA GUARD](#-kuma-guard---guarded-soc-assistant)
- [Evaluation Matrix](#-evaluation-matrix)
- [DevSecOps e segurança](#️-devsecops-e-segurança)
- [Estado da documentação](#-estado-da-documentação-e-fonte-de-verdade)
- [Artefatos públicos e estratégia do PDF](#-artefatos-públicos-e-estratégia-do-pdf)
- [Como executar](#️-como-executar)
- [Roadmap](#️-roadmap)

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
- **Evaluation Matrix** independente para avaliar claims sem suporte e falsas confirmações;
- teste E2E do contrato defensivo da V3;
- geração de métricas, gráficos, CSV e JSON;
- geração de relatório PDF analítico pelo pipeline legado, ainda não equivalente ao snapshot documental da V3;
- controles DevSecOps de qualidade, segurança, supply chain e container.

A implementação atual utiliza PostgreSQL/Supabase como infraestrutura principal de dados. A evolução arquitetural busca limitar o acoplamento ao fornecedor e manter contratos que permitam adapters e integrações futuras.

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
          ├──────────────► MITRE ATT&CK
          │                 seleção + provenance
          │
          ▼
EvidenceContext
          │
          ▼
KUMA GUARD
GuardedSocAssessment
          │
          ▼
Evaluation Matrix
          │
          ▼
Auditoria de claims
e confirmação
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
| `src/reporting/` | Métricas, gráficos e relatório PDF analítico legado; a consolidação documental V3 é uma trilha separada |
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

A V3 registra também **por que** um candidato foi selecionado e **de onde** o conhecimento foi resolvido.

Entre os campos de provenance estão:

- `selection_basis`: base utilizada para selecionar o candidato;
- `knowledge_source`: fonte que resolveu o conhecimento;
- `fallback_reason`: motivo pelo qual um fallback foi necessário.

Quando uma família MITRE não é resolvida pelo catálogo local, o sistema preserva o candidato como **não resolvido**, em vez de inventar uma técnica terminal.

O mapeamento MITRE é contexto investigativo. Ele não representa confirmação automática de ataque.

---

## ⏱️ Validação temporal

A V3 já implementa validação temporal.

O projeto possui:

- holdout temporal;
- folds temporais com janela de treino expansiva;
- suporte a `gap`;
- tratamento de timestamps empatados nas fronteiras;
- avaliação futura dos detectores após fit no passado;
- integração com features históricas causais.

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

Isso corrige uma limitação presente em versões anteriores do projeto e reduz risco de leakage temporal.

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

O pipeline possui classificação supervisionada voltada à triagem e análise das features associadas às decisões históricas representadas no dataset.

### Detecção de anomalias

O projeto trabalha com múltiplos detectores, incluindo:

| Modelo | Papel experimental |
| --- | --- |
| Isolation Forest | Isolamento de observações incomuns por particionamento |
| Local Outlier Factor | Desvio em relação à densidade local |
| One-Class SVM | Fronteira de comportamento normal |
| Elliptic Envelope | Região robusta baseada em covariância |

A seleção experimental compara métricas comuns em vez de assumir um detector universalmente superior.

### Regressão de severidade

A regressão estima um score de severidade em uma escala de risco. Essa etapa permanece experimental e deve ser interpretada dentro das limitações do dataset sintético.

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

### Último checkpoint certificado da linha V3

Em **18/09/2026**, após o E2E defensivo e a rodada de atualizações de dependências:

- **1456 testes** aprovados;
- **99,00%** de coverage total;
- Ruff lint aprovado;
- Ruff format check aprovado;
- diff-check aprovado;
- CI com Quality + Unit Tests, Integration Smoke, Secret Scanning, SBOM e Container Security aprovados.

Esses números representam um checkpoint do desenvolvimento e podem evoluir com novos commits.

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
| `docs/architecture/` | documentação técnica detalhada da arquitetura | base existente em consolidação para refletir integralmente a V3 |
| `docs/devsecops/` | documentação dos controles de qualidade e segurança | documentação técnica complementar; código e CI continuam sendo a referência executável |
| `reports/resultado_multimodelo/` | artefatos públicos de uma execução certificada anterior | **snapshot histórico v2.0.0** |
| `src/reporting/pdf_report.py` | gerador de relatório analítico de execução | formato legado do pipeline; ainda não representa o contrato defensivo completo da V3 |

A regra de documentação da linha V3 é simples: **não promover um artefato histórico a “V3” apenas porque o código ao redor evoluiu**. O snapshot V3 só será publicado quando conteúdo, proveniência, validação e identidade de versão estiverem sincronizados.

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

A documentação de arquitetura será consolidada para refletir integralmente o eixo defensivo da V3 antes do **V3 Completion Gate**.

---

## 📦 Artefatos públicos e estratégia do PDF

Os arquivos em `reports/resultado_multimodelo/` formam um **snapshot experimental público e congelado da v2.0.0**, preservado para histórico, auditoria e reprodutibilidade.

Isso inclui:

- [Relatório SOC v2.0.0 - snapshot histórico em PDF](reports/resultado_multimodelo/Relatorio_Incidente_SOC.pdf)
- [Comparação dos detectores em CSV](reports/resultado_multimodelo/comparacao_detectores.csv)
- [Comparação dos detectores em JSON](reports/resultado_multimodelo/comparacao_detectores.json)
- gráficos analíticos da execução v2.0.0;
- histórico de métricas daquele snapshot.

> **Importante:** o PDF público atual foi gerado em **21/08/2026** e **não representa a arquitetura completa da V3**. Ele não documenta `EvidenceContext`, MITRE provenance, KUMA GUARD, Evaluation Matrix ou o E2E defensivo.

### Dois artefatos diferentes

A V3 passa a distinguir explicitamente dois conceitos que antes ficavam misturados:

1. **Relatório de execução analítica**  
   É produzido pelo pipeline atual por `src/reporting/pdf_report.py`. Resume métricas, anomalias, severidade e correlação MITRE daquela execução. O formato ainda é herdado da linha v2 e não deve ser apresentado como documentação completa da V3.

2. **Snapshot documental da versão**  
   É o artefato público que representa um checkpoint certificado do projeto. Deve registrar arquitetura, contratos defensivos, proveniência, validações, limitações e evidências de qualidade da versão publicada.

Essa separação evita que uma execução recente gere um PDF com aparência de “versão atual” sem conter os contratos defensivos que definem a V3.

### Comportamento do gerador atual

Ao executar o pipeline completo, o código ainda pode gerar:

```text
reports/Relatorio_Incidente_SOC.pdf
```

Esse arquivo é **output de execução**, não substitui automaticamente o snapshot histórico em `reports/resultado_multimodelo/` e, no estado atual do gerador, **não deve ser promovido ou commitado como relatório V3**.

### Estratégia para o snapshot V3

O snapshot v2.0.0 será preservado sem sobrescrita. A publicação da V3 deve utilizar um diretório versionado próprio, por exemplo:

```text
reports/
├── resultado_multimodelo/        # snapshot histórico v2.0.0
└── snapshots/
    └── v3.0.0/                   # futuro snapshot certificado V3
```

O relatório V3 deverá nascer de um contrato de reporting atualizado e incluir, no mínimo:

- versão e checkpoint de origem;
- metadados reproduzíveis da execução/dataset sintético;
- métricas analíticas e validação temporal;
- contrato de alertas;
- `EvidenceContext`;
- proveniência MITRE ATT&CK;
- avaliação do KUMA GUARD;
- métricas da Evaluation Matrix;
- resultado do E2E defensivo e quality gates relevantes;
- limitações e distinção explícita entre fato, hipótese e confirmação.

A sequência planejada passa a ser:

```text
arquitetura V3 consolidada
        │
        ▼
contrato de reporting V3
        │
        ▼
gerador V3 desacoplado do formato legado
        │
        ▼
checkpoint funcional certificado
        │
        ▼
snapshot versionado
        │
        ▼
validação visual + técnica
        │
        ▼
publicação
```

Até essa etapa, resultados numéricos e gráficos em `reports/resultado_multimodelo/` devem ser lidos exclusivamente como resultados históricos da v2.0.0.

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
- `ALERT_STORAGE`: backend opcional para persistência dos alertas.

O arquivo `.env` não deve ser versionado.

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

> O pipeline pode gerar `reports/Relatorio_Incidente_SOC.pdf`. No estado atual, esse PDF é um **relatório analítico de execução no formato legado**, não o snapshot documental V3. Não o trate como substituto do relatório público versionado.

### 8. Executar a suíte global

```bash
uv run pytest
```

### 9. Quality gates locais

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
- a Evaluation Matrix atual cobre um núcleo de métricas de segurança e não pretende representar uma avaliação completa de agentes;
- a regressão de severidade permanece experimental;
- ainda não existe monitoramento operacional de data drift ou concept drift;
- o backend atual utiliza PostgreSQL/Supabase e a camada de adapters multi-backend é uma evolução futura;
- o PDF público disponível ainda é o snapshot histórico da v2.0.0, e o gerador PDF do pipeline ainda usa o formato analítico legado;
- frontend / Visual SOC Console permanece fora do núcleo atual da V3.

---

## 🗺️ Roadmap

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

Concluído:

- Core Integrity Checkpoint;
- Evidence Context Foundation;
- MITRE Provenance Foundation;
- KUMA GUARD - Guarded SOC Assistant MVP;
- Evaluation Matrix V3;
- E2E do contrato defensivo.

Em fechamento:

- README e identidade pública;
- consolidação da arquitetura V3;
- pitch técnico / portfólio;
- contrato de reporting V3, novo snapshot documental e relatório V3 versionado;
- V3 Completion Gate.

### 🔭 Pós-V3 / V3.1+

Possíveis evoluções, guiadas por necessidade e evidência:

- adapters para SIEM, EDR e XDR;
- laboratório com ferramentas open source;
- novos cenários e replay de investigação;
- Continuous Bug Hunter / Quality Sentinel;
- KUMA DEF como ecossistema defensivo mais amplo;
- Visual SOC Console read-only após boundary/API estável;
- novos backends de dados por adapters;
- métricas adicionais para avaliação de investigação e agentes.

---

## 🔎 Rastreabilidade da evolução V3

Alguns checkpoints principais da linha V3 foram integrados por Pull Requests separados:

- [PR #56 - Evidence Context Foundation](https://github.com/KUMA-LAB-1/soc-transaction-anomaly-detector/pull/56)
- [PR #57 - MITRE Provenance Foundation](https://github.com/KUMA-LAB-1/soc-transaction-anomaly-detector/pull/57)
- [PR #58 - KUMA GUARD MVP](https://github.com/KUMA-LAB-1/soc-transaction-anomaly-detector/pull/58)
- [PR #59 - Evaluation Matrix V3](https://github.com/KUMA-LAB-1/soc-transaction-anomaly-detector/pull/59)
- [PR #65 - E2E do contrato defensivo](https://github.com/KUMA-LAB-1/soc-transaction-anomaly-detector/pull/65)

A estratégia de evolução privilegia mudanças pequenas, contratos explícitos, testes, revisão e certificação antes de expandir o escopo.

---

## 👨‍💻 Autor

**Wellington Hikaru Kumagai**

Projeto independente do **KUMA-LAB**.

A primeira versão nasceu durante um bootcamp de GenAI, Dados e Cybersecurity. Desde então, o projeto evoluiu de forma independente dentro do KUMA-LAB.
