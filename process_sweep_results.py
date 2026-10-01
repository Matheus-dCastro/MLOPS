import wandb
import os
import json
import pandas as pd

def analyze_and_tag_best(entity="matheus-dcastro", project="mlops-lab2-sweep", sweep_id="h6ykq29c"):
    api = wandb.Api()
    sweep = api.sweep(f"{entity}/{project}/{sweep_id}")
    runs = sorted(sweep.runs, key=lambda r: r.summary.get("cv_f1_macro_mean", 0), reverse=True)

    print(f"Total runs no sweep {sweep_id}: {len(runs)}")
    if not runs:
        print("Nenhum run encontrado ainda.")
        return None

    best_run = runs[0]
    print("\n" + "="*50)
    print("🏆 MELHOR RUN ENCONTRADO:")
    print(f"ID: {best_run.id}")
    print(f"Nome: {best_run.name}")
    print(f"URL: {best_run.url}")
    print(f"CV F1 Macro Mean: {best_run.summary.get('cv_f1_macro_mean'):.4f} +/- {best_run.summary.get('cv_f1_macro_std'):.4f}")
    print(f"Test Score (Acurácia/F1): {best_run.summary.get('test_score'):.4f}")
    print(f"Train Score: {best_run.summary.get('train_score'):.4f}")
    print("Hiperparâmetros ótimos:")
    for k, v in best_run.config.items():
        if not k.startswith("_"):
            print(f"  - {k}: {v}")
    print("="*50 + "\n")

    # Adicionar o alias 'best' no artifact do modelo do melhor run
    model_artifact_name = f"model-{best_run.id}"
    try:
        artifact = api.artifact(f"{entity}/{project}/{model_artifact_name}:v0")
        if "best" not in artifact.aliases:
            artifact.aliases.append("best")
            artifact.save()
            print(f"✅ Alias 'best' adicionado com sucesso ao artifact: {model_artifact_name}")
        else:
            print(f"ℹ️ Alias 'best' já existia no artifact: {model_artifact_name}")
    except Exception as e:
        print(f"Aviso ao marcar alias 'best': {e}")

    # Coletar estatísticas de todos os runs para o relatório
    records = []
    for r in runs:
        row = {
            "run_id": r.id,
            "run_name": r.name,
            "cv_f1_macro_mean": r.summary.get("cv_f1_macro_mean"),
            "cv_f1_macro_std": r.summary.get("cv_f1_macro_std"),
            "test_score": r.summary.get("test_score"),
            "train_score": r.summary.get("train_score"),
            "n_estimators": r.config.get("n_estimators"),
            "max_depth": r.config.get("max_depth"),
            "min_samples_split": r.config.get("min_samples_split"),
            "min_samples_leaf": r.config.get("min_samples_leaf"),
            "max_features": r.config.get("max_features"),
        }
        records.append(row)

    df_results = pd.DataFrame(records)
    df_results.to_csv("sweep_results_summary.csv", index=False)
    print("Resumo de todos os runs salvo em 'sweep_results_summary.csv'.")
    return best_run

if __name__ == "__main__":
    analyze_and_tag_best()
