from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from codigo.analisador import AnalysisResult


AZUL_ESCURO = "17365D"
AZUL = "4472C4"
VERDE = "70AD47"
VERDE_ESCURO = "548235"
CINZA_FUNDO = "F7F9FC"
CINZA_BORDA = "D9E2F3"
CINZA_TEXTO = "44546A"
BRANCO = "FFFFFF"
AMARELO_CLARO = "FFF2CC"
VERDE_CLARO = "E2F0D9"
AZUL_CLARO = "D9EAF7"


def build_dashboard(results: list[AnalysisResult], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "Resumo Executivo"

    _build_summary_sheet(ws, results)

    for result in results:
        _build_partner_sheet(wb, result)

    wb.save(output_path)
    return output_path


def _build_summary_sheet(ws, results: list[AnalysisResult]) -> None:
    _prepare_sheet(ws)
    _title(ws, "Dashboard de Testes A/B de Cashback", "A1:H1")

    total_tests = len(results)
    total_profit = sum(
        float(result.metrics[result.metrics["grupo"] == result.decision_group].iloc[0]["lucro_liquido_total"])
        for result in results
    )
    avg_margin = sum(
        float(result.metrics[result.metrics["grupo"] == result.decision_group].iloc[0]["margem_sobre_gmv"])
        for result in results
    ) / total_tests
    avg_roi = sum(
        float(result.metrics[result.metrics["grupo"] == result.decision_group].iloc[0]["roi_cashback"])
        for result in results
    ) / total_tests

    _kpi_card(ws, "A3:B5", "Testes analisados", total_tests, "inteiro", AZUL_CLARO)
    _kpi_card(ws, "C3:D5", "Lucro vencedor total", total_profit, "moeda", VERDE_CLARO)
    _kpi_card(ws, "E3:F5", "Margem media", avg_margin, "percentual", AMARELO_CLARO)
    _kpi_card(ws, "G3:H5", "ROI medio", avg_roi, "percentual", AZUL_CLARO)

    headers = [
        "Parceiro",
        "Periodo",
        "Variante",
        "Lucro vencedor",
        "Margem",
        "ROI cashback",
        "Decisao",
    ]
    start_row = 8
    _write_header(ws, start_row, headers)

    for row_idx, result in enumerate(results, start=start_row + 1):
        winner = result.metrics[result.metrics["grupo"] == result.decision_group].iloc[0]
        values = [
            result.partner,
            result.period,
            result.decision_group,
            float(winner["lucro_liquido_total"]),
            float(winner["margem_sobre_gmv"]),
            float(winner["roi_cashback"]),
            result.decision,
        ]
        for col_idx, value in enumerate(values, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            _body_cell(cell)

    for row in range(start_row + 1, start_row + 1 + len(results)):
        ws.cell(row=row, column=4).number_format = 'R$ #,##0.00'
        ws.cell(row=row, column=5).number_format = '0.00%'
        ws.cell(row=row, column=6).number_format = '0.00%'
        ws.row_dimensions[row].height = 42

    _summary_charts(ws, start_row, len(results))
    _set_widths(ws, {"A": 18, "B": 24, "C": 14, "D": 18, "E": 14, "F": 14, "G": 44, "H": 14})
    ws.freeze_panes = "A8"


def _summary_charts(ws, start_row: int, row_count: int) -> None:
    max_row = start_row + row_count

    profit_chart = BarChart()
    profit_chart.title = "Lucro da variante recomendada"
    profit_chart.y_axis.title = "Lucro liquido"
    profit_chart.x_axis.title = ""
    profit_chart.legend = None
    profit_chart.style = 10
    profit_chart.height = 9
    profit_chart.width = 15
    profit_chart.add_data(Reference(ws, min_col=4, min_row=start_row, max_row=max_row), titles_from_data=True)
    profit_chart.set_categories(Reference(ws, min_col=1, min_row=start_row + 1, max_row=max_row))
    ws.add_chart(profit_chart, "A15")

    roi_chart = BarChart()
    roi_chart.title = "ROI de cashback da variante recomendada"
    roi_chart.y_axis.title = "ROI"
    roi_chart.x_axis.title = ""
    roi_chart.legend = None
    roi_chart.style = 13
    roi_chart.height = 9
    roi_chart.width = 15
    roi_chart.add_data(Reference(ws, min_col=6, min_row=start_row, max_row=max_row), titles_from_data=True)
    roi_chart.set_categories(Reference(ws, min_col=1, min_row=start_row + 1, max_row=max_row))
    ws.add_chart(roi_chart, "E15")


def _build_partner_sheet(wb: Workbook, result: AnalysisResult) -> None:
    ws = wb.create_sheet(result.partner.replace("Parceiro ", "Parceiro_")[:31])
    _prepare_sheet(ws)
    _title(ws, result.test_name, "A1:J1")

    winner = result.metrics[result.metrics["grupo"] == result.decision_group].iloc[0]
    _kpi_card(ws, "A3:B5", "Variante recomendada", result.decision_group, "texto", VERDE_CLARO)
    _kpi_card(ws, "C3:D5", "Lucro liquido", float(winner["lucro_liquido_total"]), "moeda", VERDE_CLARO)
    _kpi_card(ws, "E3:F5", "Margem GMV", float(winner["margem_sobre_gmv"]), "percentual", AMARELO_CLARO)
    _kpi_card(ws, "G3:H5", "ROI cashback", float(winner["roi_cashback"]), "percentual", AZUL_CLARO)

    ws["A7"] = "Decisao"
    ws["A7"].font = Font(bold=True, color=AZUL_ESCURO)
    ws["B7"] = result.decision
    ws["B7"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("B7:J8")
    _fill_range(ws, "A7:J8", BRANCO)

    metrics = result.metrics.sort_values("grupo").reset_index(drop=True)
    table_start = 11
    headers = [
        "Grupo",
        "Compradores",
        "GMV",
        "Cashback",
        "Lucro liquido",
        "Margem",
        "ROI",
        "Ticket medio",
    ]
    _write_header(ws, table_start, headers)

    for idx, row in metrics.iterrows():
        excel_row = table_start + 1 + idx
        values = [
            row["grupo"],
            int(row["compradores"]),
            float(row["gmv_total"]),
            float(row["cashback_total"]),
            float(row["lucro_liquido_total"]),
            float(row["margem_sobre_gmv"]),
            float(row["roi_cashback"]),
            float(row["ticket_medio"]),
        ]
        for col_idx, value in enumerate(values, start=1):
            cell = ws.cell(row=excel_row, column=col_idx, value=value)
            _body_cell(cell)
        if row["grupo"] == result.decision_group:
            _fill_row(ws, excel_row, 1, len(headers), VERDE_CLARO)

    for row in range(table_start + 1, table_start + 1 + len(metrics)):
        for col in [3, 4, 5, 8]:
            ws.cell(row=row, column=col).number_format = 'R$ #,##0.00'
        for col in [6, 7]:
            ws.cell(row=row, column=col).number_format = '0.00%'

    _partner_charts(ws, table_start, len(metrics))
    _daily_audit_table(ws, result)
    _set_widths(
        ws,
        {"A": 16, "B": 14, "C": 15, "D": 15, "E": 16, "F": 12, "G": 12, "H": 15, "I": 4, "J": 4},
    )
    ws.freeze_panes = "A11"


def _partner_charts(ws, table_start: int, row_count: int) -> None:
    max_row = table_start + row_count
    categories = Reference(ws, min_col=1, min_row=table_start + 1, max_row=max_row)

    profit_chart = BarChart()
    profit_chart.title = "Lucro liquido por grupo"
    profit_chart.y_axis.title = "R$"
    profit_chart.x_axis.title = ""
    profit_chart.legend = None
    profit_chart.style = 10
    profit_chart.height = 9
    profit_chart.width = 14
    profit_chart.add_data(Reference(ws, min_col=5, min_row=table_start, max_row=max_row), titles_from_data=True)
    profit_chart.set_categories(categories)
    ws.add_chart(profit_chart, "J3")

    margin_chart = BarChart()
    margin_chart.title = "Margem e ROI por grupo"
    margin_chart.y_axis.title = "%"
    margin_chart.x_axis.title = ""
    margin_chart.style = 13
    margin_chart.height = 9
    margin_chart.width = 14
    margin_chart.add_data(Reference(ws, min_col=6, min_row=table_start, max_col=7, max_row=max_row), titles_from_data=True)
    margin_chart.set_categories(categories)
    ws.add_chart(margin_chart, "J20")


def _daily_audit_table(ws, result: AnalysisResult) -> None:
    start_row = 34
    ws["A33"] = "Dados diarios para auditoria"
    ws["A33"].font = Font(bold=True, size=12, color=AZUL_ESCURO)

    daily = result.daily_metrics.sort_values(["data", "grupo"])
    pivot = (
        daily.pivot_table(index="data", columns="grupo", values="lucro_liquido", aggfunc="sum")
        .sort_index()
        .reset_index()
    )
    pivot["data"] = pd.to_datetime(pivot["data"]).dt.date.astype(str)

    headers = ["Data", *[str(col) for col in pivot.columns if col != "data"]]
    _write_header(ws, start_row, headers)

    for row_idx, row in enumerate(pivot.itertuples(index=False), start=start_row + 1):
        for col_idx, value in enumerate(row, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            _body_cell(cell)
            if col_idx > 1:
                cell.number_format = 'R$ #,##0.00'

    end_row = start_row + len(pivot)
    line = LineChart()
    line.title = "Lucro liquido diario por grupo"
    line.y_axis.title = "Lucro liquido"
    line.x_axis.title = "Data"
    line.style = 13
    line.height = 10
    line.width = 18
    line.add_data(Reference(ws, min_col=2, min_row=start_row, max_col=len(headers), max_row=end_row), titles_from_data=True)
    line.set_categories(Reference(ws, min_col=1, min_row=start_row + 1, max_row=end_row))
    ws.add_chart(line, "J37")


def _prepare_sheet(ws) -> None:
    ws.sheet_view.showGridLines = False
    _fill_range(ws, "A1:Z120", CINZA_FUNDO)
    for row in range(1, 121):
        ws.row_dimensions[row].height = 22


def _title(ws, text: str, cell_range: str) -> None:
    start_cell = cell_range.split(":")[0]
    ws[start_cell] = text
    ws[start_cell].font = Font(bold=True, size=18, color=BRANCO)
    ws[start_cell].alignment = Alignment(horizontal="left", vertical="center")
    ws[start_cell].fill = PatternFill("solid", fgColor=AZUL_ESCURO)
    ws.merge_cells(cell_range)
    for row in ws[cell_range]:
        for cell in row:
            cell.fill = PatternFill("solid", fgColor=AZUL_ESCURO)
    ws.row_dimensions[1].height = 32


def _kpi_card(ws, cell_range: str, label: str, value, kind: str, fill: str) -> None:
    start, end = cell_range.split(":")
    ws.merge_cells(cell_range)
    cell = ws[start]
    cell.fill = PatternFill("solid", fgColor=fill)
    cell.border = _medium_border()
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    if kind == "moeda":
        value_text = f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    elif kind == "percentual":
        value_text = f"{value * 100:.2f}%".replace(".", ",")
    else:
        value_text = str(value)

    cell.value = f"{label}\n{value_text}"
    cell.font = Font(bold=True, size=13, color=AZUL_ESCURO)

    start_col = ws[start].column
    end_col = ws[end].column
    start_row = ws[start].row
    end_row = ws[end].row
    for row in range(start_row, end_row + 1):
        ws.row_dimensions[row].height = 26
        for col in range(start_col, end_col + 1):
            ws.cell(row=row, column=col).fill = PatternFill("solid", fgColor=fill)
            ws.cell(row=row, column=col).border = _medium_border()


def _write_header(ws, row: int, headers: list[str]) -> None:
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=col_idx, value=header)
        cell.font = Font(bold=True, color=BRANCO)
        cell.fill = PatternFill("solid", fgColor=VERDE_ESCURO)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = _thin_border()


def _body_cell(cell) -> None:
    cell.fill = PatternFill("solid", fgColor=BRANCO)
    cell.border = _thin_border()
    cell.alignment = Alignment(vertical="center", wrap_text=True)
    cell.font = Font(color=CINZA_TEXTO)


def _fill_range(ws, cell_range: str, color: str) -> None:
    for row in ws[cell_range]:
        for cell in row:
            cell.fill = PatternFill("solid", fgColor=color)


def _fill_row(ws, row: int, start_col: int, end_col: int, color: str) -> None:
    for col in range(start_col, end_col + 1):
        ws.cell(row=row, column=col).fill = PatternFill("solid", fgColor=color)


def _thin_border() -> Border:
    side = Side(style="thin", color=CINZA_BORDA)
    return Border(left=side, right=side, top=side, bottom=side)


def _medium_border() -> Border:
    side = Side(style="medium", color=BRANCO)
    return Border(left=side, right=side, top=side, bottom=side)


def _set_widths(ws, widths: dict[str, int]) -> None:
    for col, width in widths.items():
        ws.column_dimensions[col].width = width
    for column_cells in ws.columns:
        col = get_column_letter(column_cells[0].column)
        if col not in widths:
            ws.column_dimensions[col].width = 12
