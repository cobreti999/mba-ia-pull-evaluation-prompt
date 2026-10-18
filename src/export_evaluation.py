"""Exporta evidências de um experimento concluído sem alterar suas notas."""

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client

METRICS = ("helpfulness", "correctness", "f1_score", "clarity", "precision")
ROOT = Path(__file__).resolve().parents[1]


class IncompleteExperimentError(ValueError):
    """As execuções ou notas ainda não estão disponíveis integralmente."""


def export_experiment(project_name: str, prompt_commit: str, output: Path):
    client = Client()
    project = client.read_project(project_name=project_name)
    dataset = client.read_dataset(dataset_id=project.reference_dataset_id)
    examples = {str(example.id): example for example in client.list_examples(dataset_id=dataset.id)}
    runs = list(client.list_runs(project_id=project.id, is_root=True))
    runs = [run for run in runs if run.reference_example_id is not None]
    if len(runs) != len(examples) or {str(run.reference_example_id) for run in runs} != set(examples):
        raise IncompleteExperimentError("O experimento não tem exatamente uma execução por exemplo.")
    feedback = list(client.list_feedback(run_ids=[run.id for run in runs]))
    rows = []
    for run in runs:
        notes = {item.key: item for item in feedback if item.run_id == run.id and item.key in METRICS}
        if run.error or not run.end_time or set(notes) != set(METRICS):
            raise IncompleteExperimentError(f"Execução incompleta ou sem as cinco métricas: {run.id}")
        if any(item.score is None or not 0 <= float(item.score) <= 1 for item in notes.values()):
            raise ValueError(f"Nota inválida: {run.id}")
        example = examples[str(run.reference_example_id)]
        rows.append({
            "run_id": str(run.id),
            "example_id": str(example.id),
            "inputs": run.inputs,
            "outputs": run.outputs,
            "reference": example.outputs,
            "scores": {key: float(notes[key].score) for key in METRICS},
            "comments": {key: notes[key].comment for key in METRICS},
        })
    rows.sort(key=lambda row: row["inputs"].get("bug_report", ""))
    means = {key: round(sum(row["scores"][key] for row in rows) / len(rows), 4) for key in METRICS}
    project_metadata = (getattr(project, "extra", None) or {}).get("metadata", {})
    metadata_keys = ("provider", "llm_model", "eval_model", "iteration", "prompt", "prompt_commit", "dataset_version", "generation_reasoning_effort", "judge_reasoning_effort", "judge_json_mode", "generation_verbosity")
    report = {
        "experiment": project.name,
        "experiment_id": str(project.id),
        "dataset_id": str(dataset.id),
        "prompt_commit": prompt_commit,
        "metadata": {key: project_metadata[key] for key in metadata_keys if key in project_metadata},
        "url": f"https://smith.langchain.com/datasets/{dataset.id}/compare?selectedSessions={project.id}",
        "example_count": len(rows),
        "scores": means,
        "average": round(sum(means.values()) / len(means), 4),
        "passed": all(score >= 0.8 for score in means.values()),
        "all_examples_passed": all(score >= 0.8 for row in rows for score in row["scores"].values()),
        "examples": rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "examples"}, ensure_ascii=False, indent=2))
    return report


def main():
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment")
    parser.add_argument("--prompt-commit", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        export_experiment(args.experiment, args.prompt_commit, args.output)
    except Exception as exc:
        print(f"Não foi possível exportar ({type(exc).__name__}). Confirme que o experimento terminou.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
