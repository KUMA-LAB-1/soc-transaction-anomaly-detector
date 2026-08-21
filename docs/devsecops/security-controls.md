# Controles de Segurança e Quality Gates

## 1. Objetivo

Este documento descreve os principais controles de qualidade e segurança
implementados no projeto `soc-transaction-anomaly-detector`.

O objetivo não é apenas listar ferramentas utilizadas, mas registrar:

- qual risco cada controle procura reduzir;
- em qual camada o controle atua;
- como o controle está configurado;
- quando sua execução ocorre;
- se o controle possui capacidade de bloquear o CI;
- quais evidências são produzidas;
- quais limitações permanecem mesmo quando o controle apresenta resultado
  satisfatório.

A estratégia adotada segue um princípio de defense in depth.

Nenhuma ferramenta individual é considerada prova suficiente de segurança.

Em vez disso, controles complementares são distribuídos entre código,
dependências, repositório, CI, software supply chain, container e runtime.

---

## 2. Modelo utilizado para documentar os controles

Cada controle pode ser analisado segundo a seguinte cadeia:

```text
Risco
  │
  ▼
Controle
  │
  ▼
Ferramenta ou mecanismo
  │
  ▼
Configuração
  │
  ▼
Execução
  │
  ▼
Enforcement
  │
  ▼
Evidência
  │
  ▼
Limitação residual
```

Essa estrutura é importante porque a presença de uma ferramenta no projeto não
significa, por si só, que existe um controle efetivo.

Por exemplo:

```text
scanner instalado
       ≠
scanner executado
       ≠
resultado analisado
       ≠
política de bloqueio
```

Por isso, a arquitetura procura distinguir explicitamente:

```text
ferramenta
política
enforcement
evidência
```

---

## 3. Categorias dos controles

Os controles atuais podem ser agrupados em:

| Camada | Controle principal |
|---|---|
| Código | Ruff |
| Código | Bandit SAST |
| Testes | Pytest |
| Testes | Coverage gate |
| Dependências | `uv.lock` |
| Dependências | pip-audit |
| Dependências | CycloneDX SBOM |
| Dependências | Dependabot |
| Repositório | Gitleaks |
| CI | `GITHUB_TOKEN` com least privilege |
| CI | Immutable GitHub Actions |
| CI | Timeouts |
| CI | Concurrency |
| Container | Multi-stage build |
| Container | Non-root runtime |
| Container | Exclusão de secrets |
| Container | Trivy vulnerability report |
| Container | Trivy security gate |

Esses controles possuem funções diferentes.

Alguns atuam principalmente como:

```text
prevenção
```

outros como:

```text
detecção
```

outros como:

```text
enforcement
```

e alguns produzem principalmente:

```text
evidência
rastreabilidade
inventário
```

---

## Parte I — Quality Engineering

### 4. Ruff

Ruff é utilizado como ferramenta de qualidade estática para o código Python.

Sua configuração principal está centralizada em:

```text
pyproject.toml
```

A configuração atual define:

```toml
[tool.ruff]
target-version = "py312"
line-length = 88
src = ["src"]
```

O projeto utiliza Python 3.12, portanto o target do Ruff permanece alinhado com a
versão utilizada pela aplicação e pelo CI.

---

### 5. Ruff lint

O lint atual seleciona:

```text
E4
E7
E9
F
I
```

Essas famílias cobrem categorias como:

- erros de estrutura e sintaxe;
- problemas relevantes detectáveis estaticamente;
- referências e imports;
- organização dos imports.

O objetivo não é habilitar indiscriminadamente todas as regras disponíveis.

A configuração atual mantém um conjunto controlado de regras compatível com o
estado do projeto.

---

### 6. Ruff format

Além do lint, o projeto verifica formatação:

```text
uv run ruff format --check .
```

A configuração inclui:

```toml
quote-style = "double"
indent-style = "space"
line-ending = "auto"
docstring-code-format = true
```

No CI, a formatação é validada sem modificar automaticamente os arquivos.

Portanto:

```text
formatação incorreta
        ↓
ruff format --check
        ↓
CI falha
```

---

### 7. Risco tratado pelo Ruff

O Ruff procura reduzir problemas relacionados a:

- inconsistência estrutural;
- erros detectáveis estaticamente;
- imports incorretos ou desorganizados;
- diferenças de estilo que dificultem revisão;
- código que viole as regras definidas pelo projeto.

Ele também contribui indiretamente para segurança ao aumentar previsibilidade e
qualidade do código.

Entretanto, Ruff não é tratado como ferramenta de segurança.

---

### 8. Enforcement do Ruff

No job `quality`, são executados:

```text
uv run ruff check .
uv run ruff format --check .
```

Como os comandos fazem parte diretamente do job, falhas impedem a conclusão
bem-sucedida dessa etapa.

Classificação:

```text
tipo: quality gate
bloqueia CI: sim
artifact formal: não
evidência: logs do workflow
```

---

### 9. Limitações do Ruff

Resultado limpo no Ruff não significa:

```text
código correto
código seguro
código funcional
```

Ele deve ser interpretado apenas dentro do escopo das regras configuradas.

Por isso, Ruff é complementado por:

```text
Pytest
Coverage
Bandit
pip-audit
Gitleaks
```

---

## Parte II — Testes e Coverage

### 10. Pytest

Pytest é utilizado como framework de testes automatizados.

A configuração principal está em:

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

A suíte é organizada entre testes unitários e testes de integração.

---

### 11. Testes unitários

O job `quality` executa:

```text
uv run pytest tests/unit
```

Os testes unitários procuram validar componentes de forma isolada.

Entre as áreas atualmente cobertas estão componentes relacionados a:

- validação de dados;
- resolução de colunas;
- acesso ao repositório;
- feature engineering;
- classificação;
- anomaly detection;
- avaliação de detectores;
- regressão;
- MITRE ATT&CK;
- métricas;
- geração de gráficos;
- geração de PDF;
- conectividade;
- orquestração do `SecurityDetector`.

---

### 12. Coverage gate

O projeto possui threshold mínimo de cobertura configurado em:

```text
95%
```

por meio de:

```text
--cov-fail-under=95
```

A configuração também determina:

```text
--cov=src
--cov-report=term-missing
```

Portanto, o CI não verifica apenas se os testes terminam com sucesso.

Também exige que a cobertura permaneça acima do threshold definido.

---

### 13. Risco tratado pelo coverage gate

Coverage não mede diretamente qualidade de testes.

Entretanto, ajuda a reduzir o risco de alterações relevantes permanecerem sem
execução durante a suíte automatizada.

Conceitualmente:

```text
mudança
  ↓
testes
  ↓
código exercitado
  ↓
coverage
  ↓
threshold
```

Se a cobertura cair abaixo de 95%, o job falha.

---

### 14. Integration Smoke

Além dos testes unitários, o pipeline executa:

```text
tests/integration/test_pipeline_smoke.py
```

com:

```text
uv run pytest tests/integration/test_pipeline_smoke.py -v --no-cov
```

Esse teste procura validar a integração do pipeline analítico completo utilizando
dados apropriados ao ambiente de teste.

Seu objetivo é detectar falhas que podem não aparecer quando componentes são
testados isoladamente.

---

### 15. Limitações dos testes

Mesmo com cobertura elevada, os testes não demonstram ausência de bugs.

Também não demonstram automaticamente:

- segurança;
- robustez contra entradas não previstas;
- comportamento correto em todos os ambientes;
- validade estatística dos modelos;
- ausência de falhas de integração externa.

Por isso:

```text
coverage alto
      ≠
corretude total
```

---

## Parte III — Static Application Security Testing

### 16. Bandit SAST

Bandit é utilizado como ferramenta de Static Application Security Testing para o
código Python.

Ele está incluído no grupo:

```text
security
```

do `pyproject.toml`:

```text
bandit[toml]>=1.9.4
```

A configuração atual exclui:

```text
tests
```

por meio de:

```toml
[tool.bandit]
exclude_dirs = ["tests"]
```

---

### 17. Escopo do Bandit

O CI executa:

```text
uv run bandit -c pyproject.toml -r src
```

Portanto, o foco do controle é o código Python da aplicação localizado em:

```text
src/
```

O objetivo é procurar padrões de implementação associados a riscos de segurança
conhecidos pela ferramenta.

---

### 18. Risco tratado pelo Bandit

O Bandit procura reduzir o risco de introdução de padrões Python potencialmente
inseguros.

Conceitualmente:

```text
código Python
     ↓
análise estática
     ↓
Bandit
     ↓
finding
     ↓
falha ou aprovação
```

---

### 19. Enforcement do Bandit

Bandit faz parte do job `quality`.

Assim, um resultado que faça o comando retornar código de saída diferente de
zero impede a conclusão bem-sucedida do job.

Classificação:

```text
tipo: SAST
bloqueia CI: sim
artifact formal: não
evidência: output do scanner no workflow
```

---

### 20. Limitações do Bandit

Resultado limpo no Bandit não demonstra que a aplicação é segura.

Bandit detecta classes específicas de padrões inseguros em Python.

Ele não substitui:

- revisão manual;
- testes de segurança;
- SCA;
- secret scanning;
- análise de container;
- modelagem de ameaças;
- controles de runtime.

Portanto:

```text
Bandit limpo
     ≠
ausência de vulnerabilidades
```

---

## Parte IV — Software Composition Analysis

### 21. pip-audit

`pip-audit` é utilizado para verificar o ambiente Python resolvido em busca de
vulnerabilidades conhecidas em dependências.

A ferramenta pertence ao grupo:

```text
security
```

e é executada no CI por:

```text
uv run pip-audit
```

---

### 22. Risco tratado pelo pip-audit

Aplicações podem possuir vulnerabilidades mesmo quando o código próprio não
contém um problema conhecido.

Isso ocorre porque bibliotecas externas também fazem parte da superfície de
ataque.

O controle procura responder:

```text
quais dependências estão instaladas?
             +
existem vulnerabilidades conhecidas associadas?
```

---

### 23. Enforcement do pip-audit

O comando é executado diretamente no job `quality`.

Uma falha relevante retornada pela ferramenta pode impedir o sucesso do job.

Classificação:

```text
tipo: SCA
bloqueia CI: sim
artifact formal: não
evidência: output do audit no workflow
```

---

### 24. Limitações do pip-audit

Um audit limpo significa apenas que não foram identificadas vulnerabilidades
conhecidas pela ferramenta no conjunto analisado naquele momento.

Não significa:

```text
dependência segura
ausência de zero-day
ausência de comprometimento de supply chain
ausência de comportamento malicioso
```

A eficácia do controle depende das informações disponíveis nas bases utilizadas
pela ferramenta.

---

## Parte V — Secret Scanning

### 25. Gitleaks

Gitleaks é utilizado para procurar possíveis secrets no histórico Git.

O projeto utiliza explicitamente:

```text
Gitleaks 8.18.4
```

Essa versão foi selecionada após validação controlada realizada durante a
implementação do controle.

---

### 26. Histórico Git completo

O job de secret scanning utiliza:

```yaml
fetch-depth: 0
```

Isso é importante porque um secret removido do estado atual do repositório pode
continuar existindo em commits anteriores.

Portanto:

```text
working tree limpa
        ≠
histórico Git limpo
```

O controle procura analisar o histórico disponível no checkout completo.

---

### 27. Integridade do binário do Gitleaks

O workflow não apenas baixa o binário.

Também baixa os checksums correspondentes e utiliza:

```text
sha256sum -c -
```

antes da instalação.

Conceitualmente:

```text
download
   ↓
checksum oficial
   ↓
verificação SHA-256
   ↓
extração
   ↓
instalação
```

Isso reduz o risco de executar um arquivo baixado sem qualquer verificação de
integridade.

---

### 28. Redação dos findings

O scan utiliza:

```text
--redact
```

O objetivo é evitar que valores identificados como possíveis secrets sejam
reproduzidos integralmente no output do CI.

A execução atual é:

```text
gitleaks detect --source . --redact --verbose
```

---

### 29. Enforcement do Gitleaks

O scanner possui job dedicado:

```text
Secret Scanning
```

Classificação:

```text
tipo: secret scanning
bloqueia CI: sim
artifact formal: não
evidência: output do scanner
escopo: histórico Git disponível
```

---

### 30. Limitações do Gitleaks

Secret scanners trabalham com regras e heurísticas.

Consequentemente:

```text
scan limpo
   ≠
garantia de ausência de secrets
```

Podem existir:

- formatos não reconhecidos;
- valores que não correspondem às regras;
- falsos negativos;
- falsos positivos;
- secrets presentes fora do escopo analisado.

Por isso, secret scanning é apenas uma camada do modelo de segurança.

---

## Parte VI — Dependency Locking e Reprodutibilidade

### 31. uv

O projeto utiliza `uv` para resolução e sincronização do ambiente Python.

O CI executa sincronizações utilizando:

```text
--locked
```

Esse comportamento relaciona a instalação ao estado registrado no lockfile.

---

### 32. uv.lock

O `uv.lock` funciona como mecanismo de reprodutibilidade das dependências
resolvidas.

Conceitualmente:

```text
pyproject.toml
      ↓
resolução
      ↓
uv.lock
      ↓
ambiente reproduzível
```

Isso reduz variações causadas por resolução diferente de dependências entre
execuções.

---

### 33. Locking não é security scanning

É importante distinguir:

```text
uv.lock
```

de:

```text
pip-audit
```

O primeiro contribui principalmente para:

```text
reprodutibilidade
determinismo
controle de versões resolvidas
```

O segundo contribui para:

```text
identificação de vulnerabilidades conhecidas
```

Um lockfile pode reproduzir perfeitamente uma dependência vulnerável.

Por isso os dois controles são complementares.

---

## Parte VII — Software Bill of Materials

### 34. CycloneDX SBOM

O projeto gera automaticamente um Software Bill of Materials no formato
CycloneDX.

A ferramenta utilizada pertence ao grupo de segurança:

```text
cyclonedx-bom
```

---

### 35. Geração do SBOM

O workflow executa:

```text
cyclonedx-py environment
```

utilizando:

```text
--pyproject pyproject.toml
--output-reproducible
--output-format JSON
--output-file artifacts/sbom.cdx.json
```

O resultado é um inventário machine-readable do ambiente de dependências
representado durante a execução.

---

### 36. Reprodutibilidade do SBOM

A opção:

```text
--output-reproducible
```

é utilizada para reduzir elementos variáveis da geração e permitir comparação
mais consistente entre outputs equivalentes.

Isso melhora:

- rastreabilidade;
- comparação;
- auditoria;
- automação posterior.

---

### 37. SBOM como artifact

O arquivo:

```text
artifacts/sbom.cdx.json
```

é publicado no GitHub Actions com o nome:

```text
cyclonedx-sbom
```

Esse é um dos artifacts formais produzidos pelo pipeline.

---

### 38. Risco tratado pelo SBOM

O SBOM procura reduzir a falta de visibilidade sobre a composição do software.

Ele ajuda a responder:

```text
o que existe neste ambiente?
```

em vez de:

```text
isso é seguro?
```

Essa diferença é fundamental.

---

### 39. Limitações do SBOM

SBOM é inventário.

Ele não é, isoladamente:

- scanner de vulnerabilidade;
- garantia de integridade;
- garantia de procedência;
- prova de ausência de código malicioso;
- mecanismo automático de correção.

Portanto:

```text
SBOM
  =
visibilidade e rastreabilidade

SBOM
  ≠
prova de segurança
```

---

## Parte VIII — Dependency Monitoring

### 40. Dependabot

Dependabot é utilizado para monitorar atualizações disponíveis.

A configuração está localizada em:

```text
.github/dependabot.yml
```

---

### 41. Ecossistemas monitorados

Atualmente são monitorados:

```text
github-actions
uv
```

Isso cobre:

- dependências utilizadas pelo GitHub Actions;
- dependências Python gerenciadas pelo ambiente `uv`.

---

### 42. Frequência

A configuração utiliza:

```text
weekly
```

para os dois ecossistemas.

Os pull requests são direcionados para:

```text
feature/devsecops
```

e existe limite de:

```text
5
```

pull requests abertos por ecossistema.

---

### 43. Dependabot não faz auto-merge

A estratégia atual não transforma atualização disponível em mudança automática
na aplicação.

O fluxo esperado é:

```text
Dependabot detecta atualização
            ↓
abre Pull Request
            ↓
CI executa
            ↓
controles avaliam mudança
            ↓
revisão
            ↓
merge deliberado
```

Isso preserva revisão humana e validação automatizada.

---

### 44. Dependabot e pip-audit

Os controles possuem responsabilidades diferentes:

```text
Dependabot
   ↓
descoberta e proposta de atualização
```

```text
pip-audit
   ↓
identificação de vulnerabilidades conhecidas
```

Dependabot contribui para manutenção.

pip-audit contribui para análise de risco conhecido nas dependências.

---

### 45. Limitações do Dependabot

Uma atualização disponível não significa automaticamente:

```text
atualização segura
atualização compatível
atualização necessária
```

Por isso o projeto não utiliza a existência do PR como justificativa automática
para merge.

---

## Parte IX — Segurança da Supply Chain do CI

### 46. Risco das GitHub Actions

GitHub Actions executadas pelo workflow também fazem parte da software supply
chain.

Uma referência mutável pode mudar o código executado pelo CI sem que o arquivo
do workflow seja alterado.

Exemplo conceitual:

```text
action@tag-mutável
       ↓
tag passa a apontar para outro conteúdo
       ↓
workflow executa código diferente
```

---

### 47. Immutable Action References

As Actions utilizadas pelo workflow são referenciadas por full commit SHA.

Exemplo conceitual:

```text
uses: action@FULL_COMMIT_SHA
```

Isso transforma a referência executada pelo workflow em uma identificação
imutável daquele commit.

---

### 48. Comentários de versão

Ao lado do SHA é preservado um comentário legível, como:

```text
# v7
# v6
# v0.36.0
```

O SHA define o conteúdo executado.

O comentário facilita compreensão e manutenção humana.

Assim:

```text
SHA
  ↓
integridade da referência

comentário
  ↓
legibilidade operacional
```

---

### 49. Actions atualmente protegidas

O workflow utiliza pinning por SHA para Actions como:

- `actions/checkout`;
- `actions/setup-python`;
- `actions/upload-artifact`;
- `astral-sh/setup-uv`;
- `aquasecurity/trivy-action`.

Isso reduz o risco de mudança silenciosa associada ao uso exclusivo de tags
mutáveis.

---

### 50. Limitações do SHA pinning

SHA pinning responde principalmente:

```text
o código referenciado mudou?
```

Ele não responde automaticamente:

```text
o código referenciado é seguro?
```

Se um commit já contiver comportamento malicioso ou vulnerável, fixá-lo por SHA
apenas torna aquela referência estável.

Portanto, pinning reduz uma classe de risco, mas não substitui avaliação da
dependência.

---

## Parte X — Segurança do GitHub Actions

### 51. Least privilege do GITHUB_TOKEN

O workflow define:

```yaml
permissions:
  contents: read
```

Isso limita o token padrão do workflow ao acesso necessário para leitura do
conteúdo.

O princípio aplicado é:

```text
não conceder permissão
que o workflow não precisa utilizar
```

---

### 52. Risco tratado pelo least privilege

Se uma etapa do workflow for comprometida, permissões excessivas podem ampliar o
impacto possível.

Reduzir privilégios não impede necessariamente o comprometimento inicial.

Entretanto, reduz capacidades disponíveis após esse comprometimento.

Conceitualmente:

```text
comprometimento
      +
token excessivo
      ↓
impacto maior
```

versus:

```text
comprometimento
      +
token restrito
      ↓
superfície de impacto reduzida
```

---

### 53. Timeouts

Os jobs possuem limites explícitos de execução.

Os jobs convencionais utilizam timeout menor, enquanto operações de container
possuem janela maior.

Isso reduz o risco de jobs permanecerem executando indefinidamente por:

- travamento;
- deadlock;
- falha externa;
- comportamento inesperado;
- consumo desnecessário de runner.

---

### 54. Concurrency

O workflow utiliza:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

Assim, execuções obsoletas do mesmo workflow/ref podem ser canceladas quando uma
execução mais nova é iniciada.

Esse controle é principalmente operacional.

Ele reduz desperdício e evita validações antigas continuarem competindo com
execuções mais recentes.

---

## Parte XI — Container Hardening

### 55. Multi-stage build

O Dockerfile utiliza duas etapas principais:

```text
builder
runtime
```

A etapa de build prepara o ambiente necessário.

A imagem final recebe apenas o necessário para execução.

Conceitualmente:

```text
builder
  │
  ├── resolução de dependências
  ├── ferramentas necessárias ao build
  │
  ▼
runtime
  │
  ├── ambiente Python
  └── código da aplicação
```

---

### 56. Separação entre build e runtime

O runtime não precisa carregar toda a superfície utilizada durante construção e
desenvolvimento.

Isso reduz:

- tamanho da imagem;
- quantidade de ferramentas disponíveis;
- superfície operacional;
- componentes desnecessários no runtime.

---

### 57. Runtime non-root

O Dockerfile cria:

```text
group: kuma
user: kuma
```

e define:

```dockerfile
USER kuma
```

A aplicação, portanto, não é executada como root por padrão dentro do container.

---

### 58. Risco tratado pelo non-root runtime

Executar aplicações como root amplia o impacto potencial de determinadas
falhas.

O non-root runtime procura reduzir os privilégios disponíveis para o processo da
aplicação.

Conceitualmente:

```text
aplicação
   ↓
usuário dedicado
   ↓
privilégios reduzidos
```

---

### 59. Validação automática do usuário

O CI não depende apenas da existência de:

```dockerfile
USER kuma
```

no Dockerfile.

Ele executa a imagem e verifica:

```text
whoami
```

esperando:

```text
kuma
```

Isso transforma uma intenção de configuração em uma propriedade validada
durante o CI.

---

### 60. Diretórios graváveis

A aplicação precisa produzir reports.

Por isso o Dockerfile cria:

```text
/app/reports/models
```

e ajusta ownership para:

```text
kuma:kuma
```

Isso permite manter o runtime non-root sem impedir a geração legítima de
artifacts da aplicação.

---

## Parte XII — Runtime Secret Protection

### 61. Exclusão de arquivos sensíveis

O `.dockerignore` exclui padrões como:

```text
.env
*.env
.env.*
```

Isso reduz a possibilidade de arquivos locais de configuração sensível entrarem
acidentalmente no build context.

---

### 62. Outros arquivos excluídos

O build context também exclui elementos que não são necessários ao runtime,
como:

- `.git`;
- `.github`;
- `.venv`;
- caches;
- arquivos de IDE;
- testes;
- documentação;
- reports;
- logs;
- arquivos temporários.

Essa redução contribui para minimizar o conteúdo disponível durante o build.

---

### 63. `.env.example`

O `.dockerignore` permite explicitamente:

```text
!.env.example
```

Isso diferencia um arquivo de exemplo de arquivos reais de configuração.

Entretanto, o Dockerfile atual copia para a imagem final apenas os elementos
explicitamente necessários.

Portanto, permitir `.env.example` no build context não significa que o arquivo
seja automaticamente incorporado ao runtime.

---

### 64. Verificação do `.env` no CI

O CI executa uma validação explícita:

```text
test ! -f /app/.env
```

dentro da imagem construída.

Isso verifica que o arquivo real `.env` não está presente em:

```text
/app/.env
```

no runtime testado.

---

### 65. Limitação da verificação de secrets

A verificação atual é específica.

Ela confirma:

```text
/app/.env não existe
```

Isso não prova que:

- nenhum outro arquivo contenha credenciais;
- nenhuma variável tenha sido exposta;
- nenhuma secret tenha sido incorporada por outro mecanismo;
- nenhum valor sensível exista em outra camada ou path.

Portanto, esse teste é uma evidência específica e não uma prova universal de
ausência de secrets na imagem.

---

## Parte XIII — Container Vulnerability Management

### 66. Trivy

Trivy é utilizado para analisar vulnerabilidades presentes na imagem construída.

O workflow utiliza a Action:

```text
aquasecurity/trivy-action
```

fixada por commit SHA.

A versão humana correspondente permanece registrada no comentário do workflow.

---

### 67. Dois usos diferentes do Trivy

O pipeline utiliza Trivy com duas finalidades distintas:

```text
1. vulnerability report
2. security gate
```

Essa distinção é importante.

Um produz evidência.

O outro implementa enforcement.

---

### 68. Trivy vulnerability report

A primeira execução utiliza:

```text
format: json
output: trivy-report.json
exit-code: "0"
severity: HIGH,CRITICAL
scanners: vuln
```

O objetivo é produzir um relatório persistente mesmo quando findings são
identificados.

O arquivo é publicado como artifact:

```text
trivy-container-report
```

---

### 69. Trivy security gate

A segunda execução utiliza:

```text
format: table
exit-code: "1"
ignore-unfixed: true
severity: HIGH,CRITICAL
scanners: vuln
```

A política atual é, portanto:

```text
HIGH ou CRITICAL
        +
correção disponível
        ↓
falha do CI
```

---

### 70. Por que separar report e gate?

Se existisse apenas o gate, a política de falha e a necessidade de evidência
ficariam acopladas.

A separação permite:

```text
scan completo de interesse
        ↓
JSON
        ↓
artifact
```

e paralelamente:

```text
política de vulnerabilidade
        ↓
fixable HIGH/CRITICAL
        ↓
enforcement
```

Isso preserva visibilidade sobre findings ao mesmo tempo que aplica uma política
objetiva de bloqueio.

---

### 71. Vulnerabilidades sem correção disponível

O gate utiliza:

```text
ignore-unfixed: true
```

Assim, vulnerabilidades HIGH/CRITICAL sem correção disponível não são utilizadas
pela execução de enforcement para falhar o pipeline segundo essa política.

Isso não significa que sejam consideradas inexistentes ou seguras.

Elas permanecem relevantes para:

- observação;
- acompanhamento;
- análise;
- futura remediação.

---

### 72. Limitações do Trivy

Resultado satisfatório depende de fatores como:

- cobertura do scanner;
- bases de vulnerabilidades disponíveis;
- identificação correta dos componentes;
- publicação das vulnerabilidades;
- disponibilidade de versões corrigidas.

Portanto:

```text
Trivy gate verde
       ≠
container livre de vulnerabilidades
```

O significado correto é:

```text
nenhuma condição configurada para bloqueio
foi identificada naquela execução
```

---

## Parte XIV — Security Artifacts

### 73. Artifacts formais atuais

O pipeline publica atualmente dois artifacts de segurança principais:

```text
cyclonedx-sbom
trivy-container-report
```

Eles representam responsabilidades diferentes.

---

### 74. CycloneDX como inventário

O artifact:

```text
cyclonedx-sbom
```

registra a composição do ambiente de dependências em formato machine-readable.

Seu valor principal está em:

- inventário;
- rastreabilidade;
- automação;
- análise posterior.

---

### 75. Trivy como evidência de vulnerabilidades

O artifact:

```text
trivy-container-report
```

registra findings HIGH/CRITICAL identificados pelo scan configurado da imagem.

Ele permite preservar evidência além do output temporário do job.

---

### 76. Evidência não é enforcement

Um conceito importante da arquitetura é:

```text
artifact
   ≠
gate
```

Um artifact preserva informação.

Um gate decide se determinada condição deve bloquear a pipeline.

Alguns controles podem fazer ambos, mas as responsabilidades devem permanecer
conceitualmente separadas.

---

## Parte XV — Matriz dos Controles

### 77. Matriz resumida

| Controle | Principal risco tratado | Bloqueia CI? | Evidência principal |
|---|---|---:|---|
| Ruff lint | problemas estáticos e imports | sim | logs |
| Ruff format | inconsistência de formatação | sim | logs |
| Pytest | regressões funcionais | sim | logs |
| Coverage gate | cobertura abaixo do threshold | sim | relatório no terminal |
| Bandit | padrões Python potencialmente inseguros | sim | logs SAST |
| pip-audit | vulnerabilidades conhecidas em dependências | sim | logs do audit |
| Gitleaks | secrets no histórico Git | sim | logs redacted |
| `uv.lock` | resolução não reproduzível | indiretamente | lockfile |
| CycloneDX | falta de inventário de dependências | não diretamente | SBOM JSON |
| Dependabot | dependências desatualizadas | não | Pull Requests |
| SHA pinning | alteração silenciosa de Actions | estrutural | workflow |
| least privilege | permissões excessivas do token | estrutural | workflow |
| timeout | execução indefinida | sim, quando excedido | status do job |
| concurrency | execução obsoleta concorrente | cancela execução antiga | status do workflow |
| non-root | privilégios excessivos no runtime | sim, via teste atual | validação do container |
| `.env` exclusion | secret local dentro da imagem | sim, via teste específico | validação do container |
| Trivy report | falta de visibilidade de vulnerabilidades | não | JSON artifact |
| Trivy gate | vulnerabilidade HIGH/CRITICAL corrigível | sim | scan + status do job |

---

### 78. Prevenção, detecção, enforcement e evidência

Uma visão alternativa pode classificar os controles por função predominante.

### Prevenção e redução de superfície

```text
SHA pinning
least privilege
multi-stage Docker build
non-root runtime
.dockerignore
dependency locking
```

### Detecção

```text
Ruff
Bandit
pip-audit
Gitleaks
Pytest
Trivy
```

### Enforcement

```text
Ruff gates
Pytest
coverage >= 95%
Bandit
pip-audit
Gitleaks
non-root validation
.env validation
Trivy fixable HIGH/CRITICAL gate
timeouts
```

### Evidência e rastreabilidade

```text
CI logs
uv.lock
CycloneDX SBOM
Trivy JSON report
Dependabot Pull Requests
Git history
```

Um mesmo controle pode participar de mais de uma categoria.

---

## Parte XVI — Defense in Depth

### 79. Por que múltiplos controles?

Cada ferramenta possui um campo de visão diferente.

Exemplo:

```text
Ruff
  ↓
qualidade estática
```

```text
Bandit
  ↓
padrões de segurança Python
```

```text
pip-audit
  ↓
vulnerabilidades conhecidas em dependências
```

```text
Gitleaks
  ↓
possíveis secrets
```

```text
Trivy
  ↓
vulnerabilidades no container
```

Nenhuma delas substitui as demais.

---

### 80. Exemplo de sobreposição complementar

Considere uma dependência Python vulnerável.

Ela pode aparecer em diferentes controles:

```text
uv.lock
   ↓
registra versão resolvida
```

```text
pip-audit
   ↓
procura vulnerabilidade conhecida
```

```text
CycloneDX
   ↓
registra componente no inventário
```

```text
Dependabot
   ↓
pode propor atualização
```

```text
Trivy
   ↓
pode identificar o componente no contexto da imagem
```

Isso demonstra defense in depth sem transformar ferramentas diferentes em
duplicações desnecessárias.

---

### 81. Falha de um controle não invalida todos os outros

A arquitetura procura evitar dependência excessiva de uma única ferramenta.

Se um scanner não possuir regra para determinada vulnerabilidade, outros
controles ainda podem fornecer:

- detecção complementar;
- evidência;
- limitação de impacto;
- rastreabilidade;
- oportunidade de revisão.

Defense in depth não significa que todas as falhas serão detectadas.

Significa que o sistema não depende conscientemente de uma única barreira.

---

## Parte XVII — O que o CI realmente garante

### 82. Interpretação correta de um pipeline verde

Um CI verde significa que:

```text
as condições automatizadas configuradas
foram satisfeitas naquela execução
```

Ele não significa:

```text
software seguro
software sem bugs
modelo estatisticamente perfeito
container sem qualquer vulnerabilidade
ausência absoluta de secrets
supply chain confiável em todos os níveis
```

Essa distinção evita transformar automação em falsa garantia.

---

### 83. Propriedades verificadas atualmente

Entre as propriedades verificadas estão:

- conformidade com as regras Ruff configuradas;
- conformidade com Ruff format;
- sucesso dos testes unitários;
- cobertura mínima de 95%;
- sucesso do integration smoke test;
- ausência de findings bloqueantes segundo Bandit;
- resultado aceitável segundo pip-audit;
- resultado aceitável segundo Gitleaks;
- geração do SBOM;
- construção da imagem Docker;
- execução como usuário `kuma`;
- ausência de `/app/.env`;
- geração do relatório Trivy;
- ausência de vulnerabilidades fixable HIGH/CRITICAL segundo a política atual.

---

### 84. Propriedades não demonstradas

O pipeline não demonstra automaticamente:

- ausência de zero-days;
- ausência de vulnerabilidades lógicas;
- ausência de falhas de autorização;
- ausência de abuso de regras de negócio;
- segurança de toda infraestrutura externa;
- segurança do host Docker;
- segurança absoluta das Actions utilizadas;
- ausência de comprometimento upstream;
- validade estatística geral dos modelos;
- comportamento correto para qualquer dataset possível.

---

## Parte XVIII — Como explicar em entrevista

### 85. Explicação resumida

Uma forma curta de explicar a estratégia é:

> O projeto utiliza uma arquitetura DevSecOps em camadas. Qualidade e testes são
> validados com Ruff, Pytest e coverage gate; o código Python passa por SAST com
> Bandit; dependências são auditadas com pip-audit, mantidas sob lock e
> inventariadas por SBOM CycloneDX; o histórico Git é analisado com Gitleaks; a
> imagem Docker utiliza multi-stage build e runtime non-root; e Trivy produz
> evidência de vulnerabilidades e bloqueia vulnerabilidades HIGH ou CRITICAL
> corrigíveis. O próprio CI também é endurecido com least privilege, timeouts,
> concurrency e Actions fixadas por commit SHA.

---

### 86. Como explicar defense in depth

Uma resposta possível:

> Eu evitei tratar qualquer scanner como prova de segurança. Cada ferramenta
> cobre uma classe diferente de risco. Bandit analisa padrões no código Python,
> pip-audit olha vulnerabilidades conhecidas nas dependências, Gitleaks procura
> secrets no histórico e Trivy analisa a imagem. Além disso, existem controles
> preventivos como non-root, SHA pinning e least privilege. A ideia é combinar
> prevenção, detecção, enforcement e evidência.

---

### 87. Como explicar o Trivy gate

Uma resposta possível:

> Eu separei o scan do container em duas responsabilidades. Primeiro gero um
> relatório JSON como evidência. Depois executo um gate específico que falha
> quando existe vulnerabilidade HIGH ou CRITICAL com correção disponível. Dessa
> forma, vulnerabilidades sem fix continuam visíveis, mas a política de bloqueio
> permanece objetiva e automatizável.

---

### 88. Como explicar SHA pinning e Dependabot

Uma resposta possível:

> As GitHub Actions são fixadas por full commit SHA para impedir que uma tag
> mutável altere silenciosamente o código executado pelo CI. Como isso poderia
> dificultar manutenção, o Dependabot monitora atualizações e abre Pull Requests.
> Assim eu combino imutabilidade na execução com atualização controlada por
> revisão e CI.

---

### 89. Como explicar SBOM e SCA

Uma resposta possível:

> O pip-audit e o SBOM têm objetivos diferentes. O pip-audit procura
> vulnerabilidades conhecidas nas dependências, enquanto o CycloneDX registra o
> inventário do ambiente. Um responde principalmente sobre risco conhecido; o
> outro responde sobre composição e rastreabilidade.

---

## Parte XIX — Limitações e Evolução

### 90. Limitações atuais

A arquitetura atual possui limitações conhecidas.

Entre elas:

- scanners dependem de regras e bases conhecidas;
- cobertura elevada não garante qualidade dos testes;
- o secret scanning pode possuir falsos negativos;
- SAST não detecta todas as classes de vulnerabilidade;
- o teste de `.env` verifica especificamente `/app/.env`;
- SBOM não demonstra segurança dos componentes;
- SHA pinning não demonstra segurança do commit fixado;
- Dependabot não demonstra compatibilidade ou segurança de uma atualização;
- vulnerabilidades sem correção disponível não bloqueiam o gate atual do Trivy;
- controles automatizados não substituem revisão e análise humana.

---

### 91. Possíveis evoluções

Evoluções futuras podem incluir, conforme a necessidade do projeto:

- políticas adicionais de branch protection;
- assinatura e verificação de artifacts;
- provenance de builds;
- geração de attestations;
- análise de licenças;
- políticas automatizadas sobre SBOM;
- scanners adicionais quando houver justificativa;
- políticas de dependências mais granulares;
- análise dinâmica;
- threat modeling formal;
- validações adicionais do container;
- políticas diferenciadas por ambiente.

Essas evoluções devem ser adotadas conforme risco e necessidade, e não apenas
para aumentar a quantidade de ferramentas.

---

### 92. Princípio de evolução

A evolução dos controles deve seguir:

```text
risco identificado
      ↓
controle necessário
      ↓
ferramenta adequada
      ↓
política explícita
      ↓
validação
      ↓
evidência
      ↓
documentação
```

e não:

```text
ferramenta interessante
      ↓
adicionar ao projeto
      ↓
descobrir depois para que serve
```

Esse princípio evita complexidade sem benefício de segurança proporcional.

---

## Parte XX — Relação com os demais documentos

### 93. Visão geral DevSecOps

O documento:

```text
docs/devsecops/overview.md
```

apresenta a arquitetura DevSecOps em nível estratégico.

Este documento aprofunda os controles individualmente.

---

### 94. Pipeline de CI

O documento:

```text
docs/devsecops/ci-pipeline.md
```

descreve como os controles são executados e relacionados dentro do GitHub
Actions.

A divisão conceitual é:

```text
overview.md
    ↓
por que a arquitetura existe

security-controls.md
    ↓
o que cada controle faz

ci-pipeline.md
    ↓
como os controles são executados
```

---

### 95. Objetivo final

A documentação dos controles permite responder não apenas:

```text
quais ferramentas o projeto usa?
```

mas principalmente:

```text
qual risco existe?
por que esse controle foi escolhido?
onde ele atua?
o que faz o CI falhar?
qual evidência permanece?
o que esse controle não consegue garantir?
```

Esse nível de documentação transforma a configuração DevSecOps em uma decisão
arquitetural explicável, auditável e evolutiva.
