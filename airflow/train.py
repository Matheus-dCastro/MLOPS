import os
import sys
import joblib
import pandas as pd
import numpy as np
import wandb
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.inspection import permutation_importance


def find_features_file():
    candidates = [
        "features.csv",
        "data/features.csv",
        "airflow/features.csv",
        "airflow/data/features.csv",
        os.path.join(os.path.dirname(__file__), "features.csv"),
        os.path.join(os.path.dirname(__file__), "data", "features.csv"),
        os.path.join(os.path.dirname(__file__), "airflow", "features.csv"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("features.csv não foi encontrado nos caminhos esperados.")


def main():
    default_config = {
        "n_estimators": 100,
        "max_depth": 5,
        "min_samples_split": 2,
        "min_samples_leaf": 1,
        "max_features": "sqrt",
    }

    run = wandb.init(project="mlops-lab2-sweep", config=default_config)
    config = wandb.config

    features_path = find_features_file()
    df = pd.read_csv(features_path)

    # Definir target caso não esteja explicitado
    if "target" not in df.columns:
        df["target"] = (df["vote_average"] >= 8.4).astype(int)

    # Separar X e y removendo metadados textuais e colunas que causariam leakage
    drop_cols = [c for c in ["target", "vote_average", "id", "title", "original_language", "overview"] if c in df.columns]
    X = df.drop(columns=drop_cols)
    y = df["target"]

    # Garantir split estratificado ou reproduzivel conforme especificacao
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Tratamento seguro para valores de hiperparametros vindos do sweep (como null/None)
    n_estimators = int(config.n_estimators)
    
    max_depth = config.max_depth
    if max_depth in ["None", "null", "none", None]:
        max_depth = None
    else:
        max_depth = int(max_depth)

    min_samples_split = int(config.min_samples_split)
    min_samples_leaf = int(config.min_samples_leaf)

    max_features = config.max_features
    if max_features in ["None", "null", "none", None]:
        max_features = None

    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        min_samples_leaf=min_samples_leaf,
        max_features=max_features,
        random_state=42,
    )
    model.fit(X_train, y_train)

    train_score = float(model.score(X_train, y_train))
    test_score = float(model.score(X_test, y_test))
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="f1_macro")

    cv_mean = float(cv_scores.mean())
    cv_std = float(cv_scores.std())

    # Log das metricas principais requeridas no desafio
    wandb.log({
        "train_score": train_score,
        "test_score": test_score,
        "cv_f1_macro_mean": cv_mean,
        "cv_f1_macro_std": cv_std,
    })

    # Permutation importance para interpretabilidade (aplicavel a qualquer estimador)
    perm = permutation_importance(model, X_test, y_test, n_repeats=10, random_state=42)
    importance_table = wandb.Table(
        data=list(zip(X.columns.tolist(), perm.importances_mean.tolist(), perm.importances_std.tolist())),
        columns=["feature", "importance_mean", "importance_std"],
    )
    wandb.log({"feature_importance": importance_table})

    # Versionamento do Dataset como W&B Artifact
    dataset_artifact = wandb.Artifact("features-dataset", type="dataset")
    dataset_artifact.add_file(features_path, name="features.csv")
    run.log_artifact(dataset_artifact)

    # Versionamento do Modelo como W&B Artifact com metadados dos hiperparametros
    model_filename = f"model_{run.id}.joblib"
    joblib.dump(model, model_filename)
    model_artifact = wandb.Artifact(
        f"model-{run.id}",
        type="model",
        metadata={
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "min_samples_split": min_samples_split,
            "min_samples_leaf": min_samples_leaf,
            "max_features": max_features,
            "cv_f1_macro_mean": cv_mean,
            "cv_f1_macro_std": cv_std,
            "test_score": test_score,
            "train_score": train_score,
        }
    )
    model_artifact.add_file(model_filename)
    run.log_artifact(model_artifact)

    print(f"Run {run.id} concluído com sucesso. cv_f1_macro_mean: {cv_mean:.4f}, test_score: {test_score:.4f}")
    run.finish()


if __name__ == "__main__":
    main()
