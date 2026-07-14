from __future__ import annotations

import argparse
from pathlib import Path

from codigo.analisador import analyze_dataset
from codigo.painel import build_dashboard


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analisa testes A/B de cashback e gera relatorios executivos."
    )
    parser.add_argument(
        "dataset",
        nargs="?",
        help="Caminho do CSV a ser analisado. Use --todos para processar todos em dados/.",
    )
    parser.add_argument(
        "--todos",
        action="store_true",
        help="Processa todos os arquivos CSV da pasta dados/.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Alias de compatibilidade para --todos.",
    )
    parser.add_argument(
        "--pasta-relatorios",
        default="relatorios",
        help="Pasta onde os relatorios Markdown e contextos de IA serao salvos.",
    )
    parser.add_argument(
        "--resumo",
        default="resumo/acompanhamento_testes.csv",
        help="CSV consolidado no formato da planilha de acompanhamento.",
    )
    parser.add_argument(
        "--painel",
        default="saidas/painel_meliuz.xlsx",
        help="Arquivo Excel visual com KPIs e graficos.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.todos or args.all:
        dataset_paths = sorted(Path("dados").glob("*.csv"))
        if not dataset_paths:
            raise SystemExit("Nenhum CSV encontrado em dados/.")
    elif args.dataset:
        dataset_paths = [Path(args.dataset)]
    else:
        raise SystemExit("Informe um dataset ou use --all.")

    results = []
    for dataset_path in dataset_paths:
        result = analyze_dataset(
            dataset_path=dataset_path,
            reports_dir=args.pasta_relatorios,
            summary_path=args.resumo,
        )
        results.append(result)
        print(f"OK: {result.test_name}")
        print(f"  Recomendacao: {result.decision}")
        print(f"  Relatorio: {result.output_paths['report']}")
        print(f"  Planilha CSV: {result.output_paths['summary']}")

    dashboard_path = build_dashboard(results, args.painel)
    print(f"  Painel visual: {dashboard_path}")


if __name__ == "__main__":
    main()
