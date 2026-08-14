from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from ..data.columns import resolver_coluna_cliente

plt.style.use("dark_background")


def gerar_grafico_detector(
    df: pd.DataFrame,
    nome_modelo: str,
    contamination: float,
    output_dir: str | Path = "reports",
) -> None:
    """Gera o gráfico individual de um detector de anomalia."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    coluna_pred = f"anomalia_{nome_modelo}"
    coluna_score = f"score_anomalia_{nome_modelo}"

    normais = df[df[coluna_pred] == 1]
    anomalas = df[df[coluna_pred] == -1]

    col_cliente = resolver_coluna_cliente(df)

    plt.figure(figsize=(12, 7))

    plt.scatter(
        normais["hora"],
        normais["valor_transacao"],
        label="Normais",
        alpha=0.30,
        s=28,
    )

    plt.scatter(
        anomalas["hora"],
        anomalas["valor_transacao"],
        marker="X",
        s=75,
        label="Anomalias",
        zorder=5,
    )

    prioritarias = anomalas.nsmallest(15, coluna_score)

    for _, row in prioritarias.iterrows():
        plt.annotate(
            f"{row[col_cliente]}\nR$ {float(row['valor_transacao']):,.0f}",
            xy=(row["hora"], row["valor_transacao"]),
            xytext=(5, 7),
            textcoords="offset points",
            fontsize=7,
        )

    titulo = nome_modelo.replace("_", " ").title()

    plt.title(f"{titulo}: detecção de desvios (contamination={contamination:.2f})")

    plt.xlabel("Hora do evento (0h - 23h)")
    plt.ylabel("Valor da transação (R$)")
    plt.xlim(-1, 24)
    plt.grid(True, linestyle=":", alpha=0.3)
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        output_dir / f"anomalias_{nome_modelo}.png",
        dpi=150,
    )

    plt.close()


def gerar_grafico_comparacao(
    comparacao: pd.DataFrame,
    output_dir: str | Path = "reports",
) -> None:
    """Compara precision, recall e F1 dos detectores."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    metricas_plot = comparacao.set_index("modelo")[
        [
            "precision_vs_status_real",
            "recall_vs_status_real",
            "f1_vs_status_real",
        ]
    ]

    ax = metricas_plot.plot(
        kind="bar",
        figsize=(11, 6),
    )

    ax.set_title("Comparação dos detectores de anomalia")
    ax.set_ylabel("Métrica (0 a 1)")
    ax.set_xlabel("Modelo")
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", linestyle=":", alpha=0.3)

    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()

    plt.savefig(
        output_dir / "comparacao_detectores.png",
        dpi=150,
    )

    plt.close()


def gerar_grafico_importancia_classificador(
    features: list[str],
    importancias,
    auc: float,
    output_dir: str | Path = "reports",
) -> None:
    """Gera o gráfico de importância das features do classificador."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(9.5, 5))

    bars = plt.barh(
        features,
        importancias,
        color="#00ffcc",
        edgecolor="cyan",
        height=0.5,
    )

    plt.title(
        "VETORES DE RISCO IDENTIFICADOS PELO CLASSIFICADOR",
        fontsize=12,
        fontweight="bold",
        color="cyan",
        pad=15,
    )

    auc_label = f"{auc:.2f}" if pd.notna(auc) else "N/D"

    plt.xlabel(
        f"Relevância na Tomada de Decisão do SOC (ROC-AUC teste: {auc_label})",
        fontsize=10,
        color="gray",
    )

    plt.grid(axis="x", linestyle="--", alpha=0.3)

    for bar in bars:
        width = bar.get_width()

        plt.text(
            width + 0.005,
            bar.get_y() + bar.get_height() / 2,
            f"{width:.1%}",
            va="center",
            ha="left",
            color="white",
            fontsize=9,
            fontweight="bold",
        )

    plt.tight_layout()

    plt.savefig(
        output_dir / "importancia_features_classificador.png",
        dpi=150,
    )

    plt.close()
