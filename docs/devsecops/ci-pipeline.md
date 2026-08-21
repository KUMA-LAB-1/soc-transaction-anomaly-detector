# Pipeline de CI e Security Gates

## 1. Objetivo

Este documento descreve a implementação atual do pipeline de Continuous
Integration (CI) do `soc-transaction-anomaly-detector`.

O objetivo é registrar:

- quando o workflow é executado;
- quais jobs fazem parte do pipeline;
- quais jobs possuem dependências entre si;
- quais controles de qualidade e segurança são executados;
- quais condições podem provocar falha;
- quais security artifacts são produzidos;
- como o próprio GitHub Actions é submetido a controles de hardening.

Enquanto `overview.md` descreve a estratégia DevSecOps em alto nível, este
documento detalha como essa estratégia é executada pelo workflow:

```text
.github/workflows/ci.yml
```

---

## 2. Visão geral

O workflow atual possui cinco jobs principais:

```text
quality
integration
secrets
sbom
container
```

Eles aparecem no GitHub Actions com os nomes:

```text
Quality + Unit Tests
Integration Smoke
Secret Scanning
Software Bill of Materials
Container Security
```

A topologia não é completamente sequencial.

Atualmente:

```text
                         ┌────────────────────► Secret Scanning
                         │
                         ├────────────────────► Software Bill of Materials
                         │
Trigger ────────┬────────┼────────────────────► Container Security
                │        │
                │        │
                ▼        │
       Quality + Unit Tests
                │
                │ needs: quality
                ▼
       Integration Smoke
```

`Integration Smoke` possui dependência explícita de `quality`.

Os jobs:

```text
secrets
sbom
container
```

não possuem `needs:` na implementação atual e, portanto, não dependem da
conclusão do job `quality` para serem elegíveis à execução.

---

## 3. Eventos que disparam o workflow

O workflow é executado em:

```text
push
pull_request
```

para as branches:

```text
main
feature/devsecops
```

A configuração atual pode ser resumida como:

```text
push
├── main
└── feature/devsecops

pull_request
├── main
└── feature/devsecops
```

Isso permite validar tanto alterações enviadas diretamente às branches
monitoradas quanto Pull Requests direcionados a elas.

---

## 4. Permissões globais

O workflow declara:

```yaml
permissions:
  contents: read
```

Isso restringe o `GITHUB_TOKEN` global às permissões de leitura necessárias para
o estado atual do pipeline.

A estratégia segue o princípio de:

```text
Least Privilege
```

Conceitualmente:

```text
Workflow
   │
   ▼
GITHUB_TOKEN
   │
   ▼
contents: read
```

Permissões adicionais devem ser introduzidas apenas caso algum job futuro
possua necessidade explícita.

---

## 5. Concurrency

O workflow possui:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

O grupo de concorrência combina:

```text
workflow
+
Git ref
```

Quando uma execução mais recente é iniciada para o mesmo grupo, uma execução
anterior ainda em andamento pode ser cancelada.

Conceitualmente:

```text
Commit A
   │
   ▼
CI em execução
           Commit B
              │
              ▼
       Nova execução CI
              │
              ▼
       Execução A obsoleta
              │
              ▼
           cancelada
```

Esse controle reduz consumo desnecessário de recursos por execuções que já foram
substituídas por alterações mais recentes.

---

## 6. Timeouts

Todos os jobs possuem limites explícitos de execução.

Configuração atual:

| Job | Timeout |
| --- | ---: |
| `quality` | 10 minutos |
| `integration` | 10 minutos |
| `secrets` | 10 minutos |
| `sbom` | 10 minutos |
| `container` | 20 minutos |

O job `container` possui uma janela maior porque inclui operações mais
custosas, como:

- build da imagem;
- inicialização de containers;
- verificações de runtime;
- vulnerability scanning;
- geração de relatório de vulnerabilidades.

Os timeouts evitam que jobs travados ou inesperadamente longos permaneçam
executando indefinidamente.

---

## Parte I — Quality + Unit Tests

### 7. Objetivo do job `quality`

O primeiro job analítico do workflow é:

```text
quality
```

Nome exibido:

```text
Quality + Unit Tests
```

Ele concentra verificações relacionadas a:

```text
qualidade
+
segurança de código
+
segurança de dependências
+
testes unitários
+
coverage gate
```

Runner:

```text
ubuntu-latest
```

Timeout:

```text
10 minutos
```

---

### 8. Checkout

O primeiro step utiliza:

```text
actions/checkout
```

A Action é referenciada por full commit SHA, mantendo um comentário com a versão
humana correspondente:

```text
v7
```

A estratégia adotada é:

```text
commit SHA
     │
     ├── identidade imutável
     │
     └── comentário de versão
          │
          └── legibilidade
```

---

### 9. Python

O ambiente utiliza:

```text
Python 3.12
```

configurado por:

```text
actions/setup-python
```

também fixado por full commit SHA.

---

### 10. uv

O pipeline instala `uv` utilizando:

```text
astral-sh/setup-uv
```

A Action já está fixada por commit SHA.

A resolução de dependências utiliza:

```text
uv.lock
```

---

### 11. Sincronização das dependências

O job executa:

```bash
uv sync --locked --group lint --group test --group security
```

A opção:

```text
--locked
```

exige compatibilidade com o estado bloqueado das dependências.

Os grupos carregados nesse job são:

```text
lint
test
security
```

Isso fornece as ferramentas necessárias para Ruff, Pytest, Bandit, pip-audit e
demais verificações realizadas nesse caminho.

---

### 12. Ruff lint

O pipeline executa:

```bash
uv run ruff check .
```

Essa etapa verifica as regras de lint configuradas para o projeto.

Uma falha do comando provoca falha do step e, consequentemente, do job.

---

### 13. Ruff format check

Também é executado:

```bash
uv run ruff format --check .
```

Essa etapa verifica se os arquivos respeitam a formatação esperada sem
reescrevê-los automaticamente durante o CI.

Portanto:

```text
formatação diferente do esperado
            │
            ▼
        CI failure
```

---

### 14. Bandit SAST

A análise estática de segurança utiliza:

```bash
uv run bandit -c pyproject.toml -r src
```

A configuração está centralizada em:

```text
pyproject.toml
```

e o escopo analisado é:

```text
src/
```

Essa etapa executa Static Application Security Testing sobre o código Python
desenvolvido no projeto.

Como o comando participa diretamente do job, uma falha segundo a política do
Bandit provoca falha do job.

---

### 15. Dependency vulnerability audit

O pipeline executa:

```bash
uv run pip-audit
```

Essa etapa analisa as dependências Python resolvidas em busca de vulnerabilidades
conhecidas.

A responsabilidade é diferente do Bandit:

```text
Bandit
  │
  ▼
código desenvolvido no projeto

pip-audit
  │
  ▼
dependências utilizadas pelo projeto
```

---

### 16. Testes unitários

O job finaliza com:

```bash
uv run pytest tests/unit
```

A configuração do Pytest definida no projeto aplica o coverage gate utilizado
pela suíte unitária.

Assim, o step verifica simultaneamente:

```text
testes unitários
      +
coverage policy
```

---

### 17. Efeito sobre o pipeline

Caso qualquer step do job `quality` falhe:

```text
quality = failed
```

Como `integration` possui:

```text
needs: quality
```

o Integration Smoke não é liberado normalmente após uma falha do quality gate.

Conceitualmente:

```text
Quality
   │
   ├── sucesso ──► Integration
   │
   └── falha ────► Integration bloqueado
```

---

## Parte II — Integration Smoke

### 18. Objetivo

O job:

```text
integration
```

é exibido como:

```text
Integration Smoke
```

Sua função é validar a execução integrada do pipeline analítico após a aprovação
do job `quality`.

Configuração:

```text
runs-on: ubuntu-latest
needs: quality
timeout-minutes: 10
```

---

### 19. Dependência explícita

A configuração:

```yaml
needs: quality
```

estabelece uma relação direta:

```text
Quality + Unit Tests
          │
          ▼
   Integration Smoke
```

Isso evita executar o smoke test integrado antes da aprovação dos controles
básicos presentes no job anterior.

---

### 20. Ambiente do Integration Smoke

O job realiza:

```text
checkout
   ↓
Python 3.12
   ↓
uv
   ↓
uv sync --locked --group test
```

Diferentemente do job `quality`, ele sincroniza apenas o grupo necessário para
os testes de integração.

---

### 21. Smoke test

O comando executado é:

```bash
uv run pytest tests/integration/test_pipeline_smoke.py -v --no-cov
```

O teste é executado com:

```text
-v
```

para saída detalhada e:

```text
--no-cov
```

porque o objetivo desse job não é recalcular a cobertura unitária.

A função principal aqui é verificar se os componentes conseguem trabalhar em
conjunto.

---

### 22. Diferença entre unit e integration tests

A arquitetura separa:

```text
Unit Tests
    │
    └── comportamento isolado

Integration Smoke
    │
    └── funcionamento integrado
```

O coverage gate pertence ao primeiro caminho.

O segundo caminho busca responder:

```text
Os principais componentes ainda funcionam juntos
depois das alterações?
```

---

## Parte III — Secret Scanning

### 23. Objetivo

O job:

```text
secrets
```

é exibido como:

```text
Secret Scanning
```

Runner:

```text
ubuntu-latest
```

Timeout:

```text
10 minutos
```

Sua responsabilidade é analisar o histórico Git utilizando Gitleaks.

---

### 24. Checkout do histórico completo

O job utiliza:

```yaml
fetch-depth: 0
```

Isso diferencia esse checkout dos demais.

O objetivo é disponibilizar todo o histórico necessário ao scanner.

Conceitualmente:

```text
shallow checkout
      ≠
full Git history
```

Como um segredo pode permanecer em commits anteriores mesmo depois de ter sido
removido do working tree atual, a análise precisa considerar o histórico.

---

### 25. Instalação do Gitleaks

O workflow instala explicitamente:

```text
Gitleaks 8.18.4
```

O processo utilizado inclui:

```text
download do archive
        │
        ▼
download dos checksums
        │
        ▼
seleção do checksum correspondente
        │
        ▼
sha256sum -c
        │
        ▼
extração
        │
        ▼
instalação
        │
        ▼
gitleaks version
```

A versão não é resolvida dinamicamente por `latest`.

Ela foi fixada para manter o comportamento previamente validado no projeto.

---

### 26. Verificação SHA-256

Antes da instalação, o archive baixado é validado utilizando:

```bash
sha256sum -c -
```

com a entrada correspondente no arquivo de checksums.

Isso adiciona uma verificação de integridade ao processo de obtenção do próprio
scanner.

A lógica é:

```text
download
   │
   ▼
verificação de integridade
   │
   ▼
execução
```

e não simplesmente:

```text
download
   ↓
execução imediata
```

---

### 27. Scan do histórico

O comando final é:

```bash
gitleaks detect --source . --redact --verbose
```

### `--source .`

Define o repositório atual como fonte.

### `--redact`

Evita imprimir diretamente no output os valores completos de secrets
potencialmente identificados.

### `--verbose`

Aumenta a visibilidade da execução.

---

### 28. Enforcement

O scan do Gitleaks é um security gate.

Se o comando retornar código de falha devido a um finding compatível com a
política da ferramenta:

```text
Secret detected
      │
      ▼
Gitleaks failure
      │
      ▼
CI failure
```

O objetivo não é apenas produzir informação, mas impedir que uma condição
detectada seja silenciosamente ignorada.

---

## Parte IV — Software Bill of Materials

### 29. Objetivo

O job:

```text
sbom
```

é exibido como:

```text
Software Bill of Materials
```

Configuração:

```text
runner: ubuntu-latest
timeout: 10 minutos
```

Sua responsabilidade é gerar e publicar o inventário CycloneDX das dependências
resolvidas.

---

### 30. Ambiente

O job executa:

```text
checkout
   ↓
Python 3.12
   ↓
uv
   ↓
uv sync --locked --group security
```

O grupo `security` contém as ferramentas necessárias para a geração do SBOM.

---

### 31. Geração do CycloneDX

Antes da geração é criado:

```text
artifacts/
```

O comando principal é:

```bash
uv run cyclonedx-py environment \
  --pyproject pyproject.toml \
  --output-reproducible \
  --output-format JSON \
  --output-file artifacts/sbom.cdx.json
```

---

### 32. Origem dos metadados

A opção:

```text
--pyproject pyproject.toml
```

associa informações do projeto ao documento produzido.

---

### 33. Reprodutibilidade

A opção:

```text
--output-reproducible
```

solicita geração reproduzível do SBOM.

Essa propriedade foi validada durante a implementação através de comparação de
hashes SHA-256 entre gerações equivalentes.

---

### 34. Formato

O arquivo é produzido em:

```text
JSON
```

e salvo em:

```text
artifacts/sbom.cdx.json
```

---

### 35. Publicação do artifact

O upload utiliza:

```text
actions/upload-artifact
```

fixado por full commit SHA.

O artifact publicado recebe o nome:

```text
cyclonedx-sbom
```

e contém:

```text
artifacts/sbom.cdx.json
```

---

### 36. Falha na ausência do arquivo

A configuração utiliza:

```text
if-no-files-found: error
```

Portanto, a ausência do SBOM esperado não é silenciosamente ignorada.

Conceitualmente:

```text
SBOM produzido
      │
      ├── sim ──► artifact
      │
      └── não ──► CI error
```

---

### 37. Papel do SBOM no CI

O SBOM é principalmente:

```text
evidence
+
inventory
```

e não um scanner de vulnerabilidades.

Ele responde:

```text
Quais componentes fazem parte deste ambiente?
```

Outras ferramentas respondem perguntas diferentes.

---

## Parte V — Container Security

### 38. Objetivo

O job:

```text
container
```

é exibido como:

```text
Container Security
```

Runner:

```text
ubuntu-latest
```

Timeout:

```text
20 minutos
```

Essa etapa possui o maior timeout do workflow atual.

---

### 39. Build da imagem hardened

O primeiro controle específico constrói:

```bash
docker build -t soc-anomaly-detector:ci .
```

A imagem é identificada localmente como:

```text
soc-anomaly-detector:ci
```

O build utiliza o Dockerfile hardened do projeto.

---

### 40. Non-root validation

Depois do build é executado:

```bash
docker run --rm --entrypoint whoami soc-anomaly-detector:ci
```

O output precisa ser:

```text
kuma
```

A validação é implementada através do comando `test`.

Portanto:

```text
runtime user = kuma
        │
        ├── sim ──► continua
        │
        └── não ──► CI failure
```

Isso transforma a política non-root em uma verificação automatizada.

---

### 41. Runtime secret exclusion

O pipeline também inicia a imagem para verificar:

```text
/app/.env
```

O teste exige que esse arquivo **não exista**.

Conceitualmente:

```text
/app/.env
    │
    ├── ausente ──► esperado
    │
    └── presente ─► CI failure
```

Essa validação fornece evidência automatizada de que o `.env` local não foi
incorporado à imagem runtime.

---

### 42. Primeira execução do Trivy

O job executa Trivy uma primeira vez para produzir evidência estruturada.

Configuração principal:

```text
image-ref: soc-anomaly-detector:ci
format: json
output: trivy-report.json
exit-code: 0
vuln-type: os,library
severity: HIGH,CRITICAL
scanners: vuln
```

---

### 43. Por que `exit-code: 0` no relatório?

Essa primeira execução não existe para bloquear o pipeline.

Ela existe para produzir:

```text
trivy-report.json
```

Portanto:

```text
Trivy report execution
        │
        ▼
Generate evidence
        │
        ▼
exit-code: 0
```

Isso permite publicar o resultado mesmo quando existem findings dentro do escopo
analisado.

---

### 44. Publicação do Trivy report

O arquivo:

```text
trivy-report.json
```

é enviado ao GitHub Actions como:

```text
trivy-container-report
```

Também utiliza:

```text
if-no-files-found: error
```

Logo, a ausência do relatório esperado provoca falha.

---

### 45. Segunda execução do Trivy

Depois de produzir o artifact, Trivy é executado novamente com função diferente.

Essa segunda execução é o:

```text
security gate
```

Configuração:

```text
format: table
exit-code: 1
ignore-unfixed: true
vuln-type: os,library
severity: HIGH,CRITICAL
scanners: vuln
```

---

### 46. Diferença entre report e gate

Essa distinção é central na arquitetura:

```text
Trivy #1
   │
   ▼
JSON report
   │
   ▼
Evidence
```

enquanto:

```text
Trivy #2
   │
   ▼
Policy evaluation
   │
   ▼
Enforcement
```

Ou seja:

```text
visibility
≠
enforcement
```

---

### 47. `ignore-unfixed`

O security gate utiliza:

```text
ignore-unfixed: true
```

Isso significa que vulnerabilidades sem correção disponível não participam da
mesma política de bloqueio aplicada aos findings corrigíveis.

Isso **não significa que elas deixem de existir**.

Elas podem continuar aparecendo no relatório gerado pela primeira execução.

---

### 48. Severidades bloqueadas

O gate considera:

```text
HIGH
CRITICAL
```

e utiliza:

```text
exit-code: 1
```

Quando um finding dentro da política configurada é identificado, a Action pode
falhar e bloquear o job.

A política pode ser resumida como:

```text
HIGH / CRITICAL
      +
fix disponível
      │
      ▼
Trivy gate
      │
      ▼
CI failure
```

---

## Parte VI — Supply Chain do próprio workflow

### 49. Action pinning

As Actions utilizadas no workflow são referenciadas por full commit SHA.

Entre elas estão:

```text
actions/checkout
actions/setup-python
actions/upload-artifact
astral-sh/setup-uv
aquasecurity/trivy-action
```

Comentários preservam versões humanas como:

```text
# v7
# v6
# v9.0.0
# v0.36.0
```

---

### 50. Por que SHA e comentário de versão?

Cada representação possui uma finalidade:

```text
full SHA
   │
   └── imutabilidade da referência

version comment
   │
   └── legibilidade para manutenção
```

Isso evita depender somente de tags mutáveis sem sacrificar a compreensão do
workflow.

---

### 51. Relação com Dependabot

O pinning por SHA é complementado pelo Dependabot.

O lifecycle esperado é:

```text
Pinned Action
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
     │
     ▼
Merge decision
```

Assim, o projeto combina:

```text
immutability
+
controlled maintenance
```

---

## Parte VII — Topologia e paralelismo

### 52. Jobs independentes

Os jobs:

```text
secrets
sbom
container
```

não possuem `needs:` na configuração atual.

Portanto, sua elegibilidade de execução não depende explicitamente da conclusão
de `quality`.

A arquitetura utiliza paralelismo onde a dependência lógica não exige
sequenciamento.

---

### 53. Job dependente

`integration` possui:

```text
needs: quality
```

Essa dependência existe porque o smoke test integrado representa uma etapa
posterior aos controles básicos de qualidade, segurança e testes unitários.

---

### 54. Topologia final

A relação pode ser visualizada como:

```text
                             ┌───────────────────────┐
                             │    Secret Scanning    │
                             └───────────────────────┘
                                      ▲
                                      │
                                      │
┌─────────┐       ┌───────────────────┴──┐
│ Trigger │──────►│ Quality + Unit Tests │
└─────────┘       └──────────┬───────────┘
     │                       │
     │                       │ needs
     │                       ▼
     │            ┌──────────────────────┐
     │            │  Integration Smoke   │
     │            └──────────────────────┘
     │
     ├────────────► Software Bill of Materials
     │
     └────────────► Container Security
```

O desenho é conceitual.

O ponto principal é:

```text
integration depends on quality
```

enquanto os demais jobs não possuem essa dependência explícita.

---

## Parte VIII — Artifacts

### 55. Security artifacts produzidos

O workflow publica atualmente dois artifacts principais de segurança:

```text
cyclonedx-sbom
trivy-container-report
```

---

### 56. CycloneDX SBOM

Nome:

```text
cyclonedx-sbom
```

Arquivo:

```text
artifacts/sbom.cdx.json
```

Função:

```text
software composition inventory
```

---

### 57. Trivy report

Nome:

```text
trivy-container-report
```

Arquivo:

```text
trivy-report.json
```

Função:

```text
container vulnerability evidence
```

---

### 58. Evidência versus decisão

Os artifacts permitem auditoria posterior.

Eles não devem ser confundidos com os security gates:

```text
Artifact
   │
   └── registra evidência
```

enquanto:

```text
Gate
   │
   └── toma decisão pass/fail
```

---

## Parte IX — Failure model

### 59. Exemplos de condições que podem falhar

O workflow pode falhar diante de condições como:

```text
Ruff lint failure
Ruff format failure
Bandit failure
pip-audit failure
unit test failure
coverage gate failure
integration smoke failure
Gitleaks detection
SBOM generation failure
artifact absence
Docker build failure
unexpected runtime user
.env presente na imagem
Trivy fixable HIGH/CRITICAL finding
```

---

### 60. Falha não significa a mesma coisa em todos os jobs

Uma falha possui significado relacionado ao controle responsável.

Exemplos:

```text
Pytest failure
→ regressão funcional

Bandit failure
→ padrão potencialmente inseguro

Gitleaks failure
→ possível secret detectado

Trivy gate failure
→ vulnerabilidade dentro da política de bloqueio

Artifact upload failure
→ evidência obrigatória não produzida/publicada
```

Essa distinção é importante durante investigação de CI.

---

## Parte X — Como explicar em entrevista

### 61. Explicação curta

> O CI é dividido em cinco jobs. O job de qualidade executa Ruff, Bandit,
> pip-audit e testes unitários com coverage gate. O smoke test de integração só
> roda depois que esse job passa. Em paralelo, existem jobs independentes para
> secret scanning, geração de SBOM e segurança do container. O container é
> construído e validado como non-root, é verificada a ausência do `.env` e o
> Trivy é executado duas vezes: uma para gerar evidência JSON e outra como
> security gate para HIGH/CRITICAL corrigíveis.

---

### 62. “Por que o integration depende de quality?”

> Porque o smoke test integrado é mais adequado depois das verificações básicas.
> Se lint, SAST, dependency audit ou testes unitários já falharam, não preciso
> depender desse caminho para validar a integração completa antes de corrigir o
> problema inicial.

---

### 63. “Por que Gitleaks, SBOM e Container não usam `needs: quality`?”

> Porque são controles sobre superfícies diferentes e não dependem logicamente
> do resultado dos testes unitários para produzir suas próprias validações. Isso
> permite executar parte do pipeline em paralelo e obter feedback de segurança
> sem transformar tudo em uma cadeia sequencial.

---

### 64. “Por que executar Trivy duas vezes?”

> Porque as execuções possuem objetivos diferentes. Uma gera um relatório JSON
> para auditoria e não falha por findings. A segunda aplica a política de
> enforcement e falha quando encontra vulnerabilidades HIGH ou CRITICAL
> corrigíveis.

---

### 65. “Por que `ignore-unfixed`?”

> O projeto separa visibilidade de enforcement. Vulnerabilidades sem correção
> disponível continuam registradas no relatório, mas o gate bloqueia o pipeline
> quando existe uma vulnerabilidade HIGH ou CRITICAL que já possui remediation
> disponível.

---

### 66. “Por que baixar Gitleaks manualmente?”

> A implementação utiliza uma versão explicitamente selecionada e verifica a
> integridade do archive através do checksum SHA-256 antes da instalação. Isso
> mantém a versão reproduzível e adiciona uma validação do artefato utilizado
> como scanner.

---

### 67. “Por que pinning por SHA?”

> Porque uma tag é uma referência mais legível, mas um commit SHA identifica uma
> revisão específica da Action. O projeto usa o SHA para imutabilidade e mantém
> o número da versão em comentário para facilitar manutenção. Dependabot
> complementa essa estratégia propondo atualizações controladas.

---

## Parte XI — Limitações e evolução

### 68. Limitações

O pipeline automatiza diversos controles, mas não deve ser interpretado como
garantia absoluta de segurança.

Entre as limitações:

- scanners dependem das regras e bases que conhecem;
- Actions pinadas ainda precisam ser avaliadas antes da adoção;
- testes não cobrem automaticamente todos os comportamentos possíveis;
- um SBOM fornece inventário, não garantia de segurança;
- vulnerability scanning representa o estado conhecido no momento da execução;
- secret scanning pode possuir gaps;
- um pipeline verde indica aprovação dos controles configurados, não ausência
  universal de risco.

---

### 69. Possíveis evoluções

Possibilidades futuras incluem:

- branch protection associada aos jobs obrigatórios;
- CodeQL ou outros mecanismos adicionais de análise;
- assinatura de artifacts;
- provenance;
- attestations;
- políticas adicionais sobre SBOM;
- container image registry;
- assinatura de imagens;
- policy-as-code;
- ambientes separados de build e deployment;
- deployment gates;
- observabilidade do CI;
- métricas de duração e taxa de falha;
- dependency review adicional;
- políticas mais granulares por severidade e contexto.

Esses itens representam possibilidades e não funcionalidades necessariamente
implementadas hoje.

---

### 70. Relação com os demais documentos

A visão geral da estratégia DevSecOps está em:

```text
docs/devsecops/overview.md
```

Este documento detalha especificamente:

```text
triggers
jobs
steps
dependencies
timeouts
artifacts
security gates
failure model
```

Documentos posteriores poderão aprofundar:

```text
security-controls.md
supply-chain.md
container-security.md
```

A intenção é manter a documentação modular sem perder a relação entre a política
DevSecOps e sua implementação real no GitHub Actions.
