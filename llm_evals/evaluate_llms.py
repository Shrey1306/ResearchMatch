"""
LLM_evals/evaluate_llms.py
Compare cached LLM answers (data/llm_results.json) with Perplexity ground truth
and save results/plots under LLM_evals/{data,plots}.
"""
from __future__ import annotations
import os, json, re, argparse
from pathlib import Path

import pandas as pd
from tqdm import tqdm
from sklearn.metrics import precision_score, recall_score, f1_score

import matplotlib.pyplot as plt
import seaborn as sns

from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# ──────────────────────────────── 0. Paths & folders ────────────────────── #
BASE_DIR   = Path(__file__).resolve().parent      # LLM_evals/
DATA_DIR   = BASE_DIR / "data"
PLOTS_DIR  = BASE_DIR / "plots"
DATA_DIR.mkdir(parents=True,  exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

# ───────────────────────────── 1. Topic normalisation ───────────────────── #
LOWER  = {"a","an","the","and","or","but","nor","for","yet","so","of","in",
          "on","to","with","by","at","as"}
ABBREV = {"ai":"artificial intelligence", "ml":"machine learning",
          "nlp":"natural language processing", "hci":"human computer interaction",
          "iot":"internet of things", "ar":"augmented reality",
          "vr":"virtual reality", "xr":"extended reality",
          "db":"database", "os":"operating systems"}

def clean_topics(raw: str | list[str]) -> list[str]:
    pieces = raw if isinstance(raw, list) else re.split(r"[,;/|]", raw.lower())
    out = []
    for w in pieces:
        w = ABBREV.get(w.strip(), w.strip())
        if not w:
            continue
        words = [x if x in LOWER else x.capitalize() for x in w.split()]
        out.append(" ".join(words))
    return sorted(set(out))

# ───────────────────────────── 2. Perplexity client ─────────────────────── #
PPLX_API_KEY = os.getenv("PPLX_API_KEY")
if not PPLX_API_KEY:
    raise RuntimeError("Please set PPLX_API_KEY!")

client_pplx = OpenAI(api_key=PPLX_API_KEY,
                     base_url="https://api.perplexity.ai")
PPLX_MODEL = "sonar"

def build_prompt(prof: str) -> str:
    return (f"I want to work under {prof}. "
            "List ALL the research topics they focus on, as keywords separated "
            "by commas. Respond in the form:\n"
            "Research Areas: topic1, topic2, …")

def call_perplexity(prompt: str) -> str:
    rsp = client_pplx.chat.completions.create(
        model=PPLX_MODEL,
        temperature=0.0,
        messages=[
            {"role":"system","content":"Be precise and concise."},
            {"role":"user","content":prompt},
        ]
    )
    return rsp.choices[0].message.content

# ───────────────────────────── 3. Metrics helpers ───────────────────────── #
def jaccard(a:set[str], b:set[str]) -> float:
    return len(a & b) / max(len(a | b), 1)

def compute_metrics(gt: list[str], pred: list[str]):
    lab       = sorted(set(gt + pred))
    gt_bin    = [t in gt   for t in lab]
    pred_bin  = [t in pred for t in lab]
    return {
        "jaccard"  : jaccard(set(gt), set(pred)),
        "precision": precision_score(gt_bin, pred_bin, zero_division=0),
        "recall"   : recall_score(gt_bin, pred_bin, zero_division=0),
        "f1"       : f1_score(gt_bin, pred_bin, zero_division=0),
    }

# ───────────────────────────── 4. Main evaluation ───────────────────────── #
def main(results_file: Path, limit: int | None):
    records = json.loads(results_file.read_text())
    rows, gt_rows, metrics_data = [], [], []

    for rec in tqdm(records[:limit], desc="Scoring"):
        prof   = rec["name"]
        prompt = build_prompt(prof)

        try:
            gt_raw  = call_perplexity(prompt)
            gt_list = clean_topics(gt_raw.split(":", 1)[-1])
            gt_rows.append({"professor":prof, "prompt":prompt,
                            "perplexity_raw":gt_raw})
        except Exception as e:
            print("Perplexity call failed for", prof, "→", e)
            continue

        # Calculate metrics for each model
        model_metrics = {}
        for model, answer in rec["research_areas"].items():
            if not answer:
                continue                                      # skip empty list
            pred_list = clean_topics(answer)
            metrics   = compute_metrics(gt_list, pred_list)
            
            # Store metrics for this model
            model_metrics[model] = {
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1": metrics["f1"],
                "jaccard": metrics["jaccard"],
                "predicted_topics": pred_list,
                "ground_truth_topics": gt_list
            }
            
            rows.append({
                "professor": prof,
                "model":     model,
                **metrics,
                "gt_raw":    gt_raw,
                "pred_raw":  ", ".join(answer),
            })

        # Add metrics to metrics data
        metrics_data.append({
            "professor": prof,
            "metrics": model_metrics
        })

    # Save metrics to separate file
    metrics_file = DATA_DIR / "metrics.json"
    with open(metrics_file, 'w') as f:
        json.dump(metrics_data, f, indent=2)

    # Save evaluation results
    pd.DataFrame(rows).to_parquet(DATA_DIR / "evaluation_results.parquet",
                                  index=False)
    with (DATA_DIR / "perplexity_outputs.jsonl").open("w", encoding="utf‑8") as f:
        for item in gt_rows:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print("✓ Saved data files under", DATA_DIR)
    return pd.DataFrame(rows)

# ───────────────────────────── 5. Plotting helpers ──────────────────────── #
def plot_results(df: pd.DataFrame):
    # Group by professor and model, taking mean of F1 scores to handle duplicates
    df_agg = df.groupby(["professor", "model"])["f1"].mean().reset_index()
    
    # Calculate average F1 by model
    avg = df_agg.groupby("model")["f1"].mean().sort_values(ascending=False)
    avg.plot(kind="bar")
    plt.ylabel("Average F₁"); plt.title("Mean F₁ by model")
    plt.tight_layout(); plt.savefig(PLOTS_DIR / "avg_f1_by_model.png", dpi=200)
    plt.close()

    # Boxplot using aggregated data
    sns.boxplot(data=df_agg, x="model", y="f1", order=avg.index)
    plt.ylabel("F₁"); plt.title("F₁ score distribution")
    plt.tight_layout(); plt.savefig(PLOTS_DIR / "boxplot_f1.png", dpi=200)
    plt.close()

    # Create pivot table from aggregated data
    pivot = df_agg.pivot(index="professor", columns="model", values="f1")
    sns.heatmap(pivot, cmap="viridis", vmin=0, vmax=1)
    plt.title("Per‑professor F₁"); plt.tight_layout()
    plt.savefig(PLOTS_DIR / "heatmap_f1.png", dpi=200); plt.close()
    print("✓ Saved plots under", PLOTS_DIR)

# ───────────────────────────── 6. CLI entry‑point ───────────────────────── #
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--results",
                        default=Path(__file__).resolve().parent.parent / "results.json",
                        type=Path,
                        help="Cached model answers (JSON)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Evaluate only the first N professors")
    args = parser.parse_args()

    df_metrics = main(args.results, args.limit)
    # plot_results(df_metrics)
