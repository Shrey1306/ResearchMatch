"""
evaluate_llms.py  ──  compare cached LLM answers with Perplexity ground truth
"""
from __future__ import annotations
import os, json, re, argparse, time
from pathlib import Path

import pandas as pd
from tqdm import tqdm
from sklearn.metrics import precision_score, recall_score, f1_score

import matplotlib.pyplot as plt
import seaborn as sns

from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# ────────────────────────────────────────────────────────────────────────────
# 1. Helpers – keyword normalisation
# ────────────────────────────────────────────────────────────────────────────
LOWER  = {"a","an","the","and","or","but","nor","for","yet","so","of","in",
          "on","to","with","by","at","as"}
ABBREV = {"ai":"artificial intelligence", "ml":"machine learning",
          "nlp":"natural language processing", "hci":"human computer interaction",
          "iot":"internet of things", "ar":"augmented reality",
          "vr":"virtual reality", "xr":"extended reality",
          "db":"database", "os":"operating systems"}

def clean_topics(raw: str | list[str]) -> list[str]:
    """Return a canonical, title‑cased list of topic strings."""
    pieces = raw if isinstance(raw, list) else re.split(r"[,;/|]", raw.lower())
    out = []
    for w in pieces:
        w = ABBREV.get(w.strip(), w.strip())
        if not w:
            continue
        words = [x if x in LOWER else x.capitalize() for x in w.split()]
        out.append(" ".join(words))
    return sorted(set(out))

# ────────────────────────────────────────────────────────────────────────────
# 2. Perplexity (ground truth) – OpenAI‑compatible
# ────────────────────────────────────────────────────────────────────────────
PPLX_API_KEY = os.getenv("PPLX_API_KEY")
if not PPLX_API_KEY:
    raise RuntimeError("Please set PPLX_API_KEY in your environment!")

client_pplx = OpenAI(api_key=PPLX_API_KEY,
                     base_url="https://api.perplexity.ai")   # <‑‑ key line
PPLX_MODEL  = "sonar"

def build_prompt(prof: str) -> str:
    return (f"I want to work under {prof}. "
            "List ALL the research topics they focus on, as keywords separated "
            "by commas. Respond in the form:\n"
            "Research Areas: topic1, topic2, …")

def call_perplexity(prompt: str) -> str:
    msg = [
        {"role": "system", "content": "Be precise and concise."},
        {"role": "user",   "content": prompt},
    ]
    resp = client_pplx.chat.completions.create(model=PPLX_MODEL,
                                               messages=msg,
                                               temperature=0.0)
    return resp.choices[0].message.content

# ────────────────────────────────────────────────────────────────────────────
# 3. Metrics
# ────────────────────────────────────────────────────────────────────────────
def jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / max(len(a | b), 1)

def compute_metrics(gt: list[str], pred: list[str]) -> dict[str, float]:
    lab = sorted(set(gt + pred))
    gt_bin   = [t in gt   for t in lab]
    pred_bin = [t in pred for t in lab]
    return {
        "jaccard"  : jaccard(set(gt), set(pred)),
        "precision": precision_score(gt_bin, pred_bin, zero_division=0),
        "recall"   : recall_score(gt_bin, pred_bin, zero_division=0),
        "f1"       : f1_score(gt_bin, pred_bin, zero_division=0),
    }

# ────────────────────────────────────────────────────────────────────────────
# 4. Main loop – consume llm_results.json only
# ────────────────────────────────────────────────────────────────────────────
def main(json_file: Path, limit: int | None = None) -> pd.DataFrame:
    records = json.loads(json_file.read_text())
    rows, gt_rows = [], []

    for rec in tqdm(records[:limit], desc="Scoring"):
        prof   = rec["name"]
        prompt = build_prompt(prof)

        try:
            gt_raw  = call_perplexity(prompt)
            gt_list = clean_topics(gt_raw.split(":", 1)[-1])
            gt_rows.append({
                "professor": prof,
                "prompt":    prompt,
                "perplexity_raw": gt_raw
            })
        except Exception as e:
            print("Perplexity error – skipping", prof, e)
            continue

        for model, answer in rec["research_areas"].items():
            if not answer:                         # skip empty lists
                continue
            pred_list = clean_topics(answer)
            m = compute_metrics(gt_list, pred_list)
            rows.append({
                "professor": prof,
                "model":     model,
                **m,
                "gt_raw":    gt_raw,
                "pred_raw":  ", ".join(answer),
            })

    df = pd.DataFrame(rows)
    df.to_parquet("evaluation_results.parquet", index=False)
    log_path = Path("perplexity_outputs.jsonl")
    with log_path.open("w", encoding="utf‑8") as f:
        for item in gt_rows:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Saved Perplexity raw replies → {log_path}")
    print("Saved metrics → evaluation_results.parquet")
    return df

# ────────────────────────────────────────────────────────────────────────────
# 5. Plotting (unchanged)
# ────────────────────────────────────────────────────────────────────────────
def plot_results(df: pd.DataFrame) -> None:
    avg = df.groupby("model")["f1"].mean().sort_values(ascending=False)
    avg.plot(kind="bar")
    plt.ylabel("Average F₁"); plt.title("Mean F₁ by model"); plt.tight_layout()
    plt.savefig("avg_f1_by_model.png", dpi=200); plt.close()

    sns.boxplot(data=df, x="model", y="f1", order=avg.index)
    plt.ylabel("F₁"); plt.title("F₁ score distribution"); plt.tight_layout()
    plt.savefig("boxplot_f1.png", dpi=200); plt.close()

    pivot = df.pivot(index="professor", columns="model", values="f1")
    sns.heatmap(pivot, cmap="viridis", vmin=0, vmax=1)
    plt.title("Per‑professor F₁"); plt.tight_layout()
    plt.savefig("heatmap_f1.png", dpi=200); plt.close()

    print("Plots saved.")

# ────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="llm_results.json", type=Path,
                    help="File containing cached model outputs")
    ap.add_argument("--limit", type=int, default=None,
                    help="Only evaluate first N professors")
    args = ap.parse_args()

    df = main(args.results, args.limit)
    plot_results(df)
