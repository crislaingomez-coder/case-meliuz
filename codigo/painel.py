from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.drawing.image import Image as ExcelImage
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from PIL import Image, ImageDraw, ImageFont

from codigo.analisador import AnalysisResult


BG = "#101417"
PANEL = "#1A2025"
PANEL_2 = "#222A30"
LINE = "#2E3840"
TEXT = "#F7F7F2"
MUTED = "#B8C0BA"
GREEN = "#426F49"
GREEN_2 = "#5E8A64"
PINK = "#F48DB8"
PINK_2 = "#E869A0"
ORANGE = "#FF8A4C"
BLUE = "#4E7DD1"
WHITE = "FFFFFF"
LIGHT_BORDER = "D9E2D9"


def build_dashboard(results: list[AnalysisResult], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image_dir = output_path.parent / "graficos"
    image_dir.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    summary_ws = wb.active
    summary_ws.title = "Resumo Executivo"
    _insert_dashboard_page(summary_ws, _summary_dashboard_image(results, image_dir / "dashboard_resumo.png"))

    for result in results:
        ws = wb.create_sheet(result.partner.replace("Parceiro ", "Parceiro_")[:31])
        _insert_dashboard_page(ws, _partner_dashboard_image(result, image_dir / f"{_slug(result.partner)}_dashboard.png"))

    _build_tracking_sheet(wb, results)
    _build_audit_sheet(wb, results)

    wb.save(output_path)
    shutil.rmtree(image_dir, ignore_errors=True)
    return output_path


def _summary_dashboard_image(results: list[AnalysisResult], path: Path) -> Path:
    width, height = 1600, 900
    img, draw = _canvas(width, height)
    _brand_header(img, draw, "Dashboard de Testes A/B", "Analise automatizada de cashback")

    winners = [r.metrics[r.metrics["grupo"] == r.decision_group].iloc[0] for r in results]
    total_profit = sum(float(row["lucro_liquido_total"]) for row in winners)
    avg_margin = sum(float(row["margem_sobre_gmv"]) for row in winners) / len(winners)
    avg_roi = sum(float(row["roi_cashback"]) for row in winners) / len(winners)

    cards = [
        ("Testes analisados", str(len(results)), PINK, "check"),
        ("Lucro vencedor total", _fmt_money(total_profit), GREEN_2, "money"),
        ("Margem media", _fmt_pct(avg_margin), ORANGE, "percent"),
        ("ROI medio", _fmt_pct(avg_roi), BLUE, "return"),
    ]
    for idx, (label, value, color, icon) in enumerate(cards):
        _kpi(draw, 64 + idx * 370, 132, 330, 118, label, value, color, icon)

    labels = [r.partner.replace("Parceiro ", "Parceiro ") for r in results]
    profit_values = [float(row["lucro_liquido_total"]) for row in winners]
    roi_values = [float(row["roi_cashback"]) for row in winners]

    _bar_panel(draw, 64, 292, 690, 300, "Lucro da variante recomendada", labels, profit_values, "moeda", [GREEN_2, PINK, ORANGE])
    _bar_panel(draw, 806, 292, 690, 300, "ROI de cashback da variante recomendada", labels, roi_values, "percentual", [PINK, PINK_2, BLUE])

    table_rows = []
    for result, winner in zip(results, winners):
        table_rows.append([
            result.partner,
            result.decision_group,
            _fmt_money(float(winner["lucro_liquido_total"])),
            _fmt_pct(float(winner["margem_sobre_gmv"])),
            _fmt_pct(float(winner["roi_cashback"])),
        ])
    _table_panel(draw, 64, 638, 900, 205, "Resumo dos testes", ["Parceiro", "Variante", "Lucro", "Margem", "ROI"], table_rows)

    best = max(zip(results, winners), key=lambda item: float(item[1]["lucro_liquido_total"]))
    insight = (
        "Conclusao geral: Grupo 1 foi recomendado nos 3 testes por preservar melhor "
        f"rentabilidade. {best[0].partner} concentrou o maior lucro vencedor."
    )
    _insight_panel(draw, 1010, 638, 486, 205, insight)

    img.save(path)
    return path


def _partner_dashboard_image(result: AnalysisResult, path: Path) -> Path:
    width, height = 1600, 900
    img, draw = _canvas(width, height)
    _brand_header(img, draw, result.test_name, f"{result.period} | recomendacao automatizada")

    metrics = result.metrics.sort_values("grupo").reset_index(drop=True)
    winner = result.metrics[result.metrics["grupo"] == result.decision_group].iloc[0]

    cards = [
        ("Variante", result.decision_group, PINK, "check"),
        ("Lucro liquido", _fmt_money(float(winner["lucro_liquido_total"])), GREEN_2, "money"),
        ("Margem GMV", _fmt_pct(float(winner["margem_sobre_gmv"])), ORANGE, "percent"),
        ("ROI cashback", _fmt_pct(float(winner["roi_cashback"])), BLUE, "return"),
    ]
    for idx, (label, value, color, icon) in enumerate(cards):
        _kpi(draw, 64 + idx * 370, 132, 330, 118, label, value, color, icon)

    labels = metrics["grupo"].tolist()
    colors = [GREEN_2 if group == result.decision_group else PINK for group in labels]
    _bar_panel(
        draw,
        64,
        292,
        690,
        300,
        "Lucro liquido por grupo",
        labels,
        metrics["lucro_liquido_total"].astype(float).tolist(),
        "moeda",
        colors,
    )
    _bar_panel(
        draw,
        806,
        292,
        690,
        300,
        "ROI de cashback por grupo",
        labels,
        metrics["roi_cashback"].astype(float).tolist(),
        "percentual",
        colors,
    )

    rows = []
    for _, row in metrics.iterrows():
        rows.append([
            row["grupo"],
            str(int(row["compradores"])),
            _fmt_money(float(row["gmv_total"])),
            _fmt_money(float(row["cashback_total"])),
            _fmt_money(float(row["lucro_liquido_total"])),
            _fmt_pct(float(row["margem_sobre_gmv"])),
            _fmt_pct(float(row["roi_cashback"])),
        ])
    _table_panel(
        draw,
        64,
        638,
        930,
        205,
        "Comparativo por variante",
        ["Grupo", "Compr.", "GMV", "Cashback", "Lucro", "Margem", "ROI"],
        rows,
    )
    insight = result.decision
    if (metrics["lucro_liquido_total"].astype(float) <= 0).any():
        insight += " Atencao: ao menos uma variante teve lucro liquido zero ou negativo."
    _insight_panel(draw, 1040, 638, 456, 205, insight)
    img.save(path)
    return path


def _build_tracking_sheet(wb: Workbook, results: list[AnalysisResult]) -> None:
    ws = wb.create_sheet("Acompanhamento")
    _plain_sheet(ws)
    headers = ["Nome do teste", "Descricao", "Parceiro", "Periodo", "Variante", "Resultado", "Decisao"]
    _write_header(ws, 1, headers)
    for row_idx, result in enumerate(results, start=2):
        ws.cell(row=row_idx, column=1, value=result.test_name)
        ws.cell(row=row_idx, column=2, value=f"Teste A/B de cashback do {result.partner} no periodo de {result.period}.")
        ws.cell(row=row_idx, column=3, value=result.partner)
        ws.cell(row=row_idx, column=4, value=result.period)
        ws.cell(row=row_idx, column=5, value=result.decision_group)
        ws.cell(row=row_idx, column=6, value=result.result_summary)
        ws.cell(row=row_idx, column=7, value=result.decision)
        for col in range(1, 8):
            _body_cell(ws.cell(row=row_idx, column=col))
    _set_widths(ws, {"A": 28, "B": 52, "C": 16, "D": 24, "E": 14, "F": 70, "G": 70})


def _build_audit_sheet(wb: Workbook, results: list[AnalysisResult]) -> None:
    ws = wb.create_sheet("Auditoria_Diaria")
    _plain_sheet(ws)
    headers = ["Parceiro", "Data", "Grupo", "Compradores", "GMV", "Comissao", "Cashback", "Lucro liquido"]
    _write_header(ws, 1, headers)
    row_idx = 2
    for result in results:
        daily = result.daily_metrics.sort_values(["data", "grupo"])
        for _, row in daily.iterrows():
            values = [
                result.partner,
                row["data"].date().isoformat(),
                row["grupo"],
                int(row["compradores"]),
                float(row["vendas_totais"]),
                float(row["comissao"]),
                float(row["cashback"]),
                float(row["lucro_liquido"]),
            ]
            for col_idx, value in enumerate(values, start=1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                _body_cell(cell)
                if col_idx >= 5:
                    cell.number_format = 'R$ #,##0.00'
            row_idx += 1
    _set_widths(ws, {"A": 16, "B": 14, "C": 12, "D": 14, "E": 16, "F": 16, "G": 16, "H": 16})


def _canvas(width: int, height: int):
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)
    return image, draw


def _brand_header(image: Image.Image, draw: ImageDraw.ImageDraw, title: str, subtitle: str) -> None:
    logo_path = Path(__file__).resolve().parents[1] / "identidade_visual" / "logo-icon-2022-1080x1080.png"
    if logo_path.exists():
        logo = Image.open(logo_path).convert("RGBA").resize((76, 76))
        image.paste(logo, (64, 40), logo)
    draw.text((164, 46), title, fill=TEXT, font=_font(38, bold=True))
    draw.text((166, 94), subtitle, fill=MUTED, font=_font(20))


def _kpi(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, label: str, value: str, color: str, icon: str) -> None:
    draw.rounded_rectangle((x, y, x + w, y + h), radius=18, fill=PANEL, outline=LINE, width=2)
    draw.ellipse((x + 22, y + 24, x + 78, y + 80), fill=color)
    _draw_icon(draw, x + 50, y + 52, icon)
    draw.text((x + 96, y + 26), label, fill=MUTED, font=_font(16))
    draw.text((x + 96, y + 56), value, fill=TEXT, font=_font(24, bold=True))


def _draw_icon(draw: ImageDraw.ImageDraw, cx: int, cy: int, icon: str) -> None:
    if icon == "check":
        draw.line((cx - 14, cy, cx - 4, cy + 11, cx + 15, cy - 13), fill=TEXT, width=5, joint="curve")
    elif icon == "money":
        draw.text((cx, cy - 17), "$", fill=TEXT, font=_font(30, bold=True), anchor="ma")
    elif icon == "percent":
        draw.text((cx, cy - 17), "%", fill=TEXT, font=_font(30, bold=True), anchor="ma")
    elif icon == "return":
        draw.arc((cx - 18, cy - 18, cx + 18, cy + 18), 40, 315, fill=TEXT, width=4)
        draw.polygon([(cx + 10, cy - 19), (cx + 22, cy - 17), (cx + 14, cy - 6)], fill=TEXT)


def _bar_panel(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, title: str, labels: list[str], values: list[float], kind: str, colors: list[str]) -> None:
    draw.rounded_rectangle((x, y, x + w, y + h), radius=18, fill=PANEL, outline=LINE, width=2)
    draw.text((x + 28, y + 24), title, fill=TEXT, font=_font(24, bold=True))
    max_value = max(max(values), 1)
    chart_x, chart_y = x + 55, y + 82
    chart_w, chart_h = w - 95, h - 130
    base = chart_y + chart_h
    gap = 34
    bar_w = max(58, int((chart_w - gap * (len(values) - 1)) / len(values)))
    for idx, (label, value) in enumerate(zip(labels, values)):
        bar_h = int((value / max_value) * (chart_h * 0.88))
        bx = chart_x + idx * (bar_w + gap)
        by = base - bar_h
        color = colors[idx % len(colors)]
        draw.rounded_rectangle((bx, by, bx + bar_w, base), radius=9, fill=color)
        draw.text((bx + bar_w / 2, by - 26), _fmt_money(value) if kind == "moeda" else _fmt_pct(value), fill=TEXT, font=_font(15, bold=True), anchor="ma")
        draw.text((bx + bar_w / 2, base + 18), label, fill=MUTED, font=_font(15), anchor="ma")
    draw.line((chart_x, base, chart_x + chart_w, base), fill=LINE, width=2)


def _table_panel(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, title: str, headers: list[str], rows: list[list[str]]) -> None:
    draw.rounded_rectangle((x, y, x + w, y + h), radius=18, fill=PANEL, outline=LINE, width=2)
    draw.text((x + 26, y + 20), title, fill=TEXT, font=_font(23, bold=True))
    top = y + 62
    row_h = 34
    col_w = (w - 52) / len(headers)
    for idx, header in enumerate(headers):
        cx = x + 26 + idx * col_w
        draw.text((cx, top), header, fill=PINK, font=_font(15, bold=True))
    for r_idx, row in enumerate(rows):
        ry = top + 32 + r_idx * row_h
        draw.line((x + 24, ry - 8, x + w - 24, ry - 8), fill=LINE, width=1)
        for c_idx, value in enumerate(row):
            cx = x + 26 + c_idx * col_w
            draw.text((cx, ry), str(value), fill=TEXT if c_idx == 0 else MUTED, font=_font(14))


def _insight_panel(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, text: str) -> None:
    draw.rounded_rectangle((x, y, x + w, y + h), radius=18, fill=PANEL_2, outline=LINE, width=2)
    draw.text((x + 26, y + 22), "Decisao acionavel", fill=PINK, font=_font(22, bold=True))
    wrapped = _wrap_text(text, 38)
    draw.multiline_text((x + 26, y + 68), wrapped, fill=TEXT, font=_font(17), spacing=8)


def _insert_dashboard_page(ws, image_path: Path) -> None:
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = None
    for row in range(1, 45):
        ws.row_dimensions[row].height = 18
    for col in range(1, 22):
        ws.column_dimensions[get_column_letter(col)].width = 10
    image = ExcelImage(str(image_path))
    image.width = 1280
    image.height = 720
    ws.add_image(image, "A1")


def _plain_sheet(ws) -> None:
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A2"


def _write_header(ws, row: int, headers: list[str]) -> None:
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=col_idx, value=header)
        cell.font = Font(bold=True, color=WHITE)
        cell.fill = PatternFill("solid", fgColor=GREEN.replace("#", ""))
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = _thin_border()


def _body_cell(cell) -> None:
    cell.fill = PatternFill("solid", fgColor="FFFFFF")
    cell.border = _thin_border()
    cell.alignment = Alignment(vertical="center", wrap_text=True)
    cell.font = Font(color="34423A")


def _thin_border() -> Border:
    side = Side(style="thin", color=LIGHT_BORDER)
    return Border(left=side, right=side, top=side, bottom=side)


def _set_widths(ws, widths: dict[str, int]) -> None:
    for col, width in widths.items():
        ws.column_dimensions[col].width = width


def _fmt_money(value: float) -> str:
    return f"R$ {float(value):,.0f}".replace(",", ".")


def _fmt_pct(value: float) -> str:
    return f"{float(value) * 100:.2f}%".replace(".", ",")


def _font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap_text(text: str, limit: int) -> str:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        if sum(len(item) for item in current) + len(current) + len(word) > limit:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return "\n".join(lines)


def _slug(value: str) -> str:
    return value.lower().replace(" ", "_")
