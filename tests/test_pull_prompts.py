"""Testes do download, independentes da API e dos testes de otimização da fase 5."""

from unittest.mock import Mock

import pytest
import yaml
from langchain_core.prompts import ChatPromptTemplate

from src import pull_prompts


@pytest.fixture
def hub(monkeypatch, tmp_path):
    client = Mock()
    client.pull_prompt.return_value = ChatPromptTemplate.from_messages([
        ("system", "Analise o relato: {bug_report}"),
        ("human", "{bug_report}"),
    ])
    client.pull_prompt.return_value.metadata = {"lc_hub_commit_hash": "abc123"}
    monkeypatch.setattr(pull_prompts, "Client", lambda: client)
    monkeypatch.setattr(pull_prompts, "OUTPUT_PATH", tmp_path / "prompts" / "v1.yml")
    return client


def test_pull_preserves_templates_and_provenance(hub):
    output = pull_prompts.pull_prompts_from_langsmith()
    data = yaml.safe_load(output.read_text())["bug_to_user_story_v1"]
    assert data["system_prompt"] == "Analise o relato: {bug_report}"
    assert data["user_prompt"] == "{bug_report}"
    assert data["source_commit"] == "abc123"
    hub.pull_prompt.assert_called_once_with(
        "leonanluppi/bug_to_user_story_v1",
        include_model=False,
        dangerously_pull_public_prompt=True,
    )


def test_unsupported_messages_do_not_overwrite_file(hub):
    output = pull_prompts.OUTPUT_PATH
    output.parent.mkdir()
    output.write_text("original")
    hub.pull_prompt.return_value = ChatPromptTemplate.from_messages([
        ("system", "Instrução"), ("human", "Entrada"), ("ai", "Exemplo"),
    ])
    with pytest.raises(ValueError):
        pull_prompts.pull_prompts_from_langsmith()
    assert output.read_text() == "original"


def test_write_failure_is_reported(hub, monkeypatch):
    monkeypatch.setattr(pull_prompts, "save_yaml", lambda *args: False)
    with pytest.raises(OSError):
        pull_prompts.pull_prompts_from_langsmith()


def test_missing_credentials_skip_network(hub, monkeypatch):
    monkeypatch.setattr(pull_prompts, "load_dotenv", lambda *args: None)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    assert pull_prompts.main() == 1
    hub.pull_prompt.assert_not_called()


def test_api_failure_returns_nonzero_without_leaking_details(hub, monkeypatch, capsys):
    monkeypatch.setenv("LANGSMITH_API_KEY", "test-key")
    hub.pull_prompt.side_effect = RuntimeError("sensitive-server-response")
    assert pull_prompts.main() == 1
    assert "sensitive-server-response" not in capsys.readouterr().out
