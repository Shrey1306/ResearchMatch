import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

PLOTS_DIR = Path("llm_evals/plots")
PLOTS_DIR.mkdir(exist_ok=True)

def load_json_to_df(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)

    if isinstance(data, dict) and "professor" in data:
        data = [data]

    records = []
    for entry in data:
        prof = entry["professor"]
        for model, metrics in entry["metrics"].items():
            records.append({
                "professor": prof,
                "model": model,
                "precision": metrics.get("precision", 0.0),
                "recall": metrics.get("recall", 0.0),
                "f1": metrics.get("f1", 0.0),
                "jaccard": metrics.get("jaccard", 0.0),
            })

    return pd.DataFrame(records)

def plot_all_metrics_from_json(json_path):
    df = load_json_to_df(json_path)

    df_agg = df.groupby(["professor", "model"]).mean(numeric_only=True).reset_index()

    for metric in ["precision", "recall", "f1", "jaccard"]:
        avg = df_agg.groupby("model")[metric].mean().sort_values(ascending=False)

        avg.plot(kind="bar")
        plt.ylabel(f"Average {metric.capitalize()}"); plt.title(f"Mean {metric.capitalize()} by Model")
        plt.tight_layout()
        plt.savefig(PLOTS_DIR / f"avg_{metric}_by_model.png", dpi=200)
        plt.close()

        sns.boxplot(data=df_agg, x="model", y=metric, order=avg.index)
        plt.ylabel(metric.capitalize()); plt.title(f"{metric.capitalize()} Score Distribution")
        plt.tight_layout()
        plt.savefig(PLOTS_DIR / f"boxplot_{metric}.png", dpi=200)
        plt.close()

        pivot = df_agg.pivot(index="professor", columns="model", values=metric)
        sns.heatmap(pivot, cmap="viridis", vmin=0, vmax=1, annot=False)
        plt.title(f"Per-professor {metric.capitalize()}")
        plt.tight_layout()
        plt.savefig(PLOTS_DIR / f"heatmap_{metric}.png", dpi=200)
        plt.close()

    print("✓ Saved plots for all metrics under", PLOTS_DIR)

plot_all_metrics_from_json("llm_evals/data/metrics.json")