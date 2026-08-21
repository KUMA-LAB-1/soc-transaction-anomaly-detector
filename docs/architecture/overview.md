# Visão Geral da Arquitetura

## 1. Objetivo do projeto

O `soc-transaction-anomaly-detector` é um projeto de análise preditiva aplicado
a um contexto de Security Operations Center (SOC), voltado à identificação,
avaliação e contextualização de comportamentos anômalos em transações.

A solução combina diferentes técnicas e componentes, incluindo:

- engenharia de features (*feature engineering*);
- classificação supervisionada para triagem;
- detecção de anomalias com múltiplos algoritmos;
- avaliação e seleção automatizada de detectores;
- regressão para estimativa de severidade de risco;
- correlação com MITRE ATT&CK;
- persistência de métricas;
- geração automatizada de gráficos e relatórios;
- controles de qualidade e segurança integrados ao CI.

A arquitetura foi evoluída para separar responsabilidades de acesso a dados,
transformação, modelos analíticos, *threat intelligence*, persistência,
*reporting* e orquestração.

Essa separação procura evitar que a lógica do sistema fique concentrada em um
único componente e permite que partes do pipeline sejam testadas, modificadas
e evoluídas de maneira independente.

Além da camada analítica, o projeto possui um pipeline DevSecOps responsável
por validar qualidade de código, testes, cobertura, segurança da aplicação,
dependências, exposição de secrets, *software supply chain* e segurança do
runtime em container.

---

## 2. Visão arquitetural

Em alto nível, a aplicação possui um fluxo analítico principal e componentes
auxiliares responsáveis por persistência, *threat intelligence* e geração de
evidências.

O fluxo principal pode ser representado da seguinte forma:

```text
Fonte de dados
     │
     ▼
Carregamento e validação
     │
     ▼
Feature Engineering
     │
     ▼
Classificação de Triagem
     │
     ▼
Execução dos Detectores de Anomalia
     │
     ▼
Avaliação e Seleção do Detector
     │
     ▼
Regressão de Severidade
     │
     ▼
Persistência das Métricas
     │
     ▼
Geração do Relatório
     │
     ├──────────────► Correlação / enriquecimento MITRE ATT&CK
     │
     └──────────────► Evidências e resultados
```

A classe `SecurityDetector` funciona principalmente como orquestradora desse
fluxo.

As responsabilidades especializadas são delegadas para módulos específicos,
reduzindo o acoplamento entre processamento de dados, modelos, persistência,
*threat intelligence* e apresentação dos resultados.

O enriquecimento MITRE ATT&CK não constitui uma etapa analítica linear entre os
modelos e o relatório. A correlação é consumida durante a geração das evidências
do relatório para contextualizar as anomalias identificadas.

---

## 3. Organização dos módulos

A implementação é organizada em módulos com responsabilidades distintas.

### `src/data/`

Responsável pela camada de acesso, validação e preparação estrutural dos dados.

Entre suas responsabilidades estão:

- validação e preparação do dataset;
- resolução de colunas necessárias ao pipeline;
- carregamento dos dados utilizados pela análise;
- acesso ao repositório de dados;
- registro de auditoria relacionado ao acesso aos dados.

Essa camada procura manter detalhes de acesso e validação separados dos modelos
analíticos.

### `src/features/`

Responsável pela engenharia de features utilizada pelos modelos.

O módulo transforma os dados preparados em atributos derivados que representam
sinais relevantes para classificação, detecção de anomalias e estimativa de
risco.

A separação dessa responsabilidade permite que a lógica de *feature engineering*
seja evoluída sem incorporar essas transformações diretamente à classe
orquestradora.

### `src/models/`

Concentra os componentes relacionados aos modelos analíticos.

Atualmente inclui responsabilidades de:

- classificação supervisionada de triagem;
- execução dos detectores de anomalia;
- avaliação dos detectores;
- seleção do detector utilizado pelo pipeline;
- regressão da severidade de risco.

A camada de modelos permanece separada da geração de relatórios e do acesso à
infraestrutura.

### `src/threat_intel/`

Responsável pela lógica de correlação e enriquecimento de *threat intelligence*.

Atualmente utiliza informações relacionadas ao MITRE ATT&CK para contextualizar
sinais observados nas transações classificadas como anômalas.

### `src/reporting/`

Responsável pela produção e persistência das evidências geradas pelo pipeline.

Inclui:

- geração de gráficos;
- persistência do histórico de métricas;
- geração do relatório PDF;
- consolidação dos resultados analíticos;
- apresentação da correlação com MITRE ATT&CK.

### `src/security_detector.py`

Contém a classe `SecurityDetector`, responsável pela coordenação do pipeline.

Sua função principal é organizar a sequência de execução e integrar os
resultados produzidos pelos módulos especializados.

### `src/db_connector.py`

Centraliza a criação das conexões utilizadas para acesso ao PostgreSQL/Supabase.

Essa separação mantém detalhes de infraestrutura de banco de dados fora da
lógica analítica principal.

### `src/ingest_mitre.py`

Responsável pelo processo de aquisição e persistência das informações utilizadas
na integração com MITRE ATT&CK.

O módulo separa transformação, download e persistência, permitindo que essas
responsabilidades sejam tratadas de maneira independente.

---

## 4. Orquestração do pipeline

`SecurityDetector` funciona como ponto de coordenação entre os diferentes
componentes da aplicação.

O fluxo executado pela classe pode ser resumido como:

```text
carregar_dados()
       │
       ▼
analisar_transacoes()
       │
       ├──► criar_features()
       │
       ├──► treinar classificação
       │
       ├──► comparar detectores de anomalia
       │
       ├──► selecionar detector
       │
       ├──► treinar regressão
       │
       └──► salvar métricas
       │
       ▼
gerar_pdf_report()
```

Essa abordagem mantém a classe responsável pela coordenação, enquanto os
detalhes de implementação permanecem nos respectivos módulos.

Entre os benefícios dessa separação estão:

- menor acoplamento;
- maior testabilidade;
- manutenção mais simples;
- substituição independente de componentes;
- evolução dos modelos sem reescrever toda a aplicação;
- reutilização da lógica analítica;
- isolamento de dependências externas;
- possibilidade de integração futura com outras fontes de dados.

---

## 5. Camada analítica

A camada analítica combina técnicas supervisionadas e não supervisionadas.

Ela não depende de um único algoritmo para produzir a avaliação final.

### 5.1 Classificação de triagem

O classificador supervisionado procura reproduzir padrões presentes no histórico
utilizado para treinamento e produz uma probabilidade associada à classificação
suspeita.

Essa etapa funciona como um sinal adicional de triagem e não substitui a
detecção independente de anomalias.

### 5.2 Detecção de anomalias

O pipeline avalia múltiplos algoritmos de *anomaly detection*.

Atualmente são utilizados:

- Isolation Forest;
- Local Outlier Factor;
- One-Class SVM;
- Elliptic Envelope.

Cada detector produz seus próprios resultados, permitindo comparação entre
diferentes abordagens.

### 5.3 Avaliação e seleção do detector

Os detectores válidos são comparados utilizando métricas comuns.

O critério atual de seleção prioriza:

1. maior F1-score;
2. maior recall em caso de empate;
3. maior precision;
4. menor tempo de execução.

O detector selecionado passa a representar o resultado principal de detecção de
anomalias utilizado pelas etapas posteriores e pelo relatório.

Os resultados individuais permanecem disponíveis para auditoria e comparação.

### 5.4 Regressão de severidade

Além da classificação e da detecção de anomalias, o pipeline executa um modelo
de regressão responsável por estimar um score de severidade de risco.

A qualidade dessa etapa é acompanhada por métricas como:

- R²;
- MAE;
- RMSE;
- validação cruzada.

A combinação entre classificação, detecção de anomalias e regressão permite
representar diferentes dimensões do problema em vez de reduzir a análise a uma
única decisão binária.

---

## 6. Threat Intelligence e MITRE ATT&CK

A integração com MITRE ATT&CK é dividida em duas responsabilidades principais:

1. ingestão e persistência da fonte de *threat intelligence*;
2. correlação e utilização dessas informações durante a geração das evidências.

### 6.1 Ingestão MITRE

O módulo `src/ingest_mitre.py` separa responsabilidades relacionadas a:

1. transformação dos dados STIX;
2. download dos dados MITRE;
3. persistência das informações no PostgreSQL/Supabase.

Essa separação permite que a lógica de transformação seja importada e testada
sem iniciar automaticamente downloads, conexões externas ou encerramento do
processo.

Conceitualmente:

```text
Fonte MITRE
     │
     ▼
Download
     │
     ▼
Dados STIX
     │
     ▼
Transformação
     │
     ▼
Persistência
```

### 6.2 Correlação e enriquecimento

O módulo `src/threat_intel/mitre.py` concentra a lógica utilizada para
correlacionar os sinais observados pelo pipeline com informações de
*threat intelligence*.

Durante a geração do relatório, sinais associados às transações anômalas podem
ser utilizados para realizar o enriquecimento.

Entre esses sinais podem estar informações relacionadas a:

- falhas recentes de login;
- utilização de dispositivo novo;
- alteração de limite;
- mudança de localização;
- tipo de transação.

O enriquecimento apresentado pelo relatório pode incluir:

- técnica MITRE associada;
- identificador da técnica;
- tática relacionada;
- critério utilizado para a correlação;
- fonte da informação;
- procedimentos sugeridos.

O fluxo de consumo pode ser representado como:

```text
Anomalia identificada
        +
Sinais da transação
        │
        ▼
Correlação de Threat Intelligence
        │
        ▼
MITRE ATT&CK
        │
        ▼
Contextualização da evidência
        │
        ▼
Relatório
```

Dessa forma, a aquisição da *threat intelligence* permanece desacoplada da
lógica que utiliza essas informações durante a geração das evidências.

---

## 7. Persistência e configuração

O acesso ao PostgreSQL/Supabase é orientado por configuração externa.

Credenciais e outras informações sensíveis não devem ser incorporadas ao
código-fonte nem à imagem Docker.

A aplicação recebe essas informações durante o runtime por meio de variáveis de
ambiente.

Conceitualmente:

```text
Aplicação
    +
Configuração do ambiente
    │
    ▼
Conexão com PostgreSQL/Supabase
```

Essa abordagem aplica o princípio de *Externalized Configuration*, mantendo
configuração e secrets separados da implementação e dos artifacts distribuídos.

As conexões PostgreSQL utilizam SSL conforme a configuração adotada pelo
projeto.

---

## 8. Reporting e evidências

O pipeline não produz apenas uma saída em memória.

Durante a execução são produzidos artifacts que permitem analisar posteriormente
os resultados e o comportamento dos modelos.

Entre os outputs estão:

- relatório PDF;
- gráficos analíticos;
- comparação entre detectores;
- métricas estruturadas;
- histórico de métricas;
- resultados em JSON e CSV;
- modelos serializados;
- evidências de correlação com MITRE ATT&CK.

Os modelos treinados são persistidos para permitir inspeção e reutilização
posterior.

A comparação entre detectores também é registrada em formatos estruturados,
permitindo auditoria do processo utilizado para selecionar o detector principal.

O relatório PDF consolida diferentes dimensões da análise, incluindo:

- resumo executivo;
- alertas identificados;
- severidade estimada;
- probabilidade associada à triagem;
- correlação com MITRE ATT&CK;
- métricas de validação;
- comparação dos detectores.

Essa estratégia transforma a execução do pipeline em um conjunto de evidências
reproduzíveis e analisáveis, em vez de limitar o resultado à saída do terminal.

---

## 9. Testes e validação

A arquitetura foi estruturada para permitir validação em diferentes níveis.

Os testes são separados principalmente entre:

```text
tests/
├── unit/
└── integration/
```

### Testes unitários

Os testes unitários validam componentes isoladamente.

A cobertura inclui áreas como:

- validação de dados;
- resolução de colunas;
- acesso ao repositório;
- conexão com banco de dados;
- feature engineering;
- classificação;
- detecção de anomalias;
- avaliação dos detectores;
- regressão;
- métricas;
- integração MITRE;
- ingestão MITRE;
- geração de gráficos;
- geração do PDF;
- orquestração do `SecurityDetector`.

Dependências externas são isoladas sempre que possível para que os testes
unitários não dependam de infraestrutura real.

### Teste de integração

O projeto possui um *integration smoke test* responsável por executar o pipeline
analítico de forma integrada utilizando dados controlados.

O objetivo é validar não apenas funções individuais, mas também a interação
entre os componentes principais e a geração dos artifacts esperados.

Essa combinação permite detectar tanto regressões locais quanto problemas de
integração entre os módulos.

---

## 10. Arquitetura DevSecOps

O projeto possui controles automatizados de qualidade, segurança e
*software supply chain* integrados ao GitHub Actions.

Os controles podem ser representados conceitualmente como:

```text
Código-fonte
     │
     ├──► Qualidade
     │      └── Ruff
     │
     ├──► Testes
     │      ├── Pytest
     │      └── Coverage Gate
     │
     ├──► Segurança da aplicação
     │      └── Bandit SAST
     │
     ├──► Dependências
     │      └── pip-audit
     │
     ├──► Secrets
     │      └── Gitleaks
     │
     ├──► Software Supply Chain
     │      ├── uv lock
     │      ├── CycloneDX SBOM
     │      ├── SHA pinning
     │      └── Dependabot
     │
     └──► Container
            ├── Build
            ├── Runtime non-root
            ├── Exclusão de secrets
            ├── Trivy report
            └── Security Gate
```

### 10.1 Qualidade e testes

O CI executa controles relacionados a:

- Ruff lint;
- Ruff format check;
- testes automatizados;
- cobertura de testes;
- coverage gate mínimo.

### 10.2 SAST

Bandit é utilizado como ferramenta de *Static Application Security Testing*
(SAST) para identificar padrões potencialmente inseguros no código Python.

O scanner representa uma camada de segurança e não é tratado como prova isolada
de ausência de vulnerabilidades.

### 10.3 Software Composition Analysis

`pip-audit` é utilizado para verificar o ambiente Python resolvido em busca de
vulnerabilidades conhecidas nas dependências.

Essa análise complementa os controles aplicados diretamente ao código-fonte.

### 10.4 Secret scanning

Gitleaks é utilizado para analisar o histórico Git em busca de possíveis
credenciais e secrets expostos.

O checkout utilizado nessa etapa possui histórico completo para permitir análise
dos commits existentes.

### 10.5 Software Bill of Materials

O pipeline gera automaticamente um SBOM no formato CycloneDX.

O SBOM fornece um inventário estruturado das dependências presentes no ambiente
resolvido utilizado pelo projeto.

O artifact é produzido durante o CI em vez de ser mantido como inventário
estático no repositório.

### 10.6 Segurança do container

A aplicação utiliza um build Docker multi-stage baseado em Python 3.12 slim.

Entre os controles de hardening estão:

- separação entre build e runtime;
- execução com usuário dedicado non-root;
- exclusão de `.env` da imagem;
- exclusão de arquivos desnecessários do contexto de build;
- separação entre ferramentas de desenvolvimento e runtime;
- diretórios de relatório graváveis pelo usuário da aplicação;
- aplicação de atualizações disponíveis do sistema operacional;
- validação automatizada do runtime.

Trivy é utilizado para análise de vulnerabilidades da imagem.

O CI possui um security gate que bloqueia a execução quando são identificadas
vulnerabilidades HIGH ou CRITICAL corrigíveis de acordo com a política definida
pelo projeto.

Além do gate, um relatório estruturado do Trivy é publicado como artifact para
permitir auditoria posterior.

### 10.7 Hardening do GitHub Actions

O workflow também aplica controles sobre a própria infraestrutura de CI.

Entre eles:

- `GITHUB_TOKEN` limitado a `contents: read`;
- GitHub Actions referenciadas por commit SHA imutável;
- comentários de versão mantidos ao lado dos SHAs;
- timeouts explícitos;
- controle de concurrency;
- cancelamento de execuções obsoletas da mesma referência.

Esses controles reduzem a superfície de ataque da própria cadeia de CI/CD.

### 10.8 Dependabot

Dependabot monitora atualizações relacionadas a:

- GitHub Actions;
- dependências Python gerenciadas pelo `uv`.

As atualizações não são aplicadas automaticamente ao código principal.

O fluxo esperado é:

```text
Dependência atual
      │
      ▼
Dependabot detecta atualização
      │
      ▼
Pull Request
      │
      ▼
Pipeline DevSecOps
      │
      ▼
Revisão
      │
      ▼
Merge
```

Isso permite automatizar a descoberta de atualizações sem eliminar a etapa de
validação e revisão.

---

## 11. Segurança em profundidade

Nenhum scanner ou controle individual é tratado como garantia suficiente de
segurança.

O projeto utiliza diferentes mecanismos complementares:

```text
Código
 │
 ├── Ruff
 ├── Testes
 ├── Bandit
 │
Dependências
 │
 ├── uv lock
 ├── pip-audit
 ├── SBOM
 └── Dependabot
 │
Repositório
 │
 └── Gitleaks
 │
CI
 │
 ├── Least Privilege
 ├── SHA Pinning
 ├── Timeouts
 └── Concurrency
 │
Container
 │
 ├── Multi-stage Build
 ├── Non-root Runtime
 ├── Secret Exclusion
 └── Trivy
```

Essa estratégia segue o princípio de *Defense in Depth*.

Uma eventual limitação ou falha em uma camada não elimina os controles
existentes nas demais.

---

## 12. Princípios arquiteturais

A evolução do projeto segue um conjunto de princípios utilizados para orientar
decisões técnicas.

### Separation of Concerns

Cada módulo deve possuir responsabilidades claramente identificáveis.

Orquestração, modelos, acesso a dados, *threat intelligence* e reporting devem
permanecer separados sempre que essa divisão reduzir acoplamento e melhorar a
manutenção.

### Testability

Componentes devem poder ser validados isoladamente sempre que possível.

Dependências externas não devem impedir testes determinísticos da lógica de
domínio e dos componentes analíticos.

### Reproducibility

Dependências, builds, modelos, métricas e artifacts devem possuir mecanismos que
favoreçam reprodução e rastreabilidade.

### Least Privilege

Aplicação, containers e CI devem operar apenas com os privilégios necessários
para executar suas responsabilidades.

### Externalized Configuration

Configurações e secrets devem permanecer separados do código-fonte e dos
artifacts distribuídos.

### Defense in Depth

Nenhum controle de segurança é considerado suficiente isoladamente.

A arquitetura utiliza múltiplas camadas complementares de prevenção, detecção,
validação e evidência.

### Observability and Evidence

Resultados relevantes do pipeline devem, sempre que possível, produzir
evidências estruturadas que permitam análise posterior.

Isso inclui métricas, relatórios, SBOMs, resultados de scanners e outros
artifacts gerados durante a execução ou pelo CI.

---

## 13. Limites atuais da solução

O projeto deve ser interpretado dentro do contexto para o qual foi desenvolvido.

Os modelos demonstram uma arquitetura e uma abordagem analítica, mas métricas
obtidas sobre datasets sintéticos ou de tamanho limitado não devem ser
interpretadas automaticamente como validação estatística para uso em produção.

Da mesma forma:

- um resultado limpo do Bandit não prova ausência de vulnerabilidades;
- um resultado limpo do `pip-audit` não elimina vulnerabilidades desconhecidas;
- um resultado limpo do Gitleaks não garante ausência absoluta de secrets;
- um resultado limpo do Trivy não garante ausência de vulnerabilidades futuras;
- a correlação MITRE ATT&CK representa contextualização baseada nos sinais e
  regras disponíveis, não atribuição definitiva de atividade maliciosa.

Essas limitações são importantes para manter transparência metodológica e evitar
que resultados de uma prova de conceito sejam apresentados como garantias de
produção.

---

## 14. Evolução arquitetural

A arquitetura atual foi construída para permitir evolução incremental.

Possíveis extensões futuras incluem:

- novas fontes de dados;
- novos detectores de anomalia;
- estratégias adicionais de ensemble;
- novos modelos de classificação;
- novas abordagens para estimativa de risco;
- ampliação da camada de threat intelligence;
- novas fontes de indicadores e contexto;
- persistência e versionamento de modelos;
- monitoramento de model drift;
- acompanhamento de data drift;
- métricas operacionais;
- observabilidade do pipeline;
- execução automatizada ou orientada a eventos;
- integração com plataformas SOC/SIEM;
- APIs para consumo dos resultados;
- políticas adicionais de segurança e governança.

Essas possibilidades representam direções de evolução e não funcionalidades
necessariamente implementadas no estado atual do projeto.

---

## 15. Objetivo desta documentação

Esta documentação registra tanto o estado atual da aplicação quanto as decisões
arquiteturais que levaram à estrutura existente.

Seu objetivo é permitir que outra pessoa consiga compreender:

- qual problema o projeto procura resolver;
- como o pipeline funciona;
- por que os módulos foram separados;
- como os modelos são utilizados;
- como ocorre a seleção do detector;
- onde o MITRE ATT&CK participa da solução;
- quais evidências são produzidas;
- como o projeto é testado;
- quais controles DevSecOps existem;
- quais limitações devem ser consideradas;
- quais caminhos de evolução permanecem disponíveis.

Documentos complementares podem aprofundar temas específicos, como:

- fluxo completo do pipeline;
- arquitetura dos modelos;
- estratégia de detecção de anomalias;
- critérios de seleção dos detectores;
- integração MITRE ATT&CK;
- persistência e acesso a dados;
- arquitetura de reporting;
- estratégia de testes;
- arquitetura DevSecOps;
- segurança de containers;
- software supply chain;
- decisões arquiteturais relevantes.

O objetivo final é reduzir a dependência de conhecimento implícito e tornar a
arquitetura compreensível, reproduzível, auditável e evolutiva.
