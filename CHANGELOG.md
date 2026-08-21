# Changelog

Todas as alterações relevantes deste projeto serão documentadas neste arquivo.

## [2.0.0] - 2026-08-21

### Adicionado

- Arquitetura modular para dados, features, modelos, Threat Intelligence, reporting e alertas SOC.
- Persistência estruturada de alertas em JSONL e SQLite.
- Consultas de alertas com filtros e paginação.
- Suíte de testes unitários e de integração.
- Cobertura mínima automatizada de testes.
- Pipeline CI/CD com GitHub Actions.
- Ruff para lint e formatação.
- Bandit para análise estática de segurança.
- Auditoria de dependências.
- Secret scanning.
- Geração de SBOM com CycloneDX.
- Docker multi-stage com execução não privilegiada.
- Scan de segurança de container.
- Dependabot para dependências e GitHub Actions.
- Estrutura de segurança PostgreSQL/Supabase baseada em menor privilégio.
- Row Level Security (RLS).
- Identidades PostgreSQL separadas por responsabilidade.
- View operacional minimizada para investigação SOC.
- Schema dedicado de auditoria.
- Pseudonimização persistente de clientes.
- Consultas forenses privilegiadas separadas do fluxo operacional.
- Seed sintético reproduzível.
- Isolamento temporal entre baseline normal e eventos anômalos.
- Documentação de arquitetura, modelos e DevSecOps.
- Snapshot público dos artefatos analíticos da v2.0.0.

### Alterado

- Refatoração do `SecurityDetector` para separar responsabilidades internas.
- Separação das conexões de banco entre runtime SOC e ingestão MITRE ATT&CK.
- Hardening das permissões PostgreSQL/Supabase.
- Ingestão do MITRE ATT&CK tornada atômica.
- Contrato canônico de pseudonimização de clientes.
- Execução principal padronizada como módulo Python.
- Estrutura do README atualizada para refletir a arquitetura real da v2.0.0.
- Resultados experimentais e artefatos públicos sincronizados com a execução final da versão.
- Fluxo recomendado de desenvolvimento atualizado para `uv`, mantendo `venv` + `pip` como alternativa.

### Segurança

- Revogação de privilégios padrão desnecessários no PostgreSQL/Supabase.
- Separação entre runtime do SOC, ingestão de Threat Intelligence e auditoria.
- Restrição do runtime aos dados necessários à análise.
- Validação positiva e negativa das permissões de banco.
- Tratamento explícito de arquivos binários e artefatos textuais no `.gitattributes`.

### Validação

- 228 testes aprovados.
- Cobertura total de 97,65%.
- Ruff lint aprovado.
- Ruff format check aprovado.
- Pipeline completo executado com sucesso.
- 1.500 transações analisadas.
- 448 mapeamentos MITRE ATT&CK disponíveis.
- Detector selecionado: `elliptic_envelope`.
- 225 anomalias identificadas pelo detector selecionado.
- Precision: 0,996.
- Recall: 0,448.
- F1-score: 0,618.
- ROC-AUC do classificador: 0,988.
- R² da regressão: 0,660.
- MAE: 13,3.
- RMSE: 20,4.

## [1.0.0] - Entrega do módulo de Análise de Dados

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
