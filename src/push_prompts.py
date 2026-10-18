"""Valida, publica e confere a v2 pública no LangSmith Prompt Hub."""

import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client

if __package__:
    from .utils import check_env_vars, load_yaml, print_section_header
else:
    from utils import check_env_vars, load_yaml, print_section_header

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = PROJECT_ROOT / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_NAME = "bug_to_user_story_v2"


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """Confere o contrato do YAML e as variáveis antes de qualquer publicação."""
    errors = []
    if not isinstance(prompt_data, dict):
        return False, ["O conteúdo do prompt deve ser um objeto YAML."]
    for field in ("description", "system_prompt", "user_prompt", "version"):
        value = prompt_data.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} deve ser um texto não vazio.")
        elif "TODO" in value:
            errors.append(f"{field} contém TODO.")
    if prompt_data.get("version") != "v2":
        errors.append("A versão deve ser v2.")
    for field in ("tags", "techniques_applied"):
        values = prompt_data.get(field)
        if not isinstance(values, list) or not values or any(
            not isinstance(value, str) or not value.strip() for value in values
        ):
            errors.append(f"{field} deve ser uma lista de textos não vazios.")
        elif field == "techniques_applied" and len(set(values)) < 2:
            errors.append("Liste pelo menos duas técnicas distintas.")
    if errors:
        return False, errors
    try:
        template = ChatPromptTemplate.from_messages([
            ("system", prompt_data["system_prompt"]),
            ("human", prompt_data["user_prompt"]),
        ])
        if template.input_variables != ["bug_report"]:
            errors.append("O template deve ter somente a variável bug_report.")
        if "{bug_report}" not in prompt_data["user_prompt"]:
            errors.append("user_prompt deve conter {bug_report}.")
    except (ValueError, TypeError):
        errors.append("O template contém variáveis ou chaves inválidas.")
    return not errors, errors


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """Publica e relê o prompt para conferir visibilidade, mensagens e metadados."""
    valid, errors = validate_prompt(prompt_data)
    if not valid:
        for error in errors:
            print(f"❌ {error}")
        return False
    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", username) or prompt_name != PROMPT_NAME:
        print("❌ Informe somente o handle em USERNAME_LANGSMITH_HUB e use o nome da v2.")
        return False
    identifier = f"{username}/{prompt_name}"
    techniques = prompt_data["techniques_applied"]
    metadata = {"version": prompt_data["version"], "techniques_applied": techniques}
    template = ChatPromptTemplate.from_messages([
        ("system", prompt_data["system_prompt"]),
        ("human", prompt_data["user_prompt"]),
    ])
    template.metadata = metadata
    readme = (
        f"# {prompt_name}\n\n{prompt_data['description']}\n\n"
        f"Versão: {prompt_data['version']}\n\n"
        "## Técnicas aplicadas\n\n"
        + "\n".join(f"- {technique}" for technique in techniques)
        + "\n\nEntrada: `bug_report`. Saída: User Story em Markdown com critérios de aceitação."
    )
    try:
        client = Client()
        url = client.push_prompt(
            identifier,
            object=template,
            is_public=True,
            description=prompt_data["description"],
            tags=prompt_data["tags"],
            readme=readme,
        )
        published = client.get_prompt(identifier)
        if published is None or not published.is_public:
            raise ValueError("A publicação pública não foi confirmada.")
        if published.description != prompt_data["description"] or not set(
            prompt_data["tags"]
        ).issubset(published.tags or []):
            raise ValueError("Os metadados publicados diferem do YAML.")
        if published.readme != readme:
            raise ValueError("A documentação das técnicas não foi confirmada.")
        # Relê o commit específico para conferir exatamente o conteúdo publicado.
        remote = client.pull_prompt(
            f"{identifier}:{published.last_commit_hash}",
            include_model=False,
            skip_cache=True,
            dangerously_pull_public_prompt=True,
        )
        if not isinstance(remote, ChatPromptTemplate) or remote.messages != template.messages:
            raise ValueError("As mensagens publicadas diferem do YAML.")
        if any((remote.metadata or {}).get(key) != value for key, value in metadata.items()):
            raise ValueError("As técnicas e a versão do template não foram confirmadas.")
    except Exception as exc:
        print(f"❌ Falha na publicação ou conferência ({type(exc).__name__}).")
        print("Verifique credenciais, acesso ao workspace e rede. Uma publicação pode já ter ocorrido.")
        return False
    print(f"✅ Prompt público conferido: {identifier}")
    print(f"   URL: {url}")
    print(f"   Commit: {published.last_commit_hash}")
    return True


def main():
    """Lê o YAML e retorna zero somente após confirmar a publicação."""
    load_dotenv(PROJECT_ROOT / ".env")
    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1
    print_section_header("PUBLICAÇÃO DO PROMPT OTIMIZADO")
    prompts = load_yaml(str(PROMPT_PATH))
    if not isinstance(prompts, dict) or set(prompts) != {PROMPT_NAME}:
        print(f"❌ O YAML deve conter somente {PROMPT_NAME}.")
        return 1
    return 0 if push_prompt_to_langsmith(PROMPT_NAME, prompts[PROMPT_NAME]) else 1


if __name__ == "__main__":
    sys.exit(main())
