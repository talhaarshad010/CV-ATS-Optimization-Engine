import os
import mlflow

# Resolve absolute path to cv-platform/ml/mlruns
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TRACKING_DIR = os.path.join(ROOT_DIR, "ml", "mlruns")
mlflow.set_tracking_uri(f"file://{TRACKING_DIR}")

def log_extraction_run(candidate_id: str, method: str, char_count: int, duration_seconds: float):
    """
    Logs metadata about the text extraction phase.
    """
    mlflow.set_experiment("cv_extraction")
    with mlflow.start_run():
        mlflow.set_tag("candidate_id", candidate_id)
        mlflow.set_tag("method", method)
        mlflow.log_param("extraction_method", method)
        mlflow.log_metric("char_count", char_count)
        mlflow.log_metric("duration_seconds", duration_seconds)

def log_ats_score_run(candidate_id: str, job_id: str, score: int, breakdown: dict):
    """
    Logs ATS score evaluation runs, including category percentages.
    """
    mlflow.set_experiment("ats_scoring")
    with mlflow.start_run():
        mlflow.set_tag("candidate_id", candidate_id)
        mlflow.set_tag("job_id", job_id)
        mlflow.set_tag("model_version", "1.0.0")
        mlflow.log_metric("ats_score", score)
        
        # Log breakdown categories as metrics
        for category, details in breakdown.items():
            if isinstance(details, dict) and "percentage" in details:
                mlflow.log_metric(f"breakdown_{category}_pct", float(details["percentage"]))

def log_ner_run(candidate_id: str, ner_method: str, fields_found: list, duration: float):
    """
    Logs Named Entity Recognition performance and fields extracted.
    """
    mlflow.set_experiment("ner_extraction")
    with mlflow.start_run():
        mlflow.set_tag("candidate_id", candidate_id)
        mlflow.set_tag("ner_method", ner_method)
        mlflow.log_param("ner_method", ner_method)
        mlflow.log_metric("fields_found_count", len(fields_found))
        mlflow.log_metric("duration_seconds", duration)
