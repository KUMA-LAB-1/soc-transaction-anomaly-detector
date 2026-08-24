import numpy as np
import pandas as pd
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.tree import DecisionTreeClassifier

from .validation import criar_folds_temporais, dividir_holdout_temporal

FEATURES_BASE_CLASSIFICACAO = [
    "hora",
    "media_historica_cliente",
    "desvio_historico_cliente",
    "qtd_transacoes_anteriores",
    "zscore_valor_cliente",
    "dia_semana",
    "falhas_login_recentes",
    "dispositivo_novo_flag",
    "alteracao_limite_flag",
    "mudanca_localizacao_flag",
]

STATUS_SUSPEITOS = [
    "Em Análise",
    "Bloqueada por Suspeita",
]

ESTRATEGIA_RANDOM = "random"
ESTRATEGIA_TEMPORAL = "temporal"

ESTRATEGIAS_VALIDACAO = {
    ESTRATEGIA_RANDOM,
    ESTRATEGIA_TEMPORAL,
}


def treinar_classificador_triagem(
    df: pd.DataFrame,
    *,
    estrategia_validacao: str = ESTRATEGIA_RANDOM,
) -> dict:
    """Treina e avalia o classificador supervisionado de triagem do SOC."""
    if estrategia_validacao not in ESTRATEGIAS_VALIDACAO:
        raise ValueError("estrategia_validacao deve ser 'random' ou 'temporal'.")

    df_class = pd.get_dummies(
        df,
        columns=["tipo_transacao"],
        drop_first=True,
    )

    features_tipo = [
        coluna for coluna in df_class.columns if coluna.startswith("tipo_transacao_")
    ]

    candidatos = features_tipo + FEATURES_BASE_CLASSIFICACAO
    features = [coluna for coluna in candidatos if coluna in df_class.columns]

    X = df_class[features].fillna(0).astype(float)

    y = df_class["status_transacao"].isin(STATUS_SUSPEITOS).astype(int)

    if estrategia_validacao == ESTRATEGIA_TEMPORAL:
        indices_treino, indices_teste = dividir_holdout_temporal(
            df_class,
            test_size=0.25,
        )

        X_train = X.iloc[indices_treino]
        X_test = X.iloc[indices_teste]
        y_train = y.iloc[indices_treino]
        y_test = y.iloc[indices_teste]
    else:
        estratificar = y if y.nunique() > 1 else None

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.25,
            random_state=42,
            stratify=estratificar,
        )

    modelo = DecisionTreeClassifier(
        max_depth=4,
        random_state=42,
        class_weight="balanced",
    )

    modelo.fit(X_train, y_train)

    classes_no_treino = len(modelo.classes_)

    y_pred = modelo.predict(X_test)

    auc = float("nan")
    if y_test.nunique() > 1 and classes_no_treino > 1:
        y_proba = modelo.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_proba)

    relatorio = classification_report(
        y_test,
        y_pred,
        labels=[0, 1],
        output_dict=True,
        zero_division=0,
    )

    cv_scores = []

    if estrategia_validacao == ESTRATEGIA_TEMPORAL:
        folds_temporais = criar_folds_temporais(
            df_class,
            n_splits=3,
        )

        folds_validos = [
            (indices_treino, indices_teste)
            for indices_treino, indices_teste in folds_temporais
            if y.iloc[indices_treino].nunique() > 1
            and y.iloc[indices_teste].nunique() > 1
        ]

        if folds_validos:
            cv_scores = cross_val_score(
                modelo,
                X,
                y,
                cv=folds_validos,
                scoring="roc_auc",
            ).tolist()

    elif y.nunique() > 1 and y.value_counts().min() >= 3:
        skf = StratifiedKFold(
            n_splits=3,
            shuffle=True,
            random_state=42,
        )

        cv_scores = cross_val_score(
            modelo,
            X,
            y,
            cv=skf,
            scoring="roc_auc",
        ).tolist()

    X_full = df_class[features].fillna(0).astype(float)

    if classes_no_treino > 1:
        proba_suspeita = modelo.predict_proba(X_full)[:, 1]
    else:
        valor_constante = 1.0 if modelo.classes_[0] == 1 else 0.0
        proba_suspeita = np.full(len(X_full), valor_constante)

    metricas = {
        "estrategia_validacao": estrategia_validacao,
        "n_treino": len(X_train),
        "n_teste": len(X_test),
        "classes_no_treino": classes_no_treino,
        "roc_auc_teste": float(auc),
        "roc_auc_cv_media": (float(np.mean(cv_scores)) if cv_scores else None),
        "precision_classe_suspeita": (relatorio.get("1", {}).get("precision")),
        "recall_classe_suspeita": (relatorio.get("1", {}).get("recall")),
        "f1_classe_suspeita": (relatorio.get("1", {}).get("f1-score")),
        "matriz_confusao": confusion_matrix(
            y_test,
            y_pred,
            labels=[0, 1],
        ).tolist(),
    }

    return {
        "modelo": modelo,
        "features": features,
        "metricas": metricas,
        "cv_scores": cv_scores,
        "proba_suspeita": proba_suspeita,
        "importancias": modelo.feature_importances_,
        "classes_no_treino": classes_no_treino,
    }
