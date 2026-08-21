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

O pipeline completo pode ser representado, de forma simplificada, como:

```text
PostgreSQL / Supabase
        │
        ▼
Carregamento do dataset
        │
        ▼
Preparação temporal
        │
        ▼
Feature Engineering
        │
        ├─────────────────────────────┐
        │                             │
        ▼                             ▼
Classificação supervisionada    Detecção de anomalias
        │                             │
        │                       ┌─────┼─────┬──────────┐
        │                       ▼     ▼     ▼          ▼
        │                      IF    LOF   OCSVM     Elliptic
        │                       │     │     │        Envelope
        │                       └─────┴─────┴──────────┘
        │                             │
        │                             ▼
        │                     Avaliação comparativa
        │                             │
        │                             ▼
        │                     Seleção do detector
        │                             │
        └──────────────┬──────────────┘
                       │
                       ▼
                Regressão de
                 severidade
                       │
                       ▼
              Persistência de
                  métricas
                       │
                       ▼
               Dataset analisado
                       │
                       ▼
             Reporting / evidências
                       │
              ┌────────┼─────────┐
              ▼        ▼         ▼
           gráficos   PDF      artifacts
                        │
                        ▼
                MITRE ATT&CK
                 enrichment
```

O enriquecimento MITRE ATT&CK pertence à camada de geração de evidências e
reporting. Ele não participa do treinamento ou da seleção dos modelos
analíticos.

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

O dataset é dividido em:

```text
75% treino
25% teste
```

com:

```text
random_state = 42
```

Quando existem múltiplas classes, a divisão utiliza estratificação.

---

### 15. Avaliação da classificação

Entre as métricas produzidas estão:

```text
ROC-AUC de teste
precision da classe suspeita
recall da classe suspeita
F1 da classe suspeita
matriz de confusão
```

Quando a distribuição das classes permite, também é executada validação
cruzada estratificada de três folds utilizando ROC-AUC.

Caso apenas uma classe esteja presente no treino, o pipeline sinaliza a
limitação e continua a execução.

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

O pipeline estima inicialmente a proporção histórica de transações suspeitas:

```text
taxa_suspeita_real
```

A estimativa de `contamination` é limitada inicialmente ao intervalo:

```text
2% ≤ contamination_estimado ≤ 30%
```

Em seguida, é aplicado um teto operacional adicional:

```text
CONTAMINATION_TETO_PRATICO = 15%
```

Portanto:

```text
contamination =
    min(contamination_estimado, 0.15)
```

Esse limite evita que datasets de desenvolvimento com proporções
artificialmente altas de eventos suspeitos façam os detectores classificarem
uma parcela excessiva das observações como anômalas.

---

### 20. Isolation Forest

O `IsolationForest` é configurado atualmente com:

```text
n_estimators = 300
random_state = 42
n_jobs = -1
```

e utiliza o `contamination` calculado pelo pipeline.

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

e ajusta dinamicamente a quantidade de vizinhos de acordo com o tamanho do
dataset.

---

### 22. One-Class SVM

O `OneClassSVM` também utiliza normalização:

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

---

### 23. Elliptic Envelope

O quarto detector utiliza:

```text
StandardScaler
        │
        ▼
EllipticEnvelope
```

com o mesmo `contamination` utilizado pelos demais detectores.

---

### 24. Independência em relação ao target

Os quatro detectores são treinados sem utilizar `status_transacao` como feature
de entrada.

Depois das predições, entretanto, o status histórico é convertido para uma
referência binária e utilizado para auditoria comparativa.

Essa distinção é importante:

```text
status_transacao
      │
      ├── NÃO entra nas features dos detectores
      │
      └── É usado posteriormente para avaliar as predições
```

Portanto, as métricas contra o status histórico não transformam os detectores
em modelos supervisionados.

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

### 28. Seleção do melhor detector

A função:

```python
selecionar_melhor_detector()
```

utiliza a seguinte prioridade:

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

O detector vencedor é armazenado em:

```text
melhor_detector
```

e sua instância fica disponível por meio de:

```text
modelo_agrupamento
```

---

### 29. Resultado dos detectores

Para cada detector executado com sucesso, o `DataFrame` recebe:

```text
anomalia_<detector>
score_anomalia_<detector>
```

Depois da seleção, o detector vencedor também alimenta as colunas de
compatibilidade:

```text
anomalia_score
anomalia_score_bruto
```

Os modelos são persistidos em:

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

Também é produzido um gráfico comparativo.

Isso permite analisar posteriormente não apenas o detector vencedor, mas o
desempenho relativo dos algoritmos avaliados.

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

Assim como na classificação, a divisão utilizada é:

```text
75% treino
25% teste
```

com:

```text
random_state = 42
```

São calculadas:

```text
R²
MAE
RMSE
```

Também é realizada validação cruzada com cinco folds.

R² negativo em validação cruzada é tratado explicitamente como sinal de baixa
capacidade de generalização, situação especialmente relevante em datasets
pequenos.

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

recebendo:

```text
dataset analisado
melhor detector
indicador de amostra pequena
engine de banco de dados
```

A camada de reporting utiliza essas informações para consolidar evidências
analíticas e contexto adicional.

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

Uma falha individual em um algoritmo de anomaly detection não impede
automaticamente a execução dos demais.

A falha é registrada junto às métricas do detector.

Somente a ausência de qualquer detector válido impede a seleção final.

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

> O sistema carrega transações, constrói features comportamentais e contextuais,
> executa uma classificação supervisionada de triagem e compara quatro
> detectores de anomalia não supervisionados. Os detectores são avaliados contra
> o status histórico para fins de auditoria, e o melhor é selecionado por F1,
> recall, precision e tempo de execução. Em paralelo, uma regressão estima uma
> severidade contínua de risco. Os resultados são persistidos e utilizados na
> geração de evidências e de um relatório enriquecido com MITRE ATT&CK.

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

Algoritmos de anomaly detection fazem hipóteses diferentes sobre os dados.

Por isso, o projeto não assume antecipadamente que um único detector será
sempre superior.

A estratégia implementada é:

```text
executar
   ↓
medir
   ↓
comparar
   ↓
selecionar
```

A escolha torna-se uma decisão observável e registrada, em vez de uma
preferência fixa escondida no código.

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

O fluxo completo pode ser lembrado pela sequência:

```text
CARREGAR
   ↓
PREPARAR
   ↓
CRIAR FEATURES
   ↓
CLASSIFICAR
   ↓
DETECTAR
   ↓
COMPARAR
   ↓
SELECIONAR
   ↓
ESTIMAR SEVERIDADE
   ↓
REGISTRAR MÉTRICAS
   ↓
GERAR EVIDÊNCIAS
   ↓
ENRIQUECER COM MITRE
```

Essa sequência representa o caminho principal percorrido pelos dados durante a
execução atual do projeto.

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
