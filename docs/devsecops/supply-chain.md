# Segurança da Software Supply Chain

## 1. Objetivo

Este documento descreve os controles de software supply chain implementados no
`soc-transaction-anomaly-detector`.

O objetivo é registrar como o projeto trata diferentes riscos relacionados a:

- declaração de dependências;
- resolução e locking;
- reprodutibilidade;
- vulnerabilidades conhecidas;
- inventário de componentes;
- integridade das GitHub Actions;
- integridade de ferramentas baixadas durante o CI;
- monitoramento de atualizações;
- vulnerabilidades presentes no container resultante.

A estratégia atual procura responder a diferentes perguntas em etapas
complementares.

---

## 2. Visão geral

A supply chain do projeto pode ser representada de forma simplificada como:

```text
pyproject.toml
      │
      ▼
Declaração das dependências
      │
      ▼
uv.lock
      │
      ▼
uv sync --locked
      │
      ├──────────────► pip-audit
      │
      ├──────────────► CycloneDX SBOM
      │
      └──────────────► ambiente da aplicação
                              │
                              ▼
                         Docker build
                              │
                              ▼
                           Trivy
```

Ao redor desse fluxo existem controles adicionais:

```text
GitHub Actions
      │
      ├── full commit SHA pinning
      └── Dependabot monitoring

Gitleaks
      │
      ├── versão explícita
      └── checksum SHA-256
```

Esses controles possuem objetivos distintos e não devem ser interpretados como
equivalentes.

---

## 3. Perguntas respondidas por cada controle

Uma forma prática de compreender a arquitetura é associar cada mecanismo a uma
pergunta específica.

### `pyproject.toml`

```text
Quais dependências e constraints o projeto declara?
```

### `uv.lock`

```text
Quais versões foram efetivamente resolvidas?
```

### `uv sync --locked`

```text
O ambiente pode ser reconstruído respeitando o estado bloqueado?
```

### pip-audit

```text
Existem vulnerabilidades conhecidas nas dependências auditadas?
```

### CycloneDX

```text
Quais componentes formam o ambiente?
```

### SHA pinning

```text
Qual revisão exata de uma GitHub Action será executada?
```

### Checksum SHA-256

```text
O archive baixado corresponde ao artifact esperado segundo o checksum usado?
```

### Dependabot

```text
Existem atualizações disponíveis?
```

### Trivy

```text
Quais vulnerabilidades são identificadas no container resultante?
```

A arquitetura busca manter essas responsabilidades separadas.

---

## Parte I — Declaração das dependências

### 4. `pyproject.toml`

As dependências do projeto são declaradas em:

```text
pyproject.toml
```

A aplicação define:

```text
Python >= 3.12 e < 3.13
```

As dependências principais incluem componentes utilizados para:

- análise de dados;
- Machine Learning;
- persistência;
- conexão PostgreSQL;
- geração de gráficos;
- geração de PDF;
- requests HTTP;
- serialização de modelos.

---

### 5. Dependency groups

Além das dependências de runtime, o projeto utiliza grupos dedicados.

Atualmente:

```text
lint
security
test
```

Essa separação permite evitar que ferramentas de desenvolvimento e segurança
sejam tratadas automaticamente como dependências da aplicação em runtime.

---

### 6. Grupo `lint`

O grupo contém:

```text
ruff
```

Seu objetivo é disponibilizar ferramentas de qualidade durante desenvolvimento
e CI.

---

### 7. Grupo `security`

O grupo contém atualmente:

```text
bandit[toml]
cyclonedx-bom
pip-audit
```

Essas ferramentas possuem finalidades distintas:

```text
Bandit
  ↓
SAST

pip-audit
  ↓
SCA

CycloneDX
  ↓
inventário / SBOM
```

Agrupar essas ferramentas separadamente facilita isolar a toolchain de
segurança das dependências necessárias à execução normal da aplicação.

---

### 8. Grupo `test`

O grupo inclui:

```text
pytest-cov
```

e suporta a suíte automatizada de testes e cobertura.

---

## Parte II — Dependency Locking

### 9. `uv.lock`

O projeto utiliza:

```text
uv.lock
```

como lockfile da resolução de dependências.

Esse arquivo registra versões e artifacts resolvidos pelo `uv`.

---

### 10. Reprodutibilidade

Sem um lockfile, duas instalações realizadas em momentos diferentes podem
resolver versões diferentes dentro das constraints declaradas.

Conceitualmente:

```text
pyproject.toml
      ↓
constraints
      ↓
resolução variável
```

Com lockfile:

```text
pyproject.toml
      +
uv.lock
      ↓
resolução conhecida
```

Isso reduz variação entre execuções.

---

### 11. Metadados e hashes no lockfile

O `uv.lock` inclui informações relacionadas às distribuições resolvidas.

Para componentes como CycloneDX, por exemplo, o lockfile registra:

- versão;
- source distribution;
- wheel;
- URL;
- hash SHA-256;
- tamanho.

Esses dados contribuem para uma resolução mais rastreável.

---

### 12. Locking não significa segurança

Um lockfile pode reproduzir perfeitamente uma versão vulnerável.

Portanto:

```text
reprodutibilidade
      ≠
segurança
```

Por isso o projeto combina locking com controles adicionais.

---

## Parte III — `uv sync --locked`

### 13. Sincronização bloqueada

O CI utiliza:

```text
uv sync --locked
```

em diferentes jobs.

Esse comportamento exige que o ambiente permaneça consistente com o lockfile.

---

### 14. Job `quality`

O job de qualidade executa:

```text
uv sync --locked --group lint --group test --group security
```

Isso prepara o ambiente necessário para:

- Ruff;
- Bandit;
- pip-audit;
- testes;
- coverage.

---

### 15. Job `integration`

O integration smoke utiliza:

```text
uv sync --locked --group test
```

Carregando apenas a toolchain necessária para esse caminho.

---

### 16. Job `sbom`

O job de SBOM executa:

```text
uv sync --locked --group security
```

Esse ambiente contém a ferramenta utilizada para geração CycloneDX.

---

### 17. Docker build

O Dockerfile também utiliza:

```text
uv sync --locked
```

durante o builder stage.

Assim, a resolução utilizada no runtime parte do mesmo estado bloqueado do
projeto.

---

## Parte IV — Software Composition Analysis

### 18. pip-audit

O projeto utiliza:

```text
pip-audit
```

para realizar Software Composition Analysis sobre o ambiente Python.

---

### 19. Objetivo

A ferramenta procura identificar vulnerabilidades conhecidas associadas às
dependências resolvidas.

Ela responde principalmente:

```text
Existe vulnerabilidade conhecida
em algum componente auditado?
```

---

### 20. Execução

No CI:

```text
uv run pip-audit
```

é executado no job `quality`.

---

### 21. Enforcement

Como o comando faz parte diretamente do job, uma condição que cause falha do
pip-audit também impede a conclusão bem-sucedida do job.

Portanto:

```text
known vulnerable dependency
           ↓
pip-audit
           ↓
failure
           ↓
CI blocked
```

de acordo com o comportamento da ferramenta e da política configurada.

---

### 22. Limitações

pip-audit depende de vulnerabilidades publicadas e reconhecidas.

Ele não detecta automaticamente:

- zero-days ainda não publicados;
- comportamento malicioso sem CVE;
- comprometimento upstream desconhecido;
- lógica insegura dentro da aplicação;
- todos os riscos da supply chain.

---

## Parte V — Software Bill of Materials

### 23. CycloneDX

O projeto utiliza:

```text
cyclonedx-bom
```

para produzir um SBOM.

---

### 24. Geração

O CI executa:

```text
uv run cyclonedx-py environment
```

com:

```text
--pyproject pyproject.toml
--output-reproducible
--output-format JSON
--output-file artifacts/sbom.cdx.json
```

---

### 25. Artifact produzido

O arquivo gerado é:

```text
artifacts/sbom.cdx.json
```

e é publicado pelo GitHub Actions como:

```text
cyclonedx-sbom
```

---

### 26. Função do SBOM

O SBOM fornece um inventário machine-readable da composição do ambiente.

Ele responde principalmente:

```text
O que existe aqui?
```

---

### 27. SBOM versus SCA

É importante não confundir:

```text
CycloneDX
   ↓
inventory
```

com:

```text
pip-audit
   ↓
known vulnerability analysis
```

Uma dependência pode estar corretamente inventariada no SBOM e ainda possuir
vulnerabilidade.

---

### 28. Reprodutibilidade

O pipeline utiliza:

```text
--output-reproducible
```

para gerar um output mais estável entre execuções equivalentes.

Durante a implementação, a reprodutibilidade do SBOM foi validada através de
comparação de hashes SHA-256.

---

### 29. Limitações do SBOM

SBOM não prova:

- segurança;
- integridade de todos os componentes;
- procedência confiável;
- ausência de malware;
- ausência de vulnerabilidades;
- validade operacional.

Seu principal valor é visibilidade e rastreabilidade.

---

## Parte VI — GitHub Actions Supply Chain

### 30. GitHub Actions como dependências executáveis

As Actions utilizadas pelo CI executam código durante o workflow.

Por isso, também fazem parte da software supply chain.

---

### 31. Actions utilizadas

O workflow atual referencia Actions como:

```text
actions/checkout
actions/setup-python
astral-sh/setup-uv
actions/upload-artifact
aquasecurity/trivy-action
```

---

### 32. Risco de referências mutáveis

Uma referência como:

```text
action@tag
```

é legível, porém uma tag pode ser alterada para apontar para outra revisão.

Isso cria a possibilidade conceitual de:

```text
workflow inalterado
       +
tag alterada
       ↓
código diferente executado
```

---

### 33. SHA pinning

Para reduzir esse risco, as Actions são referenciadas por:

```text
full commit SHA
```

Exemplo conceitual:

```text
uses: action@0123456789abcdef...
```

---

### 34. Comentários de versão

Ao lado do SHA permanecem comentários como:

```text
# v7
# v6
# v9.0.0
# v0.36.0
```

Isso combina:

```text
imutabilidade
+
legibilidade
```

---

### 35. Actions atualmente pinadas

A configuração atual utiliza SHA pinning para:

- `actions/checkout`;
- `actions/setup-python`;
- `astral-sh/setup-uv`;
- `actions/upload-artifact`;
- `aquasecurity/trivy-action`.

---

### 36. Limitações do SHA pinning

Pinning garante principalmente:

```text
referência estável
```

Ele não garante:

```text
código seguro
código sem backdoor
dependência confiável
ausência de vulnerabilidades
```

Uma revisão insegura continua insegura mesmo quando fixada por SHA.

---

## Parte VII — Integridade de ferramentas baixadas

### 37. Gitleaks

Diferentemente das GitHub Actions utilizadas diretamente pelo YAML, o Gitleaks
é baixado durante o workflow.

A versão utilizada é:

```text
8.18.4
```

---

### 38. Download explícito

O CI baixa:

```text
gitleaks_8.18.4_linux_x64.tar.gz
```

a partir da release correspondente.

Também baixa:

```text
gitleaks_8.18.4_checksums.txt
```

---

### 39. Verificação SHA-256

Antes da instalação, o pipeline seleciona o checksum correspondente ao archive e
executa:

```text
sha256sum -c -
```

---

### 40. Cadeia de integridade

O fluxo é:

```text
release version
      ↓
archive
      +
checksums
      ↓
SHA-256 verification
      ↓
extract
      ↓
install
      ↓
execute
```

Isso evita executar imediatamente o binário baixado sem uma verificação de
integridade.

---

### 41. O que o checksum prova

A verificação procura confirmar que:

```text
arquivo baixado
=
arquivo representado pelo checksum utilizado
```

---

### 42. O que o checksum não prova

Checksum não prova automaticamente:

- que a release é legítima;
- que o upstream não foi comprometido;
- que o binário é seguro;
- que o checksum não foi comprometido junto com o artifact.

Ele adiciona uma camada de integridade, não uma garantia absoluta de confiança.

---

## Parte VIII — Dependency Update Monitoring

### 43. Dependabot

O projeto utiliza:

```text
.github/dependabot.yml
```

para monitorar atualizações.

---

### 44. Ecossistema GitHub Actions

Dependabot monitora:

```text
package-ecosystem: github-actions
```

na raiz do repositório.

---

### 45. Ecossistema `uv`

Também monitora:

```text
package-ecosystem: uv
```

para o ambiente Python.

---

### 46. Frequência

Os dois ecossistemas utilizam:

```text
weekly
```

---

### 47. Target branch

Os Pull Requests são direcionados para:

```text
feature/devsecops
```

---

### 48. Limite de PRs

A configuração limita:

```text
5
```

Pull Requests abertos por ecossistema.

---

### 49. Update lifecycle

A arquitetura adotada é:

```text
locked / pinned dependency
          ↓
Dependabot monitoring
          ↓
update available
          ↓
Pull Request
          ↓
CI validation
          ↓
manual review
          ↓
merge decision
```

---

### 50. Sem auto-merge

A configuração atual não habilita auto-merge.

Isso preserva:

```text
automated discovery
       +
controlled acceptance
```

---

### 51. Dependabot e SHA pinning

SHA pinning cria estabilidade.

Dependabot cria manutenção.

A combinação resolve dois objetivos diferentes:

```text
SHA pinning
   ↓
não mudar silenciosamente
```

```text
Dependabot
   ↓
não ficar congelado indefinidamente
```

---

### 52. Dependabot e `uv.lock`

No ambiente Python, Dependabot monitora o ecossistema gerenciado pelo `uv`.

Atualizações propostas ainda precisam passar pelo processo de resolução,
validação e revisão do projeto.

---

### 53. Limitações do Dependabot

Um Pull Request automático não demonstra:

- compatibilidade;
- ausência de breaking changes;
- segurança;
- necessidade da atualização;
- adequação ao projeto.

O CI e a revisão permanecem necessários.

---

## Parte IX — Container como resultado da Supply Chain

### 54. Docker build

A aplicação final é empacotada em container.

O Dockerfile utiliza:

```text
python:3.12-slim
```

como base dos stages.

---

### 55. uv no builder

O builder copia `uv` de:

```text
ghcr.io/astral-sh/uv:0.11.27
```

utilizando explicitamente a versão:

```text
0.11.27
```

---

### 56. Dependências resolvidas no build

O builder executa:

```text
uv sync --locked
```

utilizando:

```text
pyproject.toml
uv.lock
README.md
```

---

### 57. Separação builder/runtime

A imagem final recebe o ambiente resolvido a partir do builder.

Isso reduz a quantidade de ferramentas presentes no runtime.

---

### 58. Trivy no resultado final

Depois da construção da imagem, Trivy analisa:

```text
soc-anomaly-detector:ci
```

---

### 59. Escopo do Trivy

A configuração atual utiliza:

```text
vuln-type: os,library
severity: HIGH,CRITICAL
scanners: vuln
```

Isso permite avaliar tanto componentes do sistema operacional quanto bibliotecas
identificadas na imagem.

---

### 60. Relação com o SBOM

CycloneDX e Trivy observam aspectos diferentes.

```text
CycloneDX
   ↓
dependency inventory
```

```text
Trivy
   ↓
vulnerability analysis of container
```

---

## Parte X — Vulnerability Evidence e Enforcement

### 61. Trivy report

A primeira execução do Trivy utiliza:

```text
format: json
exit-code: 0
```

e gera:

```text
trivy-report.json
```

---

### 62. Artifact

O relatório é publicado como:

```text
trivy-container-report
```

---

### 63. Security gate

A segunda execução utiliza:

```text
exit-code: 1
ignore-unfixed: true
severity: HIGH,CRITICAL
```

---

### 64. Política atual

A política pode ser resumida como:

```text
HIGH ou CRITICAL
       +
correção disponível
       ↓
CI failure
```

---

### 65. Visibility versus enforcement

O projeto separa:

```text
report
  ↓
visibility
```

de:

```text
gate
  ↓
enforcement
```

Isso permite preservar findings que não fazem o pipeline falhar segundo a
política atual.

---

## Parte XI — Lifecycle completo

### 66. Fluxo das dependências Python

```text
pyproject.toml
      ↓
dependency constraints
      ↓
uv.lock
      ↓
locked resolution
      ↓
uv sync --locked
      │
      ├──► tests
      ├──► pip-audit
      ├──► CycloneDX
      └──► Docker build
```

---

### 67. Fluxo das GitHub Actions

```text
Action dependency
      ↓
full commit SHA
      ↓
deterministic reference
      ↓
Dependabot monitoring
      ↓
update PR
      ↓
CI validation
      ↓
review
```

---

### 68. Fluxo do Gitleaks

```text
version selected
      ↓
archive download
      +
checksum download
      ↓
SHA-256 validation
      ↓
installation
      ↓
secret scan
```

---

### 69. Fluxo do container

```text
locked Python environment
      ↓
multi-stage build
      ↓
runtime image
      ↓
Trivy report
      +
Trivy security gate
```

---

### 70. Visão integrada

```text
                 DECLARAÇÃO
                     │
                     ▼
              pyproject.toml
                     │
                     ▼
                  LOCKING
                     │
                     ▼
                  uv.lock
                     │
                     ▼
              LOCKED INSTALL
                     │
          ┌──────────┼───────────┐
          ▼          ▼           ▼
      pip-audit     SBOM       Docker
          │          │           │
          ▼          ▼           ▼
      Known CVEs   Inventory    Runtime
                                 │
                                 ▼
                               Trivy

GitHub Actions ──► SHA pinning ──► Dependabot

Gitleaks release ──► SHA-256 verification ──► execution
```

---

## Parte XII — Defense in Depth da Supply Chain

### 71. Nenhum controle é suficiente isoladamente

Exemplos:

```text
lockfile
  ≠
security scanner
```

```text
SBOM
  ≠
vulnerability scanner
```

```text
SHA pinning
  ≠
trust validation
```

```text
Dependabot
  ≠
automatic security decision
```

---

### 72. Controles complementares

Uma mesma dependência pode ser observada por diferentes mecanismos:

```text
uv.lock
  ↓
versão resolvida
```

```text
pip-audit
  ↓
known vulnerability
```

```text
CycloneDX
  ↓
inventory
```

```text
Dependabot
  ↓
update opportunity
```

```text
Trivy
  ↓
runtime vulnerability context
```

---

### 73. Diferentes pontos da cadeia

Os controles atuam em momentos diferentes:

```text
before execution
during dependency resolution
during CI
during container build
after container construction
during maintenance
```

Isso aumenta a visibilidade sobre diferentes fases da supply chain.

---

## Parte XIII — Matriz dos controles

### 74. Matriz resumida

| Controle | Pergunta principal | Tipo | Bloqueia CI? |
|---|---|---|---:|
| `pyproject.toml` | o que declaramos? | metadata | não |
| `uv.lock` | o que foi resolvido? | locking | indiretamente |
| `uv sync --locked` | o lock continua válido? | reproducibility | sim |
| pip-audit | há vulnerabilidade conhecida? | SCA | sim |
| CycloneDX | quais componentes existem? | inventory | não diretamente |
| SHA pinning | qual Action exata roda? | integrity | estrutural |
| Gitleaks checksum | o archive corresponde ao checksum? | integrity | sim |
| Dependabot | existe atualização? | maintenance | não |
| Trivy report | o que o scanner encontrou? | evidence | não |
| Trivy gate | há HIGH/CRITICAL corrigível? | enforcement | sim |

---

### 75. Evidências produzidas

A supply chain deixa diferentes tipos de evidência:

```text
uv.lock
CycloneDX SBOM
Trivy JSON report
GitHub Actions logs
Dependabot Pull Requests
workflow com SHAs fixados
```

Esses artifacts e registros permitem auditoria posterior.

---

## Parte XIV — Limitações

### 76. Upstream trust

O projeto ainda depende de componentes externos.

Exemplos:

- PyPI;
- GitHub Actions;
- Docker base images;
- GitHub Container Registry;
- releases do Gitleaks.

Os controles atuais reduzem alguns riscos, mas não eliminam a necessidade de
confiar parcialmente nesses ecossistemas.

---

### 77. Lockfile compromise

Se o próprio lockfile for alterado de forma maliciosa e essa alteração for
aceita, a reprodutibilidade apenas reproduzirá o estado comprometido.

---

### 78. Vulnerabilidades desconhecidas

pip-audit e Trivy dependem de vulnerabilidades conhecidas.

Zero-days ou falhas ainda não publicadas podem não ser identificadas.

---

### 79. SHA pinning

SHA pinning evita mudança silenciosa da referência, mas não garante qualidade ou
segurança do commit escolhido.

---

### 80. Checksum

Checksum valida integridade contra o valor utilizado como referência.

Se artifact e checksum forem comprometidos em conjunto, essa validação pode não
ser suficiente.

---

### 81. Dependabot

Dependabot automatiza descoberta de atualizações, não avaliação completa de
risco.

---

### 82. SBOM

SBOM registra composição.

Não demonstra automaticamente:

- origem confiável;
- integridade;
- segurança;
- licença adequada;
- ausência de malware.

---

## Parte XV — Como explicar em entrevista

### 83. Explicação resumida

> Eu tratei software supply chain como um lifecycle. As dependências Python são
> declaradas no `pyproject.toml`, resolvidas e fixadas no `uv.lock` e instaladas
> no CI com `uv sync --locked`. Depois o ambiente passa por `pip-audit` e gera
> um SBOM CycloneDX. As GitHub Actions são fixadas por commit SHA e monitoradas
> pelo Dependabot. O Gitleaks é baixado em versão explícita e o archive é
> validado por SHA-256 antes da instalação. Por fim, o container resultante é
> analisado com Trivy.

---

### 84. “Por que lockfile e pip-audit?”

> Porque resolvem problemas diferentes. O lockfile torna o ambiente
> reproduzível. O pip-audit verifica vulnerabilidades conhecidas nas dependências
> resolvidas. Um lockfile pode reproduzir perfeitamente uma dependência
> vulnerável, por isso os dois controles são complementares.

---

### 85. “Por que SBOM se já existe pip-audit?”

> Porque o pip-audit é um controle de vulnerabilidade conhecida, enquanto o SBOM
> é um inventário de composição. O SBOM permite responder quais componentes
> existem no ambiente e pode ser reutilizado em outras análises e processos de
> auditoria.

---

### 86. “Por que SHA pinning e Dependabot juntos?”

> SHA pinning impede que uma referência mutável mude silenciosamente o código
> executado pelo CI. Dependabot evita que essa imutabilidade vire estagnação,
> monitorando atualizações e abrindo Pull Requests que ainda passam pelo CI e
> revisão manual.

---

### 87. “Por que verificar checksum do Gitleaks?”

> Porque o scanner é baixado durante o workflow. Antes de executar o binário, o
> pipeline valida o archive usando o checksum SHA-256 fornecido para aquela
> release. Isso adiciona uma verificação de integridade ao processo de instalação.

---

### 88. “O checksum garante que o Gitleaks é confiável?”

> Não. Ele confirma que o arquivo corresponde ao checksum utilizado. Se o
> upstream e o checksum forem comprometidos juntos, o controle pode não detectar
> isso. Por isso eu trato checksum como uma camada de integridade e não como
> garantia absoluta de confiança.

---

### 89. “Onde entra o Trivy nessa supply chain?”

> O Trivy observa o artifact final de runtime. Enquanto o pip-audit analisa
> dependências Python e o SBOM registra composição, o Trivy analisa
> vulnerabilidades identificadas no container resultante, incluindo componentes
> do sistema operacional e bibliotecas.

---

## Parte XVI — Possíveis evoluções

### 90. Provenance

Uma evolução futura pode incluir geração e verificação de provenance do build.

Isso permitiria registrar informações adicionais sobre:

- origem;
- processo de construção;
- identidade do workflow;
- artifact resultante.

---

### 91. Attestations

Attestations poderiam fornecer evidências assinadas sobre propriedades do build
e dos artifacts produzidos.

---

### 92. Assinatura de imagens

Uma futura publicação em registry poderia ser acompanhada de assinatura das
imagens e políticas de verificação antes do deployment.

---

### 93. Dependency review

Controles adicionais podem ser considerados para analisar mudanças de
dependências diretamente em Pull Requests.

---

### 94. License analysis

O SBOM também poderia ser utilizado futuramente como base para políticas de
licenciamento e compliance.

---

### 95. Policy as Code

Outra evolução possível é transformar políticas de supply chain em regras
automatizadas e versionadas.

---

### 96. Princípio de evolução

Novos controles devem responder a riscos concretos.

A estratégia desejada é:

```text
risco
  ↓
controle
  ↓
política
  ↓
automação
  ↓
evidência
```

e não simplesmente aumentar o número de ferramentas.

---

## Parte XVII — Relação com os demais documentos

### 97. DevSecOps overview

A visão geral está em:

```text
docs/devsecops/overview.md
```

---

### 98. CI pipeline

A implementação do GitHub Actions está descrita em:

```text
docs/devsecops/ci-pipeline.md
```

---

### 99. Security controls

A análise individual dos controles está em:

```text
docs/devsecops/security-controls.md
```

---

### 100. Próximo aprofundamento

O próximo documento específico da arquitetura DevSecOps é:

```text
docs/devsecops/container-security.md
```

Ele detalhará:

- Dockerfile;
- multi-stage build;
- runtime non-root;
- build context;
- secrets;
- atualização do sistema operacional;
- Trivy;
- política de vulnerability management;
- artifacts do container;
- limitações do modelo atual.

---

### 101. Objetivo final

A documentação de supply chain procura tornar explícita a cadeia:

```text
declare
  ↓
lock
  ↓
resolve
  ↓
audit
  ↓
inventory
  ↓
build
  ↓
scan
  ↓
monitor
  ↓
review
```

O objetivo é que atualizações, dependências e artifacts possam ser analisados
como partes de um lifecycle controlado e não como elementos independentes.
