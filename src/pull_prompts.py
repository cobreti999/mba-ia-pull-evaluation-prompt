"""Baixa o prompt semente do desafio e preserva seu conteúdo em YAML."""

import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langsmith import Client

if __package__:
    from .utils import check_env_vars, print_section_header, save_yaml
else:
    from utils import check_env_vars, print_section_header, save_yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPT_ID = "leonanluppi/bug_to_user_story_v1"
OUTPUT_PATH = PROJECT_ROOT / "prompts" / "bug_to_user_story_v1.yml"


def pull_prompts_from_langsmith():
    """Faz pull e salva a v1, sem otimizar ou interpolar suas variáveis."""
    client = Client()
    prompt = client.pull_prompt(
        PROMPT_ID,
        include_model=False,
        dangerously_pull_public_prompt=True,
    )

    # O YAML do projeto representa exatamente uma mensagem system e uma user.
    # Rejeitamos outros formatos para não perder mensagens silenciosamente.
    if not isinstance(prompt, ChatPromptTemplate) or len(prompt.messages) != 2:
        raise ValueError("O prompt semente deve conter uma mensagem system e uma user.")
    system, user = prompt.messages
    if not isinstance(system, SystemMessagePromptTemplate) or not isinstance(
        user, HumanMessagePromptTemplate
    ):
        raise ValueError("Esperadas mensagens de texto na ordem system, user.")
    for message in (system, user):
        if not hasattr(message.prompt, "template") or message.prompt.template_format != "f-string":
            raise ValueError("O YAML do projeto exige templates de texto no formato f-string.")
        if message.prompt.partial_variables:
            raise ValueError("O YAML do projeto não representa variáveis pré-preenchidas.")
        if not message.prompt.template.strip():
            raise ValueError("O prompt recebido contém uma mensagem vazia.")
    if prompt.partial_variables:
        raise ValueError("O YAML do projeto não representa variáveis pré-preenchidas.")

    data = {
        "bug_to_user_story_v1": {
            "description": "Prompt para converter relatos de bugs em User Stories",
            "system_prompt": system.prompt.template,
            "user_prompt": user.prompt.template,
            "version": "v1",
            "source": PROMPT_ID,
            "source_commit": (prompt.metadata or {}).get("lc_hub_commit_hash"),
            "tags": ["bug-analysis", "user-story", "product-management"],
        }
    }
    if not save_yaml(data, str(OUTPUT_PATH)):
        raise OSError("Não foi possível salvar o prompt localmente.")
    return OUTPUT_PATH


def main():
    """Retorna zero somente quando o download e a gravação terminam."""
    load_dotenv(PROJECT_ROOT / ".env")
    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1
    print_section_header(f"Pull do prompt: {PROMPT_ID}")
    try:
        output = pull_prompts_from_langsmith()
    except Exception as exc:
        # Evita imprimir respostas de servidores ou dados de credenciais.
        print(f"❌ Falha no pull ({type(exc).__name__}). Verifique credenciais, rede e formato do prompt.")
        return 1
    print(f"✅ Prompt salvo em: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
