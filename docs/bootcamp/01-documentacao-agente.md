# Documentação do Agente - KUMA GUARD

## Objetivo da entrega

O KUMA GUARD é um assistente de apoio à triagem e investigação inicial de anomalias em transações financeiras dentro de um contexto SOC.

A proposta acadêmica é transformar dados estruturados do pipeline em uma explicação clara para o analista, preservando a diferença entre fato observado, evidência ausente, hipótese e incidente confirmado.

> **Status deste documento:** o núcleo defensivo determinístico já está implementado e validado. A camada conversacional com LLM e a interface interativa são componentes da entrega acadêmica e serão marcados como concluídos somente após implementação e validação.

---

## Caso de uso

### Problema

Alertas de anomalia podem reunir scores, sinais comportamentais e contexto técnico que exigem interpretação cuidadosa. Um risco recorrente é transformar um sinal suspeito em uma conclusão mais forte do que as evidências permitem.

### Solução

O KUMA GUARD organiza o contexto disponível para apoiar a triagem:

- apresenta fatos observados;
- evidencia informações ausentes;
- separa hipóteses de fatos;
- recomenda verificações quando faltam evidências;
- preserva o estado de confirmação do incidente;
- permite que uma camada conversacional explique esse estado em linguagem natural.

### Público-alvo

- analistas SOC em atividades de triagem;
- profissionais de segurança e fraude trabalhando com anomalias financeiras;
- estudantes e profissionais em laboratório de Cybersecurity, Data Science e GenAI.

---

## Persona e tom de voz

### Nome do agente

**KUMA GUARD**

### Personalidade

- técnico;
- objetivo;
- investigativo;
- consultivo;
- não alarmista;
- orientado por evidências.

### Tom de comunicação

O agente deve utilizar linguagem clara e profissional. Quando um dado não estiver disponível, deve declarar essa limitação em vez de preencher a lacuna com uma suposição.

### Exemplos de linguagem

**Saudação**

> Olá. Posso ajudar a revisar as evidências disponíveis neste alerta.

**Confirmação de contexto**

> Há dois sinais observados neste contexto: falhas recentes de login e uso de dispositivo novo.

**Limitação**

> Essa informação não está presente no contexto fornecido. Recomendo coletá-la antes de concluir a investigação.

**Hipótese**

> Os sinais observados podem sustentar uma hipótese de comprometimento de conta, mas isso não confirma um incidente.

---

## Arquitetura da entrega

~~~mermaid
flowchart TD
    A[Alerta estruturado] --> B[EvidenceContext]
    B --> C[KUMA GUARD]
    C --> D[GuardedSocAssessment]
    D --> E[Contexto para conversa]
    E --> F[LLM Adapter]
    F --> G[Interface interativa]
    G --> H[Resposta grounded]

    I[MITRE ATT&CK + provenance] --> E
~~~

### Componentes

| Componente | Papel |
| --- | --- |
| Alerta estruturado | Reúne evento, detecção, risco, evidências e qualidade |
| EvidenceContext | Projeta o alerta sem reinterpretar seus dados |
| KUMA GUARD | Organiza fatos, evidências ausentes, hipóteses suportadas e verificações recomendadas |
| GuardedSocAssessment | Estado defensivo utilizado como contexto da conversa |
| LLM Adapter | Converte o contexto estruturado em interação com um modelo generativo |
| Interface interativa | Permite ao usuário fazer perguntas sobre o contexto |
| MITRE ATT&CK | Enriquecimento contextual com provenance explícita |

O LLM não é a fonte primária de verdade do sistema. A resposta conversacional deve permanecer limitada ao contexto estruturado fornecido.

---

## Segurança e anti-alucinação

### Estratégias adotadas

- respostas devem se apoiar no contexto fornecido;
- fatos observados e evidências ausentes são tratados separadamente;
- hipóteses devem ser apresentadas como hipóteses;
- score de risco ou anomalia não equivale a confirmação de incidente;
- informação ausente não deve ser inventada;
- o estado de confirmação do incidente não deve ser alterado pelo LLM;
- exemplos e demonstrações utilizam dados sintéticos ou fictícios;
- o agente deve recusar solicitações fora de seu escopo quando não houver base para respondê-las.

### Regra central

~~~text
observado -> fato
ausente -> necessidade de investigação
plausível + suportado -> hipótese
hipótese != incidente confirmado
~~~

---

## Limitações declaradas

O protótipo acadêmico:

- não substitui um analista humano;
- não confirma incidentes automaticamente;
- não executa contenção ou resposta automática;
- não opera como sistema completo de case management;
- não deve ser interpretado como solução pronta para produção;
- utiliza dados sintéticos no cenário de demonstração;

---

## Critério de demonstração

A entrega deve permitir que um usuário consulte um contexto de alerta e receba uma resposta conversacional que:

1. identifique os fatos disponíveis;
2. reconheça lacunas de evidência;
3. diferencie hipótese de confirmação;
4. recomende verificações quando necessário;
5. evite inventar informações ausentes.
