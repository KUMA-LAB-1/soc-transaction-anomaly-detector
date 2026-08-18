# Visão Geral da Arquitetura DevSecOps

## 1. Objetivo

A arquitetura DevSecOps do `soc-transaction-anomaly-detector` integra controles
de qualidade, segurança e software supply chain diretamente ao ciclo de
desenvolvimento.

O objetivo não é depender de uma única ferramenta de segurança, mas aplicar
múltiplas camadas complementares de validação e proteção.

A estratégia atual combina controles voltados a:

- qualidade de código;
- testes automatizados;
- cobertura;
- Static Application Security Testing (SAST);
- Software Composition Analysis (SCA);
- secret scanning;
- Software Bill of Materials (SBOM);
- hardening de containers;
- vulnerability scanning;
- segurança da própria infraestrutura de CI;
- manutenção controlada de dependências.

---

## 2. Princípio geral

A arquitetura segue uma abordagem de Defense in Depth.

Nenhum scanner ou controle individual é tratado como garantia suficiente de
segurança.

Em vez disso, diferentes mecanismos atuam sobre superfícies distintas:

```text
Código
  │
  ├── qualidade
  ├── testes
  └── SAST
  │
Dependências
  │
  ├── locking
  ├── SCA
  ├── SBOM
  └── update monitoring
  │
Repositório
  │
  └── secret scanning
  │
CI
  │
  ├── least privilege
  ├── immutable Actions
  ├── timeouts
  └── concurrency
  │
Container
  │
  ├── multi-stage build
  ├── non-root runtime
  ├── secret exclusion
  └── vulnerability scanning
```

Essas camadas possuem funções complementares de prevenção, detecção, evidência,
enforcement e manutenção.

---

## 3. Fluxo DevSecOps

O fluxo atual pode ser representado, de forma simplificada, como:

```text
Alteração de código
       │
       ▼
Ruff
       │
       ▼
Pytest + Coverage Gate
       │
       ▼
Bandit SAST
       │
       ▼
pip-audit / SCA
       │
       ▼
Gitleaks
       │
       ▼
CycloneDX SBOM
       │
       ▼
Docker Build
       │
       ▼
Runtime Validation
       │
       ▼
Trivy Scan
       │
       ▼
Container Security Gate
```

Nem todas as etapas representam exatamente um único job sequencial.

O diagrama representa a lógica de cobertura dos controles.

---

## 4. Categorias de controles

Os controles do projeto podem ser agrupados em cinco funções principais.

### Prevention

Controles que procuram reduzir a probabilidade de uma condição insegura ser
introduzida.

Exemplos:

- least privilege;
- execução non-root;
- exclusão de secrets da imagem;
- SHA pinning;
- dependency locking;
- separação entre build e runtime.

### Detection

Controles destinados a identificar condições potencialmente inseguras.

Exemplos:

- Bandit;
- pip-audit;
- Gitleaks;
- Trivy.

### Evidence

Controles ou artifacts que registram informações utilizadas para auditoria e
rastreabilidade.

Exemplos:

- CycloneDX SBOM;
- Trivy JSON report;
- resultados dos scanners;
- histórico de métricas;
- artifacts publicados pelo CI.

### Enforcement

Controles que podem impedir a integração ou continuidade do pipeline quando
determinada política é violada.

Exemplos:

- coverage gate;
- falha nos testes;
- falha do SAST;
- falha da auditoria de dependências;
- secret scanning;
- Trivy security gate para vulnerabilidades corrigíveis HIGH/CRITICAL.

### Maintenance

Controles responsáveis por reduzir o risco de dependências permanecerem
desatualizadas indefinidamente.

Exemplo:

- Dependabot.

---

## 5. Quality Engineering

Antes dos controles específicos de segurança, o pipeline valida qualidade e
comportamento funcional.

As principais ferramentas são:

```text
Ruff
Pytest
Coverage
```

Ruff verifica padrões de lint e formatação.

Pytest executa testes unitários e de integração.

Coverage mede a quantidade de código exercitada pelos testes.

O projeto também utiliza um coverage gate mínimo, impedindo regressões abaixo da
política definida.

Esses controles não são ferramentas de segurança por si só, mas aumentam a
confiabilidade da base sobre a qual os demais mecanismos atuam.

---

## 6. Static Application Security Testing

Bandit é utilizado como ferramenta de Static Application Security Testing
(SAST).

Sua função é analisar o código Python em busca de padrões conhecidos que possam
representar implementações potencialmente inseguras.

O escopo principal é:

```text
src/
```

O Bandit não substitui testes funcionais, SCA, secret scanning ou análise do
runtime.

Ele representa uma camada específica voltada ao código desenvolvido no projeto.

---

## 7. Software Composition Analysis

`pip-audit` é utilizado para verificar dependências Python em busca de
vulnerabilidades conhecidas.

Essa análise complementa o SAST.

A diferença conceitual é:

```text
Bandit
  ↓
código próprio

pip-audit
  ↓
dependências externas
```

Um resultado limpo no `pip-audit` significa apenas que nenhuma vulnerabilidade
conhecida foi identificada no conjunto auditado naquele momento.

---

## 8. Secret Scanning

Gitleaks é utilizado para analisar o histórico Git em busca de possíveis
credenciais ou secrets expostos.

A análise utiliza histórico completo do repositório.

Isso é importante porque remover uma credencial do estado atual de um arquivo
não remove automaticamente sua existência em commits anteriores.

Conceitualmente:

```text
Working tree atual
        ≠
Histórico completo
```

Por isso, a análise considera os commits disponíveis no repositório.

---

## 9. Software Bill of Materials

O pipeline gera automaticamente um Software Bill of Materials em formato
CycloneDX.

O SBOM fornece um inventário machine-readable da composição do ambiente
resolvido.

Sua função principal é responder:

```text
Quais componentes e versões fazem parte deste software?
```

O SBOM não substitui scanners de vulnerabilidades.

A relação é:

```text
SBOM
  ↓
inventário

SCA
  ↓
vulnerabilidades conhecidas
```

---

## 10. Container Hardening

A aplicação utiliza um Docker build multi-stage.

A estratégia separa:

```text
Builder
   │
   ▼
Runtime
```

A imagem final contém somente os componentes necessários para a execução da
aplicação.

Entre os controles implementados estão:

- imagem baseada em Python slim;
- multi-stage build;
- usuário dedicado non-root;
- exclusão do `.env`;
- exclusão de artifacts e arquivos de desenvolvimento;
- separação das ferramentas de segurança do runtime;
- permissões específicas para geração dos reports;
- aplicação de atualizações disponíveis do sistema operacional.

---

## 11. Runtime Secret Management

Credenciais não são incorporadas à imagem Docker.

Elas são fornecidas somente durante a execução.

Conceitualmente:

```text
Image
  +
Runtime secret
  ↓
Application
```

em vez de:

```text
Secret
  ↓
Docker image
```

Isso reduz o risco de distribuir credenciais junto com a imagem.

---

## 12. Container Vulnerability Scanning

Trivy é utilizado para analisar vulnerabilidades presentes na imagem.

O scanner verifica componentes do sistema operacional e bibliotecas presentes no
runtime.

O pipeline mantém duas responsabilidades distintas:

```text
Trivy report
      ↓
evidence

Trivy gate
      ↓
enforcement
```

O relatório registra os findings.

O gate define quando esses findings devem impedir a continuidade do CI.

---

## 13. Política de vulnerabilidades do container

A política atual bloqueia o pipeline quando Trivy identifica vulnerabilidades:

```text
HIGH ou CRITICAL
+
correção disponível
```

Conceitualmente:

```text
Fixable HIGH/CRITICAL
        │
        ▼
Security Gate
        │
        ▼
CI Failure
```

Vulnerabilidades sem correção disponível não são interpretadas como inexistentes.

Elas permanecem visíveis nos resultados de segurança, mas não bloqueiam o
pipeline até existir remediation disponível.

Essa estratégia separa:

```text
visibility
```

de:

```text
enforcement
```

---

## 14. Segurança da infraestrutura de CI

O próprio workflow do GitHub Actions também faz parte da superfície de ataque.

Por isso, foram implementados controles específicos.

### Least privilege

O `GITHUB_TOKEN` possui:

```text
contents: read
```

como permissão global.

### Immutable Actions

GitHub Actions utilizadas pelo workflow são referenciadas por full commit SHA.

Isso reduz dependência de tags mutáveis.

### Timeouts

Todos os jobs possuem limites explícitos de execução.

### Concurrency

Execuções obsoletas do mesmo workflow/ref podem ser canceladas quando uma nova
execução é iniciada.

---

## 15. Immutable Actions e manutenção

SHA pinning cria uma referência imutável:

```text
Action
   ↓
commit SHA específico
```

Entretanto, dependências imutáveis ainda precisam ser atualizadas.

Por isso, o projeto combina:

```text
SHA pinning
     +
Dependabot
```

A relação é:

```text
Immutability
     │
     ▼
Dependência reproduzível
     │
     ▼
Dependabot monitoring
     │
     ▼
Update Pull Request
     │
     ▼
CI validation
     │
     ▼
Manual review
```

Isso evita escolher entre imutabilidade e manutenção.

---

## 16. Dependabot

Dependabot monitora:

- GitHub Actions;
- dependências Python gerenciadas pelo `uv`.

A configuração atual não habilita auto-merge.

Dependabot automatiza a descoberta e proposta de atualização.

A decisão final continua sujeita a:

```text
Pull Request
    ↓
CI
    ↓
Review
    ↓
Merge
```

---

## 17. Dependency Locking

O ambiente Python utiliza `uv.lock`.

O lockfile registra uma resolução específica das dependências.

Isso melhora:

- reprodutibilidade;
- consistência entre ambientes;
- rastreabilidade das versões utilizadas.

Dependabot e `pip-audit` atuam sobre responsabilidades diferentes:

```text
uv.lock
  ↓
estado reproduzível

Dependabot
  ↓
atualizações disponíveis

pip-audit
  ↓
vulnerabilidades conhecidas
```

---

## 18. Security Artifacts

O pipeline produz artifacts relacionados à segurança.

Atualmente incluem:

```text
CycloneDX SBOM
Trivy vulnerability report
```

Esses artifacts fornecem evidências complementares.

### CycloneDX

Registra composição.

### Trivy report

Registra vulnerabilidades identificadas no container.

Conceitualmente:

```text
SBOM
  ↓
What is present?

Trivy
  ↓
What is vulnerable?
```

---

## 19. Matriz de controles

| Superfície | Controle | Função principal |
| --- | --- | --- |
| Código | Ruff | qualidade |
| Código | Pytest | validação funcional |
| Código | Coverage | evidência / enforcement |
| Código | Bandit | SAST |
| Dependências | `uv.lock` | reprodutibilidade |
| Dependências | pip-audit | SCA |
| Dependências | CycloneDX | inventário / SBOM |
| Dependências | Dependabot | manutenção |
| Repositório | Gitleaks | secret scanning |
| CI | Least privilege | prevenção |
| CI | SHA pinning | supply-chain integrity |
| CI | Timeouts | controle operacional |
| CI | Concurrency | controle operacional |
| Container | Multi-stage build | redução de superfície |
| Container | Non-root | least privilege |
| Container | Secret exclusion | proteção de credenciais |
| Container | Trivy | vulnerability scanning |
| Container | Trivy gate | enforcement |

---

## 20. Defense in Depth

O projeto não trata nenhum controle como suficiente isoladamente.

Exemplo:

```text
Bandit limpo
     ≠
dependências seguras
```

Da mesma forma:

```text
pip-audit limpo
     ≠
ausência de secrets
```

e:

```text
Trivy limpo
     ≠
aplicação livre de falhas lógicas
```

Por isso, os mecanismos atuam em camadas.

---

## 21. O que bloqueia o CI

Entre os controles que podem impedir a continuidade do pipeline estão:

- falhas de lint ou formatação;
- testes automatizados;
- coverage gate;
- findings configurados como falha no Bandit;
- vulnerabilidades identificadas pelo dependency audit;
- secret scanning;
- falha na geração dos artifacts obrigatórios;
- falha no build do container;
- falha nas validações do runtime;
- vulnerabilidades corrigíveis HIGH/CRITICAL identificadas pelo Trivy.

Essa lista representa a política atual e pode evoluir conforme o projeto.

---

## 22. O que gera evidência

Alguns controles não existem apenas para bloquear uma execução.

Eles também produzem evidências úteis para auditoria.

Exemplos:

```text
CycloneDX SBOM
Trivy JSON report
test results
coverage metrics
scanner output
```

Essa distinção permite separar:

```text
pass/fail
```

de:

```text
evidence
```

---

## 23. Limitações

Nenhum controle implementado oferece garantia absoluta de segurança.

Alguns exemplos:

- Bandit depende das regras e padrões que conhece;
- pip-audit depende das vulnerabilidades publicadas;
- Gitleaks pode possuir gaps de detecção;
- SBOM inventaria componentes, mas não prova sua segurança;
- Trivy depende de bases de vulnerabilidade e disponibilidade de correções;
- SHA pinning reduz risco de mudança silenciosa, mas não prova que o código
  referenciado é seguro;
- Dependabot identifica atualizações, mas não determina sozinho se elas devem
  ser aceitas.

Essas limitações justificam a utilização de múltiplas camadas.

---

## 24. Estratégia resumida

A estratégia pode ser lembrada como:

```text
PREVENIR
   │
   ▼
DETECTAR
   │
   ▼
VALIDAR
   │
   ▼
GERAR EVIDÊNCIA
   │
   ▼
BLOQUEAR QUANDO NECESSÁRIO
   │
   ▼
MONITORAR ATUALIZAÇÕES
```

---

## 25. Como explicar em entrevista

Uma forma curta de apresentar a arquitetura:

> Eu não tratei DevSecOps como a instalação de um único scanner. Estruturei
> controles em diferentes superfícies. O código passa por lint, testes e SAST;
> as dependências passam por locking, SCA e geração de SBOM; o histórico Git é
> analisado por secret scanning; o container utiliza multi-stage build,
> non-root runtime e Trivy; e o próprio GitHub Actions foi endurecido com least
> privilege, timeouts, concurrency e Actions fixadas por SHA. Dependabot
> complementa o pinning ao propor atualizações que ainda precisam passar pelo CI
> e revisão antes do merge.

---

## 26. Relação com a arquitetura da aplicação

A documentação da arquitetura principal está localizada em:

```text
docs/architecture/
```

A camada DevSecOps não altera a responsabilidade dos módulos analíticos.

Ela cria controles ao redor do ciclo de desenvolvimento e execução:

```text
Aplicação
   │
   ▼
Quality + Security Controls
   │
   ▼
Validated Artifact
```

---

## 27. Próximos documentos

Esta visão geral serve como mapa da arquitetura DevSecOps.

Documentos complementares poderão detalhar:

- pipeline de CI;
- controles de segurança;
- software supply chain;
- segurança de containers;
- estratégia de dependency management;
- geração e utilização de security artifacts;
- decisões arquiteturais relacionadas ao DevSecOps.
