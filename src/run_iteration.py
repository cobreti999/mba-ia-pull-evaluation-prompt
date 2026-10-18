"""Executa uma iteração usando os geradores e avaliadores originais do desafio."""

import argparse
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client

# Os módulos fornecidos usam imports relativos ao diretório src.
if __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluate
import metrics
from export_evaluation import IncompleteExperimentError, export_experiment



@contextmanager
def configured_judge(reasoning_effort=None, json_mode=False):
    """Configura o cliente dos juízes e restaura a fábrica ao terminar a avaliação."""
    original_factory = metrics.get_evaluator_llm
    options = {}
    if reasoning_effort:
        options["reasoning_effort"] = reasoning_effort
    if json_mode:
        options["response_format"] = {"type": "json_object"}
    if options:
        metrics.get_evaluator_llm = lambda: original_factory().bind(**options)
    try:
        yield
    finally:
        metrics.get_evaluator_llm = original_factory


def main():
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("iteration", help="Identificador da iteração, por exemplo 02")
    parser.add_argument("--concurrency", type=int, default=3)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--reasoning-effort", choices=("minimal", "low", "medium", "high"))
    parser.add_argument("--judge-reasoning-effort", choices=("minimal", "low", "medium", "high"))
    parser.add_argument("--verbosity", choices=("low", "medium", "high"))
    parser.add_argument("--judge-json", action="store_true", help="Exige JSON válido na resposta do juiz OpenAI")
    args = parser.parse_args()
    if args.concurrency < 1:
        parser.error("--concurrency deve ser positivo")
    if (args.reasoning_effort or args.judge_reasoning_effort or args.judge_json or args.verbosity) and os.environ['LLM_PROVIDER'] != 'openai':
        parser.error("As opções de raciocínio e JSON exigem o provider openai")
    client = Client()
    dataset_name = f"{os.environ['LANGSMITH_PROJECT']}-eval"
    identifier = f"{os.environ['USERNAME_LANGSMITH_HUB']}/bug_to_user_story_v2"
    published = client.get_prompt(identifier)
    if published is None or not published.last_commit_hash:
        raise ValueError("Publique a v2 antes de avaliar.")
    commit = published.last_commit_hash
    template = evaluate.pull_prompt_from_langsmith(client, f"{identifier}:{commit}")
    llm = evaluate.get_llm()
    if args.reasoning_effort:
        llm = llm.bind(reasoning_effort=args.reasoning_effort)
    if args.verbosity:
        llm = llm.bind(verbosity=args.verbosity)
    with configured_judge(args.judge_reasoning_effort, args.judge_json):
        results = client.evaluate(
            evaluate.build_target(template, llm),
            data=dataset_name,
            evaluators=[evaluate.evaluate_all_metrics],
            experiment_prefix=f"{identifier.replace('/', '-')}-iteration-{args.iteration}",
            max_concurrency=args.concurrency,
            metadata={
                "prompt": identifier, "prompt_commit": commit, "iteration": args.iteration,
                "llm_model": os.environ['LLM_MODEL'], "eval_model": os.environ['EVAL_MODEL'],
                "provider": os.environ['LLM_PROVIDER'],
                "generation_reasoning_effort": args.reasoning_effort or "provider_default",
                "judge_reasoning_effort": args.judge_reasoning_effort or "provider_default",
                "judge_json_mode": args.judge_json,
                "generation_verbosity": args.verbosity or "provider_default",
            },
        )
        # Consumir os resultados garante que geração e avaliação terminaram.
        for index, _ in enumerate(results, 1):
            print(f"Exemplo {index} avaliado.", flush=True)
    print(f"Experimento: {results.experiment_name}", flush=True)
    print(f"URL: {results.url}", flush=True)
    client.flush()
    for attempt in range(4):
        try:
            report = export_experiment(results.experiment_name, commit, args.output)
            return 0 if report["passed"] else 1
        except IncompleteExperimentError:
            if attempt == 3:
                print("Avaliação concluída; notas ainda em propagação. Reexecute somente export_evaluation.py.")
                return 1
            print("Aguardando propagação das notas no LangSmith...", flush=True)
            time.sleep(10)
    return 0


if __name__ == "__main__":
    sys.exit(main())
