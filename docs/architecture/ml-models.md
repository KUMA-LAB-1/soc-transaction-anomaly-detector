# Modelos Analíticos e Estratégia de Machine Learning

## 1. Objetivo

Este documento descreve a camada analítica do
`soc-transaction-anomaly-detector`.

O objetivo não é apenas listar os algoritmos utilizados, mas explicar:

- qual problema cada modelo procura resolver;
- como classificação, detecção de anomalias e regressão se complementam;
- quais features cada abordagem utiliza;
- como os modelos são avaliados;
- como o detector principal é selecionado;
- quais outputs são produzidos;
- quais limitações metodológicas devem ser consideradas.

A arquitetura atual utiliza três perspectivas analíticas diferentes:

```text
                         CAMADA ANALÍTICA
                               │
              ┌────────────────┼─────────────────┐
              ▼                ▼                 ▼
        Classificação      Anomaly Detection   Regressão
       supervisionada      multi-detector      severidade
              │                 │                │
              ▼           ┌─────┴─────┐          ▼
       proba_suspeita     ▼           ▼   score_risco_predito
                     Benchmark    Política
                    retrospectivo operacional
                         │             │
                         ▼             ▼
                melhor_detector   detector_operacional
                  _benchmark
```

Essas abordagens não são equivalentes e não devem ser interpretadas como
substitutas umas das outras.

---

## 2. Visão conceitual

A camada de Machine Learning procura responder a três perguntas diferentes.

### Classificação

```text
Com base no histórico disponível,
esta transação se parece com casos classificados como suspeitos?
```

### Detecção de anomalias

```text
Esta transação apresenta comportamento estatisticamente incomum
em relação ao conjunto analisado?
```

### Regressão de severidade

```text
Qual score contínuo de severidade o modelo estima para esta transação,
de acordo com a escala definida pelo projeto?
```

A combinação dessas três perspectivas permite representar diferentes dimensões
do comportamento analisado.

### Estratégias de validação disponíveis na V3

A arquitetura analítica suporta estratégias de validação diferentes conforme o
tipo de modelo.

No estado atual:

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

---

## Parte I — Classificação supervisionada

### 3. Objetivo da classificação

O classificador de triagem utiliza aprendizado supervisionado.

Sua função é aprender padrões associados aos status históricos utilizados pelo
projeto e produzir uma probabilidade de suspeita para cada transação.

A implementação está localizada em:

```text
src/models/classification.py
```

A função principal é:

```python
treinar_classificador_triagem()
```

---

### 4. Algoritmo utilizado

O modelo atual é:

```text
DecisionTreeClassifier
```

Configuração:

```text
max_depth = 4
random_state = 42
class_weight = balanced
```

### `max_depth = 4`

Limita a profundidade máxima da árvore.

Essa configuração reduz a complexidade do modelo em comparação com uma árvore
sem limite explícito.

### `random_state = 42`

Mantém reprodutibilidade nas operações que dependem de aleatoriedade.

### `class_weight = balanced`

Ajusta automaticamente o peso das classes de acordo com sua frequência.

Esse controle é especialmente útil quando a quantidade de transações suspeitas
é diferente da quantidade de transações consideradas normais.

---

### 5. Construção do target

Os status definidos como suspeitos são:

```text
Em Análise
Bloqueada por Suspeita
```

O target binário é construído como:

```text
1 = status suspeito
0 = demais status
```

Portanto:

```text
status_transacao
       │
       ▼
Regra de classificação
       │
       ▼
Target supervisionado
```

Esse uso do status histórico diferencia o classificador dos detectores de
anomalia.

---

### 6. Features utilizadas

A classificação utiliza as seguintes features-base:

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

Também utiliza:

```text
tipo_transacao
```

após transformação por one-hot encoding.

O pipeline seleciona apenas as features efetivamente disponíveis após a
transformação do dataset.

---

### 7. Train/test split

O dataset é dividido em:

```text
75% treino
25% teste
```

utilizando:

```text
random_state = 42
```

Quando existe mais de uma classe, a divisão é estratificada.

Isso busca preservar aproximadamente a distribuição das classes entre os
conjuntos de treino e teste.

---

### 8. Métricas da classificação

A avaliação produz métricas como:

```text
ROC-AUC
precision
recall
F1
matriz de confusão
```

As métricas de precision, recall e F1 são obtidas especificamente para a classe
considerada suspeita.

Quando a distribuição das classes permite, também é executada validação cruzada
estratificada com três folds.

```text
StratifiedKFold
n_splits = 3
shuffle = True
random_state = 42
```

O scoring utilizado na validação cruzada é:

```text
ROC-AUC
```

---

### 9. Caso de classe única

Datasets pequenos ou desequilibrados podem produzir um conjunto de treino
contendo apenas uma classe.

Nesse cenário:

- o pipeline não encerra imediatamente;
- a limitação é sinalizada;
- ROC-AUC pode ficar indisponível;
- a probabilidade é representada de maneira compatível com a única classe
  observada.

Essa tolerância permite manter a execução útil em desenvolvimento e prova de
conceito sem esconder a limitação metodológica.

---

### 10. Output da classificação

Depois do treinamento, o modelo é aplicado ao conjunto completo.

A principal coluna produzida é:

```text
proba_suspeita
```

Ela representa a probabilidade estimada pelo classificador para a classe
suspeita.

O modelo é persistido em:

```text
reports/models/classificador.joblib
```

Também é produzido um gráfico de importância das features.

---

### 11. Como interpretar `proba_suspeita`

`proba_suspeita` deve ser interpretada como uma saída do classificador
supervisionado treinado sobre os rótulos históricos utilizados.

Ela não deve ser apresentada automaticamente como:

```text
probabilidade real de fraude
```

ou:

```text
probabilidade real de incidente
```

O significado tecnicamente correto é mais próximo de:

```text
probabilidade estimada de pertencimento
à classe histórica definida como suspeita
```

Essa distinção é importante porque o modelo aprende a partir da definição
histórica de `status_transacao`.

---

## Parte II — Detecção de anomalias

### 12. Objetivo da abordagem multi-detector

O projeto não assume que um único algoritmo será sempre superior.

Por isso, a camada de anomaly detection executa diferentes modelos e compara
seus resultados.

A implementação principal está localizada em:

```text
src/models/anomaly_detection.py
```

Os detectores atuais são:

```text
Isolation Forest
Local Outlier Factor
One-Class SVM
Elliptic Envelope
```

A estratégia é:

```text
executar
   ↓
avaliar
   ↓
comparar
   ↓
selecionar
```

---

### 13. Features utilizadas pelos detectores

Os detectores utilizam:

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

O pipeline utiliza somente as colunas disponíveis.

Valores ausentes são preenchidos com zero antes da execução.

---

### 14. O papel de `status_transacao`

Uma distinção arquitetural importante é que:

```text
status_transacao
```

não faz parte das features utilizadas para treinar os detectores.

O status histórico é usado posteriormente apenas como referência para avaliação
comparativa.

Portanto:

```text
features
   │
   ▼
detector não supervisionado
   │
   ▼
predição de anomalia
   │
   ▼
comparação com status histórico
```

e não:

```text
status histórico
   ↓
treinamento do detector
```

Essa distinção preserva a natureza não supervisionada ou de novelty detection
dos algoritmos utilizados.

---

### 15. Política de contamination

O parâmetro `contamination` representa uma configuração explícita da política
de detecção de anomalias.

A implementação atual define:

```text
CONTAMINATION_PISO_PRATICO = 0.02
CONTAMINATION_TETO_PRATICO = 0.15
CONTAMINATION_PADRAO = 0.15
```

Portanto, o valor configurado deve permanecer no intervalo:

```text
0.02 <= contamination <= 0.15
```

Quando nenhum valor é informado explicitamente, a configuração padrão utilizada
é:

```text
contamination = 0.15
```

O mesmo valor configurado é compartilhado pelos detectores que utilizam esse
parâmetro ou conceito equivalente:

```text
Isolation Forest
Local Outlier Factor
One-Class SVM
Elliptic Envelope
```

A taxa histórica de status considerados suspeitos continua sendo calculada como:

```text
taxa_suspeita_real
```

mas possui finalidade distinta.

A relação atual é:

```text
contamination configurado
          │
          ├── validação entre 0.02 e 0.15
          │
          ▼
configuração dos detectores


status_transacao
          │
          ▼
taxa_suspeita_real
          │
          ▼
auditoria retrospectiva
```
`status_transacao` e `taxa_suspeita_real` não configuram o parâmetro
`contamination`.

Essa separação evita que labels históricos ou proporções artificiais presentes
em datasets sintéticos determinem implicitamente a quantidade esperada de
anomalias.

---

### 16. Por que contamination é uma política explícita?

`contamination` influencia diretamente o comportamento dos algoritmos que
estimam ou utilizam uma proporção esperada de observações anômalas.

Por esse motivo, a configuração não deve ser derivada automaticamente dos
labels utilizados posteriormente para avaliar os detectores.

A arquitetura separa:

```text
configuração do detector
          │
          ▼
contamination

          ≠

referência retrospectiva
          │
          ▼
status_transacao
```

O intervalo atualmente aceito, entre 2% e 15%, funciona como uma política
explícita do projeto.

O valor padrão atual é:

`15%`

Esse valor não deve ser interpretado como parâmetro universal ideal nem como
estimativa da taxa real de fraude ou de ataques.

Ele representa apenas a política configurada no estado atual da implementação e
pode ser alterado explicitamente dentro dos limites suportados.

A qualidade dos detectores continua sendo avaliada separadamente por meio das
métricas produzidas contra a referência histórica disponível.

---

## Parte III — Detectores

### 17. Isolation Forest

O primeiro detector é:

```text
IsolationForest
```

Configuração atual:

```text
n_estimators = 300
random_state = 42
n_jobs = -1
contamination = valor configurado
```

O parâmetro `contamination` recebido pela camada de detecção é validado antes da
criação do modelo e permanece dentro do intervalo suportado pelo projeto.

O valor padrão atual é:

`0.15`

Isolation Forest procura identificar observações que podem ser isoladas mais
facilmente por particionamentos aleatórios.

No projeto, ele funciona como uma das perspectivas utilizadas na comparação
multi-detector.

---

### 18. Local Outlier Factor

O segundo detector utiliza:

```text
StandardScaler
      │
      ▼
LocalOutlierFactor
```

O número de vizinhos é ajustado dinamicamente de acordo com o tamanho do
conjunto utilizado para treinamento.

A implementação utiliza:

`novelty = True`

Essa configuração permite utilizar o modelo posteriormente por meio da interface
de predição.

O parâmetro:

`contamination`

recebe o mesmo valor explicitamente configurado para a execução dos demais
detectores que utilizam essa política.

Ele não é derivado de `status_transacao` nem de `taxa_suspeita_real`.

---

### 19. One-Class SVM

A implementação utiliza:

```text
StandardScaler
      │
      ▼
OneClassSVM
```

Configuração atual:

```text
kernel = rbf
gamma = scale
nu = contamination
```

Para o `OneClassSVM`, o valor explicitamente configurado como `contamination`
na camada comum de detecção é utilizado como parâmetro `nu`.

Assim:

```text
contamination configurado
          │
          ▼
         nu
```

A normalização é aplicada antes do modelo porque essa abordagem é sensível à
escala das features.

Assim como nos demais detectores, esse valor não é derivado dos labels
históricos utilizados posteriormente para auditoria.

---

### 20. Elliptic Envelope

O quarto detector utiliza:

```text
StandardScaler
      │
      ▼
EllipticEnvelope
```

Configuração relevante:

```text
contamination = valor configurado
random_state = 42
support_fraction = None
```

O mesmo valor de `contamination` validado pela camada comum de detecção é
fornecido ao modelo.

O modelo representa uma abordagem baseada em distribuição e covariância,
distinta das demais técnicas presentes no conjunto de detectores.

Assim como nas outras abordagens, `status_transacao` não participa da
configuração do modelo.

Os labels históricos são utilizados apenas posteriormente para avaliação
retrospectiva.

---

### 21. Por que alguns detectores utilizam `StandardScaler`?

LOF, One-Class SVM e Elliptic Envelope são executados dentro de pipelines que
incluem normalização.

Isso reduz o efeito de diferenças de escala entre features como:

```text
valor_transacao
hora
falhas_login_recentes
zscore_valor_cliente
```

Isolation Forest, por outro lado, é utilizado diretamente sem `StandardScaler`
na implementação atual.

---

## Parte IV — Avaliação dos detectores

### 22. Conversão das predições

Os detectores utilizados retornam:

```text
1  = observação normal
-1 = anomalia
```

Para comparação com o status histórico, a implementação converte:

```text
-1 → 1
 1 → 0
```

produzindo uma representação binária compatível com as métricas utilizadas.

---

### 23. Métricas comparativas

A função:

```python
avaliar_detector()
```

calcula, para cada detector executado com sucesso:

```text
precision
recall
F1
ROC-AUC
```

Também são registrados metadados e indicadores da execução, incluindo:

```text
quantidade de anomalias
taxa de anomalias
tempo de execução
estratégia de validação
quantidade de registros de treino
quantidade de registros de avaliação
contamination configurado
contamination utilizado
```

A execução também preserva:

`taxa_suspeita_real`

como referência retrospectiva do dataset.

Essa taxa não participa da configuração de `contamination`.

Portanto:

```text
contamination_configurado
contamination_usado
          │
          ▼
configuração / registro da execução


taxa_suspeita_real
          │
          ▼
referência para auditoria retrospectiva
```

As métricas permitem comparar os detectores sob uma referência comum sem
confundir o desempenho retrospectivo com a política utilizada para configurar
os modelos.

---

### 24. Significado dessas métricas

As métricas comparam as anomalias identificadas pelo detector com os status
históricos classificados como suspeitos.

Portanto, elas representam:

```text
concordância com o rótulo histórico
```

e não necessariamente:

```text
capacidade absoluta de identificar fraude real
```

Essa distinção é essencial para interpretar corretamente F1, precision, recall e
ROC-AUC nesse contexto.

---

### 25. Tratamento de falha individual

Cada detector é executado isoladamente dentro de tratamento de exceção.

Se um detector falhar:

```text
status = erro
```

é registrado para ele.

Os demais continuam sendo executados.

Essa abordagem melhora a resiliência da comparação:

```text
Detector A → sucesso
Detector B → erro
Detector C → sucesso
Detector D → sucesso
           │
           ▼
comparação dos válidos
```

Somente quando não existe nenhum detector válido a seleção final gera erro.

---

## Parte V - Benchmark e política operacional

### 26. Critério do benchmark

A comparação retrospectiva dos detectores utiliza a função:

```python
selecionar_melhor_detector_benchmark()
```

Somente os detectores que concluíram sua execução com sucesso participam dessa
seleção.

Os critérios utilizados são, nesta ordem:

```text
1. maior F1
2. maior recall
3. maior precision
4. menor tempo de execução
```

O processo pode ser representado como:

```text
F1
 │
 └── empate
       ▼
     Recall
       │
       └── empate
             ▼
          Precision
             │
             └── empate
                   ▼
             menor tempo
```

O resultado representa desempenho retrospectivo contra os labels históricos
disponíveis.

Ele não constitui, por si só, promoção operacional do detector.

O nome do vencedor do benchmark é armazenado em:

`self.melhor_detector_benchmark`

A função:

```python
selecionar_melhor_detector()
```

permanece disponível temporariamente apenas como compatibilidade com a API
anterior e delega sua execução ao seletor de benchmark.

---

### 27. Por que F1 é o primeiro critério?

F1 combina `precision` e `recall` em uma única métrica.

No contexto atual do projeto, ele funciona como primeiro critério do benchmark
para evitar comparar os detectores olhando apenas para uma dessas dimensões.

Depois disso:

`recall`

é utilizado como primeiro desempate.

Em seguida:

`precision`

e finalmente:

`tempo de execução`

O ranking produzido por esses critérios possui finalidade comparativa e
retrospectiva.

Portanto:

```text
melhor resultado no benchmark
              │
              ▼
evidência comparativa

              ≠

decisão operacional automática
```

Essa distinção permite avaliar novos modelos sem alterar silenciosamente o
comportamento operacional do pipeline.

---

### 28. Detector operacional

A política operacional é independente do resultado do benchmark.

O detector desejado é definido inicialmente por:

`self.detector_operacional_configurado`

O padrão atual é:

`isolation_forest`

Depois da execução dos detectores, o pipeline verifica se o detector
configurado está entre aqueles que concluíram com sucesso.

O fluxo é:

```text
detector_operacional_configurado
              │
              ▼
   detector executou com sucesso?
          │              │
         sim            não
          │              │
          ▼              ▼
detector_operacional   RuntimeError
```

Quando validado, o detector passa a ser registrado em:

`self.detector_operacional`

e sua instância correspondente é mantida em:

`self.modelo_agrupamento`

O detector operacional alimenta as colunas canônicas:

```text
anomalia_score
anomalia_score_bruto
```

e também é utilizado pelas etapas operacionais posteriores, incluindo:

```text
geração de alertas
relatório PDF
```

Se o detector operacional configurado não estiver disponível entre os modelos
executados com sucesso, a execução falha explicitamente.

O pipeline não promove silenciosamente o vencedor do benchmark como substituto.

A relação arquitetural é:

```text
resultados válidos
        │
        ├──────────────────────┐
        │                      │
        ▼                      ▼
benchmark retrospectivo   política operacional
        │                      │
        ▼                      ▼
melhor_detector_benchmark  detector_operacional_configurado
                               │
                               ▼
                        validação fail-closed
                               │
                               ▼
                        detector_operacional
                               │
                   ┌───────────┼───────────┐
                   ▼           ▼           ▼
             anomaly score   alertas      PDF
```

O atributo:

`self.melhor_detector`

permanece temporariamente como alias de compatibilidade com consumidores da API
anterior.

Ele não representa mais a fonte canônica da política operacional.

---

### 29. Resultados individuais preservados

O benchmark e a definição do detector operacional não eliminam os resultados
individuais dos demais detectores.

Para cada modelo executado com sucesso são preservadas colunas específicas,
como:

```text
anomalia_isolation_forest
score_anomalia_isolation_forest

anomalia_local_outlier_factor
score_anomalia_local_outlier_factor

anomalia_one_class_svm
score_anomalia_one_class_svm

anomalia_elliptic_envelope
score_anomalia_elliptic_envelope
```

Esses resultados permitem:

- auditoria dos detectores;
- comparação retrospectiva;
- investigação de divergências;
- geração de métricas individuais;
- avaliação de futuros modelos challengers.

As colunas:

```text
anomalia_score
anomalia_score_bruto
```

possuem finalidade diferente.

Elas representam o detector operacional validado e fornecem uma interface comum
para as etapas posteriores do pipeline.

Assim:

```text
resultados individuais
        │
        ▼
comparação / auditoria

detector operacional
        │
        ▼
sinal canônico do pipeline
```

---

### 30. Persistência dos detectores

Cada modelo é salvo em:

```text
reports/models/<nome_do_detector>.joblib
```

A persistência torna possível inspecionar posteriormente as instâncias treinadas
na execução.

---

## Parte VI — Regressão de severidade

### 31. Objetivo

A terceira perspectiva analítica do pipeline é a regressão.

A implementação atual utiliza:

```text
LinearRegression
```

A função principal está em:

```python
treinar_regressao_severidade()
```

---

### 32. Construção do target de severidade

O projeto define a seguinte escala:

```text
Aprovada                 → 5
Concluída                → 5
Em Análise               → 55
Bloqueada por Suspeita   → 95
```

Status não encontrados no mapa recebem:

```text
30
```

Essa escala é uma convenção definida pelo projeto.

Ela não representa uma escala externa padronizada de fraude, incidente ou risco.

---

### 33. Interpretação correta do target

O target pode ser entendido como:

```text
representação numérica interna
da severidade associada ao status histórico
```

e não como:

```text
probabilidade estatística real de fraude
```

Essa distinção deve ser preservada em relatórios, documentação e apresentações.

---

### 34. Features utilizadas pela regressão

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

Essas features procuram combinar comportamento financeiro, histórico e sinais
contextuais.

---

### 35. Treinamento

A divisão utilizada é:

```text
75% treino
25% teste
```

com:

```text
random_state = 42
```

O modelo treinado é:

```text
LinearRegression
```

---

### 36. Métricas da regressão

A avaliação utiliza:

```text
R²
MAE
RMSE
```

Também é executada validação cruzada com:

```text
5 folds
```

O pipeline registra:

```text
r2_teste
mae_teste
rmse_teste
r2_cv_media
r2_cv_desvio
```

---

### 37. R² negativo

R² negativo em validação cruzada é interpretado como sinal de que o modelo ainda
não generaliza adequadamente para os folds avaliados.

O pipeline não esconde essa condição.

Ela é sinalizada para que resultados obtidos sobre bases pequenas sejam
interpretados de maneira adequada.

---

### 38. Score final de severidade

Depois do treinamento, a regressão é aplicada ao dataset completo.

As predições são limitadas para:

```text
0 ≤ score_risco_predito ≤ 100
```

O resultado é armazenado na coluna:

```text
score_risco_predito
```

Esse score representa a saída do modelo de regressão de acordo com a escala de
target definida pelo projeto.

---

### 39. Persistência da regressão

O modelo treinado é persistido em:

```text
reports/models/regressao.joblib
```

---

## Parte VII — Persistência dos modelos

### 40. Artifacts produzidos

A execução atual pode produzir:

```text
reports/models/
├── classificador.joblib
├── isolation_forest.joblib
├── local_outlier_factor.joblib
├── one_class_svm.joblib
├── elliptic_envelope.joblib
└── regressao.joblib
```

A existência de um arquivo específico depende da conclusão bem-sucedida do
respectivo modelo.

---

### 41. Estado mantido pelo orquestrador

`SecurityDetector` mantém durante a execução:

```text
modelo_classificacao
modelos_anomalia
melhor_detector
modelo_agrupamento
modelo_regressao
metricas
```

Isso permite que a camada de orquestração integre resultados produzidos por
componentes especializados.

---

## Parte VIII — Relação entre as três abordagens

### 42. Classificação

```text
Tipo:
supervisionada

Aprende com:
status histórico

Output principal:
proba_suspeita
```

---

### 43. Anomaly Detection

```text
Tipo:
não supervisionada / novelty detection

Aprende com:
features das transações

Status histórico:
usado somente na avaliação comparativa

Output principal:
anomalia_score
```

---

### 44. Regressão

```text
Tipo:
supervisionada

Aprende com:
target de severidade derivado dos status históricos

Output principal:
score_risco_predito
```

---

### 45. Visão combinada

A arquitetura pode ser resumida como:

```text
                    TRANSAÇÃO
                        │
                        ▼
                     FEATURES
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
    CLASSIFICAÇÃO    ANOMALIA      REGRESSÃO
          │             │             │
          ▼             ▼             ▼
 proba_suspeita   anomaly signal   risk score
                        │
                        ▼
                  detector escolhido
          └─────────────┼─────────────┘
                        ▼
                   REPORTING
```

As três saídas fornecem perspectivas complementares.

---

## Parte IX — Limitações metodológicas

### 46. Dataset sintético ou limitado

Resultados obtidos em datasets sintéticos, controlados ou pequenos não devem ser
interpretados automaticamente como desempenho de produção.

Valores altos de:

```text
ROC-AUC
F1
R²
```

podem refletir características específicas do conjunto analisado.

---

### 47. Status histórico não é verdade absoluta

O projeto utiliza `status_transacao` em diferentes papéis:

```text
classificação → target
regressão → origem do target de severidade
detecção de anomalia → referência de auditoria
```

Esses status representam a referência disponível no dataset.

Eles não provam automaticamente a ocorrência real de fraude ou incidente.

---

### 48. Severidade é definida pelo projeto

A escala:

```text
5 / 30 / 55 / 95
```

é uma decisão interna de modelagem.

Ela não deve ser apresentada como score padronizado reconhecido externamente.

---

### 49. Seleção do detector depende do dataset

O melhor detector é escolhido de acordo com o conjunto analisado.

Isso significa que:

```text
elliptic_envelope
```

ser vencedor em uma execução não implica que será o melhor algoritmo para todos
os datasets futuros.

A própria existência do mecanismo de comparação busca evitar essa suposição.

---

### 50. Contamination não é universal

O teto atual de 15% é uma regra operacional da implementação.

Em outro domínio ou dataset, o valor apropriado pode ser diferente.

Por isso, esse parâmetro deve ser entendido como configuração atual do projeto,
não como constante universal de anomaly detection.

---

## Parte X — Decisões atuais

### 51. Por que Decision Tree?

No estado atual do projeto, `DecisionTreeClassifier` fornece uma abordagem
supervisionada simples e interpretável para triagem.

A profundidade limitada também mantém o modelo relativamente controlado.

A implementação não afirma que Decision Tree seja necessariamente o algoritmo
ótimo para produção.

Ela funciona como componente da arquitetura atual e como base para comparação e
evolução futura.

---

### 52. Por que quatro detectores?

Os algoritmos utilizados fazem hipóteses diferentes sobre os dados.

Manter múltiplos detectores permite:

```text
diversidade de abordagem
        ↓
comparação objetiva
        ↓
seleção observável
```

em vez de fixar antecipadamente um único algoritmo como vencedor permanente.

---

### 53. Por que Linear Regression?

A regressão atual oferece uma baseline simples para transformar sinais
analíticos em uma estimativa contínua de severidade.

Ela também permite acompanhar métricas conhecidas como:

```text
R²
MAE
RMSE
```

A implementação pode ser evoluída futuramente caso dados maiores ou mais
representativos justifiquem modelos adicionais.

---

## Parte XI — Como explicar em entrevista

### 54. “Por que você usa classificação e anomaly detection?”

Uma resposta curta:

> Porque eles resolvem problemas diferentes. O classificador supervisionado
> aprende padrões associados aos status históricos e produz uma probabilidade
> de suspeita. Os detectores de anomalia não utilizam esse status como feature;
> eles procuram observações incomuns nas features. Depois eu uso o status
> histórico apenas para comparar o desempenho dos detectores.

---

### 55. “Por que quatro detectores?”

> Porque anomaly detection depende bastante das características dos dados. Em vez
> de escolher arbitrariamente um algoritmo, eu executo quatro abordagens,
> calculo métricas comparáveis e seleciono o melhor detector daquele conjunto
> por F1, recall, precision e tempo de execução.

---

### 56. “Isso não torna anomaly detection supervisionada?”

> Não. O `status_transacao` não entra como feature de treinamento dos detectores.
> Ele é utilizado posteriormente como referência de auditoria para comparar as
> anomalias produzidas pelos modelos.

---

### 57. “O que significa `proba_suspeita`?”

> É a probabilidade produzida pelo classificador para a classe histórica definida
> como suspeita. Eu não interpreto esse valor automaticamente como probabilidade
> real de fraude, porque ele depende da definição dos rótulos históricos
> disponíveis.

---

### 58. “O que significa `score_risco_predito`?”

> É uma estimativa contínua produzida pela regressão usando uma escala de
> severidade definida dentro do projeto. Ela serve para demonstração e
> priorização analítica, mas não representa uma escala universal ou uma
> probabilidade real de fraude.

---

### 59. “Como contamination é definido atualmente?”

> `contamination` é uma política explícita da camada de detecção de anomalias.
> O valor padrão atual é 15%, e valores configurados explicitamente devem
> permanecer entre 2% e 15%. A taxa histórica de status suspeitos continua
> disponível para auditoria retrospectiva, mas não configura os detectores.
> Essa separação impede que os labels utilizados posteriormente para avaliação
> determinem implicitamente o comportamento dos modelos não supervisionados.

---

### 60. “Por que salvar todos os modelos se existe um vencedor no benchmark?”

> Porque o benchmark possui finalidade comparativa e não elimina a importância
> da auditoria. Os modelos e resultados individuais são preservados para
> permitir comparação, reprodução e investigação das diferenças entre os
> detectores. Além disso, o vencedor do benchmark não é promovido
> automaticamente para uso operacional: a política operacional é configurada e
> validada separadamente.

---

## Parte XII - Validação temporal

### 61. Estratégias de validação

A V3 adiciona estratégias temporais explícitas às três famílias de modelos
analíticos.

Essas estratégias são capacidades disponíveis na camada de modelos e não
alteram automaticamente os defaults utilizados pelo `SecurityDetector`.

A configuração atual é:

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

Portanto, a existência da estratégia temporal não significa que toda execução do
pipeline utilize validação temporal por padrão.

O `SecurityDetector` atualmente chama os módulos sem substituir suas estratégias
padrão.

Essa decisão preserva compatibilidade com o comportamento anterior enquanto a
infraestrutura temporal é desenvolvida e validada incrementalmente.

---

### 62. Holdout temporal

A estratégia temporal utiliza separação cronológica entre passado e futuro.

O holdout é construído por:

```python
dividir_holdout_temporal()
```

A proporção de teste utilizada atualmente pelos modelos que ativam essa
estratégia é:

`test_size = 0.25`

Conceitualmente:

```text
passado
  │
  ▼
treino
  │
  ├───────────────────────┐
  │                       │
  ▼                       ▼
modelo                  futuro
                          │
                          ▼
                     avaliação
```

A divisão não utiliza embaralhamento aleatório.

Os índices retornados são posicionais e podem ser aplicados ao `DataFrame` com
`.iloc`.

---

### 63. Fronteiras temporais estritas

Registros com timestamps idênticos são tratados como pertencentes ao mesmo
bloco temporal quando não existe outra informação que estabeleça uma ordem
causal entre eles.

Por isso, um mesmo timestamp não pode aparecer simultaneamente nos conjuntos de
treino e avaliação.

A propriedade exigida é:

`max(timestamp_treino) < min(timestamp_teste)`

e não apenas:

`max(timestamp_treino) <= min(timestamp_teste)`

Uma ordenação estável continua sendo utilizada para manter determinismo entre
registros empatados, mas estabilidade de ordenação não é interpretada como
evidência de causalidade.

No holdout, quando o corte desejado atravessaria um grupo de timestamps
empatados, é escolhida a fronteira temporal válida mais próxima.

Quando duas fronteiras válidas estão à mesma distância, a menor posição é
utilizada como desempate determinístico.

Se o dataset não possuir nenhuma fronteira entre timestamps distintos, a
divisão falha explicitamente.

O pipeline não inventa uma ordem causal que os dados não conseguem demonstrar.

---

### 64. Validação cruzada temporal

Classificação e regressão também podem utilizar validação cruzada temporal com
janela de treino expansiva.

Os folds são construídos por:

```python
criar_folds_temporais()
```

A topologia inicial das janelas utiliza `TimeSeriesSplit`.

Conceitualmente:

```text
Fold 1
Treino ───────► Teste

Fold 2
Treino ─────────────► Teste

Fold 3
Treino ───────────────────► Teste
```

Quando o início original de uma janela de teste atravessaria um bloco de
timestamps empatados, o início do teste avança até a primeira fronteira temporal
causalmente válida dentro da própria janela.

O teste nunca é deslocado para trás para invadir uma janela de avaliação
anterior.

A propriedade temporal permanece:

`max(timestamp_treino) < min(timestamp_teste)`

Se uma janela não possuir fronteira temporal válida, a criação dos folds falha
explicitamente.

---

### 65. Semântica de gap

O parâmetro:

`gap`

continua representando quantidade de registros.

Ele não representa quantidade de timestamps únicos.

Quando uma fronteira de teste precisa avançar por causa de timestamps
empatados, o final do conjunto de treino é recalculado para preservar exatamente
o número configurado de registros entre treino e teste.

Exemplo conceitual para:

`gap = 1`

```text
treino
  │
  ▼
[ registros de treino ]
          │
          ▼
     [ 1 registro ]
          │
          ▼
         teste
```

Essa política preserva a semântica original do parâmetro enquanto impede
sobreposição causal entre treino e avaliação.

---

### 66. Validação temporal por família de modelo

Na classificação supervisionada, a estratégia temporal utiliza:

```text
holdout temporal
+
3 folds temporais para validação cruzada
```

Folds sem diversidade de classes suficiente para avaliação ROC AUC são
descartados da validação cruzada.

Na regressão de severidade, a estratégia temporal utiliza:

```text
holdout temporal
+
5 folds temporais para validação cruzada
```

Folds pequenos demais para a avaliação configurada são desconsiderados.

Na detecção de anomalias, a estratégia temporal utiliza:

```text
passado
  │
  ▼
fit dos detectores
  │
  ▼
futuro
  │
  ▼
predict + avaliação retrospectiva
```

Ou seja, os detectores são ajustados apenas no conjunto de treino e avaliados no
período futuro.

A estratégia padrão da detecção de anomalias continua sendo `in_sample`.

---

### 67. Relação com features históricas causais

A validação temporal complementa a geração causal de features históricas.

Features associadas ao histórico de um cliente devem representar somente
informações disponíveis antes do registro corrente.

Conceitualmente:

```text
histórico anterior
        │
        ▼
feature causal
        │
        ▼
registro atual
        │
        ▼
modelo
```

A combinação de features históricas causais com separações temporais reduz o
risco de leakage entre observações futuras e decisões realizadas no passado.

Essa propriedade é especialmente importante para avaliações que procuram
aproximar o comportamento que seria observado em execução cronológica real.

---

## Parte XIII - Possíveis evoluções

### 68. Evoluções futuras

A arquitetura permite avaliar futuramente, conforme a disponibilidade de dados e
as necessidades do projeto:

- novos classificadores;
- novos detectores de anomalia;
- ensemble de detectores;
- tuning sistemático de hiperparâmetros;
- calibração das probabilidades;
- backtesting temporal com múltiplas janelas;
- avaliação de diferentes horizontes temporais;
- datasets maiores e mais representativos;
- tratamento mais avançado de desbalanceamento;
- versionamento formal dos modelos;
- tracking de experimentos;
- model registry;
- monitoramento de model drift;
- monitoramento de data drift;
- explicabilidade adicional dos modelos;
- avaliação de custo de falsos positivos e falsos negativos.

Esses itens representam possibilidades de evolução e não funcionalidades
implementadas no estado atual.

A validação temporal básica, incluindo holdout cronológico, validação cruzada
expansiva e tratamento de timestamps empatados nas fronteiras, já faz parte da
implementação V3 e, portanto, não é classificada como evolução futura.

---

### 69. Relação com os demais documentos

A visão arquitetural geral está em:

```text
docs/architecture/overview.md
```

O fluxo completo de execução está descrito em:

```text
docs/architecture/pipeline.md
```

Este documento concentra especificamente:

```text
modelos
targets
features
avaliação
seleção
interpretação
limitações
```

Documentos posteriores poderão aprofundar testes, DevSecOps, MITRE ATT&CK e
decisões arquiteturais específicas.
