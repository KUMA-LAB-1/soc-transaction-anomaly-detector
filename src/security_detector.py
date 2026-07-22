# src/security_detector.py
"""
SecurityDetector - Pipeline de SOC Preditivo (v2)
==================================================
Além das correções da v1 (MITRE dinâmico corrigido, regressão não-circular,
validação de modelos, features históricas, contamination data-driven), esta
versão adiciona:

  6. Threat hunting real com MITRE: a técnica agora é escolhida por
     CORRELAÇÃO COM SINAIS DE tbl_logs_seguranca (falhas de login, dispositivo
     novo, alteração de limite, mudança de localização) — vindos da view
     v_analise_investigacao_soc atualizada — em vez de um if/elif fixo sobre
     o texto do tipo de transação (que agora só serve de fallback).

  7. Guardrail de amostra pequena: se o dataset de treino for pequeno demais
     para gerar métricas estáveis (o teste feito pelo usuário tinha N=34 e
     R² de validação cruzada negativo), o pipeline sinaliza isso
     explicitamente no console e no PDF, em vez de apresentar números
     instáveis como se fossem conclusivos.

  8. Teto prático de contamination: além do valor data-driven, aplica um teto
     operacional (15%) — em bases de teste com muitos seeds de ataque
     relativos a poucos seeds normais, o valor puramente estatístico vira
     inutilizável (ex.: 30% de tudo marcado como anomalia).

  9. Sanitização do texto do MITRE ATT&CK: remove links em markdown e
     citações antes de inserir no PDF (o texto bruto do MITRE não é pensado
     para relatório executivo) e escapa caracteres especiais antes de montar
     o Paragraph do reportlab.

 10. Auditoria de acesso: cada execução registra em tbl_auditoria_acessos
     quem rodou o pipeline, quantas linhas sensíveis foram lidas e quando
     (accountability, LGPD art. 6º, X).

Pré-requisito: rode 08_hardening_e_correlacao.sql antes de usar esta versão —
ela depende das colunas novas da view (cliente_pseudonimo,
falhas_login_recentes, dispositivo_novo_flag, alteracao_limite_flag,
mudanca_localizacao_flag).
"""

import os
import re
import html
import json
import getpass
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib

from db_connector import DBConnector

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM
from sklearn.covariance import EllipticEnvelope
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score, f1_score, precision_score, recall_score,
    r2_score, mean_absolute_error, mean_squared_error
)

from sqlalchemy import text

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


MAPA_SEVERIDADE_STATUS = {
    "Aprovada": 5, "Concluída": 5,
    "Em Análise": 55, "Bloqueada por Suspeita": 95,
}
SEVERIDADE_PADRAO = 30

# Abaixo deste tamanho de treino, o pipeline continua rodando (é útil para
# desenvolvimento/teste), mas sinaliza explicitamente que as métricas não são
# estatisticamente confiáveis ainda.
MIN_AMOSTRAS_TREINO_CONFIAVEL = 60

# Teto operacional de contamination — 30% de tudo marcado como anômalo não é
# acionável na prática, mesmo que a taxa histórica real diga isso (geralmente
# sinal de dataset de teste com seeds de ataque desproporcionais).
CONTAMINATION_TETO_PRATICO = 0.15


class SecurityDetector:
    def __init__(self):
        self.engine = DBConnector.get_engine()
        self.modelo_classificacao = None
        self.modelo_agrupamento = None
        self.modelos_anomalia = {}
        self.melhor_detector = None
        self.modelo_regressao = None
        self.metricas = {}
        self.aviso_amostra_pequena = False

        os.makedirs("reports", exist_ok=True)
        os.makedirs("reports/models", exist_ok=True)
        plt.style.use('dark_background')

    # ------------------------------------------------------------------
    # Carga, preparação e auditoria
    # ------------------------------------------------------------------
    def validar_e_preparar_dataset(self, df, nome_tabela):
        if df.isnull().sum().sum() > 0:
            df = df.fillna(0)
        return df.drop_duplicates()

    def _registrar_auditoria(self, view_acessada, qtd_linhas, finalidade):
        """[ITEM 10] Log de accountability: quem acessou dados sensíveis, quando, quantos."""
        try:
            usuario = os.getenv("SOC_PIPELINE_USER") or getpass.getuser() or "pipeline_automatizado"
            conn = DBConnector.get_raw_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO tbl_auditoria_acessos "
                "(usuario_execucao, view_ou_tabela_acessada, qtd_linhas_retornadas, finalidade) "
                "VALUES (%s, %s, %s, %s)",
                (usuario, view_acessada, int(qtd_linhas), finalidade),
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"⚠️ Não foi possível registrar auditoria de acesso (tabela existe? rode 08_hardening_e_correlacao.sql): {e}")

    def carregar_dados(self):
        try:
            query_view = "SELECT * FROM v_analise_investigacao_soc;"
            df_consolidado = pd.read_sql_query(query_view, self.engine)
            df_consolidado = self.validar_e_preparar_dataset(df_consolidado, "v_analise_investigacao_soc")
            self._registrar_auditoria(
                "v_analise_investigacao_soc", len(df_consolidado),
                "Execução do pipeline de detecção preditiva do SOC"
            )
            return df_consolidado
        except Exception as e:
            print(f"❌ Erro na leitura segura do banco: {e}")
            raise

    def _col_cliente(self, df):
        for candidato in ('cliente_pseudonimo', 'cliente_anonimizado', 'cliente_anonimado'):
            if candidato in df.columns:
                return candidato
        df['cliente_pseudonimo'] = 'Usuário Anonimizado'
        return 'cliente_pseudonimo'

    def engenharia_de_features(self, df):
        col_cliente = self._col_cliente(df)
        df = df.sort_values([col_cliente, 'data_hora_transacao']).reset_index(drop=True)

        grupo_cliente = df.groupby(col_cliente, group_keys=False)['valor_transacao']
        df['media_historica_cliente'] = grupo_cliente.apply(lambda s: s.shift(1).expanding().mean())
        df['desvio_historico_cliente'] = grupo_cliente.apply(lambda s: s.shift(1).expanding().std())
        df['qtd_transacoes_anteriores'] = df.groupby(col_cliente).cumcount()

        media_global = df['valor_transacao'].mean()
        desvio_global = df['valor_transacao'].std() or 1.0
        df['media_historica_cliente'] = df['media_historica_cliente'].fillna(media_global)
        df['desvio_historico_cliente'] = df['desvio_historico_cliente'].fillna(desvio_global).replace(0, 0.01)
        df['zscore_valor_cliente'] = (df['valor_transacao'] - df['media_historica_cliente']) / df['desvio_historico_cliente']
        df['dia_semana'] = pd.to_datetime(df['data_hora_transacao']).dt.dayofweek

        # [ITEM 6] Sinais de logs de segurança, já vindos da view (correlação
        # feita no banco). Garantimos os tipos e a presença das colunas mesmo
        # se a view antiga (sem hardening) ainda estiver em uso.
        for col, default in [
            ('falhas_login_recentes', 0), ('dispositivo_novo_flag', False),
            ('alteracao_limite_flag', False), ('mudanca_localizacao_flag', False),
        ]:
            if col not in df.columns:
                df[col] = default
        df['falhas_login_recentes'] = df['falhas_login_recentes'].fillna(0).astype(int)
        for col in ('dispositivo_novo_flag', 'alteracao_limite_flag', 'mudanca_localizacao_flag'):
            df[col] = df[col].fillna(False).astype(bool)

        return df

    # ------------------------------------------------------------------
    # Orquestração
    # ------------------------------------------------------------------
    def processar_modelos_e_graficos(self, df_soc):
        df = df_soc.copy()
        df['hora'] = pd.to_datetime(df['data_hora_transacao']).dt.hour
        col_cliente = self._col_cliente(df)

        df = self.engenharia_de_features(df)

        if len(df) < MIN_AMOSTRAS_TREINO_CONFIAVEL:
            self.aviso_amostra_pequena = True
            print(f"\n⚠️ ATENÇÃO: apenas {len(df)} transações na base (mínimo recomendado para "
                  f"métricas estáveis: {MIN_AMOSTRAS_TREINO_CONFIAVEL}). Os modelos vão treinar "
                  f"normalmente, mas trate os resultados como PROVA DE CONCEITO, não como validação "
                  f"estatística — isso ficará marcado no relatório.")

        df = self._treinar_classificacao(df)
        df = self._comparar_detectores_anomalia(df)
        df = self._treinar_regressao(df)
        self._salvar_metricas()
        return df

    def _treinar_classificacao(self, df):
        """
        Classificador de TRIAGEM (reproduz decisões históricas de status_transacao,
        não descobre ataques inéditos — essa função é do Isolation Forest).
        [ITEM 6] Agora inclui os sinais de logs de segurança como features.
        """
        print("\n⚙️ Treinando classificador de triagem (features históricas + sinais de log)...")

        df_class = pd.get_dummies(df, columns=['tipo_transacao'], drop_first=True)
        candidatos = [c for c in df_class.columns if c.startswith('tipo_transacao_')] + [
            'hora', 'media_historica_cliente', 'desvio_historico_cliente',
            'qtd_transacoes_anteriores', 'zscore_valor_cliente', 'dia_semana',
            'falhas_login_recentes', 'dispositivo_novo_flag',
            'alteracao_limite_flag', 'mudanca_localizacao_flag',
        ]
        features = [f for f in candidatos if f in df_class.columns]

        X = df_class[features].fillna(0).astype(float)
        y = df_class['status_transacao'].isin(['Em Análise', 'Bloqueada por Suspeita']).astype(int)

        estratificar = y if y.nunique() > 1 else None
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=estratificar
        )

        self.modelo_classificacao = DecisionTreeClassifier(max_depth=4, random_state=42, class_weight='balanced')
        self.modelo_classificacao.fit(X_train, y_train)

        # [PROTEÇÃO] Com dataset pequeno, o split pode deixar só uma classe no
        # treino (o modelo nunca vê a classe "suspeita"). Isso não é bug de
        # lógica, é sintoma de amostra pequena/desbalanceada — mas o código
        # precisa continuar rodando em vez de quebrar em predict_proba.
        classes_no_treino = len(self.modelo_classificacao.classes_)
        if classes_no_treino < 2:
            self.aviso_amostra_pequena = True
            print(f"   ⚠️ O treino ficou com apenas 1 classe presente ({self.modelo_classificacao.classes_[0]}) "
                  f"— dataset pequeno demais para o classificador aprender as duas classes ainda. "
                  f"Aumente o volume de transações rotuladas (principalmente da classe minoritária).")

        y_pred = self.modelo_classificacao.predict(X_test)
        auc = float('nan')
        if y_test.nunique() > 1 and classes_no_treino > 1:
            y_proba = self.modelo_classificacao.predict_proba(X_test)[:, 1]
            auc = roc_auc_score(y_test, y_proba)

        relatorio = classification_report(y_test, y_pred, labels=[0, 1], output_dict=True, zero_division=0)
        cv_scores = []
        if y.nunique() > 1 and y.value_counts().min() >= 3:
            skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
            cv_scores = cross_val_score(self.modelo_classificacao, X, y, cv=skf, scoring='roc_auc').tolist()

        self.metricas['classificacao'] = {
            "n_treino": len(X_train), "n_teste": len(X_test),
            "classes_no_treino": classes_no_treino,
            "roc_auc_teste": auc,
            "roc_auc_cv_media": float(np.mean(cv_scores)) if cv_scores else None,
            "precision_classe_suspeita": relatorio.get('1', {}).get('precision'),
            "recall_classe_suspeita": relatorio.get('1', {}).get('recall'),
            "f1_classe_suspeita": relatorio.get('1', {}).get('f1-score'),
            "matriz_confusao": confusion_matrix(y_test, y_pred, labels=[0, 1]).tolist(),
        }
        print(f"   ROC-AUC (teste): {auc:.3f}" if not np.isnan(auc) else "   ROC-AUC indisponível (classe única no treino ou no teste)")
        if cv_scores:
            print(f"   ROC-AUC (CV 3-fold): {np.mean(cv_scores):.3f} ± {np.std(cv_scores):.3f}")

        X_full = df_class[features].fillna(0).astype(float)
        if classes_no_treino > 1:
            df['proba_suspeita'] = self.modelo_classificacao.predict_proba(X_full)[:, 1]
        else:
            # só existe 1 classe -> não há "probabilidade da classe suspeita" a extrair;
            # usamos 1.0 se a única classe aprendida for a suspeita, senão 0.0
            valor_constante = 1.0 if self.modelo_classificacao.classes_[0] == 1 else 0.0
            df['proba_suspeita'] = valor_constante

        importancias = self.modelo_classificacao.feature_importances_
        plt.figure(figsize=(9.5, 5))
        bars = plt.barh(features, importancias, color='#00ffcc', edgecolor='cyan', height=0.5)
        plt.title('VETORES DE RISCO IDENTIFICADOS PELO CLASSIFICADOR', fontsize=12, fontweight='bold', color='cyan', pad=15)
        auc_label = f"{auc:.2f}" if not np.isnan(auc) else "N/D"
        plt.xlabel(f'Relevância na Tomada de Decisão do SOC (ROC-AUC teste: {auc_label})', fontsize=10, color='gray')
        plt.grid(axis='x', linestyle='--', alpha=0.3)
        for bar in bars:
            width = bar.get_width()
            plt.text(width + 0.005, bar.get_y() + bar.get_height() / 2, f'{width:.1%}',
                      va='center', ha='left', color='white', fontsize=9, fontweight='bold')
        plt.tight_layout()
        plt.savefig('reports/importancia_features_classificador.png', dpi=150)
        plt.close()

        joblib.dump(self.modelo_classificacao, 'reports/models/classificador.joblib')
        return df

    def _comparar_detectores_anomalia(self, df):
        """
        Treina quatro detectores de anomalia com as mesmas features e o mesmo
        orçamento operacional de alertas. Cada detector é salvo separadamente,
        recebe métricas próprias e produz um gráfico individual.

        IMPORTANTE: status_transacao não entra no treino dos detectores. Ele é
        usado apenas como referência de auditoria para comparar os resultados.
        """
        print("\n⚙️ Comparando detectores de anomalia...")

        taxa_suspeita_real = df['status_transacao'].isin(
            ['Em Análise', 'Bloqueada por Suspeita']
        ).mean()
        contamination_estimado = float(np.clip(taxa_suspeita_real, 0.02, 0.30))
        contamination = min(contamination_estimado, CONTAMINATION_TETO_PRATICO)

        print(f"   taxa histórica suspeita: {taxa_suspeita_real:.3f}")
        print(f"   contamination comum aos modelos: {contamination:.3f}")

        features = [
            'valor_transacao', 'hora', 'zscore_valor_cliente',
            'qtd_transacoes_anteriores', 'falhas_login_recentes',
            'dispositivo_novo_flag', 'alteracao_limite_flag',
            'mudanca_localizacao_flag',
        ]
        features = [col for col in features if col in df.columns]
        X = df[features].fillna(0).astype(float)
        y_real = df['status_transacao'].isin(
            ['Em Análise', 'Bloqueada por Suspeita']
        ).astype(int)

        n_vizinhos = max(5, min(35, len(X) - 1))
        detectores = {
            'isolation_forest': IsolationForest(
                contamination=contamination,
                n_estimators=300,
                random_state=42,
                n_jobs=-1,
            ),
            'local_outlier_factor': Pipeline([
                ('scaler', StandardScaler()),
                ('modelo', LocalOutlierFactor(
                    n_neighbors=n_vizinhos,
                    contamination=contamination,
                    novelty=True,
                    n_jobs=-1,
                )),
            ]),
            'one_class_svm': Pipeline([
                ('scaler', StandardScaler()),
                ('modelo', OneClassSVM(
                    kernel='rbf', gamma='scale', nu=contamination,
                )),
            ]),
            'elliptic_envelope': Pipeline([
                ('scaler', StandardScaler()),
                ('modelo', EllipticEnvelope(
                    contamination=contamination,
                    random_state=42,
                    support_fraction=None,
                )),
            ]),
        }

        resultados = []
        for nome, modelo in detectores.items():
            print(f"\n   ▶ {nome}")
            inicio = time.perf_counter()
            try:
                modelo.fit(X)
                predicao_original = modelo.predict(X)  # 1 normal, -1 anomalia
                score_original = modelo.decision_function(X)  # maior = mais normal
                segundos = time.perf_counter() - inicio

                y_pred = (predicao_original == -1).astype(int)
                precision = precision_score(y_real, y_pred, zero_division=0)
                recall = recall_score(y_real, y_pred, zero_division=0)
                f1 = f1_score(y_real, y_pred, zero_division=0)
                auc = None
                if y_real.nunique() > 1 and len(np.unique(score_original)) > 1:
                    auc = float(roc_auc_score(y_real, -score_original))

                slug = nome
                df[f'anomalia_{slug}'] = predicao_original
                df[f'score_anomalia_{slug}'] = score_original
                joblib.dump(modelo, f'reports/models/{slug}.joblib')
                self.modelos_anomalia[nome] = modelo

                resultado = {
                    'modelo': nome,
                    'status': 'ok',
                    'features': features,
                    'contamination_estimado': contamination_estimado,
                    'contamination_usado': contamination,
                    'qtd_anomalias': int(y_pred.sum()),
                    'taxa_anomalias': float(y_pred.mean()),
                    'precision_vs_status_real': float(precision),
                    'recall_vs_status_real': float(recall),
                    'f1_vs_status_real': float(f1),
                    'roc_auc_score_anomalia': auc,
                    'tempo_segundos': float(segundos),
                    'nota': (
                        'Modelo não supervisionado/novelty detection. '
                        'status_transacao foi usado somente para auditoria comparativa.'
                    ),
                }
                resultados.append(resultado)
                self.metricas[nome] = resultado

                print(
                    f"      anomalias={resultado['qtd_anomalias']} | "
                    f"precision={precision:.3f} | recall={recall:.3f} | "
                    f"F1={f1:.3f} | tempo={segundos:.3f}s"
                )
                self._gerar_grafico_detector(df, nome, contamination)

            except Exception as exc:
                segundos = time.perf_counter() - inicio
                resultado = {
                    'modelo': nome,
                    'status': 'erro',
                    'erro': str(exc),
                    'tempo_segundos': float(segundos),
                }
                resultados.append(resultado)
                self.metricas[nome] = resultado
                print(f"      ⚠️ modelo ignorado por erro: {exc}")

        validos = [r for r in resultados if r.get('status') == 'ok']
        if not validos:
            raise RuntimeError('Nenhum detector de anomalia conseguiu concluir o treinamento.')

        # Critério transparente: maior F1; desempate por recall, precision e menor tempo.
        melhor = max(
            validos,
            key=lambda r: (
                r['f1_vs_status_real'], r['recall_vs_status_real'],
                r['precision_vs_status_real'], -r['tempo_segundos'],
            ),
        )
        self.melhor_detector = melhor['modelo']
        self.modelo_agrupamento = self.modelos_anomalia[self.melhor_detector]

        # Mantém compatibilidade com o restante do pipeline e com o PDF.
        df['anomalia_score'] = df[f'anomalia_{self.melhor_detector}']
        df['anomalia_score_bruto'] = df[f'score_anomalia_{self.melhor_detector}']

        self.metricas['comparacao_detectores'] = {
            'criterio_selecao': 'maior F1; desempate por recall, precision e menor tempo',
            'melhor_modelo': self.melhor_detector,
            'resultados': resultados,
        }

        comparacao = pd.DataFrame(validos).sort_values(
            ['f1_vs_status_real', 'recall_vs_status_real'], ascending=False
        )
        comparacao.to_csv('reports/comparacao_detectores.csv', index=False, encoding='utf-8-sig')
        with open('reports/comparacao_detectores.json', 'w', encoding='utf-8') as arquivo:
            json.dump(self.metricas['comparacao_detectores'], arquivo, ensure_ascii=False, indent=2)

        self._gerar_grafico_comparacao(comparacao)
        print(f"\n   🏆 Detector selecionado para o relatório: {self.melhor_detector}")
        return df

    def _gerar_grafico_detector(self, df, nome_modelo, contamination):
        """Gera um gráfico legível por detector, rotulando apenas os alertas prioritários."""
        coluna_pred = f'anomalia_{nome_modelo}'
        coluna_score = f'score_anomalia_{nome_modelo}'
        normais = df[df[coluna_pred] == 1]
        anomalas = df[df[coluna_pred] == -1]
        col_cliente = self._col_cliente(df)

        plt.figure(figsize=(12, 7))
        plt.scatter(
            normais['hora'], normais['valor_transacao'],
            label='Normais', alpha=0.30, s=28,
        )
        plt.scatter(
            anomalas['hora'], anomalas['valor_transacao'],
            marker='X', s=75, label='Anomalias', zorder=5,
        )

        # Evita o novelo visual do gráfico anterior: somente os 15 scores mais anômalos.
        prioritarias = anomalas.nsmallest(15, coluna_score)
        for _, row in prioritarias.iterrows():
            plt.annotate(
                f"{row[col_cliente]}\nR$ {float(row['valor_transacao']):,.0f}",
                xy=(row['hora'], row['valor_transacao']),
                xytext=(5, 7), textcoords='offset points', fontsize=7,
            )

        titulo = nome_modelo.replace('_', ' ').title()
        plt.title(f'{titulo}: detecção de desvios (contamination={contamination:.2f})')
        plt.xlabel('Hora do evento (0h - 23h)')
        plt.ylabel('Valor da transação (R$)')
        plt.xlim(-1, 24)
        plt.grid(True, linestyle=':', alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig(f'reports/anomalias_{nome_modelo}.png', dpi=150)
        plt.close()

    @staticmethod
    def _gerar_grafico_comparacao(comparacao):
        """Compara F1, precision e recall dos detectores em um único artefato."""
        metricas_plot = comparacao.set_index('modelo')[[
            'precision_vs_status_real', 'recall_vs_status_real', 'f1_vs_status_real'
        ]]
        ax = metricas_plot.plot(kind='bar', figsize=(11, 6))
        ax.set_title('Comparação dos detectores de anomalia')
        ax.set_ylabel('Métrica (0 a 1)')
        ax.set_xlabel('Modelo')
        ax.set_ylim(0, 1.05)
        ax.grid(axis='y', linestyle=':', alpha=0.3)
        plt.xticks(rotation=20, ha='right')
        plt.tight_layout()
        plt.savefig('reports/comparacao_detectores.png', dpi=150)
        plt.close()

    def _treinar_regressao(self, df):
        print("⚙️ Treinando regressão de severidade de risco...")

        df['severidade_real'] = df['status_transacao'].map(MAPA_SEVERIDADE_STATUS).fillna(SEVERIDADE_PADRAO)
        features_r = ['valor_transacao', 'hora', 'media_historica_cliente',
                      'desvio_historico_cliente', 'zscore_valor_cliente',
                      'qtd_transacoes_anteriores', 'dia_semana', 'falhas_login_recentes']
        X_r = df[features_r].fillna(0)
        y_r = df['severidade_real']

        X_train, X_test, y_train, y_test = train_test_split(X_r, y_r, test_size=0.25, random_state=42)
        self.modelo_regressao = LinearRegression()
        self.modelo_regressao.fit(X_train, y_train)

        y_pred_test = self.modelo_regressao.predict(X_test)
        r2 = r2_score(y_test, y_pred_test)
        mae = mean_absolute_error(y_test, y_pred_test)
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred_test)))
        cv_scores = cross_val_score(self.modelo_regressao, X_r, y_r, cv=5, scoring='r2')

        self.metricas['regressao'] = {
            "r2_teste": r2, "mae_teste": mae, "rmse_teste": rmse,
            "r2_cv_media": float(np.mean(cv_scores)),
        }
        print(f"   R² (teste): {r2:.3f} | MAE: {mae:.1f} | RMSE: {rmse:.1f}")
        print(f"   R² (CV 5-fold): {np.mean(cv_scores):.3f} ± {np.std(cv_scores):.3f}")
        if np.mean(cv_scores) < 0:
            print("   ⚠️ R² negativo em validação cruzada: o modelo de severidade ainda não "
                  "generaliza de forma confiável (típico de base pequena). Isso será sinalizado no PDF.")

        df['score_risco_predito'] = self.modelo_regressao.predict(X_r).clip(0, 100)
        joblib.dump(self.modelo_regressao, 'reports/models/regressao.joblib')
        return df

    def _salvar_metricas(self):
        registro = {"timestamp": datetime.utcnow().isoformat(),
                    "amostra_pequena": self.aviso_amostra_pequena, **self.metricas}
        caminho = Path("reports/historico_metricas.jsonl")
        with open(caminho, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False, default=str) + "\n")
        print(f"📈 Métricas registradas em {caminho}")

    # ------------------------------------------------------------------
    # Threat hunting MITRE [ITEM 6]
    # ------------------------------------------------------------------
    def _determinar_padrao_por_correlacao(self, sinais):
        """
        Decide a técnica MITRE a partir de sinais REAIS de comportamento
        (correlação com tbl_logs_seguranca), não do texto do tipo de transação.
        Retorna (termo_busca, descricao_criterio) ou (None, None) se nenhum
        sinal de log bateu — nesse caso cai no fallback por tipo de transação.
        """
        if sinais.get('falhas_login_recentes', 0) >= 2:
            return "%T1110%", "múltiplas falhas de login antes da transação (força bruta)"
        if sinais.get('dispositivo_novo_flag') and sinais.get('alteracao_limite_flag'):
            return "%T1098%", "dispositivo novo vinculado + alteração de limite Pix (tomada de conta)"
        if sinais.get('mudanca_localizacao_flag'):
            return "%T1078%", "mudança de localização entre acessos recentes (uso de credencial fora do padrão)"
        return None, None

    @staticmethod
    def _limpar_texto_mitre(texto):
        """[ITEM 9] Remove links markdown/citações do texto bruto do MITRE e escapa
        caracteres especiais antes de ir para o Paragraph do reportlab."""
        if not texto:
            return "Nenhum procedimento de mitigação listado."
        texto = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', texto)     # [Nome](url) -> Nome
        texto = re.sub(r'\(Citation:[^)]*\)', '', texto)            # remove (Citation: ...)
        texto = re.sub(r'\s+', ' ', texto).strip()
        if len(texto) > 450:
            texto = texto[:450].rsplit(' ', 1)[0] + "…"
        return html.escape(texto)

    def enriquecer_com_mitre(self, tipo_evento, sinais=None):
        sinais = sinais or {}
        termo_busca, criterio = self._determinar_padrao_por_correlacao(sinais)
        if not termo_busca:
            criterio = "tipo de transação (fallback, sem correlação de log disponível)"
            if "Pix" in tipo_evento:
                termo_busca = "%T1565%"
            elif "Transferência" in tipo_evento:
                termo_busca = "%T1043%"
            else:
                termo_busca = "%T1110%"

        try:
            query = text("""
                SELECT mitre_id, mitre_tecnica, mitre_tatica, procedimentos
                FROM tbl_mitre_mapping
                WHERE mitre_id ILIKE :termo OR mitre_tecnica ILIKE :termo
                ORDER BY mitre_id
                LIMIT 1;
            """)
            with self.engine.connect() as conn:
                result = conn.execute(query, {"termo": termo_busca}).fetchone()
                if result:
                    return {
                        "mitre_id": html.escape(str(result[0])),
                        "tecnica": html.escape(str(result[1])),
                        "tatica": html.escape(str(result[2])),
                        "procedimentos": self._limpar_texto_mitre(result[3]),
                        "fonte": "banco de dados (dinâmico)",
                        "criterio": criterio,
                    }
        except Exception as e:
            print(f"⚠️ Alerta ao consultar Threat Intel no banco: {e}. Usando mapeamento local resiliente.")

        if "Pix" in tipo_evento:
            return {
                "mitre_id": "T1565.001",
                "tecnica": "Manipulação de Dados: Transferência Financeira Não Autorizada",
                "tatica": "Impacto / Roubo de Ativos",
                "procedimentos": "Aplicar MFA mandatório para transações fora do horário comercial.",
                "fonte": "fallback local", "criterio": criterio,
            }
        return {
            "mitre_id": "T1110.001",
            "tecnica": "Ataque de Força Bruta (Brute Force Credential Stuffing)",
            "tatica": "Acesso Inicial",
            "procedimentos": "Bloquear temporariamente o IP de origem e forçar redefinição de senha.",
            "fonte": "fallback local", "criterio": criterio,
        }

    # ------------------------------------------------------------------
    # Relatório PDF
    # ------------------------------------------------------------------
    def gerar_pdf_report(self, df_analisado):
        pdf_path = "reports/Relatorio_Incidente_SOC.pdf"
        print(f"\n📄 Compilando Relatório Executivo PDF em '{pdf_path}'...")

        col_cliente = self._col_cliente(df_analisado)
        col_id_transacao = 'id_transacao' if 'id_transacao' in df_analisado.columns else None

        doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        titulo_style = ParagraphStyle('TituloSOC', parent=styles['Heading1'], fontSize=20, leading=24,
                                       textColor=colors.HexColor('#0f2b5c'), spaceAfter=15)
        sub_style = ParagraphStyle('SubSOC', parent=styles['Normal'], fontSize=10,
                                    textColor=colors.HexColor('#555555'), spaceAfter=25)
        corpo_style = ParagraphStyle('CorpoSOC', parent=styles['Normal'], fontSize=10, leading=14,
                                      textColor=colors.HexColor('#333333'), spaceAfter=12)
        aviso_style = ParagraphStyle('AvisoSOC', parent=styles['Normal'], fontSize=10, leading=14,
                                      textColor=colors.HexColor('#8a2b00'), spaceAfter=12,
                                      backColor=colors.HexColor('#fff3e0'))

        elementos = [
            Paragraph("RELATÓRIO DE DETECÇÃO DE INCIDENTES - SOC PREDITIVO", titulo_style),
            Paragraph("Análise de ML, validação de modelos e mapeamento MITRE ATT&CK", sub_style),
        ]

        m_reg_preview = self.metricas.get('regressao', {})
        if self.aviso_amostra_pequena or (m_reg_preview.get('r2_cv_media', 0) or 0) < 0:
            texto_aviso = (
                "⚠️ AVISO DE CONFIABILIDADE: a base analisada é pequena e/ou os modelos ainda não "
                "generalizam de forma estável (ver métricas na seção 4). Trate os números deste "
                "relatório como PROVA DE CONCEITO, não como validação estatística definitiva. "
                "Recomenda-se aumentar o volume de transações reais/rotuladas antes de usar estes "
                "scores operacionalmente."
            )
            elementos.append(Paragraph(texto_aviso, aviso_style))
            elementos.append(Spacer(1, 10))

        elementos.append(Paragraph("<b>1. Resumo Executivo</b>", styles['Heading2']))

        anomalias = df_analisado[df_analisado['anomalia_score'] == -1]
        qtd_anomalias = len(anomalias)
        m_clf = self.metricas.get('classificacao', {})
        m_detector = self.metricas.get(self.melhor_detector or 'isolation_forest', {})
        m_reg = self.metricas.get('regressao', {})

        auc_txt = f"{m_clf.get('roc_auc_teste'):.2f}" if m_clf.get('roc_auc_teste') is not None and not np.isnan(m_clf.get('roc_auc_teste', float('nan'))) else "N/D"
        r2_txt = f"{m_reg.get('r2_teste'):.2f}" if m_reg.get('r2_teste') is not None else "N/D"
        mae_txt = f"{m_reg.get('mae_teste'):.1f}" if m_reg.get('mae_teste') is not None else "N/D"

        texto_resumo = (
            f"Este relatório documenta {qtd_anomalias} transações sinalizadas por detecção de anomalias "
            f"({(self.melhor_detector or 'isolation_forest').replace('_', ' ').title()}, contamination={m_detector.get('contamination_usado', 0):.2f}). "
            f"O classificador de triagem atingiu ROC-AUC de {auc_txt} em dados de teste. "
            f"O modelo de severidade (regressão) obteve R²={r2_txt} e erro médio absoluto "
            f"de {mae_txt} pontos em uma escala de 0-100."
        )
        elementos.append(Paragraph(texto_resumo, corpo_style))
        elementos.append(Spacer(1, 10))

        elementos.append(Paragraph("<b>2. Detalhes Técnicos dos Alertas de Alta Severidade</b>", styles['Heading2']))
        tabela_dados = [["Ref/ID", "Cliente (LGPD)", "Valor", "Horário", "Score Predito", "Prob. Suspeita"]]
        for i, (idx, row) in enumerate(anomalias.iterrows(), start=1):
            id_referencia = str(row[col_id_transacao]) if col_id_transacao else f"INC-{i:03d}"
            tabela_dados.append([
                id_referencia, str(row[col_cliente]),
                f"R$ {float(row['valor_transacao']):,.2f}",
                f"{int(row['hora'])}:00h",
                f"{row['score_risco_predito']:.1f}/100",
                f"{row.get('proba_suspeita', 0):.0%}",
            ])
        t_incidentes = Table(tabela_dados, colWidths=[55, 100, 90, 60, 80, 80])
        t_incidentes.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f2b5c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7f9fc')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        elementos.append(t_incidentes)
        elementos.append(Spacer(1, 25))

        elementos.append(Paragraph("<b>3. Correlação de Threat Intelligence (MITRE ATT&CK)</b>", styles['Heading2']))
        if qtd_anomalias == 0:
            elementos.append(Paragraph("Nenhuma anomalia crítica correlacionada com táticas MITRE.", corpo_style))
        else:
            ameacas_vistas = set()
            for _, row in anomalias.iterrows():
                tipo_evento = row.get('tipo_transacao', 'Pix')
                sinais = {
                    'falhas_login_recentes': row.get('falhas_login_recentes', 0),
                    'dispositivo_novo_flag': row.get('dispositivo_novo_flag', False),
                    'alteracao_limite_flag': row.get('alteracao_limite_flag', False),
                    'mudanca_localizacao_flag': row.get('mudanca_localizacao_flag', False),
                }
                intel = self.enriquecer_com_mitre(tipo_evento, sinais)
                chave = (intel['mitre_id'], row[col_cliente])
                if intel and chave not in ameacas_vistas:
                    ameacas_vistas.add(chave)
                    texto_dinamico_mitre = (
                        f"<b>Técnica associada:</b> {intel['tecnica']} (ID: <b>{intel['mitre_id']}</b>), "
                        f"tática <b>{intel['tatica']}</b>. Fonte: {intel['fonte']}.<br/>"
                        f"• <b>Critério de correlação:</b> {html.escape(intel['criterio'])}.<br/>"
                        f"• <b>Cliente (pseudônimo):</b> {row[col_cliente]} às {int(row['hora'])}:00h.<br/>"
                        f"• <b>Procedimentos sugeridos:</b> {intel['procedimentos']}"
                    )
                    elementos.append(Paragraph(texto_dinamico_mitre, corpo_style))
                    elementos.append(Spacer(1, 10))

        elementos.append(Paragraph("<b>4. Validação dos Modelos (transparência metodológica)</b>", styles['Heading2']))
        precision_clf = m_clf.get('precision_classe_suspeita') or 0
        recall_clf = m_clf.get('recall_classe_suspeita') or 0
        precision_detector = m_detector.get('precision_vs_status_real') or 0
        recall_detector = m_detector.get('recall_vs_status_real') or 0
        f1_detector = m_detector.get('f1_vs_status_real') or 0
        r2_cv = m_reg.get('r2_cv_media') or 0
        n_treino = m_clf.get('n_treino', 0)
        n_teste = m_clf.get('n_teste', 0)
        texto_validacao = (
            f"Amostra: {n_treino} transações de treino / {n_teste} de teste. "
            f"Classificador de triagem: precision={precision_clf:.2f}, recall={recall_clf:.2f} "
            f"(reproduz decisões históricas, não detecta ataques inéditos). "
            f"Detector selecionado ({(self.melhor_detector or 'N/D').replace('_', ' ')}): "
            f"precision={precision_detector:.2f}, recall={recall_detector:.2f}, F1={f1_detector:.2f} "
            f"(rótulo usado somente para auditoria comparativa). "
            f"Regressão de severidade: R² (validação cruzada 5-fold)={r2_cv:.2f}."
        )
        elementos.append(Paragraph(texto_validacao, corpo_style))

        comparacao_info = self.metricas.get('comparacao_detectores', {}).get('resultados', [])
        comparacao_validos = [r for r in comparacao_info if r.get('status') == 'ok']
        if comparacao_validos:
            elementos.append(Spacer(1, 14))
            elementos.append(Paragraph("<b>5. Comparação dos Detectores de Anomalia</b>", styles['Heading2']))
            tabela_modelos = [["Modelo", "Alertas", "Precision", "Recall", "F1", "Tempo (s)"]]
            for r in sorted(comparacao_validos, key=lambda x: x['f1_vs_status_real'], reverse=True):
                tabela_modelos.append([
                    r['modelo'].replace('_', ' '), str(r['qtd_anomalias']),
                    f"{r['precision_vs_status_real']:.2f}", f"{r['recall_vs_status_real']:.2f}",
                    f"{r['f1_vs_status_real']:.2f}", f"{r['tempo_segundos']:.3f}",
                ])
            t_modelos = Table(tabela_modelos, colWidths=[120, 55, 60, 55, 45, 65])
            t_modelos.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f2b5c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
            ]))
            elementos.append(t_modelos)
            elementos.append(Spacer(1, 8))
            elementos.append(Paragraph(
                "O modelo destacado no resumo foi selecionado pelo maior F1, com desempate por recall, "
                "precision e menor tempo. Essa escolha é válida apenas como comparação experimental na "
                "base simulada atual, não como validação para produção.", corpo_style
            ))

        doc.build(elementos)
        print(f"🚀 [SUCESSO] Relatório PDF '{pdf_path}' gerado.")

    def executar_pipeline_completo(self):
        df_soc = self.carregar_dados()
        df_analisado = self.processar_modelos_e_graficos(df_soc)
        self.gerar_pdf_report(df_analisado)
        print("\n🏆 Pipeline do SOC Preditivo Concluído com Sucesso!")


if __name__ == "__main__":
    detector = SecurityDetector()
    detector.executar_pipeline_completo()
