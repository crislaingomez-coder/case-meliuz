from __future__ import annotations

import json
import math
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd


EXPECTED_COLUMNS = {
    "data": "data",
    "grupos de usuarios": "grupo",
    "parceiro": "parceiro",
    "compradores": "compradores",
    "comissao": "comissao",
    "cashback": "cashback",
    "vendas totais": "vendas_totais",
}

MONEY_COLUMNS = ["comissao", "cashback", "vendas_totais"]


@dataclass
class AnalysisResult:
    dataset_path: Path
    test_name: str
    partner: str
    period: str
    decision_group: str
    decision: str
    result_summary: str
    quality_notes: list[str]
    metrics: pd.DataFrame
    daily_metrics: pd.DataFrame
    output_paths: dict[str, Path]


def analyze_dataset(
    dataset_path: str | Path,
    reports_dir: str | Path = "reports",
    summary_path: str | Path = "summary/acompanhamento_testes.csv",
) -> AnalysisResult:
    dataset_path = Path(dataset_path)
    reports_dir = Path(reports_dir)
    summary_path = Path(summary_path)
    reports_dir.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    raw = _read_csv(dataset_path)
    df, quality_notes = _clean_dataset(raw)
    daily_metrics = _build_daily_metrics(df)
    metrics = _build_group_metrics(daily_metrics)

    decision_group, decision, result_summary = _make_decision(metrics)
    partner = _single_value(df["parceiro"])
    period = f"{df['data'].min().date()} a {df['data'].max().date()}"
    test_name = f"Teste cashback - {partner}"

    slug = _slugify(dataset_path.stem)
    markdown_path = reports_dir / f"{slug}.md"
    json_path = reports_dir / f"{slug}_ai_context.json"

    markdown_path.write_text(
        _render_markdown_report(
            test_name=test_name,
            partner=partner,
            period=period,
            decision_group=decision_group,
            decision=decision,
            result_summary=result_summary,
            quality_notes=quality_notes,
            metrics=metrics,
        ),
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps(
            _build_ai_context(
                test_name=test_name,
                partner=partner,
                period=period,
                decision_group=decision_group,
                decision=decision,
                result_summary=result_summary,
                quality_notes=quality_notes,
                metrics=metrics,
            ),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    _upsert_summary(
        summary_path=summary_path,
        row={
            "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "nome_teste": test_name,
            "descricao": f"Teste A/B de cashback do {partner} no periodo de {period}.",
            "dataset": dataset_path.name,
            "parceiro": partner,
            "periodo": period,
            "variante_recomendada": decision_group,
            "resultado": result_summary,
            "decisao": decision,
            "relatorio": str(markdown_path),
        },
    )

    return AnalysisResult(
        dataset_path=dataset_path,
        test_name=test_name,
        partner=partner,
        period=period,
        decision_group=decision_group,
        decision=decision,
        result_summary=result_summary,
        quality_notes=quality_notes,
        metrics=metrics,
        daily_metrics=daily_metrics,
        output_paths={"report": markdown_path, "ai_context": json_path, "summary": summary_path},
    )


def _read_csv(path: Path) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "utf-8", "latin1"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)


def _clean_dataset(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    df = raw.copy()
    df.columns = [_normalize_text(col) for col in df.columns]

    missing = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Colunas obrigatorias ausentes: {missing}")

    df = df.rename(columns=EXPECTED_COLUMNS)
    df = df[list(EXPECTED_COLUMNS.values())]

    notes: list[str] = []
    before = len(df)
    duplicated = int(df.duplicated().sum())
    if duplicated:
        df = df.drop_duplicates()
        notes.append(f"{duplicated} linha(s) duplicada(s) removida(s).")

    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df["compradores"] = pd.to_numeric(df["compradores"], errors="coerce")
    for col in MONEY_COLUMNS:
        df[col] = df[col].map(_parse_money)

    null_counts = df.isna().sum()
    null_notes = [f"{col}: {int(count)}" for col, count in null_counts.items() if count > 0]
    if null_notes:
        notes.append("Valores invalidos/nulos encontrados - " + "; ".join(null_notes))
        df = df.dropna()

    if len(df) < before:
        notes.append(f"Base passou de {before} para {len(df)} linhas apos limpeza.")
    else:
        notes.append("Nenhuma perda de linha apos validacao de tipos e nulos.")

    if (df[["compradores", *MONEY_COLUMNS]] < 0).any().any():
        raise ValueError("Foram encontrados valores negativos em metricas de negocio.")

    return df, notes


def _build_daily_metrics(df: pd.DataFrame) -> pd.DataFrame:
    daily = df.copy()
    daily["lucro_liquido"] = daily["comissao"] - daily["cashback"]
    daily["margem_gmv"] = _safe_divide(daily["lucro_liquido"], daily["vendas_totais"])
    daily["roi_cashback"] = _safe_divide(daily["lucro_liquido"], daily["cashback"])
    daily["ticket_medio"] = _safe_divide(daily["vendas_totais"], daily["compradores"])
    daily["cashback_por_comprador"] = _safe_divide(daily["cashback"], daily["compradores"])
    return daily


def _build_group_metrics(daily: pd.DataFrame) -> pd.DataFrame:
    rows = []
    baseline_group = sorted(daily["grupo"].unique())[0]
    baseline = daily[daily["grupo"] == baseline_group]
    baseline_profit_day = baseline["lucro_liquido"].mean()
    baseline_gmv_day = baseline["vendas_totais"].mean()

    for group, group_df in daily.groupby("grupo", sort=True):
        lucro_total = group_df["lucro_liquido"].sum()
        gmv_total = group_df["vendas_totais"].sum()
        cashback_total = group_df["cashback"].sum()
        comissao_total = group_df["comissao"].sum()
        compradores_total = group_df["compradores"].sum()
        avg_profit_day = group_df["lucro_liquido"].mean()
        avg_gmv_day = group_df["vendas_totais"].mean()
        std_profit_day = group_df["lucro_liquido"].std(ddof=1)
        n_days = len(group_df)
        ci95 = 1.96 * std_profit_day / math.sqrt(n_days) if n_days > 1 else 0

        rows.append(
            {
                "grupo": group,
                "dias": n_days,
                "compradores": compradores_total,
                "gmv_total": gmv_total,
                "comissao_total": comissao_total,
                "cashback_total": cashback_total,
                "lucro_liquido_total": lucro_total,
                "lucro_liquido_medio_dia": avg_profit_day,
                "ic95_lucro_dia": ci95,
                "margem_sobre_gmv": _scalar_divide(lucro_total, gmv_total),
                "roi_cashback": _scalar_divide(lucro_total, cashback_total),
                "ticket_medio": _scalar_divide(gmv_total, compradores_total),
                "cashback_por_comprador": _scalar_divide(cashback_total, compradores_total),
                "uplift_lucro_vs_baseline": _scalar_divide(avg_profit_day - baseline_profit_day, baseline_profit_day),
                "uplift_gmv_vs_baseline": _scalar_divide(avg_gmv_day - baseline_gmv_day, baseline_gmv_day),
            }
        )

    metrics = pd.DataFrame(rows)
    metrics["ranking_lucro"] = metrics["lucro_liquido_total"].rank(ascending=False, method="min").astype(int)
    metrics["ranking_roi"] = metrics["roi_cashback"].rank(ascending=False, method="min").astype(int)
    return metrics.sort_values(["ranking_lucro", "ranking_roi", "grupo"]).reset_index(drop=True)


def _make_decision(metrics: pd.DataFrame) -> tuple[str, str, str]:
    winner = metrics.iloc[0]
    runner_up = metrics.iloc[1] if len(metrics) > 1 else None
    winner_group = str(winner["grupo"])

    if runner_up is not None:
        profit_gap = winner["lucro_liquido_total"] - runner_up["lucro_liquido_total"]
        if abs(runner_up["lucro_liquido_total"]) > 0:
            gap_label = _pct(_scalar_divide(profit_gap, abs(runner_up["lucro_liquido_total"])))
        else:
            gap_label = "sem base percentual positiva"
    else:
        profit_gap = winner["lucro_liquido_total"]
        gap_label = "sem comparativo"

    if winner["lucro_liquido_total"] <= 0:
        decision = (
            f"Nao escalar automaticamente. {winner_group} foi o melhor grupo relativo, "
            "mas o teste nao gerou lucro liquido positivo."
        )
    else:
        decision = (
            f"Escalar {winner_group} para 100% do trafego, mantendo monitoramento de margem "
            "e cashback pago nos primeiros dias."
        )

    result_summary = (
        f"{winner_group} liderou em lucro liquido total ({_brl(winner['lucro_liquido_total'])}), "
        f"com margem sobre GMV de {_pct(winner['margem_sobre_gmv'])} e ROI de cashback de "
        f"{_pct(winner['roi_cashback'])}. A diferenca para o segundo colocado foi de "
        f"{_brl(profit_gap)} ({gap_label})."
    )
    return winner_group, decision, result_summary


def _render_markdown_report(
    test_name: str,
    partner: str,
    period: str,
    decision_group: str,
    decision: str,
    result_summary: str,
    quality_notes: list[str],
    metrics: pd.DataFrame,
) -> str:
    view = metrics.copy()
    money_cols = [
        "gmv_total",
        "comissao_total",
        "cashback_total",
        "lucro_liquido_total",
        "lucro_liquido_medio_dia",
        "ticket_medio",
        "cashback_por_comprador",
    ]
    pct_cols = ["margem_sobre_gmv", "roi_cashback", "uplift_lucro_vs_baseline", "uplift_gmv_vs_baseline"]
    for col in money_cols:
        view[col] = view[col].map(_brl)
    for col in pct_cols:
        view[col] = view[col].map(_pct)

    table_cols = [
        "grupo",
        "dias",
        "compradores",
        "gmv_total",
        "cashback_total",
        "lucro_liquido_total",
        "margem_sobre_gmv",
        "roi_cashback",
        "uplift_lucro_vs_baseline",
        "uplift_gmv_vs_baseline",
    ]
    quality = "\n".join([f"- {note}" for note in quality_notes])

    table = _markdown_table(view[table_cols])

    return f"""# {test_name}

## Resumo executivo

Parceiro: **{partner}**

Periodo analisado: **{period}**

Variante recomendada: **{decision_group}**

Decisao: **{decision}**

{result_summary}

## Tabela comparativa

{table}

## Leitura de negocio

A recomendacao prioriza lucro liquido absoluto, porque o objetivo do teste de cashback nao e apenas aumentar GMV, mas encontrar a alavanca com melhor retorno economico para escalar. GMV, margem e ROI de cashback entram como criterios de validacao para evitar escolher uma variante que venda mais, mas destrua margem.

## Qualidade dos dados

{quality}

## Limitacoes

- O dataset nao informa usuarios expostos por grupo. Por isso, a analise nao calcula taxa de conversao real nem significancia sobre conversao.
- A comparacao estatistica usa variacao diaria de lucro/GMV como sinal de estabilidade, mas a decisao final deve ser monitorada apos o rollout.
- Caso novos datasets tragam centavos, o parser de moeda ja trata virgula decimal e separador de milhar.
"""


def _build_ai_context(
    test_name: str,
    partner: str,
    period: str,
    decision_group: str,
    decision: str,
    result_summary: str,
    quality_notes: list[str],
    metrics: pd.DataFrame,
) -> dict:
    return {
        "test_name": test_name,
        "partner": partner,
        "period": period,
        "recommended_variant": decision_group,
        "decision": decision,
        "result_summary": result_summary,
        "quality_notes": quality_notes,
        "metrics": metrics.to_dict(orient="records"),
        "instruction_for_ai": (
            "Use estes indicadores para revisar a recomendacao executiva. "
            "Nao invente metricas ausentes; mencione explicitamente a limitacao de nao haver usuarios expostos."
        ),
    }


def _upsert_summary(summary_path: Path, row: dict[str, str]) -> None:
    columns = [
        "data_registro",
        "nome_teste",
        "descricao",
        "dataset",
        "parceiro",
        "periodo",
        "variante_recomendada",
        "resultado",
        "decisao",
        "relatorio",
    ]
    if summary_path.exists():
        summary = pd.read_csv(summary_path)
        summary = summary[summary["nome_teste"] != row["nome_teste"]]
        summary = pd.concat([summary, pd.DataFrame([row])], ignore_index=True)
    else:
        summary = pd.DataFrame([row])
    for column in columns:
        if column not in summary.columns:
            summary[column] = ""
    summary = summary[columns]
    summary = summary.sort_values(["parceiro", "nome_teste"])
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")


def _markdown_table(df: pd.DataFrame) -> str:
    headers = [str(col) for col in df.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in df.iterrows():
        values = [str(row[col]) for col in df.columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def _normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value))
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"\s+", " ", value.strip().lower())
    return value


def _parse_money(value) -> float:
    if pd.isna(value):
        return float("nan")
    text = str(value).strip()
    text = text.replace("R$", "").replace(" ", "")
    text = re.sub(r"[^0-9,.-]", "", text)
    if not text:
        return float("nan")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    else:
        text = text.replace(".", "")
    return float(text)


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator.divide(denominator.replace({0: pd.NA})).fillna(0)


def _scalar_divide(numerator: float, denominator: float) -> float:
    if denominator == 0 or pd.isna(denominator):
        return 0.0
    return float(numerator / denominator)


def _single_value(series: pd.Series) -> str:
    values = sorted(series.dropna().unique())
    if len(values) != 1:
        return ", ".join(map(str, values))
    return str(values[0])


def _slugify(value: str) -> str:
    value = _normalize_text(value).replace(" ", "_")
    return re.sub(r"[^a-z0-9_=-]", "", value)


def _brl(value: float) -> str:
    return "R$ " + f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%".replace(".", ",")
