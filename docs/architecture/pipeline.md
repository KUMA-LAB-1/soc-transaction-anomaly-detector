# Pipeline Analítico

## 1. Objetivo

Este documento descreve o fluxo de execução do
`soc-transaction-anomaly-detector`, desde o carregamento dos dados até a
produção das métricas, modelos e evidências analíticas.

Enquanto `overview.md` apresenta a arquitetura geral da solução, este documento
detalha como os componentes participam da execução do pipeline e quais dados
são produzidos em cada etapa.

A implementação atual utiliza `SecurityDetector` como orquestrador principal,
delegando responsabilidades específicas aos módulos especializados.

---

## 2. Visão geral do fluxo

A execução completa é coordenada pelo `SecurityDetector`.

De forma simplificada, o pipeline segue a seguinte ordem operacional:

```text
PostgreSQL / Supabase
        │
        ▼
Carregamento do dataset
        │
        ▼
Validação e preparação
        │
        ▼
Feature Engineering
        │
        ▼
Classificação supervisionada
        │
        ▼
Detecção de anomalias
        │
        ├───────────────────────────────────────┐
        │                                       │
        ▼                                       ▼
Benchmark retrospectivo                 Política operacional
        │                                       │
        ▼                                       ▼
melhor_detector_benchmark      detector_operacional_configurado
                                                │
                                                ▼
                                      validação fail-closed
                                                │
                                                ▼
                                      detector_operacional
                                                │
                                                ▼
                              anomalia_score / anomalia_score_bruto
        │
        ▼
Regressão de severidade
        │
        ▼
Geração de alertas
        │
        ▼
Persistência de alertas
        │
        ▼
Persistência de métricas
        │
        ▼
Dataset analisado
        │
        ▼
Reporting / evidências
        │
   ┌────┼──────────┐
   ▼    ▼          ▼
gráficos PDF    artifacts
          │
          ▼
     MITRE ATT&CK
      enrichment
```

A sequência acima representa a ordem de orquestração do pipeline.

Ela não significa que classificação, detecção de anomalias e regressão formem
uma cadeia de dependência entre modelos.

As três abordagens utilizam perspectivas analíticas distintas:

```text
Classificação
      │
      ▼
proba_suspeita


Anomaly Detection
      │
      ▼
resultados individuais
      │
      ├── benchmark retrospectivo
      │
      └── detector operacional
              │
              ▼
      anomalia_score
      anomalia_score_bruto


Regressão
      │
      ▼
score_risco_predito
```

A regressão de severidade não utiliza automaticamente a saída da classificação
ou da detecção de anomalias como feature.

O enriquecimento MITRE ATT&CK pertence à camada de geração de evidências e
reporting. Ele não participa do treinamento, do benchmark ou da política
operacional dos modelos analíticos.

### Benchmark e política operacional

Na detecção de anomalias, duas decisões são tratadas separadamente.

O benchmark responde:

```text
qual detector apresentou o melhor desempenho retrospectivo
contra a referência histórica disponível?
```

A política operacional responde:

```text
qual detector explicitamente configurado está autorizado
a produzir o sinal canônico utilizado pelo pipeline?
```

Portanto:

```text
melhor_detector_benchmark
            │
            ▼
resultado experimental / retrospectivo

            ≠

detector_operacional
            │
            ▼
sinal canônico do pipeline
```

O vencedor do benchmark não é promovido automaticamente para uso operacional.

O detector operacional precisa estar entre os modelos que concluíram sua
execução com sucesso. Caso contrário, o pipeline falha explicitamente em vez de
utilizar silenciosamente outro detector.

### Estratégias de validação disponíveis na V3

A camada de modelos suporta estratégias alternativas de validação:

```text
Classificação
├── random   [padrão atual]
└── temporal [opt-in]

Regressão
├── random   [padrão atual]
└── temporal [opt-in]

Anomaly Detection
├── in_sample [padrão atual]
└── temporal  [opt-in]
```

O `SecurityDetector` atualmente chama esses módulos sem substituir suas
estratégias padrão.

Portanto, a infraestrutura temporal está implementada e disponível, mas não é
ativada automaticamente pelo fluxo operacional padrão.

Quando a estratégia temporal é utilizada, a implementação preserva separação
causal entre passado e futuro.

Entre as propriedades dessa validação estão:

- holdout cronológico;
- validação cruzada temporal expansiva para classificação e regressão;
- tratamento de timestamps empatados como blocos temporais indivisíveis;
- exigência de fronteira estrita entre treino e teste;
- preservação de `gap` como quantidade de registros;
- falha explícita quando uma fronteira temporal válida não pode ser formada.

A propriedade fundamental é:

```text
max(timestamp_treino) < min(timestamp_teste)
```

---

## Parte I — Entrada, preparação e feature engineering

### 3. Ponto de entrada

A execução completa é coordenada pelo método:

```python
SecurityDetector.executar_pipeline_completo()
```

Em alto nível, ele executa três operações:

```text
carregar_dados()
       │
       ▼
analisar_transacoes()
       │
       ▼
gerar_pdf_report()
```

Essa estrutura mantém a coordenação centralizada sem concentrar toda a
implementação analítica dentro da classe `SecurityDetector`.

---

### 4. Inicialização do `SecurityDetector`

Durante a inicialização, o pipeline recebe opcionalmente uma instância de
`sqlalchemy.engine.Engine`.

Quando nenhum engine é fornecido, a conexão é obtida por:

```python
DBConnector.get_engine()
```

A classe também inicializa o repositório de dados:

```python
SocDataRepository
```

e mantém referências para os principais resultados da execução:

- modelo de classificação;
- modelos de detecção de anomalias;
- detector selecionado;
- modelo de regressão;
- métricas;
- indicador de amostra pequena.

Os diretórios necessários para os artifacts de runtime também são preparados:

```text
reports/
reports/models/
```

---

### 5. Carregamento dos dados

O método:

```python
SecurityDetector.carregar_dados()
```

delega o acesso ao dataset para:

```python
SocDataRepository.carregar_dataset_soc()
```

Essa separação evita que a lógica de persistência fique acoplada à
orquestração analítica.

Conceitualmente:

```text
SecurityDetector
       │
       ▼
SocDataRepository
       │
       ▼
PostgreSQL / Supabase
```

A camada de repository também concentra responsabilidades relacionadas ao
registro de auditoria de acesso aos dados.

---

### 6. Preparação inicial

O método:

```python
SecurityDetector.analisar_transacoes()
```

começa criando uma cópia do `DataFrame` recebido.

Em seguida, deriva a hora da transação a partir de:

```text
data_hora_transacao
```

produzindo:

```text
hora
```

Depois disso, o dataset é encaminhado para a camada de feature engineering.

---

### 7. Validação e preparação do dataset

O módulo:

```text
src/data/validation.py
```

contém a função:

```python
validar_e_preparar_dataset()
```

responsável por operações básicas de preparação, atualmente:

- preenchimento de valores ausentes;
- remoção de registros duplicados.

A existência dessa função mantém a validação básica separada das etapas de
Machine Learning.

A utilização efetiva dessa validação depende do fluxo de carregamento definido
na camada de repository.

---

### 8. Identidade pseudonimizada

O dataset consumido pelo pipeline possui uma identidade pseudonimizada canônica:

```text
cliente_pseudonimo
```

Essa coluna faz parte do contrato obrigatório do dataset SOC e é exposta pela view:

```text
v_analise_investigacao_soc
```

O módulo:

```text
src/data/columns.py
```

valida a presença de `cliente_pseudonimo` antes que componentes dependentes utilizem a identidade lógica do cliente.

Datasets que não contenham essa coluna são considerados incompatíveis com o contrato esperado pelo pipeline e devem falhar explicitamente, em vez de receber aliases legados ou identidades genéricas criadas em tempo de execução.

Essa abordagem mantém um único contrato de identidade entre:

- banco de dados;
- camada de acesso aos dados;
- feature engineering;
- geração de alertas;
- reporting.

A identidade pseudonimizada é persistida na origem dos dados e propagada pelo pipeline sem expor identificadores pessoais diretos na view utilizada pela rotina de análise.

Esse modelo evita comportamentos silenciosos de compatibilidade com estruturas antigas e torna incompatibilidades de schema explicitamente detectáveis durante a execução.

---

### 9. Feature Engineering

A transformação principal ocorre em:

```python
criar_features()
```

no módulo:

```text
src/features/engineering.py
```

Antes de calcular o histórico, as transações são ordenadas por cliente e por
data/hora.

Isso é importante porque as features históricas utilizam somente observações
anteriores da mesma identidade pseudonimizada.

### 9.1 Média histórica

É calculada:

```text
media_historica_cliente
```

utilizando a média expansiva das transações anteriores.

A transação atual é removida do cálculo por meio de `shift(1)`.

Conceitualmente:

```text
T1 ──► histórico de T2
T1,T2 ──► histórico de T3
T1,T2,T3 ──► histórico de T4
```

Isso reduz o risco de utilizar o próprio valor da observação atual na
construção de seu histórico.

### 9.2 Desvio histórico

Também é produzido:

```text
desvio_historico_cliente
```

com base no desvio padrão das observações anteriores.

Quando ainda não existe histórico suficiente, são utilizados valores globais
do dataset como fallback.

Valores de desvio iguais a zero são substituídos por um pequeno valor para
evitar divisão por zero.

### 9.3 Quantidade de transações anteriores

A feature:

```text
qtd_transacoes_anteriores
```

registra quantas transações daquela identidade ocorreram antes da observação
atual.

### 9.4 Z-score do valor

A feature:

```text
zscore_valor_cliente
```

mede o afastamento do valor atual em relação ao comportamento histórico do
cliente:

```text
valor atual - média histórica
──────────────────────────────
       desvio histórico
```

Valores absolutos maiores representam maior afastamento do padrão histórico.

### 9.5 Dia da semana

A partir de:

```text
data_hora_transacao
```

é criada:

```text
dia_semana
```

### 9.6 Sinais contextuais

O pipeline também utiliza sinais relacionados ao contexto da transação:

```text
falhas_login_recentes
dispositivo_novo_flag
alteracao_limite_flag
mudanca_localizacao_flag
```

Quando essas colunas não estão disponíveis, valores padrão são adicionados para
preservar a compatibilidade do pipeline.

---

### 10. Controle de amostra pequena

O pipeline possui o parâmetro:

```text
MIN_AMOSTRAS_TREINO_CONFIAVEL = 60
```

Quando o dataset contém menos de 60 registros, a execução não é interrompida.

Em vez disso:

```text
aviso_amostra_pequena = True
```

é ativado.

Os modelos continuam sendo executados, mas os resultados devem ser
interpretados como prova de conceito, e não como evidência de validação
estatística robusta.

Essa decisão permite manter datasets pequenos úteis para desenvolvimento e
testes sem mascarar suas limitações.

---

## Parte II — Classificação supervisionada

### 11. Classificador de triagem

A classificação é implementada por:

```python
treinar_classificador_triagem()
```

utilizando:

```text
DecisionTreeClassifier
```

com:

```text
max_depth = 4
random_state = 42
class_weight = balanced
```

O objetivo é estimar a probabilidade de uma transação pertencer ao conjunto de
status considerados suspeitos.

---

### 12. Target da classificação

Os seguintes status são tratados como suspeitos:

```text
Em Análise
Bloqueada por Suspeita
```

Eles são convertidos para:

```text
1 = suspeito
0 = não suspeito
```

Portanto, diferentemente dos detectores de anomalia, esta etapa é
supervisionada.

---

### 13. Features da classificação

As features-base incluem:

```text
hora
media_historica_cliente
desvio_historico_cliente
qtd_transacoes_anteriores
zscore_valor_cliente
dia_semana
falhas_login_recentes
dispositivo_novo_flag
alteracao_limite_flag
mudanca_localizacao_flag
```

A variável:

```text
tipo_transacao
```

é transformada por one-hot encoding.

Somente as features efetivamente presentes no dataset transformado são
utilizadas.

---

### 14. Divisão treino/teste

O classificador suporta duas estratégias de validação:

```text
random   [padrão atual]
temporal [opt-in]
```

A estratégia é definida pelo parâmetro:

```python
estrategia_validacao
```

da função:

```python
treinar_classificador_triagem()
```

### Estratégia `random`

No modo padrão, o conjunto é dividido utilizando `train_test_split`.

A proporção atual é:

```text
75% treino
25% teste
```

com:

```text
random_state = 42
```

Quando o target possui mais de uma classe, a divisão utiliza estratificação para
preservar melhor a proporção das classes entre treino e teste.

Conceitualmente:

```text
dataset
   │
   ▼
divisão aleatória estratificada
   │
   ├───────────────┐
   ▼               ▼
treino            teste
75%               25%
```

Quando apenas uma classe está disponível, a execução continua sem
estratificação e essa limitação é tratada explicitamente pelas etapas
posteriores.

### Estratégia `temporal`

Quando a estratégia temporal é ativada, o classificador utiliza:

```python
dividir_holdout_temporal()
```

com:

```text
test_size = 0.25
```

Nesse modo não ocorre embaralhamento aleatório.

A divisão procura representar:

```text
passado
   │
   ▼
treino
   │
   ▼
futuro
   │
   ▼
teste
```

Os índices retornados pela estratégia temporal são aplicados posicionalmente ao
conjunto de features e ao target.

A fronteira temporal deve respeitar:

```text
max(timestamp_treino) < min(timestamp_teste)
```

Registros com timestamps idênticos não são separados artificialmente entre
treino e teste quando os dados não oferecem informação adicional capaz de
estabelecer uma ordem causal.

Se uma fronteira temporal válida não puder ser formada, a operação falha
explicitamente em vez de inventar uma ordenação causal.

O `SecurityDetector` atualmente chama o classificador sem substituir
`estrategia_validacao`.

Portanto:

```text
fluxo operacional padrão
          │
          ▼
        random

capacidade disponível na V3
          │
          ▼
       temporal
```

---

### 15. Avaliação da classificação

Depois do treinamento, o classificador é avaliado no conjunto reservado para
teste.

Entre as métricas produzidas estão:

```text
ROC-AUC de teste
precision da classe suspeita
recall da classe suspeita
F1 da classe suspeita
matriz de confusão
```

Também é gerado um `classification_report` para as classes:

```text
0 = não suspeita
1 = suspeita
```

A implementação utiliza:

```text
zero_division = 0
```

para manter comportamento definido quando alguma métrica não puder ser
calculada normalmente por ausência de predições de determinada classe.

### Validação cruzada no modo `random`

Quando a estratégia padrão `random` é utilizada, o pipeline mantém validação
cruzada estratificada de três folds utilizando:

```text
ROC-AUC
```

como métrica de avaliação.

Essa avaliação complementa o holdout treino/teste e fornece uma segunda
perspectiva sobre a estabilidade do classificador.

### Validação cruzada no modo `temporal`

Quando:

```text
estrategia_validacao = temporal
```

os folds são construídos por:

```python
criar_folds_temporais()
```

com:

```text
n_splits = 3
```

A validação utiliza janelas de treino expansivas.

Conceitualmente:

```text
Fold 1
treino ─────────► teste

Fold 2
treino ─────────────────► teste

Fold 3
treino ─────────────────────────► teste
```

Antes de utilizar um fold na avaliação ROC-AUC, o classificador verifica se
existe diversidade de classes tanto no conjunto de treino quanto no conjunto de
teste.

Somente folds que atendem simultaneamente:

```text
mais de uma classe no treino
            +
mais de uma classe no teste
```

participam da validação cruzada.

Isso evita calcular ROC-AUC em uma janela temporal que não possui a diversidade
mínima necessária para essa métrica.

Quando existem folds temporais válidos, a avaliação utiliza:

```text
scoring = roc_auc
```

Os resultados são armazenados em:

```text
cv_scores
```

e resumidos nas métricas do modelo.

Entre os metadados preservados também estão:

```text
estrategia_validacao
n_treino
n_teste
classes_no_treino
roc_auc_teste
roc_auc_cv_media
```

Quando não existem folds válidos para a validação cruzada temporal,
`roc_auc_cv_media` pode permanecer indisponível em vez de produzir uma métrica
enganosa.

---

### 16. Probabilidade de suspeita

Depois do treinamento, o classificador é aplicado ao conjunto completo para
produzir:

```text
proba_suspeita
```

Essa coluna representa a probabilidade estimada pelo classificador para a
classe suspeita.

O modelo treinado é persistido em:

```text
reports/models/classificador.joblib
```

Também é gerado um gráfico de importância das features.

---

## Parte III — Detecção de anomalias

### 17. Estratégia multi-detector

O projeto não depende de um único algoritmo de anomaly detection.

A implementação atual executa quatro detectores:

```text
Isolation Forest
Local Outlier Factor
One-Class SVM
Elliptic Envelope
```

Eles utilizam uma configuração comum para permitir comparação posterior.

---

### 18. Features dos detectores

A camada de anomaly detection utiliza:

```text
valor_transacao
hora
zscore_valor_cliente
qtd_transacoes_anteriores
falhas_login_recentes
dispositivo_novo_flag
alteracao_limite_flag
mudanca_localizacao_flag
```

Somente as features disponíveis no `DataFrame` são selecionadas.

Valores ausentes são preenchidos com zero antes da execução.

---

### 19. Contamination

A camada de detecção de anomalias recebe `contamination` como uma configuração
explícita.

A implementação atual define:

```text
CONTAMINATION_PISO_PRATICO = 0.02
CONTAMINATION_TETO_PRATICO = 0.15
CONTAMINATION_PADRAO = 0.15
```

Assim, o valor informado deve permanecer dentro do intervalo:

```text
0.02 <= contamination <= 0.15
```

Quando nenhum valor é fornecido explicitamente, a execução utiliza:

```text
contamination = 0.15
```

O fluxo atual é:

```text
contamination configurado
          │
          ▼
validação entre 0.02 e 0.15
          │
          ▼
configuração comum dos detectores
```

Separadamente, o pipeline calcula:

```text
taxa_suspeita_real
```

a partir da referência histórica derivada de `status_transacao`.

Essa informação possui finalidade retrospectiva e é preservada para métricas,
auditoria e comparação.

Ela não determina o valor de `contamination`.

Portanto:

```text
contamination
      │
      ▼
configuração dos modelos

      ≠

taxa_suspeita_real
      │
      ▼
auditoria retrospectiva
```

Essa separação impede que a proporção dos labels históricos ou a composição de
um dataset sintético configure implicitamente os detectores não supervisionados.

---

### 20. Isolation Forest

O `IsolationForest` é configurado atualmente com:

```text
n_estimators = 300
random_state = 42
n_jobs = -1
contamination = valor configurado
```

O parâmetro `contamination` é recebido da política explícita da camada de
detecção e já foi validado antes da criação do modelo.

O `IsolationForest` não utiliza `status_transacao` durante o treinamento.

Os labels históricos participam somente da avaliação retrospectiva realizada
depois das predições.

---

### 21. Local Outlier Factor

O `LocalOutlierFactor` é executado dentro de um pipeline com:

```text
StandardScaler
        │
        ▼
LocalOutlierFactor
```

A implementação utiliza:

```text
novelty = True
```

Essa configuração permite utilizar o detector por meio da interface de predição
depois do treinamento.

A quantidade de vizinhos é ajustada dinamicamente de acordo com o tamanho do
conjunto utilizado para treino.

O detector recebe o mesmo valor explícito de:

```text
contamination
```

utilizado pela política comum de detecção.

Esse valor não é derivado de `status_transacao` nem de
`taxa_suspeita_real`.

---

### 22. One-Class SVM

O `OneClassSVM` também utiliza normalização:

```text
StandardScaler
        │
        ▼
OneClassSVM
```

A configuração atual é:

```text
kernel = rbf
gamma = scale
nu = contamination
```

Para esse detector, o valor configurado como `contamination` pela camada comum
é utilizado como parâmetro:

```text
nu
```

Portanto:

```text
contamination configurado
          │
          ▼
         nu
```

A normalização é aplicada antes do modelo porque o `OneClassSVM` é sensível às
diferenças de escala entre as features.

Assim como nos demais detectores, os labels históricos não participam dessa
configuração.

---

### 23. Elliptic Envelope

O quarto detector utiliza:

```text
StandardScaler
        │
        ▼
EllipticEnvelope
```

A configuração relevante é:

```text
contamination = valor configurado
random_state = 42
support_fraction = None
```

O mesmo valor explícito de `contamination` validado pela camada comum é
fornecido ao modelo.

O `EllipticEnvelope` representa uma abordagem baseada em distribuição e
covariância, distinta das demais técnicas presentes no conjunto.

`status_transacao` não participa da configuração do detector.

A referência histórica é utilizada somente depois das predições para avaliação
retrospectiva.

---

### 24. Independência em relação ao target

Os quatro detectores são treinados sem utilizar `status_transacao` como feature
de entrada.

O target histórico também não determina o valor configurado de
`contamination`.

Depois das predições, `status_transacao` é convertido para uma referência
binária e utilizado exclusivamente na avaliação retrospectiva dos detectores.

A separação é:

```text
status_transacao
      │
      ├── NÃO entra nas features dos detectores
      │
      ├── NÃO configura contamination
      │
      └── É usado posteriormente para auditoria
          e métricas comparativas
```

Essa arquitetura preserva a natureza não supervisionada ou de novelty detection
dos algoritmos utilizados.

Ao mesmo tempo, permite comparar seus resultados com a referência histórica
disponível no dataset.

Essas métricas devem ser interpretadas como concordância retrospectiva com os
labels disponíveis, e não como prova absoluta de capacidade de detectar fraude
real.

---

### 25. Representação das anomalias

Os detectores do scikit-learn utilizados pelo projeto retornam:

```text
 1 = observação normal
-1 = anomalia
```

Para comparação com o status histórico, o pipeline converte:

```text
-1 → 1 = anomalia
 1 → 0 = normal
```

---

### 26. Avaliação dos detectores

Cada detector é avaliado por:

```python
avaliar_detector()
```

As métricas calculadas incluem:

```text
precision
recall
F1
ROC-AUC do score de anomalia
tempo de execução
quantidade de anomalias
taxa de anomalias
```

O tempo de execução também participa do processo de desempate.

---

### 27. Isolamento de falhas

Cada detector é executado dentro de tratamento individual de exceção.

Caso um algoritmo falhe:

```text
status = erro
```

é registrado para aquele detector.

Os demais continuam sendo avaliados.

Isso impede que uma incompatibilidade isolada em um detector necessariamente
interrompa toda a comparação.

Caso nenhum detector consiga concluir com sucesso, a etapa de seleção gera
erro explícito.

---

### 28. Benchmark e política operacional

Depois da execução, somente os detectores cujo resultado possui:

```text
status = ok
```

participam do benchmark retrospectivo.

A função utilizada é:

```python
selecionar_melhor_detector_benchmark()
```

Os critérios são aplicados nesta ordem:

```text
1. maior F1
2. maior recall
3. maior precision
4. menor tempo de execução
```

Formalmente:

```text
F1
 │
 └── empate
       ▼
     recall
       │
       └── empate
             ▼
          precision
             │
             └── empate
                   ▼
              menor tempo
```

O vencedor é registrado em:

```text
melhor_detector_benchmark
```

Esse valor representa exclusivamente o melhor resultado no benchmark
retrospectivo contra os labels históricos disponíveis.

Ele não define automaticamente qual modelo produzirá o sinal operacional.

A política operacional segue uma trilha independente:

```text
detector_operacional_configurado
              │
              ▼
está entre os detectores executados
       com sucesso?
          │           │
         sim         não
          │           │
          ▼           ▼
detector_operacional  RuntimeError
```

O padrão atual de configuração operacional é:

```text
isolation_forest
```

Quando o detector configurado está disponível, ele é ativado em:

```text
detector_operacional
```

A instância correspondente também é referenciada por:

```text
modelo_agrupamento
```

A arquitetura pode ser resumida como:

```text
resultados válidos
        │
        ├───────────────────────┐
        │                       │
        ▼                       ▼
benchmark retrospectivo    política operacional
        │                       │
        ▼                       ▼
melhor_detector_benchmark  detector_operacional_configurado
                                │
                                ▼
                         validação fail-closed
                                │
                                ▼
                         detector_operacional
```

Se o detector operacional configurado falhar ou não estiver disponível entre os
modelos válidos, a execução é interrompida explicitamente.

O vencedor do benchmark não é utilizado como fallback silencioso.

O atributo legado:

```text
melhor_detector
```

permanece temporariamente como alias de compatibilidade e recebe o mesmo valor
de `detector_operacional`.

Ele não representa mais a fonte canônica da decisão operacional.

---

### 29. Resultado dos detectores

Para cada detector executado com sucesso, o `DataFrame` recebe colunas
específicas:

```text
anomalia_<detector>
score_anomalia_<detector>
```

Essas colunas preservam os resultados individuais utilizados para comparação,
auditoria e investigação.

Separadamente, o detector operacional validado alimenta as colunas canônicas:

```text
anomalia_score
anomalia_score_bruto
```

Portanto:

```text
resultados individuais
        │
        ▼
anomalia_<detector>
score_anomalia_<detector>
        │
        ▼
benchmark / auditoria


detector_operacional
        │
        ▼
anomalia_score
anomalia_score_bruto
        │
        ▼
consumidores operacionais
```

As colunas canônicas não representam necessariamente o detector com maior
pontuação no benchmark.

Elas representam o detector aprovado pela política operacional explícita.

Essa distinção permite alterar, comparar ou experimentar detectores sem promover
automaticamente um modelo para o caminho operacional.

Os modelos treinados são persistidos em:

```text
reports/models/<detector>.joblib
```

---

### 30. Evidências da comparação

A comparação entre os detectores é persistida em:

```text
reports/comparacao_detectores.csv
reports/comparacao_detectores.json
```

Também é produzido um gráfico comparativo dos detectores válidos.

As evidências preservam duas dimensões distintas:

```text
benchmark retrospectivo
          │
          ▼
desempenho comparativo


política operacional
          │
          ▼
detector efetivamente utilizado
```

Entre as informações registradas pela comparação estão:

```text
criterio_benchmark
melhor_modelo_benchmark
detector_operacional_configurado
detector_operacional
politica_operacional
resultados individuais
```

Campos legados ainda podem permanecer temporariamente na estrutura de métricas
para compatibilidade com consumidores anteriores.

Eles não alteram a separação canônica entre benchmark e política operacional.

Os arquivos de comparação permitem reconstruir posteriormente:

- quais detectores concluíram com sucesso;
- quais métricas cada detector produziu;
- qual modelo venceu o benchmark retrospectivo;
- qual detector estava configurado para operação;
- qual detector foi efetivamente ativado.

Essa separação melhora a rastreabilidade das decisões do pipeline e impede que
ranking experimental e política operacional sejam tratados como o mesmo
conceito.

---

## Parte IV — Regressão de severidade

### 31. Objetivo

Além da classificação e da detecção de anomalias, o pipeline produz uma
estimativa contínua de severidade.

A implementação atual utiliza:

```text
LinearRegression
```

---

### 32. Target de severidade

O target é derivado de `status_transacao` utilizando o seguinte mapeamento:

```text
Aprovada                 → 5
Concluída                → 5
Em Análise               → 55
Bloqueada por Suspeita   → 95
```

Status não mapeados recebem:

```text
30
```

como severidade padrão.

Esse target é uma representação definida pelo projeto e não deve ser
interpretado como escala universal de risco.

---

### 33. Features da regressão

A regressão utiliza:

```text
valor_transacao
hora
media_historica_cliente
desvio_historico_cliente
zscore_valor_cliente
qtd_transacoes_anteriores
dia_semana
falhas_login_recentes
```

---

### 34. Treinamento e avaliação

A regressão de severidade suporta duas estratégias de validação:

```text
random   [padrão atual]
temporal [opt-in]
```

A estratégia é definida pelo parâmetro:

```python
estrategia_validacao
```

da função:

```python
treinar_regressao_severidade()
```

### Estratégia `random`

No modo padrão, a divisão treino/teste utiliza:

```text
75% treino
25% teste
```

com:

```text
random_state = 42
```

A validação cruzada utiliza cinco folds.

Essa estratégia preserva compatibilidade com o comportamento anterior do
pipeline.

### Estratégia `temporal`

Quando a estratégia temporal é ativada, o holdout utiliza:

```python
dividir_holdout_temporal()
```

com:

```text
test_size = 0.25
```

A validação cruzada utiliza:

```python
criar_folds_temporais()
```

com:

```text
n_splits = 5
```

Os folds seguem uma janela de treino expansiva e preservam a separação causal
entre observações passadas e futuras.

Folds são utilizados na validação cruzada somente quando possuem tamanho
suficiente para a avaliação configurada.

A propriedade temporal exigida é:

```text
max(timestamp_treino) < min(timestamp_teste)
```

Timestamps empatados não são divididos artificialmente entre treino e teste
quando não existe informação adicional que estabeleça uma ordem causal.

Para ambas as estratégias são calculadas métricas como:

```text
R²
MAE
RMSE
```

A execução também registra a média e a dispersão dos resultados de validação
cruzada quando folds válidos estão disponíveis.

R² negativo em validação cruzada é tratado explicitamente como sinal de baixa
capacidade de generalização, situação especialmente relevante em datasets
pequenos.

O `SecurityDetector` atualmente chama a regressão sem substituir
`estrategia_validacao`.

Portanto, `random` continua sendo o modo utilizado pelo fluxo operacional padrão,
enquanto `temporal` é uma capacidade opt-in da V3.

---

### 35. Score de risco predito

Depois do treinamento, a regressão é aplicada ao dataset completo.

O resultado é limitado ao intervalo:

```text
0 ≤ score_risco_predito ≤ 100
```

e armazenado em:

```text
score_risco_predito
```

O modelo treinado é persistido em:

```text
reports/models/regressao.joblib
```

---

## Parte V — Métricas e artifacts

### 36. Consolidação das métricas

Durante a execução, `SecurityDetector` mantém:

```text
self.metricas
```

que recebe resultados das diferentes etapas.

Entre os grupos registrados estão:

```text
classificacao
detectores individuais
comparacao_detectores
regressao
```

Depois da análise, essas informações são encaminhadas para:

```python
salvar_historico_metricas()
```

---

### 37. Dataset analisado

Ao final de:

```python
analisar_transacoes()
```

o `DataFrame` original foi enriquecido com features e resultados produzidos
pelas etapas analíticas.

Entre as colunas que podem estar presentes estão:

```text
hora
media_historica_cliente
desvio_historico_cliente
qtd_transacoes_anteriores
zscore_valor_cliente
dia_semana
proba_suspeita
anomalia_<detector>
score_anomalia_<detector>
anomalia_score
anomalia_score_bruto
score_risco_predito
```

Esse `DataFrame` enriquecido é utilizado posteriormente pela camada de
reporting.

---

## Parte VI — Reporting e MITRE ATT&CK

### 38. Separação entre análise e reporting

Uma distinção arquitetural importante é:

```text
analisar_transacoes()
```

não executa diretamente a correlação MITRE ATT&CK.

O fluxo é:

```text
análise dos modelos
       │
       ▼
DataFrame enriquecido
       │
       ▼
geração do relatório
       │
       ▼
correlação / enriquecimento MITRE
```

Isso mantém threat intelligence desacoplada do treinamento e da seleção dos
modelos.

---

### 39. Geração do relatório

O método:

```python
SecurityDetector.gerar_pdf_report()
```

delega a produção do relatório para:

```python
gerar_relatorio_pdf()
```

A camada recebe informações como:

```text
dataset analisado
métricas consolidadas
detector operacional
indicador de amostra pequena
engine de banco de dados
```

Na interface atual de reporting, o parâmetro que recebe o detector ainda possui
o nome legado:

```text
melhor_detector
```

Entretanto, o `SecurityDetector` fornece explicitamente:

```text
self.detector_operacional
```

como valor desse parâmetro.

Portanto:

```text
parâmetro legado do PDF
melhor_detector
        │
        ▼
valor efetivamente fornecido
detector_operacional
```

O relatório não recebe automaticamente
`self.melhor_detector_benchmark` como detector principal.

Essa distinção preserva a separação arquitetural entre:

```text
benchmark retrospectivo
          │
          ▼
melhor_detector_benchmark

          ≠

política operacional
          │
          ▼
detector_operacional
```

A camada de reporting utiliza o detector operacional, as métricas e o dataset
analisado para consolidar evidências e contexto adicional.

O nome `melhor_detector` na interface de reporting é mantido temporariamente por
compatibilidade e pode ser revisado em uma evolução futura da API.

---

### 40. MITRE ATT&CK

O enriquecimento MITRE utiliza a camada:

```text
src/threat_intel/
```

A aquisição e persistência da fonte MITRE são mantidas separadamente em:

```text
src/ingest_mitre.py
```

Essa separação produz duas responsabilidades distintas:

```text
MITRE ingestion
      │
      ▼
armazenamento
```

e:

```text
resultado analítico
      │
      ▼
MITRE enrichment
      │
      ▼
evidência / relatório
```

Portanto, a threat intelligence contextualiza os resultados sem participar da
decisão interna dos modelos.

---

## Parte VII — Tratamento de limitações

### 41. Dataset pequeno

O pipeline permite execução com datasets pequenos para facilitar:

- desenvolvimento;
- testes;
- demonstrações;
- provas de conceito.

Entretanto, resultados obtidos nessas condições não devem ser apresentados
como validação estatística robusta.

O próprio pipeline mantém um indicador explícito dessa condição.

---

### 42. Classes insuficientes

Quando o classificador encontra apenas uma classe no conjunto de treino:

- a execução continua;
- a limitação é sinalizada;
- métricas incompatíveis podem ficar indisponíveis;
- a probabilidade é tratada de forma compatível com a única classe observada.

---

### 43. Falha de detector

Uma falha individual em um algoritmo de anomaly detection não interrompe
automaticamente a execução dos demais detectores.

Cada detector é executado de forma isolada e seu resultado registra:

```text
status = ok
```

ou:

```text
status = erro
```

junto das informações relevantes da execução.

Os detectores concluídos com sucesso continuam disponíveis para comparação
retrospectiva.

Entretanto, existem duas condições distintas de falha global.

A primeira ocorre quando nenhum detector conclui com sucesso:

```text
nenhum detector válido
        │
        ▼
benchmark impossível
        │
        ▼
RuntimeError
```

A segunda ocorre quando existem detectores válidos, mas o detector
explicitamente configurado para operação não está entre eles:

```text
detectores válidos existem
          │
          ▼
detector_operacional_configurado
não está disponível
          │
          ▼
RuntimeError
```

Nesse segundo caso, o vencedor do benchmark não é promovido automaticamente
como fallback.

Essa política fail-closed impede que uma falha operacional altere
silenciosamente qual detector está autorizado a produzir o sinal canônico do
pipeline.

---

### 44. Interpretação das métricas

As métricas produzidas pelo pipeline devem ser interpretadas no contexto do
dataset utilizado.

Resultados elevados em datasets sintéticos, pequenos ou controlados não
representam automaticamente desempenho equivalente em produção.

Da mesma forma, o uso de `status_transacao` para auditoria dos detectores mede
concordância com essa referência histórica, não uma verdade universal sobre a
existência de fraude ou incidente.

---

## Parte VIII — Como explicar o pipeline

### 45. Explicação curta

Uma forma resumida de apresentar o projeto é:

> O sistema carrega transações, constrói features comportamentais e contextuais
> e executa três perspectivas analíticas: classificação supervisionada, detecção
> de anomalias multi-detector e regressão de severidade. Os detectores de
> anomalia são avaliados retrospectivamente contra o status histórico para fins
> de benchmark, mas o vencedor dessa comparação não é promovido automaticamente
> para operação. O detector operacional é definido explicitamente e validado
> antes de produzir o sinal canônico utilizado por alertas e reporting. Os
> resultados, métricas e evidências são persistidos e o relatório pode ser
> enriquecido com contexto MITRE ATT&CK.

Essa explicação preserva quatro distinções importantes:

```text
classificação supervisionada
             ≠
detecção de anomalias

benchmark retrospectivo
             ≠
política operacional
```

Também evita interpretar `proba_suspeita`, `anomalia_score` ou
`score_risco_predito` automaticamente como probabilidade real de fraude.

---

### 46. Explicação arquitetural

Em uma discussão mais técnica, o ponto principal é que o projeto separa:

```text
dados
features
classificação
anomaly detection
avaliação
regressão
threat intelligence
reporting
```

`SecurityDetector` coordena essas etapas, mas a implementação de cada domínio
permanece em módulos especializados.

Isso reduz acoplamento e permite testar, substituir ou evoluir componentes
individualmente.

---

### 47. Diferença entre classificação e anomaly detection

Um ponto importante para explicar é:

```text
Classificação
    │
    ├── supervisionada
    ├── aprende a partir de status históricos
    └── produz probabilidade de suspeita
```

enquanto:

```text
Anomaly Detection
    │
    ├── detectores não supervisionados / novelty detection
    ├── não recebem status_transacao como feature
    └── procuram padrões estatisticamente incomuns
```

O status histórico é utilizado posteriormente para comparar os detectores.

Isso permite observar duas perspectivas diferentes do mesmo conjunto de
transações.

---

### 48. Por que múltiplos detectores?

Algoritmos de anomaly detection fazem hipóteses diferentes sobre a estrutura dos
dados.

Por isso, o projeto executa múltiplas abordagens:

```text
Isolation Forest
Local Outlier Factor
One-Class SVM
Elliptic Envelope
```

Os resultados são preservados individualmente e comparados retrospectivamente.

O fluxo experimental é:

```text
executar
   │
   ▼
medir
   │
   ▼
comparar
   │
   ▼
benchmark
```

Esse benchmark permite observar qual detector apresentou o melhor desempenho
contra a referência histórica disponível segundo os critérios definidos pelo
projeto.

Entretanto:

```text
vencedor do benchmark
          │
          ▼
evidência experimental

          ≠

detector operacional
          │
          ▼
política explícita
```

A escolha operacional não é delegada automaticamente ao ranking.

O detector utilizado pelo pipeline é configurado explicitamente e validado
contra os modelos que concluíram sua execução com sucesso.

Essa separação permite experimentar e comparar novos detectores sem alterar
silenciosamente o comportamento operacional da solução.

Também cria uma base para evoluções futuras como:

```text
model challengers
promotion policy
model registry
backtesting
monitoramento de drift
```

sem misturar experimentação com decisão operacional.

---

### 49. Por que separar MITRE dos modelos?

MITRE ATT&CK não é utilizado como target ou feature dos modelos atuais.

Sua função é enriquecer a interpretação das evidências.

Essa separação evita misturar:

```text
detecção estatística
```

com:

```text
contextualização de threat intelligence
```

permitindo que ambas evoluam independentemente.

---

### 50. Resumo operacional

O fluxo principal pode ser lembrado pela sequência:

```text
CARREGAR
   │
   ▼
VALIDAR / PREPARAR
   │
   ▼
CRIAR FEATURES
   │
   ▼
CLASSIFICAR
   │
   ▼
EXECUTAR DETECTORES
   │
   ▼
COMPARAR NO BENCHMARK
   │
   ├──────────────────────────────┐
   │                              │
   ▼                              ▼
REGISTRAR VENCEDOR          VALIDAR DETECTOR
DO BENCHMARK                OPERACIONAL
                                  │
                                  ▼
                           ATIVAR DETECTOR
                             OPERACIONAL
                                  │
                                  ▼
                         PRODUZIR SINAL CANÔNICO
                                  │
                                  ▼
                         ESTIMAR SEVERIDADE
                                  │
                                  ▼
                          GERAR ALERTAS
                                  │
                                  ▼
                         PERSISTIR ALERTAS
                                  │
                                  ▼
                         REGISTRAR MÉTRICAS
                                  │
                                  ▼
                         GERAR EVIDÊNCIAS
                                  │
                                  ▼
                         ENRIQUECER COM MITRE
```

O diagrama representa a ordem conceitual das responsabilidades do pipeline.

A comparação entre detectores produz um resultado de benchmark.

A validação do detector operacional produz uma decisão operacional distinta.

Portanto:

```text
COMPARAR
   │
   ▼
benchmark

não significa

COMPARAR
   │
   ▼
promover automaticamente
```

Essa separação é uma propriedade central da arquitetura V3.

---

### 51. Relação com os demais documentos

Este documento descreve o comportamento do pipeline.

A visão arquitetural geral está registrada em:

```text
docs/architecture/overview.md
```

Documentos posteriores poderão detalhar separadamente:

- arquitetura de testes;
- modelos e critérios de avaliação;
- estratégia de anomaly detection;
- integração MITRE ATT&CK;
- persistência;
- reporting;
- arquitetura DevSecOps;
- decisões arquiteturais relevantes.

O objetivo é manter cada documento focado em uma dimensão da solução sem perder
a rastreabilidade entre arquitetura, implementação e evidências.
