"""Testes da publicação, sem chamadas externas ou alterações no Hub."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import yaml

from src import push_prompts


@pytest.fixture
def data():
    return yaml.safe_load(push_prompts.PROMPT_PATH.read_text())[push_prompts.PROMPT_NAME]


@pytest.fixture
def hub(monkeypatch):
    client = Mock()
    monkeypatch.setenv("USERNAME_LANGSMITH_HUB", "lailson")
    monkeypatch.setattr(push_prompts, "Client", lambda: client)

    def publish(identifier, **kwargs):
        client.get_prompt.return_value = SimpleNamespace(
            is_public=True, description=kwargs["description"], tags=kwargs["tags"],
            readme=kwargs["readme"], last_commit_hash="abc123",
        )
        client.pull_prompt.return_value = deepcopy(kwargs["object"])
        return f"https://smith.langchain.com/hub/{identifier}"

    client.push_prompt.side_effect = publish
    return client


def test_publication_preserves_content_metadata_and_checks_commit(data, hub):
    assert push_prompts.push_prompt_to_langsmith(push_prompts.PROMPT_NAME, data)
    args, kwargs = hub.push_prompt.call_args
    assert args == ("lailson/bug_to_user_story_v2",)
    assert kwargs["is_public"] is True
    assert kwargs["object"].metadata["techniques_applied"] == data["techniques_applied"]
    assert kwargs["object"].messages[0].prompt.template == data["system_prompt"]
    assert kwargs["object"].messages[1].prompt.template == data["user_prompt"]
    hub.pull_prompt.assert_called_once_with(
        "lailson/bug_to_user_story_v2:abc123", include_model=False,
        skip_cache=True, dangerously_pull_public_prompt=True,
    )


@pytest.mark.parametrize("field,value", [
    ("system_prompt", ""), ("user_prompt", "{unexpected}"),
    ("version", "v1"), ("tags", "tag"),
    ("techniques_applied", ["Role Prompting", "Role Prompting"]),
])
def test_invalid_yaml_does_not_publish(data, hub, field, value):
    data[field] = value
    assert not push_prompts.push_prompt_to_langsmith(push_prompts.PROMPT_NAME, data)
    hub.push_prompt.assert_not_called()


def test_private_prompt_fails_verification(data, hub):
    original = hub.push_prompt.side_effect

    def publish(*args, **kwargs):
        url = original(*args, **kwargs)
        hub.get_prompt.return_value.is_public = False
        return url

    hub.push_prompt.side_effect = publish
    assert not push_prompts.push_prompt_to_langsmith(push_prompts.PROMPT_NAME, data)


def test_different_remote_content_fails_verification(data, hub):
    from langchain_core.prompts import ChatPromptTemplate

    hub.pull_prompt.side_effect = lambda *args, **kwargs: ChatPromptTemplate.from_messages([
        ("system", "Conteúdo diferente"), ("human", "{bug_report}"),
    ])
    assert not push_prompts.push_prompt_to_langsmith(push_prompts.PROMPT_NAME, data)


def test_api_failure_does_not_print_response(data, hub, capsys):
    hub.push_prompt.side_effect = RuntimeError("sensitive-response")
    assert not push_prompts.push_prompt_to_langsmith(push_prompts.PROMPT_NAME, data)
    assert "sensitive-response" not in capsys.readouterr().out


def test_handle_must_not_include_prompt_name(data, hub, monkeypatch):
    monkeypatch.setenv("USERNAME_LANGSMITH_HUB", "lailson/exampleprompt")
    assert not push_prompts.push_prompt_to_langsmith(push_prompts.PROMPT_NAME, data)
    hub.push_prompt.assert_not_called()
