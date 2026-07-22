# Changelog

Todas as alterações relevantes deste projeto serão documentadas neste arquivo.

## [1.0.0] - Entrega do módulo de Análise de Dados

### Adicionado

- Integração com PostgreSQL e Supabase.
- Estrutura de banco para transações e eventos de segurança.
- População com dados sintéticos normais e anômalos.
- Preparação e validação dos dados.
- Engenharia de features comportamentais.
- Classificador supervisionado para triagem.
- Regressão para estimativa de severidade.
- Comparação entre quatro detectores de anomalias:
  - Isolation Forest
  - Local Outlier Factor
  - One-Class SVM
  - Elliptic Envelope
- Seleção automática do detector com melhor F1-score.
- Geração de gráficos comparativos.
- Relatório executivo em PDF.
- Correlação com MITRE ATT&CK.
- Pseudonimização e auditoria de acesso.
