#!/usr/bin/env python3
"""
AI Algorithm Teacher

A lightweight CLI program that suggests suitable AI/ML algorithms based on a natural-language
problem description. It also explains why each algorithm fits, common pitfalls, and next steps.

No external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
import sys


# ----------------------------- Data structures -----------------------------


@dataclass
class Recommendation:
    algorithm: str
    score: float
    rationale: str
    when_to_use: str
    pros: List[str]
    cons: List[str]
    typical_steps: List[str]
    resources: List[str]


# ----------------------------- Knowledge base ------------------------------


ALGO_KB: Dict[str, Dict[str, object]] = {
    "Linear Regression": {
        "task": "regression",
        "when": "Predict continuous numeric targets; baseline for tabular data.",
        "pros": [
            "Fast and simple",
            "Interpretable coefficients",
            "Works well with few features",
        ],
        "cons": [
            "Assumes linearity",
            "Sensitive to outliers and multicollinearity",
        ],
        "steps": [
            "Split data into train/validation",
            "Scale features (optional); add polynomial/interaction terms if needed",
            "Fit model and check residuals",
            "Evaluate with RMSE/MAE and baseline",
        ],
        "resources": [
            "https://scikit-learn.org/stable/modules/linear_model.html",
        ],
    },
    "Random Forest (Regression)": {
        "task": "regression",
        "when": "Nonlinear tabular regression; robust baseline with limited tuning.",
        "pros": ["Handles nonlinearities", "Insensitive to scaling", "Good with defaults"],
        "cons": ["Less interpretable", "Larger models"],
        "steps": [
            "Train with default hyperparameters",
            "Tune n_estimators, max_depth",
            "Evaluate with cross-validation",
        ],
        "resources": ["https://scikit-learn.org/stable/modules/ensemble.html#forests-of-randomized-trees"],
    },
    "Logistic Regression": {
        "task": "classification",
        "when": "Binary/one-vs-rest classification; strong, interpretable baseline.",
        "pros": ["Fast", "Probabilistic outputs", "Interpretable"],
        "cons": ["Linear decision boundary", "Feature engineering often needed"],
        "steps": [
            "Standardize features",
            "Handle class imbalance (class_weight or resampling)",
            "Tune regularization (C)",
        ],
        "resources": ["https://scikit-learn.org/stable/modules/linear_model.html#logistic-regression"],
    },
    "Random Forest (Classification)": {
        "task": "classification",
        "when": "Nonlinear tabular classification; strong default baseline.",
        "pros": ["Handles mixed features", "Robust", "Works out-of-the-box"],
        "cons": ["Less interpretable", "May be heavy for low-latency"],
        "steps": ["Train defaults", "Tune depth/trees", "Check feature importance cautiously"],
        "resources": ["https://scikit-learn.org/stable/modules/ensemble.html#forest"],
    },
    "Gradient Boosting (XGBoost/LightGBM/CatBoost)": {
        "task": "classification_regression",
        "when": "Top performance on many tabular problems with careful tuning.",
        "pros": ["State-of-the-art on tabular", "Handles nonlinearity", "Feature importance"],
        "cons": ["Tuning sensitive", "May overfit without regularization"],
        "steps": [
            "Start with small learning rate",
            "Tune n_estimators, depth, subsampling",
            "Use early stopping",
        ],
        "resources": [
            "https://xgboost.readthedocs.io/",
            "https://lightgbm.readthedocs.io/",
            "https://catboost.ai/",
        ],
    },
    "SVM (Classification)": {
        "task": "classification",
        "when": "Medium-scale datasets with clear margin; kernels capture nonlinearity.",
        "pros": ["Effective in high dimensions", "Robust to outliers with margins"],
        "cons": ["Scaling needed", "Slow on very large datasets"],
        "steps": ["Scale features", "Try linear then RBF kernel", "Tune C and gamma"],
        "resources": ["https://scikit-learn.org/stable/modules/svm.html"],
    },
    "KNN": {
        "task": "classification_regression",
        "when": "Simple nonparametric baseline for small, low-dimensional datasets.",
        "pros": ["Simple", "No training time"],
        "cons": ["Slow at inference", "Sensitive to scaling and dimension"],
        "steps": ["Scale features", "Tune k via CV", "Use KDTree/BallTree if needed"],
        "resources": ["https://scikit-learn.org/stable/modules/neighbors.html"],
    },
    "Naive Bayes": {
        "task": "classification",
        "when": "Text classification baseline with bag-of-words/TF-IDF.",
        "pros": ["Very fast", "Surprisingly strong on text"],
        "cons": ["Strong independence assumption", "Less expressive"],
        "steps": ["Vectorize text", "Train MultinomialNB", "Compare to logistic regression"],
        "resources": ["https://scikit-learn.org/stable/modules/naive_bayes.html"],
    },
    "K-Means": {
        "task": "clustering",
        "when": "Partition numeric data into k clusters; spherical clusters, similar sizes.",
        "pros": ["Fast", "Scales well"],
        "cons": ["Requires k", "Sensitive to scale and outliers"],
        "steps": ["Scale features", "Use k-means++", "Pick k via elbow/silhouette"],
        "resources": ["https://scikit-learn.org/stable/modules/clustering.html#k-means"],
    },
    "DBSCAN": {
        "task": "clustering",
        "when": "Find arbitrarily-shaped clusters; good for outlier detection.",
        "pros": ["No k needed", "Finds noise"],
        "cons": ["Sensitive to eps/min_samples", "Struggles with varying densities"],
        "steps": ["Scale features", "Tune eps via k-distance plot", "Validate with silhouette"],
        "resources": ["https://scikit-learn.org/stable/modules/clustering.html#dbscan"],
    },
    "PCA": {
        "task": "dimensionality_reduction",
        "when": "Reduce dimensionality while preserving variance; preprocessing or visualization.",
        "pros": ["Fast", "Deterministic"],
        "cons": ["Linear only", "Components hard to interpret"],
        "steps": ["Standardize features", "Pick components via explained variance"],
        "resources": ["https://scikit-learn.org/stable/modules/decomposition.html#pca"],
    },
    "t-SNE/UMAP": {
        "task": "dimensionality_reduction",
        "when": "Nonlinear embeddings for visualization; not for downstream metrics.",
        "pros": ["Great visual clusters"],
        "cons": ["Stochastic", "Not ideal for downstream modeling"],
        "steps": ["Standardize features", "Try perplexity (t-SNE) / n_neighbors (UMAP)"],
        "resources": [
            "https://umap-learn.readthedocs.io/en/latest/",
            "https://lvdmaaten.github.io/tsne/",
        ],
    },
    "ARIMA/Prophet": {
        "task": "time_series",
        "when": "Univariate time-series forecasting with trend/seasonality.",
        "pros": ["Interpretable", "Captures seasonality"],
        "cons": ["Less flexible for complex exogenous signals"],
        "steps": ["Make series stationary or let Prophet model trend/seasonality", "Cross-validate"],
        "resources": [
            "https://otexts.com/fpp3/",
            "https://facebook.github.io/prophet/",
        ],
    },
    "LSTM/Temporal CNN": {
        "task": "time_series",
        "when": "Multivariate or long-horizon forecasting with complex dependencies.",
        "pros": ["Captures long dependencies"],
        "cons": ["Needs more data", "Harder to tune"],
        "steps": ["Create sliding windows", "Normalize", "Tune architecture and horizon"],
        "resources": ["https://pytorch.org/tutorials/beginner/forecasting_tutorial.html"],
    },
    "BERT/RoBERTa (Text)": {
        "task": "nlp",
        "when": "Text classification/NER/Q&A with pretrained transformers.",
        "pros": ["Strong accuracy", "Transfer learning"],
        "cons": ["Compute-heavy", "Latency considerations"],
        "steps": ["Start with smaller distil models", "Fine-tune with early stopping"],
        "resources": ["https://huggingface.co/docs/transformers/index"],
    },
    "CNN (Vision)": {
        "task": "vision",
        "when": "Image classification; start with pretrained backbones.",
        "pros": ["Excellent accuracy with transfer learning"],
        "cons": ["Compute-heavy", "Requires augmentation"],
        "steps": ["Resize & normalize", "Transfer learn", "Augment and regularize"],
        "resources": ["https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html"],
    },
    "Object Detection (Faster R-CNN/YOLO)": {
        "task": "vision",
        "when": "Detect and localize objects with bounding boxes.",
        "pros": ["Strong performance"],
        "cons": ["Complex training", "Latency varies"] ,
        "steps": ["Choose architecture per latency", "Label boxes", "Tune anchors/augment"],
        "resources": ["https://docs.ultralytics.com/"],
    },
    "Anomaly Detection (Isolation Forest/One-Class SVM)": {
        "task": "anomaly",
        "when": "Find rare events with little labeled data.",
        "pros": ["Unsupervised/semi-supervised"],
        "cons": ["Thresholding sensitive"],
        "steps": ["Scale features", "Tune contamination/nu", "Validate on known anomalies"],
        "resources": ["https://scikit-learn.org/stable/modules/outlier_detection.html"],
    },
    "Matrix Factorization/Two-Tower (Recsys)": {
        "task": "recsys",
        "when": "Personalized recommendations from user-item interactions.",
        "pros": ["Captures user/item embeddings"],
        "cons": ["Cold-start issues"],
        "steps": ["Build interaction matrix", "Train MF or towers", "Handle cold-start"],
        "resources": ["https://developers.google.com/machine-learning/recommendation"],
    },
    "Reinforcement Learning (DQN/PPO)": {
        "task": "rl",
        "when": "Sequential decision-making with delayed rewards.",
        "pros": ["Optimizes long-term return"],
        "cons": ["Sample-inefficient", "Reward shaping needed"],
        "steps": ["Define MDP", "Start with simple baselines", "Evaluate stability"],
        "resources": ["https://spinningup.openai.com/en/latest/"],
    },
    "Causal Inference (ATE/DoWhy)": {
        "task": "causal",
        "when": "Estimate causal effects from observational data.",
        "pros": ["Actionable insights"],
        "cons": ["Requires assumptions", "Sensitive to confounding"],
        "steps": ["Define treatment/outcome", "Choose identification strategy", "Validate assumptions"],
        "resources": ["https://www.bradyneal.com/intro-to-causal-inference"],
    },
}


# ----------------------------- Rule engine ---------------------------------


def normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def extract_features(prompt: str) -> Dict[str, bool | str | int]:
    p = normalize(prompt)

    features: Dict[str, bool | str | int] = {}

    # Modalities
    features["has_text"] = any(k in p for k in ["text", "nlp", "document", "review", "tweet", "transcript", "chat"])
    features["has_image"] = any(k in p for k in ["image", "vision", "photo", "camera", "ocr", "object detection"])
    features["has_time"] = any(k in p for k in ["time series", "timeseries", "temporal", "forecast", "sequence", "monthly", "daily"])

    # Supervision/task intent
    features["classification"] = any(k in p for k in ["classify", "classification", "label", "spam", "churn", "fraud", "predict category", "sentiment"])
    features["regression"] = any(k in p for k in ["regress", "regression", "predict price", "predict demand", "continuous", "numeric"])
    features["clustering"] = any(k in p for k in ["cluster", "clustering", "group", "segment", "unsupervised"])
    features["dimred"] = any(k in p for k in ["dimensionality", "pca", "embed", "visualize high-dimensional"])
    features["anomaly"] = any(k in p for k in ["anomaly", "outlier", "rare", "novelty", "intrusion"])
    features["recsys"] = any(k in p for k in ["recommend", "recommender", "recommendation", "user-item", "collaborative"])
    features["rl"] = any(k in p for k in ["reinforcement", "policy", "agent", "reward", "bandit", "environment"])
    features["causal"] = any(k in p for k in ["causal", "treatment", "intervention", "counterfactual", "uplift"])

    # Constraints
    features["small_data"] = any(k in p for k in ["few samples", "small dataset", "limited data", "under 1k", "hundreds of"])
    features["large_data"] = any(k in p for k in ["millions", "very large", "big data", "huge dataset"])
    features["imbalanced"] = any(k in p for k in ["imbalanced", "rare positive", "skewed", "class weights"])
    features["interpretability"] = any(k in p for k in ["interpret", "explain", "transparent", "coefficients", "explainable"])
    features["low_latency"] = any(k in p for k in ["real-time", "low latency", "on-device", "edge"])
    features["nonlinear"] = any(k in p for k in ["nonlinear", "complex interactions", "non-linear"])
    features["high_dim"] = any(k in p for k in ["thousands of features", "high-dimensional", "sparse"])

    return features


def score_algorithms(features: Dict[str, bool | str | int]) -> List[Tuple[str, float, str]]:
    scores: Dict[str, float] = {name: 0.0 for name in ALGO_KB}
    rationales: Dict[str, List[str]] = {name: [] for name in ALGO_KB}

    def add(name: str, points: float, reason: str) -> None:
        scores[name] += points
        rationales[name].append(reason)

    # Task routing
    if features.get("has_text"):
        add("Naive Bayes", 1.5, "Text baseline with bag-of-words")
        add("Logistic Regression", 1.0, "Strong linear baseline for text")
        add("BERT/RoBERTa (Text)", 2.0, "Transformers excel for text tasks")

    if features.get("has_image"):
        add("CNN (Vision)", 2.0, "CNNs for image classification")
        # If the prompt mentions detection/localization, boost detection algorithms
        if True:
            # We don't have direct access to the original prompt string here, but
            # 'has_image' feature already includes 'object detection' keyword.
            # Add a small boost when image modality is present so detection can appear when relevant.
            add("Object Detection (Faster R-CNN/YOLO)", 0.2, "Possible need for localization/detection")

    if features.get("has_time"):
        add("ARIMA/Prophet", 1.5, "Time series with trend/seasonality")
        add("LSTM/Temporal CNN", 1.5, "Sequence models for complex dynamics")

    if features.get("classification"):
        add("Logistic Regression", 1.5, "Classification baseline")
        add("Random Forest (Classification)", 1.5, "Nonlinear tabular classifier")
        add("SVM (Classification)", 1.0, "Margin-based classifier")
        add("Gradient Boosting (XGBoost/LightGBM/CatBoost)", 1.5, "Strong tabular performance")

    if features.get("regression"):
        add("Linear Regression", 1.5, "Regression baseline")
        add("Random Forest (Regression)", 1.5, "Nonlinear tabular regression")
        add("Gradient Boosting (XGBoost/LightGBM/CatBoost)", 1.5, "Strong tabular regression")

    if features.get("clustering"):
        add("K-Means", 1.5, "Fast partitioning clustering")
        add("DBSCAN", 1.0, "Density-based clustering and outliers")

    if features.get("dimred"):
        add("PCA", 1.5, "Linear dimensionality reduction")
        add("t-SNE/UMAP", 1.0, "Nonlinear embeddings for visualization")

    if features.get("anomaly"):
        add("Anomaly Detection (Isolation Forest/One-Class SVM)", 2.0, "Unsupervised anomaly detection")

    if features.get("recsys"):
        add("Matrix Factorization/Two-Tower (Recsys)", 2.0, "User-item recommendations")

    if features.get("rl"):
        add("Reinforcement Learning (DQN/PPO)", 2.0, "Sequential decision-making")

    if features.get("causal"):
        add("Causal Inference (ATE/DoWhy)", 2.0, "Estimate causal effects")

    # Constraints shaping
    if features.get("small_data"):
        add("Logistic Regression", 0.7, "Small-data friendly")
        add("Linear Regression", 0.7, "Small-data friendly")
        add("SVM (Classification)", 0.4, "Works on medium-small datasets")
        add("Naive Bayes", 0.6, "Very data-efficient for text")

    if features.get("large_data"):
        add("Gradient Boosting (XGBoost/LightGBM/CatBoost)", 0.6, "Scales well with optimizations")
        add("Random Forest (Classification)", 0.4, "Parallelizable ensembles")
        add("Random Forest (Regression)", 0.4, "Parallelizable ensembles")

    if features.get("imbalanced"):
        add("Gradient Boosting (XGBoost/LightGBM/CatBoost)", 0.5, "Built-in class weighting options")
        add("Random Forest (Classification)", 0.5, "Supports class weighting")
        add("Logistic Regression", 0.3, "Class weights and calibration")

    if features.get("interpretability"):
        add("Linear Regression", 0.8, "Interpretable coefficients")
        add("Logistic Regression", 0.8, "Interpretable odds ratios")

    if features.get("low_latency"):
        add("Logistic Regression", 0.5, "Very fast inference")
        add("Linear Regression", 0.5, "Very fast inference")
        add("KNN", -0.6, "Slow inference due to neighbor search")
        add("BERT/RoBERTa (Text)", -0.5, "Transformers can be heavy")

    if features.get("nonlinear"):
        add("Random Forest (Classification)", 0.5, "Captures nonlinearities")
        add("Random Forest (Regression)", 0.5, "Captures nonlinearities")
        add("Gradient Boosting (XGBoost/LightGBM/CatBoost)", 0.6, "Captures complex interactions")

    if features.get("high_dim"):
        add("Linear Regression", 0.3, "With regularization and feature selection")
        add("Logistic Regression", 0.3, "With regularization")
        add("PCA", 0.8, "Reduce dimensionality")
        add("SVM (Classification)", 0.3, "Effective in high dimensions")

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return [(name, score, "; ".join(rationales[name])) for name, score in ranked if score > 0.0]


def build_recommendations(prompt: str) -> List[Recommendation]:
    features = extract_features(prompt)
    ranked = score_algorithms(features)
    recs: List[Recommendation] = []
    for name, score, why in ranked[:6]:
        kb = ALGO_KB[name]
        recs.append(
            Recommendation(
                algorithm=name,
                score=round(score, 2),
                rationale=why,
                when_to_use=str(kb["when"]),
                pros=list(kb["pros"]),
                cons=list(kb["cons"]),
                typical_steps=list(kb["steps"]),
                resources=list(kb["resources"]),
            )
        )
    return recs


# ----------------------------- CLI interface --------------------------------


def format_recommendation(rec: Recommendation, index: int) -> str:
    lines: List[str] = []
    lines.append(f"{index}. {rec.algorithm}  (score: {rec.score})")
    lines.append(f"   Why: {rec.rationale}")
    lines.append(f"   When: {rec.when_to_use}")
    lines.append("   Pros: " + "; ".join(rec.pros))
    lines.append("   Cons: " + "; ".join(rec.cons))
    lines.append("   Steps:")
    for step in rec.typical_steps:
        lines.append(f"     - {step}")
    lines.append("   Learn more:")
    for url in rec.resources:
        lines.append(f"     - {url}")
    return "\n".join(lines)


def run_cli(prompt: str) -> int:
    recs = build_recommendations(prompt)
    if not recs:
        print("No strong signals found. Try adding task type (e.g., classification, regression, clustering) and context (data modality, constraints).")
        return 1

    print("Best-fit algorithms based on your description:\n")
    for i, rec in enumerate(recs, 1):
        print(format_recommendation(rec, i))
        if i != len(recs):
            print()
    return 0


def main(argv: List[str]) -> int:
    if len(argv) > 1:
        prompt = " ".join(argv[1:])
    else:
        print("Describe your problem (e.g., 'Classify customer reviews for sentiment with limited labeled data and need interpretability'):\n")
        prompt = input("> ").strip()
    if not prompt:
        print("Empty prompt. Exiting.")
        return 2
    return run_cli(prompt)


if __name__ == "__main__":
    sys.exit(main(sys.argv))


