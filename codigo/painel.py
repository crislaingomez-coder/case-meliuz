from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from codigo.analisador import AnalysisResult


BLUE = "1F4E79"
GREEN = "0F8B5F"
RED = "C0392B"
LIGHT_BLUE = "D9EAF7"
LIGHT_GREEN = "DDEFE7"
LIGHT_GRAY = "F3F6F8"
WHITE = "FFFFFF"


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
    ws["A1"] = "Dashboard de Testes A/B de Cashback"
    ws["A1"].font = Font(bold=True, size=18, color=WHITE)
    ws["A1"].fill = PatternFill("solid", fgColor=BLUE)
    ws.merge_cells("A1:H1")

    headers = [
        "Teste",
        "Parceiro",
        "Periodo",
        "Variante recomendada",
        "Lucro vencedor",
        "Margem",
        "ROI cashback",
        "Decisao",
    ]
    _write_header(ws, 3, headers)

    for row_idx, result in enumerate(results, start=4):
        winner = result.metrics[result.metrics["grupo"] == result.decision_group].iloc[0]
        values = [
            result.test_name,
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
            _style_body_cell(cell)

    for row in range(4, 4 + len(results)):
        ws.cell(row=row, column=5).number_format = 'R$ #,##0.00'
        ws.cell(row=row, column=6).number_format = '0.00%'
        ws.cell(row=row, column=7).number_format = '0.00%'

    _autosize(ws)
    ws.freeze_panes = "A4"

    chart = BarChart()
    chart.title = "Lucro liquido da variante recomendada"
    chart.y_axis.title = "Lucro liquido"
    chart.x_axis.title = "Parceiro"
    data = Reference(ws, min_col=5, min_row=3, max_row=3 + len(results))
    cats = Reference(ws, min_col=2, min_row=4, max_row=3 + len(results))
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    chart.height = 8
    chart.width = 16
    ws.add_chart(chart, "J3")


def _build_partner_sheet(wb: Workbook, result: AnalysisResult) -> None:
    title = result.partner.replace("Parceiro ", "Parceiro_")
    ws = wb.create_sheet(title[:31])

    ws["A1"] = f"{result.test_name}"
    ws["A1"].font = Font(bold=True, size=16, color=WHITE)
    ws["A1"].fill = PatternFill("solid", fgColor=BLUE)
    ws.merge_cells("A1:J1")

    cards = [
        ("Periodo", result.period),
        ("Recomendacao", result.decision_group),
        ("Decisao", result.decision),
    ]
    for idx, (label, value) in enumerate(cards, start=1):
        row = 3 + idx
        ws.cell(row=row, column=1, value=label).font = Font(bold=True, color=BLUE)
        ws.cell(row=row, column=2, value=value)

    headers = [
        "Grupo",
        "Dias",
        "Compradores",
        "GMV",
        "Comissao",
        "Cashback",
        "Lucro liquido",
        "Margem GMV",
        "ROI cashback",
        "Ticket medio",
    ]
    table_start = 9
    _write_header(ws, table_start, headers)

    metrics = result.metrics.sort_values("grupo").reset_index(drop=True)
    for idx, row in metrics.iterrows():
        excel_row = table_start + 1 + idx
        values = [
            row["grupo"],
            int(row["dias"]),
            int(row["compradores"]),
            float(row["gmv_total"]),
            float(row["comissao_total"]),
            float(row["cashback_total"]),
            float(row["lucro_liquido_total"]),
            float(row["margem_sobre_gmv"]),
            float(row["roi_cashback"]),
            float(row["ticket_medio"]),
        ]
        for col_idx, value in enumerate(values, start=1):
            cell = ws.cell(row=excel_row, column=col_idx, value=value)
            _style_body_cell(cell)

    for row in range(table_start + 1, table_start + 1 + len(metrics)):
        for col in [4, 5, 6, 7, 10]:
            ws.cell(row=row, column=col).number_format = 'R$ #,##0.00'
        for col in [8, 9]:
            ws.cell(row=row, column=col).number_format = '0.00%'

    _add_partner_charts(ws, table_start, len(metrics))
    _add_daily_data(ws, result)
    _autosize(ws)
    ws.freeze_panes = "A10"


def _add_partner_charts(ws, table_start: int, row_count: int) -> None:
    max_row = table_start + row_count

    profit_chart = BarChart()
    profit_chart.title = "Lucro liquido por grupo"
    profit_chart.y_axis.title = "Lucro liquido"
    profit_chart.x_axis.title = "Grupo"
    profit_data = Reference(ws, min_col=7, min_row=table_start, max_row=max_row)
    cats = Reference(ws, min_col=1, min_row=table_start + 1, max_row=max_row)
    profit_chart.add_data(profit_data, titles_from_data=True)
    profit_chart.set_categories(cats)
    profit_chart.height = 7
    profit_chart.width = 14
    ws.add_chart(profit_chart, "L3")

    roi_chart = BarChart()
    roi_chart.title = "ROI de cashback por grupo"
    roi_chart.y_axis.title = "ROI"
    roi_chart.x_axis.title = "Grupo"
    roi_data = Reference(ws, min_col=9, min_row=table_start, max_row=max_row)
    roi_chart.add_data(roi_data, titles_from_data=True)
    roi_chart.set_categories(cats)
    roi_chart.height = 7
    roi_chart.width = 14
    ws.add_chart(roi_chart, "L18")


def _add_daily_data(ws, result: AnalysisResult) -> None:
    start_col = 1
    start_row = 18
    ws.cell(row=start_row, column=start_col, value="Dados diarios para auditoria").font = Font(
        bold=True, color=BLUE
    )
    headers = ["Data", "Grupo", "GMV", "Cashback", "Lucro liquido"]
    _write_header(ws, start_row + 2, headers)

    daily = result.daily_metrics.sort_values(["grupo", "data"])
    for idx, (_, row) in enumerate(daily.iterrows(), start=start_row + 3):
        values = [
            row["data"].date().isoformat(),
            row["grupo"],
            float(row["vendas_totais"]),
            float(row["cashback"]),
            float(row["lucro_liquido"]),
        ]
        for col_idx, value in enumerate(values, start=start_col):
            cell = ws.cell(row=idx, column=col_idx, value=value)
            _style_body_cell(cell)

    for row in range(start_row + 3, start_row + 3 + len(daily)):
        for col in [3, 4, 5]:
            ws.cell(row=row, column=col).number_format = 'R$ #,##0.00'

    end_row = start_row + 2 + len(daily)
    line = LineChart()
    line.title = "Lucro liquido diario"
    line.y_axis.title = "Lucro liquido"
    line.x_axis.title = "Observacoes"
    data = Reference(ws, min_col=5, min_row=start_row + 2, max_row=end_row)
    line.add_data(data, titles_from_data=True)
    line.height = 7
    line.width = 14
    ws.add_chart(line, "L33")


def _write_header(ws, row: int, headers: list[str]) -> None:
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=col_idx, value=header)
        cell.font = Font(bold=True, color=WHITE)
        cell.fill = PatternFill("solid", fgColor=GREEN)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = _thin_border()


def _style_body_cell(cell) -> None:
    cell.fill = PatternFill("solid", fgColor=LIGHT_GRAY)
    cell.border = _thin_border()
    cell.alignment = Alignment(vertical="center", wrap_text=True)


def _thin_border() -> Border:
    side = Side(style="thin", color="D9D9D9")
    return Border(left=side, right=side, top=side, bottom=side)


def _autosize(ws) -> None:
    for column_cells in ws.columns:
        length = 0
        column = get_column_letter(column_cells[0].column)
        for cell in column_cells:
            value = "" if cell.value is None else str(cell.value)
            length = max(length, min(len(value), 55))
        ws.column_dimensions[column].width = max(12, length + 2)
