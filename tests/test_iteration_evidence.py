"""Protege a integridade das evidências e distingue média de nota por exemplo."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src import export_evaluation


@pytest.fixture
def experiment(monkeypatch):
    client = Mock()
    client.read_project.return_value = SimpleNamespace(
        id="experiment", name="iteration-test", reference_dataset_id="dataset",
    )
    client.read_dataset.return_value = SimpleNamespace(id="dataset")
    examples = [SimpleNamespace(id=str(i), outputs={"reference": "referência"}) for i in range(2)]
    runs = [SimpleNamespace(
        id=str(i), reference_example_id=str(i), error=None, end_time=True,
        inputs={"bug_report": str(i)}, outputs={"answer": "resposta"},
    ) for i in range(2)]
    client.list_examples.return_value = examples
    client.list_runs.return_value = runs
    client.list_feedback.return_value = [SimpleNamespace(
        run_id=str(i), key=key, score=score, comment="justificativa",
    ) for i, score in enumerate((0.7, 1.0)) for key in export_evaluation.METRICS]
    monkeypatch.setattr(export_evaluation, "Client", lambda: client)
    return client


def test_report_distinguishes_averages_from_individual_scores(experiment, tmp_path):
    output = tmp_path / "report.json"
    export_evaluation.export_experiment("iteration-test", "commit", output)
    report = json.loads(output.read_text())
    assert report["scores"] == dict.fromkeys(export_evaluation.METRICS, 0.85)
    assert report["passed"] is True
    assert report["all_examples_passed"] is False
    assert report["example_count"] == 2


def test_incomplete_feedback_does_not_create_evidence(experiment, tmp_path):
    experiment.list_feedback.return_value.pop()
    output = tmp_path / "report.json"
    with pytest.raises(ValueError, match="cinco métricas"):
        export_evaluation.export_experiment("iteration-test", "commit", output)
    assert not output.exists()


def test_duplicate_example_does_not_create_evidence(experiment, tmp_path):
    experiment.list_runs.return_value[1].reference_example_id = "0"
    output = tmp_path / "report.json"
    with pytest.raises(ValueError, match="uma execução por exemplo"):
        export_evaluation.export_experiment("iteration-test", "commit", output)
    assert not output.exists()


def test_judge_options_preserve_formulas_and_restore_factory(monkeypatch):
    from src import run_iteration

    judge = Mock()
    judge.invoke.side_effect = [
        SimpleNamespace(text='{"precision": 0.9, "recall": 0.8, "reasoning": "ok"}'),
        SimpleNamespace(text='{"score": 0.86, "reasoning": "ok"}'),
        SimpleNamespace(text='{"score": 0.9, "reasoning": "ok"}'),
    ]
    model = Mock()
    model.bind.return_value = judge
    factory = Mock(return_value=model)
    monkeypatch.setattr(run_iteration.metrics, "get_evaluator_llm", factory)
    with run_iteration.configured_judge("high", True):
        results = run_iteration.evaluate.evaluate_all_metrics(
            {"bug_report": "bug"}, {"answer": "história"}, {"reference": "referência"},
        )
    scores = {item["key"]: item["score"] for item in results["results"]}
    assert scores == {
        "helpfulness": 0.88, "correctness": 0.8736,
        "f1_score": 0.8471, "clarity": 0.86, "precision": 0.9,
    }
    assert all(call.kwargs == {
        "reasoning_effort": "high", "response_format": {"type": "json_object"},
    } for call in model.bind.call_args_list)
    assert run_iteration.metrics.get_evaluator_llm is factory


def test_judge_factory_is_restored_after_failure(monkeypatch):
    from src import run_iteration

    factory = Mock()
    monkeypatch.setattr(run_iteration.metrics, "get_evaluator_llm", factory)
    with pytest.raises(RuntimeError):
        with run_iteration.configured_judge("high", True):
            raise RuntimeError("falha de API simulada")
    assert run_iteration.metrics.get_evaluator_llm is factory
