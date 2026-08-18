# Segurança de Containers e Runtime Hardening

## 1. Objetivo

Este documento descreve a arquitetura de segurança do container utilizado pelo
`soc-transaction-anomaly-detector`.

O objetivo é registrar não apenas como a imagem é construída, mas também:

- quais decisões de hardening foram implementadas;
- como build e runtime são separados;
- como dependências são instaladas;
- quais arquivos podem entrar no build context;
- como secrets são tratados;
- como privilégios são reduzidos;
- como permissões de filesystem são preservadas;
- quais propriedades são validadas automaticamente no CI;
- como vulnerabilidades são registradas;
- qual política determina falha do pipeline;
- quais limitações permanecem no modelo atual.

A estratégia segue princípios de:

```text
minimal runtime
least privilege
externalized secrets
reproducible dependencies
defense in depth
automated validation
vulnerability visibility
policy enforcement
```

---

## 2. Visão geral

O fluxo atual pode ser representado como:

```text
Repository
    │
    ▼
Docker build context
    │
    ├── .dockerignore
    │
    ▼
Builder Stage
    │
    ├── Python 3.12 slim
    ├── uv 0.11.27
    ├── pyproject.toml
    ├── uv.lock
    └── uv sync --locked
    │
    ▼
Python virtual environment
    │
    ▼
Runtime Stage
    │
    ├── Python 3.12 slim
    ├── OS package updates
    ├── /app/.venv
    ├── /app/src
    ├── user: kuma
    └── writable reports
    │
    ▼
Runtime validation
    │
    ├── image builds
    ├── whoami = kuma
    └── /app/.env absent
    │
    ▼
Trivy
    │
    ├── JSON vulnerability report
    └── fixable HIGH/CRITICAL gate
```

---

## 3. Arquivos responsáveis

A arquitetura de container é definida principalmente por:

```text
Dockerfile
.dockerignore
.github/workflows/ci.yml
pyproject.toml
uv.lock
```

Cada arquivo possui uma responsabilidade diferente.

```text
Dockerfile
    ↓
estrutura e runtime da imagem

.dockerignore
    ↓
controle do build context

pyproject.toml
    ↓
declaração das dependências

uv.lock
    ↓
resolução bloqueada

ci.yml
    ↓
validação e enforcement
```

---

## Parte I — Arquitetura Multi-Stage

### 4. Builder stage

O primeiro stage é definido por:

```dockerfile
FROM python:3.12-slim AS builder
```

Sua função principal é preparar o ambiente Python utilizado posteriormente pelo
runtime.

---

### 5. Runtime stage

O segundo stage utiliza:

```dockerfile
FROM python:3.12-slim AS runtime
```

Ele representa a imagem efetivamente utilizada para executar a aplicação.

---

### 6. Separação builder/runtime

A arquitetura evita executar a aplicação diretamente no ambiente utilizado para
preparar dependências.

Conceitualmente:

```text
builder
   │
   ├── resolução
   ├── preparação
   └── virtual environment
          │
          ▼
runtime
   │
   ├── ambiente resolvido
   ├── código da aplicação
   └── usuário dedicado
```

---

### 7. Risco tratado pelo multi-stage build

Separar build e runtime reduz a quantidade de componentes que precisam
permanecer na imagem final.

Isso pode reduzir:

```text
ferramentas disponíveis
arquivos de desenvolvimento
superfície operacional
tamanho da imagem
componentes desnecessários
```

---

### 8. O que é transferido do builder

O runtime recebe:

```dockerfile
COPY --from=builder --chown=kuma:kuma /app/.venv /app/.venv
```

Portanto, o ambiente virtual resolvido no builder é reutilizado no stage final.

---

### 9. Código da aplicação

O código é adicionado por:

```dockerfile
COPY --chown=kuma:kuma src ./src
```

Isso significa que o Dockerfile não utiliza uma cópia indiscriminada de todo o
repositório para o runtime.

---

### 10. Conteúdo final explícito

No estado atual, os elementos copiados explicitamente para o runtime são
principalmente:

```text
/app/.venv
/app/src
```

Além dos componentes já presentes na imagem base e dos diretórios criados pelo
Dockerfile.

---

## Parte II — Imagem Base

### 11. Python 3.12 slim

Os dois stages utilizam:

```text
python:3.12-slim
```

Essa escolha mantém alinhamento com:

```toml
requires-python = ">=3.12,<3.13"
```

e com o Python utilizado no CI.

---

### 12. Motivo para imagem slim

Uma variante `slim` contém menos componentes que uma imagem Python mais ampla.

Isso contribui para:

```text
menor superfície
menos pacotes desnecessários
imagem mais compacta
menor quantidade potencial de componentes vulneráveis
```

---

### 13. Limitação da tag da imagem base

A referência atual é:

```text
python:3.12-slim
```

e não um digest imutável.

Isso significa que diferentes builds realizados em momentos distintos podem
receber conteúdo diferente quando a tag upstream é atualizada.

Portanto:

```text
tag de versão
      ≠
digest imutável
```

---

### 14. Trade-off atual

A utilização da tag permite receber atualizações da imagem base sem alterar
manualmente o Dockerfile.

Em contrapartida, reduz a reprodutibilidade absoluta do artifact final.

Essa é uma decisão que pode ser revista futuramente caso o projeto adote pinning
por digest e mecanismos automatizados de atualização da imagem base.

---

## Parte III — uv no Builder

### 15. Origem do uv

O builder obtém `uv` por:

```dockerfile
COPY --from=ghcr.io/astral-sh/uv:0.11.27 /uv /uvx /bin/
```

A versão indicada é:

```text
0.11.27
```

---

### 16. Separação do uv no runtime

O `uv` é utilizado no builder para preparar o ambiente.

O Dockerfile não copia explicitamente:

```text
/uv
/uvx
```

para o runtime.

Isso evita manter a ferramenta de resolução como dependência necessária à
execução normal da aplicação.

---

### 17. `UV_NO_CACHE`

O builder configura:

```text
UV_NO_CACHE=1
```

Isso evita depender de cache persistente do `uv` dentro da construção.

---

### 18. `UV_COMPILE_BYTECODE`

Também é definido:

```text
UV_COMPILE_BYTECODE=1
```

permitindo preparação de bytecode durante a instalação.

---

### 19. Arquivos copiados antes da resolução

Antes do `uv sync`, são copiados:

```text
pyproject.toml
uv.lock
README.md
```

---

### 20. Locked resolution

O comando utiliza:

```text
--locked
```

Isso exige compatibilidade da resolução com:

```text
uv.lock
```

---

### 21. `--no-dev`

O builder utiliza:

```text
--no-dev
```

para evitar grupos de desenvolvimento padrão no ambiente destinado ao runtime.

---

### 22. `--no-install-project`

Também é utilizado:

```text
--no-install-project
```

O projeto em si não é instalado como package durante essa etapa.

O runtime recebe o código diretamente em:

```text
/app/src
```

---

### 23. `--no-editable`

A opção:

```text
--no-editable
```

evita instalação editable.

---

### 24. Resultado da etapa

O principal artifact do builder utilizado posteriormente é:

```text
/app/.venv
```

---

### 25. Limitação da referência do uv

A origem atual utiliza:

```text
ghcr.io/astral-sh/uv:0.11.27
```

como tag.

Assim como a imagem Python, essa referência não está atualmente fixada por
digest no Dockerfile.

---

## Parte IV — Atualização do Sistema Operacional

### 26. Atualização dos índices

O runtime executa:

```text
apt-get update
```

antes da atualização dos pacotes.

---

### 27. Upgrade

Em seguida:

```text
apt-get upgrade -y
```

aplica atualizações disponíveis aos pacotes presentes na imagem.

---

### 28. Limpeza dos índices

Depois:

```text
rm -rf /var/lib/apt/lists/*
```

remove os índices baixados pelo APT.

---

### 29. Objetivo de segurança

Esse bloco foi introduzido para reduzir vulnerabilidades corrigíveis presentes
nos componentes do sistema operacional da imagem base.

---

### 30. Relação com o Trivy

O ciclo é:

```text
base image
    ↓
OS package update
    ↓
runtime image
    ↓
Trivy
```

A atualização busca reduzir findings corrigíveis antes da avaliação do scanner.

---

### 31. Trade-off de reprodutibilidade

`apt-get upgrade` depende do estado dos repositórios Debian disponível no
momento do build.

Assim:

```text
mesmo Dockerfile
+
momento diferente
=
pacotes potencialmente diferentes
```

Esse comportamento favorece atualização disponível no momento da construção,
mas reduz reprodutibilidade byte-a-byte.

---

### 32. Significado correto

A estratégia atual procura construir uma imagem com patches disponíveis naquele
momento.

Ela não representa:

```text
artifact totalmente determinístico
```

---

## Parte V — Configuração do Runtime

### 33. `PYTHONDONTWRITEBYTECODE`

O runtime define:

```text
PYTHONDONTWRITEBYTECODE=1
```

para impedir criação automática de arquivos `.pyc` durante execução normal.

---

### 34. `PYTHONUNBUFFERED`

Também é definido:

```text
PYTHONUNBUFFERED=1
```

para evitar buffering padrão da saída Python.

Isso é útil em containers porque torna logs disponíveis de maneira mais
imediata.

---

### 35. PATH

O ambiente configura:

```text
PATH="/app/.venv/bin:$PATH"
```

Assim, o Python e executáveis instalados no `.venv` são utilizados pelo runtime.

---

### 36. Workdir

O diretório operacional é:

```text
/app
```

---

## Parte VI — Least Privilege no Runtime

### 37. Grupo dedicado

O Dockerfile cria:

```text
group: kuma
```

como grupo de sistema.

---

### 38. Usuário dedicado

Também cria:

```text
user: kuma
```

como usuário de sistema associado ao grupo.

---

### 39. USER

O runtime é finalizado com:

```dockerfile
USER kuma
```

Portanto, o processo da aplicação não é iniciado como root por padrão.

---

### 40. Risco tratado

Executar a aplicação com privilégios administrativos dentro do container aumenta
o impacto potencial de determinadas falhas.

O usuário dedicado reduz os privilégios disponíveis ao processo.

---

### 41. Least privilege

Conceitualmente:

```text
root
  ↓
privilégios amplos
```

versus:

```text
kuma
  ↓
privilégios necessários ao runtime
```

---

### 42. Non-root não é isolamento absoluto

Executar como non-root não torna o container automaticamente seguro.

A proteção continua dependendo também de:

- configuração do runtime;
- kernel;
- host;
- capabilities;
- mounts;
- secrets;
- vulnerabilidades da aplicação;
- vulnerabilidades das dependências.

---

## Parte VII — Filesystem e Permissões

### 43. Diretório de reports

O Dockerfile cria:

```text
/app/reports/models
```

---

### 44. Ownership

Depois executa:

```text
chown -R kuma:kuma /app/reports
```

---

### 45. Motivo

A aplicação precisa produzir:

```text
reports
models
metrics
PDFs
gráficos
```

durante sua execução.

---

### 46. Non-root e funcionalidade

Sem permissões adequadas, uma imagem non-root poderia impedir a própria
aplicação de produzir artifacts legítimos.

A configuração procura equilibrar:

```text
least privilege
+
funcionalidade necessária
```

---

### 47. Ownership dos arquivos copiados

O `.venv` é copiado utilizando:

```text
--chown=kuma:kuma
```

---

### 48. Ownership do código

O código também utiliza:

```text
--chown=kuma:kuma
```

durante o `COPY`.

---

### 49. Escrita controlada

A intenção não é tornar todo `/app` indiscriminadamente gravável.

A necessidade operacional explícita está concentrada principalmente em:

```text
/app/reports
```

---

## Parte VIII — Build Context

### 50. `.dockerignore`

O arquivo:

```text
.dockerignore
```

reduz o conjunto de arquivos enviados ao daemon durante o build.

---

### 51. Git metadata

São excluídos:

```text
.git
.github
```

---

### 52. Virtual environments locais

Também ficam fora:

```text
.venv
venv
env
```

---

### 53. Caches Python

São excluídos:

```text
__pycache__
*.py[cod]
.pytest_cache
.ruff_cache
.coverage
htmlcov
```

---

### 54. IDEs

Também não entram:

```text
.vscode
.idea
```

---

### 55. Material de desenvolvimento

O contexto exclui:

```text
tests
docs
reports
```

---

### 56. Arquivos temporários

Também são ignorados:

```text
*.log
*.tmp
*.bak
```

---

### 57. Benefício

Reduzir o build context contribui para:

- menor transferência de dados;
- menor risco de copiar material desnecessário;
- menor exposição acidental;
- build mais controlado.

---

## Parte IX — Secret Protection

### 58. `.env`

Arquivos de ambiente reais são excluídos pelo `.dockerignore`.

Entre os padrões utilizados estão:

```text
.env
*.env
.env.*
```

---

### 59. `.env.example`

Existe uma exceção para:

```text
!.env.example
```

permitindo que um arquivo de exemplo permaneça elegível ao build context.

---

### 60. Elegível não significa copiado

O Dockerfile não utiliza:

```text
COPY . .
```

Portanto, estar disponível no context não significa que `.env.example` será
automaticamente colocado na imagem final.

---

### 61. Runtime secret model

Credenciais são esperadas externamente à imagem.

Conceitualmente:

```text
container image
      +
runtime environment
      ↓
application
```

---

### 62. Objetivo

A estratégia procura evitar:

```text
secret
  ↓
build
  ↓
image layer
  ↓
distribution
```

---

### 63. Teste automatizado

O CI executa:

```text
test ! -f /app/.env
```

dentro da imagem construída.

---

### 64. Propriedade validada

Esse teste comprova especificamente:

```text
/app/.env
```

ausente na imagem avaliada.

---

### 65. Limitação

Ele não comprova automaticamente:

```text
ausência de qualquer secret em qualquer arquivo
```

Nem verifica todos os paths possíveis.

---

### 66. Relação com Gitleaks

Os controles operam em superfícies diferentes:

```text
Gitleaks
   ↓
Git history
```

```text
.dockerignore + runtime check
   ↓
container image
```

---

## Parte X — Entrypoint Operacional

### 67. CMD

O comando padrão é:

```dockerfile
CMD ["python", "-m", "src.security_detector"]
```

---

### 68. Execução como módulo

A aplicação é iniciada como módulo Python:

```text
python -m src.security_detector
```

---

### 69. Usuário do processo

Como `USER kuma` aparece antes do `CMD`, o comando padrão é executado pelo
usuário:

```text
kuma
```

---

## Parte XI — Validação Automatizada no CI

### 70. Job dedicado

O workflow possui:

```text
Container Security
```

como job específico.

---

### 71. Runner

O job utiliza:

```text
ubuntu-latest
```

---

### 72. Timeout

O limite atual é:

```text
20 minutos
```

---

### 73. Build validation

O CI executa:

```text
docker build -t soc-anomaly-detector:ci .
```

Se a imagem não puder ser construída, o job falha.

---

### 74. Runtime user validation

Depois é executado:

```text
docker run --rm --entrypoint whoami soc-anomaly-detector:ci
```

---

### 75. Valor esperado

O resultado precisa ser:

```text
kuma
```

---

### 76. Enforcement

A expressão utiliza:

```text
test
```

no shell.

Se o usuário retornado for diferente:

```text
condition false
      ↓
exit code != 0
      ↓
CI failure
```

---

### 77. Secret exclusion validation

O CI também executa:

```text
test ! -f /app/.env
```

---

### 78. Intenção versus propriedade

Essas verificações são importantes porque distinguem:

```text
Dockerfile diz que deveria acontecer
```

de:

```text
container construído realmente apresenta a propriedade
```

---

## Parte XII — Trivy Vulnerability Report

### 79. Scanner

A imagem é analisada utilizando:

```text
aquasecurity/trivy-action
```

---

### 80. Referência da Action

A Action está fixada por full commit SHA no workflow.

O comentário registra:

```text
v0.36.0
```

para legibilidade.

---

### 81. Primeira execução

A primeira execução do Trivy possui função de geração de evidência.

---

### 82. Formato

Ela utiliza:

```text
format: json
```

---

### 83. Output

O arquivo gerado é:

```text
trivy-report.json
```

---

### 84. Severidades

O relatório é filtrado para:

```text
HIGH
CRITICAL
```

---

### 85. Vulnerability types

A configuração inclui:

```text
os
library
```

---

### 86. Scanner

O scanner selecionado é:

```text
vuln
```

---

### 87. Exit code

Essa execução utiliza:

```text
exit-code: "0"
```

---

### 88. Significado

Findings não provocam falha nessa execução específica.

O objetivo principal é:

```text
generate evidence
```

---

### 89. Artifact

O relatório é publicado com o nome:

```text
trivy-container-report
```

---

### 90. Ausência do arquivo

O upload utiliza:

```text
if-no-files-found: error
```

Logo, não produzir o relatório esperado é tratado como erro.

---

## Parte XIII — Trivy Security Gate

### 91. Segunda execução

Trivy é executado novamente com função de enforcement.

---

### 92. Formato

O gate utiliza:

```text
format: table
```

---

### 93. Exit code

A configuração utiliza:

```text
exit-code: "1"
```

---

### 94. `ignore-unfixed`

O gate define:

```text
ignore-unfixed: true
```

---

### 95. Severidades

São avaliadas:

```text
HIGH
CRITICAL
```

---

### 96. Política atual

Conceitualmente:

```text
HIGH ou CRITICAL
       +
fix disponível
       ↓
Trivy finding
       ↓
exit code 1
       ↓
CI failure
```

---

### 97. Findings sem fix

Uma vulnerabilidade sem correção disponível não participa do mesmo enforcement
devido a:

```text
ignore-unfixed: true
```

---

### 98. Isso não significa ausência

Uma vulnerabilidade ignorada pelo gate continua sendo uma vulnerabilidade
relevante para acompanhamento.

---

### 99. Visibility versus enforcement

A arquitetura separa:

```text
Trivy report
     ↓
visibility
```

de:

```text
Trivy gate
     ↓
enforcement
```

---

### 100. Benefício da separação

Isso permite manter evidência sobre findings sem obrigar que toda condição
detectada produza exatamente a mesma decisão de pipeline.

---

## Parte XIV — Vulnerability Management

### 101. Estado inicial versus estado corrigido

Durante o desenvolvimento do hardening, o container foi analisado antes e depois
da aplicação de atualizações do sistema operacional.

A finalidade desse processo foi utilizar o scanner não apenas como observador,
mas também como instrumento de validação de remediation.

---

### 102. Resultado relevante para a política

A validação final buscou atingir:

```text
0 fixable HIGH/CRITICAL
```

segundo a política do gate utilizada no projeto.

---

### 103. Formulação correta

Isso deve ser descrito como:

```text
0 vulnerabilidades HIGH/CRITICAL
com correção disponível dentro do escopo configurado
```

e não como:

```text
0 vulnerabilidades no container
```

---

### 104. Importância da precisão

A segunda afirmação seria tecnicamente excessiva porque:

- podem existir findings sem fix;
- podem existir severidades fora do filtro;
- podem existir vulnerabilidades ainda desconhecidas;
- scanners possuem limitações.

---

### 105. Remediation lifecycle

O fluxo pode ser representado como:

```text
scan
 ↓
finding
 ↓
fix disponível?
 ↓
remediation
 ↓
rebuild
 ↓
rescan
```

---

## Parte XV — Resultados Operacionais

### 106. Execução non-root

A imagem hardened foi validada executando como:

```text
kuma
```

---

### 107. Escrita em reports

O diretório de reports foi preparado para permitir geração legítima de artifacts
pelo usuário non-root.

---

### 108. Pipeline dentro do container

A aplicação foi validada executando o pipeline analítico no runtime do
container.

Essa validação é importante porque hardening não deve tornar a aplicação
inoperável.

---

### 109. Segredos em runtime

O fluxo de execução utiliza configuração sensível fornecida durante runtime,
sem incorporar o `.env` à imagem.

---

### 110. Segurança versus funcionalidade

O objetivo do hardening não é simplesmente remover permissões e componentes.

É preservar:

```text
menor privilégio possível
        +
funcionalidade necessária
```

---

## Parte XVI — Matriz de Controles

### 111. Matriz resumida

| Controle | Risco principal | Enforcement |
|---|---|---|
| Multi-stage build | ferramentas desnecessárias no runtime | estrutural |
| `python:3.12-slim` | superfície excessiva | estrutural |
| `uv sync --locked` | resolução divergente | build falha |
| `--no-dev` | dependências de desenvolvimento | estrutural |
| `.dockerignore` | arquivos desnecessários/sensíveis no context | estrutural |
| `USER kuma` | runtime privilegiado | validado no CI |
| ownership de reports | quebra funcional do non-root | runtime |
| `/app/.env` check | secret local na imagem | CI falha |
| OS package upgrade | vulnerabilidades corrigíveis do SO | build |
| Trivy JSON | falta de evidência | artifact |
| Trivy gate | fixable HIGH/CRITICAL | CI falha |
| timeout | job indefinido | CI |

---

### 112. Prevention

Controles predominantemente preventivos:

```text
slim image
multi-stage build
.dockerignore
--no-dev
non-root
secret externalization
```

---

### 113. Detection

Controles de detecção:

```text
runtime property checks
Trivy vulnerability scanning
```

---

### 114. Enforcement

Controles que podem impedir aprovação:

```text
Docker build
non-root validation
.env validation
Trivy gate
timeout
```

---

### 115. Evidence

Evidências preservadas:

```text
CI logs
Trivy JSON report
workflow status
Dockerfile
uv.lock
```

---

## Parte XVII — Defense in Depth

### 116. Por que não basta Trivy?

Trivy observa vulnerabilidades conhecidas nos componentes identificados.

Ele não garante:

```text
application logic security
secret hygiene
least privilege
correct filesystem permissions
secure business logic
```

---

### 117. Por que não basta non-root?

Non-root reduz privilégios disponíveis.

Ele não remove vulnerabilidades das dependências nem do sistema operacional.

---

### 118. Por que não basta `.dockerignore`?

`.dockerignore` reduz conteúdo disponível ao build.

Um Dockerfile ainda poderia copiar explicitamente algum conteúdo indesejado ou
introduzir um secret por outro mecanismo.

---

### 119. Combinação

Por isso a imagem utiliza múltiplos controles:

```text
build context reduction
       ↓
multi-stage build
       ↓
dependency locking
       ↓
OS patching
       ↓
non-root runtime
       ↓
secret validation
       ↓
vulnerability scanning
       ↓
security gate
```

---

## Parte XVIII — Limitações Atuais

### 120. Base image por tag

A imagem Python não está fixada por digest.

---

### 121. uv image por tag

A imagem utilizada para obter `uv` também está referenciada por tag/version.

---

### 122. `apt-get upgrade`

O conteúdo instalado depende do estado dos repositórios no momento do build.

---

### 123. Ausência de digest pinning

Sem digest pinning, dois builds realizados em momentos diferentes podem resolver
imagens base diferentes sob a mesma tag.

---

### 124. Secret check específico

O teste atual verifica especificamente:

```text
/app/.env
```

---

### 125. Trivy não cobre tudo

A configuração atual utiliza o scanner de vulnerabilidades.

Isso não equivale a:

- análise dinâmica;
- runtime monitoring;
- malware analysis completa;
- configuração Kubernetes;
- host hardening;
- network policy;
- análise lógica da aplicação.

---

### 126. Container não é sandbox absoluta

A segurança depende também do runtime e do host.

Um container não deve ser tratado automaticamente como fronteira perfeita de
segurança.

---

### 127. CI verde

Um job `Container Security` verde significa que as propriedades e políticas
automatizadas configuradas foram satisfeitas.

Não significa:

```text
container universalmente seguro
```

---

## Parte XIX — Possíveis Evoluções

### 128. Digest pinning

Uma evolução possível é fixar imagens base por digest.

Exemplo conceitual:

```text
python:3.12-slim@sha256:...
```

Isso aumentaria determinismo da referência.

---

### 129. Atualização automatizada de digests

Caso digest pinning seja adotado, a manutenção precisará ser automatizada ou
monitorada para evitar congelamento permanente.

---

### 130. HEALTHCHECK

Dependendo do modelo futuro de execução, um health check explícito poderia ser
considerado.

No estado atual, ele não faz parte do Dockerfile.

---

### 131. Read-only root filesystem

Uma evolução possível é avaliar execução com filesystem raiz read-only e paths
específicos graváveis.

Isso exigiria validação contra as necessidades reais da aplicação.

---

### 132. Capabilities

Políticas adicionais poderiam remover Linux capabilities desnecessárias no
runtime.

---

### 133. Image registry

Caso as imagens passem a ser publicadas, o projeto poderá adicionar um registry
controlado.

---

### 134. Image signing

Imagens publicadas poderiam ser assinadas e verificadas antes de deployment.

---

### 135. Provenance

O build poderia produzir provenance associando:

```text
source
workflow
build
artifact
```

---

### 136. Attestations

Attestations poderiam registrar propriedades verificáveis sobre o artifact
produzido.

---

### 137. Runtime policies

Em ambientes orquestrados, políticas adicionais poderiam controlar:

- usuário;
- capabilities;
- filesystem;
- networking;
- secrets;
- resource limits.

---

### 138. Princípio de evolução

Novos controles devem ser adicionados conforme risco concreto e necessidade
operacional.

A sequência desejada é:

```text
risco
  ↓
controle
  ↓
implementação
  ↓
teste
  ↓
enforcement
  ↓
evidência
```

---

## Parte XX — Como Explicar em Entrevista

### 139. Explicação resumida

> Eu construí o container usando multi-stage build. O primeiro stage resolve o
> ambiente Python com `uv` e `uv.lock`, e o segundo recebe apenas o virtualenv e
> o código necessários ao runtime. O processo roda como usuário `kuma`, com
> permissões específicas para reports. O `.dockerignore` reduz o build context e
> exclui arquivos de ambiente, e o CI valida tanto o usuário non-root quanto a
> ausência de `/app/.env`. Depois o Trivy gera um relatório JSON e executa um
> segundo scan como gate para vulnerabilidades HIGH ou CRITICAL corrigíveis.

---

### 140. “Por que multi-stage?”

> Porque ferramentas e arquivos necessários para construir a aplicação não
> precisam necessariamente existir no runtime. Eu separo essas responsabilidades
> e transfiro apenas o ambiente Python resolvido e o código necessário.

---

### 141. “Por que non-root?”

> Porque o processo da aplicação não precisa de privilégios de root. Se houver
> uma falha explorável, reduzir privilégios também reduz parte do impacto
> potencial disponível dentro do container.

---

### 142. “Como você garante que non-root funciona?”

> Eu não dependo apenas da linha `USER kuma` no Dockerfile. O GitHub Actions
> constrói a imagem, executa `whoami` dentro dela e exige que o resultado seja
> `kuma`.

---

### 143. “Como você protege secrets?”

> Arquivos `.env` reais são excluídos pelo `.dockerignore`, o Dockerfile copia
> apenas elementos explícitos e o CI executa a imagem para confirmar que
> `/app/.env` não existe. Credenciais necessárias são fornecidas em runtime.

---

### 144. “Isso prova que não existe nenhum secret na imagem?”

> Não. O teste atual prova uma propriedade específica: `/app/.env` está ausente.
> Por isso eu combino esse controle com secret scanning no histórico Git e evito
> tratar qualquer verificação isolada como garantia universal.

---

### 145. “Por que Trivy roda duas vezes?”

> Porque eu separei evidência de enforcement. O primeiro scan gera JSON para
> auditoria e não falha por findings. O segundo aplica a política de segurança e
> falha em HIGH ou CRITICAL corrigíveis.

---

### 146. “Por que `ignore-unfixed`?”

> Findings sem correção disponível continuam relevantes e permanecem visíveis
> no relatório, mas o gate atual bloqueia aquilo que já pode ser remediado. Isso
> separa visibilidade de capacidade imediata de correção.

---

### 147. “Então seu container tem zero vulnerabilidades?”

> Não é isso que o resultado demonstra. A formulação correta é que o gate não
> encontrou vulnerabilidades HIGH ou CRITICAL corrigíveis dentro do escopo
> configurado. Vulnerabilidades sem fix, outras severidades ou problemas ainda
> desconhecidos não podem ser transformados em inexistentes.

---

### 148. “Por que executar `apt-get upgrade`?”

> Durante o hardening, o scan identificou vulnerabilidades corrigíveis nos
> componentes do sistema operacional. A atualização dos pacotes reduziu esses
> findings. O trade-off é que o resultado do build passa a depender do estado
> dos repositórios Debian naquele momento.

---

### 149. “Sua imagem é totalmente reproduzível?”

> As dependências Python são bloqueadas pelo `uv.lock`, mas a imagem completa
> ainda possui fontes variáveis, como a tag `python:3.12-slim`, a referência do
> `uv` por tag e o `apt-get upgrade`. Portanto eu separo reprodutibilidade das
> dependências Python de reprodutibilidade absoluta da imagem.

---

## Parte XXI — Relação com os Demais Documentos

### 150. DevSecOps overview

A estratégia geral está em:

```text
docs/devsecops/overview.md
```

---

### 151. CI pipeline

O funcionamento do workflow está em:

```text
docs/devsecops/ci-pipeline.md
```

---

### 152. Security controls

Os controles individuais estão documentados em:

```text
docs/devsecops/security-controls.md
```

---

### 153. Supply chain

A cadeia de dependências e integridade está em:

```text
docs/devsecops/supply-chain.md
```

---

### 154. Papel deste documento

`container-security.md` concentra:

```text
Docker build
runtime
filesystem
privileges
secrets
OS patching
Trivy
container security policy
```

---

### 155. Visão final

A estratégia atual pode ser resumida como:

```text
REDUZIR O CONTEXTO
        ↓
SEPARAR BUILD E RUNTIME
        ↓
BLOQUEAR DEPENDÊNCIAS
        ↓
ATUALIZAR COMPONENTES
        ↓
REDUZIR PRIVILÉGIOS
        ↓
PROTEGER SECRETS
        ↓
VALIDAR PROPRIEDADES
        ↓
ESCANEAR
        ↓
GERAR EVIDÊNCIA
        ↓
APLICAR POLICY GATE
```

O objetivo é construir um runtime menor, verificável e sujeito a controles
automatizados, sem interpretar esses controles como garantia absoluta de
segurança.
