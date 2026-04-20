"""
Exporter strategies — CSV and PDF export for table data.
Pattern: GoF Strategy. Call get_exporter(fmt).export(...) to produce a file.
New formats can be added by subclassing Exporter and registering in _REGISTRY
without changing any call sites (Open/Closed Principle).
"""
import csv
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

_DANGEROUS_PREFIXES = ("=", "+", "-", "@")


def _sanitize_cell(value):
    s = "" if value is None else str(value)
    if s.startswith(_DANGEROUS_PREFIXES):
        s = "'" + s
    return s


class Exporter(ABC):
    @abstractmethod
    def export(self, title: str, columns: list, rows: list, path) -> None:
        ...


class CSVExporter(Exporter):
    extension = ".csv"

    def export(self, title, columns, rows, path):
        path = Path(path)
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for row in rows:
                writer.writerow(_sanitize_cell(c) for c in row)


class PDFExporter(Exporter):
    extension = ".pdf"

    def export(self, title, columns, rows, path):
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import (SimpleDocTemplate, Table,
                                             TableStyle, Paragraph, Spacer)
        except ImportError:
            raise ImportError(
                "reportlab is required for PDF export.\n"
                "Install it with:  pip install reportlab"
            )
        doc = SimpleDocTemplate(str(path), pagesize=landscape(A4))
        styles = getSampleStyleSheet()
        elements = [
            Paragraph(f"<b>{title}</b>", styles["Title"]),
            Paragraph(f"Generated: {datetime.now():%Y-%m-%d %H:%M}",
                      styles["Normal"]),
            Spacer(1, 12),
        ]
        data = [columns] + [[_sanitize_cell(c) for c in row] for row in rows]
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID",       (0, 0), (-1, -1), 0.25, colors.grey),
            ("FONTSIZE",   (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F9FAFB")]),
        ]))
        elements.append(table)
        doc.build(elements)


_REGISTRY = {"csv": CSVExporter, "pdf": PDFExporter}


def get_exporter(fmt: str) -> Exporter:
    try:
        return _REGISTRY[fmt.lower()]()
    except KeyError:
        raise ValueError(f"Unsupported export format: {fmt!r}")


def default_filename(table_name: str, fmt: str) -> str:
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    return f"{table_name.lower()}_{stamp}.{fmt}"
