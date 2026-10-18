"""Valida o prompt v2 local, sem chamadas à OpenAI ou ao LangSmith."""

import re
from pathlib import Path

import pytest
import yaml

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "bug_to_user_story_v2.yml"


@pytest.fixture(scope="module")
def prompt():
    """Lê o artefato entregue, independentemente do diretório de execução."""
    document = yaml.safe_load(PROMPT_PATH.read_text(encoding="utf-8"))
    assert isinstance(document, dict), "O YAML deve conter um objeto de prompts."
    assert "bug_to_user_story_v2" in document, "O YAML deve conter a versão v2."
    data = document["bug_to_user_story_v2"]
    assert isinstance(data, dict), "Os campos do prompt v2 devem formar um objeto."
    return data


def system_text(prompt):
    """Evita que campos ausentes ou de tipo inválido produzam erros obscuros."""
    text = prompt.get("system_prompt")
    assert isinstance(text, str) and text.strip(), "system_prompt deve ser texto não vazio."
    return text


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        system_text(prompt)

    def test_prompt_has_role_definition(self, prompt):
        """Confere a atribuição explícita da persona usada neste projeto."""
        assert re.search(
            r"\bvocê\s+é\s+(?:um|uma)\s+product\s+manager\b",
            system_text(prompt),
            re.IGNORECASE,
        ), "O system_prompt deve atribuir explicitamente a persona de Product Manager."

    def test_prompt_mentions_format(self, prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        # Os exemplos não substituem uma instrução de formato para a resposta.
        instructions = re.split(
            r"(?m)^\s*Exemplo\s+\d+\s*[—:\-]", system_text(prompt), maxsplit=1
        )[0]
        markdown = re.search(r"\b(?:usando|em|formato)\s+Markdown\b", instructions, re.IGNORECASE)
        user_story = re.search(
            r"Como\s+\[[^\]]+\].*?eu quero\s+\[[^\]]+\].*?para que\s+\[[^\]]+\]",
            instructions,
            re.IGNORECASE | re.DOTALL,
        )
        assert markdown or user_story, "Instrua o uso de Markdown ou do formato padrão de User Story."

    def test_prompt_has_few_shot_examples(self, prompt):
        """Exige pelo menos dois exemplos completos, além do rótulo da técnica."""
        examples = re.split(r"(?m)^\s*Exemplo\s+\d+\s*[—:\-][^\n]*\n", system_text(prompt))[1:]
        assert len(examples) >= 2, "Few-shot requer pelo menos dois exemplos de entrada e saída."
        for number, example in enumerate(examples, start=1):
            pair = re.search(
                r"(?ms)^Entrada:\s*\n(?P<input>.*?)^Saída:\s*\n(?P<output>.+)", example
            )
            assert pair, f"Exemplo {number}: faltam os blocos Entrada e Saída, nessa ordem."
            assert pair["input"].strip(), f"Exemplo {number}: a entrada está vazia."
            output = pair["output"].strip()
            assert re.search(r"(?m)^## User Story\s*$", output), f"Exemplo {number}: falta a User Story."
            assert re.search(r"(?m)^Como\s+.+", output), f"Exemplo {number}: falta o conteúdo da User Story."
            assert re.search(r"(?m)^## Critérios de Aceitação\s*$", output), f"Exemplo {number}: faltam critérios."
            assert all(word in output for word in ("Dado que", "Quando", "Então")), (
                f"Exemplo {number}: os critérios devem demonstrar contexto, ação e resultado."
            )

    def test_prompt_no_todos(self, prompt):
        """Procura placeholders no texto e nos metadados, inclusive campos aninhados."""
        serialized = yaml.safe_dump(prompt, allow_unicode=True)
        assert not re.search(r"\bTODO\b", serialized), "Remova os TODOs do prompt e dos metadados."

    def test_minimum_techniques(self, prompt):
        """Exige duas técnicas distintas, sem contar nomes vazios ou repetidos."""
        techniques = prompt.get("techniques_applied")
        assert isinstance(techniques, list), "techniques_applied deve ser uma lista."
        assert all(isinstance(item, str) and item.strip() for item in techniques), (
            "Cada técnica deve ter um nome textual não vazio."
        )
        distinct = {item.strip().casefold() for item in techniques}
        assert len(distinct) >= 2, "Liste pelo menos duas técnicas distintas em techniques_applied."


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v", "--tb=short"]))
