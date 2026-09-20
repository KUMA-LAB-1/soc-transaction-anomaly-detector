# Base de Conhecimento - KUMA GUARD

## Visão geral

A base de conhecimento da demonstração acadêmica é formada por dados estruturados e sintéticos produzidos pelo próprio pipeline do KUMA-LAB.

O agente não precisa consultar um conjunto aberto de documentos para responder ao cenário principal. O contexto relevante é preparado a partir do alerta e de seus artefatos estruturados antes de chegar à camada conversacional.

---

## Fontes utilizadas

| Fonte | Formato | Utilização |
| --- | --- | --- |
| Alert | objeto estruturado | evento, detecção, risco, evidências, qualidade e contexto MITRE |
| EvidenceContext | objeto estruturado | projeção das evidências do alerta sem reinterpretação |
| GuardedSocAssessment | objeto estruturado | fatos observados, evidências ausentes, hipóteses suportadas, checks e confirmação |
| MITRE ATT&CK com provenance | contexto estruturado | enriquecimento técnico quando disponível |
| dados sintéticos do projeto | dataset controlado | geração de cenários reproduzíveis para testes e demonstração |

---

## Estratégia de integração

### Como os dados são carregados

O pipeline produz um alerta estruturado. Esse alerta é projetado em um EvidenceContext e processado pelo KUMA GUARD antes de ser utilizado pela camada conversacional.

~~~text
Alert
  |
  v
EvidenceContext
  |
  v
KUMA GUARD
  |
  v
GuardedSocAssessment
  |
  v
Contexto da conversa
~~~

### Como os dados são usados pelo agente

A camada generativa recebe somente o contexto necessário para responder à pergunta do usuário.

O contexto pode incluir:

- identificador do alerta;
- fatos observados;
- evidências ausentes;
- risco e severidade;
- detecção e scores disponíveis;
- hipóteses previamente suportadas pelo contexto;
- verificações recomendadas;
- estado de confirmação do incidente;
- contexto MITRE com provenance, quando aplicável.

Informações não presentes nesse contexto não devem ser tratadas como fatos.

---

## Exemplo de contexto sintético

O exemplo abaixo usa dados fictícios de laboratório:

~~~text
alert_id: ALT-KUMA-GUARD-E2E-001

detection:
  suspicious_probability: 0.96
  anomaly_detected: true
  detector: isolation_forest

risk:
  score: 94
  severity: high

observed_facts:
  failed_logins: 5
  new_device: true

missing_evidence:
  limit_change
  location_change

supported_hypotheses:
  possible_account_compromise
  support:
    - failed_logins
    - new_device

recommended_checks:
  - collect_missing_evidence: limit_change
  - collect_missing_evidence: location_change

incident_confirmed: false
~~~

Uma resposta adequada pode explicar que existem sinais compatíveis com uma hipótese de comprometimento de conta, mas deve preservar incident_confirmed: false.

---

## Dados sintéticos e privacidade

A demonstração utiliza dados sintéticos ou fictícios.

Isso permite:

- evitar exposição de dados pessoais reais;
- executar testes reproduzíveis;
- conhecer a truth de cenários controlados;
- avaliar comportamento do agente sem depender de informações sensíveis.

---

## Limites da base de conhecimento

A ausência de um campo no contexto significa que o agente não possui evidência para afirmar aquele dado.

Exemplos:

- IP de origem não fornecido -> não inventar IP;
- geolocalização não observada -> não afirmar localização;
- identidade do atacante desconhecida -> não atribuir autoria;
- incidente não confirmado -> não declarar comprometimento como fato.

---

## Escopo acadêmico

Para o protótipo do bootcamp, o contexto estruturado é suficiente para demonstrar integração entre dados, KUMA GUARD e IA generativa.

Não é requisito desta entrega acadêmica adicionar banco vetorial, RAG amplo ou ingestão universal de documentos.
