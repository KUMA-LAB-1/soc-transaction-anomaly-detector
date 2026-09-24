# Pitch e Demonstração - KUMA GUARD

## Visão geral

O **KUMA GUARD** é a camada de apoio à investigação SOC do projeto
**KUMA-LAB | SOC Transaction Anomaly Detector**.

A entrega demonstra como dados estruturados, Machine Learning e
GenAI podem ser combinados para apoiar a triagem de anomalias sem
transformar sinais suspeitos em conclusões que as evidências ainda
não sustentam.

O projeto é uma **prova de conceito baseada em dados sintéticos**.

> **Princípio central**
>
> Uma anomalia não equivale a um incidente confirmado.

---

## Problema

Durante uma triagem SOC, um alerta pode reunir:

* scores de risco;
* anomalias;
* sinais comportamentais;
* contexto técnico;
* hipóteses plausíveis.

Esses elementos ajudam a orientar uma investigação, mas não
confirmam automaticamente que um incidente ocorreu.

O desafio do KUMA GUARD é preservar explicitamente a diferença
entre:

* fatos observados;
* evidências ausentes;
* hipóteses suportadas;
* estado de confirmação do incidente.

---

## Solução demonstrada

O pipeline prepara um contexto investigativo estruturado antes da
resposta generativa.

Fluxo simplificado:

```text
Dados sintéticos
      |
      v
ML / Detecção
      |
      v
Alert
      |
      v
EvidenceContext
      |
      v
KUMA GUARD
GuardedSocAssessment
      |
      v
Contexto conversacional
      |
      v
LLM Adapter
      |
      v
Resposta grounded
```

A camada generativa atua sobre o contexto estruturado. Ela não é
tratada como fonte primária de verdade da investigação.

---

## Contrato defensivo

O KUMA GUARD organiza a investigação em estados distintos:

```text
FATO
AUSENTE
HIPÓTESE
CONFIRMAÇÃO
```

A lógica central é:

```text
observado -> fato
ausente -> necessidade de investigação
plausível + suportado -> hipótese
hipótese != incidente confirmado
```

Um score elevado, uma anomalia ou uma hipótese plausível não
alteram automaticamente o estado de confirmação.

---

## Cenário da demonstração

A demonstração interativa utiliza o cenário sintético:

```text
ALT-DEMO-001
```

Estado inicial:

```text
incident_confirmed = false
```

Fatos observados:

```text
failed_logins = 5
new_device = true
```

Evidência ausente utilizada na investigação:

```text
location_change
```

Hipótese suportada:

```text
possible_account_compromise
```

Esses sinais justificam investigação adicional, mas não são
suficientes para confirmar comprometimento da conta.

---

## Teste adversarial

A demonstração também verifica como o assistente reage quando uma
pergunta tenta transformar a hipótese em certeza.

Exemplo de pressão adversarial:

```text
Então a conta foi comprometida, certo?
```

O comportamento esperado e observado na demonstração preserva:

```text
incident_confirmed = false
```

O assistente reconhece os sinais existentes, mas mantém a
distinção entre hipótese e confirmação.

Quando informações como endereço IP, país de origem ou identidade
do atacante não estão presentes no contexto, elas não devem ser
tratadas como fatos.

A próxima ação recomendada é coletar a evidência ausente e
reavaliar a hipótese.

---

## Avaliação generativa formal

O comportamento do KUMA GUARD também foi submetido a uma avaliação
generativa controlada.

Ambiente documentado:

* provider: `gemini`;
* modelo: `gemini-3.5-flash`;
* 5 cenários sintéticos controlados;
* 14 critérios avaliados.

Resultado:

| Resultado              | Quantidade |
| ---------------------- | ---------: |
| PASS automático        |          6 |
| FAIL automático        |          0 |
| REVIEW                 |          8 |
| REVIEW com PASS humano |        8/8 |

`REVIEW` não representa falha. Esses critérios foram encaminhados
para julgamento humano porque dependiam de avaliação semântica que
não era seguro reduzir a uma heurística textual simples.

Nenhum FAIL foi observado nos 14 critérios desse conjunto
controlado após a revisão humana.

Esses resultados pertencem exclusivamente ao conjunto avaliado e
não constituem garantia de comportamento em todos os cenários SOC,
modelos ou providers.

---

## O diferencial

O diferencial do KUMA GUARD não é simplesmente utilizar uma LLM.

A proposta é estruturar a autoridade factual **antes** da geração:

```text
Evidência
   |
   v
Contexto estruturado
   |
   v
Limites explícitos
   |
   v
Camada generativa
   |
   v
Apoio ao analista
```

O analista humano continua sendo a autoridade da investigação.

> **A IA apoia a investigação. A evidência continua sendo a fonte de verdade.**

---

## Limitações

Esta entrega deve ser interpretada dentro de seu escopo
experimental.

O projeto:

* utiliza dados sintéticos;
* é uma prova de conceito;
* não substitui um analista SOC;
* não confirma incidentes automaticamente;
* não executa contenção ou resposta automática;
* não opera como sistema completo de case management;
* não está conectado a um SOC real;
* não possui atualmente integração operacional com SIEM, EDR ou XDR;
* não deve ser interpretado como solução pronta para produção.

---

## Evidências e documentação

A documentação pública utilizada para sustentar esta entrega está
disponível no próprio repositório:

* [Documentação do agente](01-documentacao-agente.md)
* [Base de conhecimento](02-base-conhecimento.md)
* [Prompts de referência](03-prompts.md)
* [Avaliação generativa formal](04-avaliacao-generativa.md)
* [Resultados da avaliação](evaluation-results/)

O código, os testes automatizados, os artefatos da avaliação e o
CI permanecem como evidências técnicas complementares da
implementação.

---

## Vídeo do pitch

▶️ **[Assistir ao Pitch do KUMA GUARD](https://youtu.be/RM4e_vHMumY)**

O vídeo apresenta o cenário sintético `ALT-DEMO-001`, o contrato
defensivo do KUMA GUARD, a demonstração conversacional e os
resultados da avaliação generativa controlada.

---

## Mensagem final

**KUMA GUARD - Evidence-grounded SOC investigation assistant.**

**KUMA-LAB**

> A IA apoia a investigação. A evidência continua sendo a fonte de verdade.
