#!/usr/bin/env python
# FILE: pdf2text.py
# AUTHOR: Duong Vu (Modified for PDF support)

import argparse
import bisect
import html
import re
from typing import Any, Dict, List, Tuple

import fitz  # PyMuPDF

parser = argparse.ArgumentParser(
    prog="pdf2text.py",
    usage="%(prog)s [options] -i document -o output",
    description="Extract body text from a PDF, with tables and figures filtered out.",
    epilog="Written by Duong Vu duong.t.vu@gmail.com",
)

parser.add_argument("-i", "--input", required=True, help="Input PDF path.")
parser.add_argument("-o", "--out", required=True, help="Output text file path.")

args = parser.parse_args()
doc_path = args.input
output_path = args.out

doc = fitz.open(doc_path)

TABLE_CAPTION_RE = re.compile(r"^Table\s+\d", re.I)


# ---------------------------------------------------------------------------
# Basic block helpers
# ---------------------------------------------------------------------------

def block_text(block: dict) -> str:
    """Return all text in a block as a flat string."""
    parts = []
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            parts.append(span.get("text", ""))
    return "".join(parts).rstrip()


def is_first_word_bold(block: dict) -> bool:
    if "lines" not in block or not block["lines"]:
        return False
    first_line = block["lines"][0]
    if "spans" not in first_line or not first_line["spans"]:
        return False
    font_name = first_line["spans"][0].get("font", "")
    return ".B" in font_name


_AUTHOR_NAME = re.compile(r"[A-Z]\.[A-Z]?\.\s*[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\-]+")


def is_author_list(text: str) -> bool:
    return len(_AUTHOR_NAME.findall(text)) >= 2


def is_caption(text: str) -> bool:
    if " ET AL." in text:
        return True
    if is_author_list(text):
        return True
    if (
        "Peer review under responsibility of Westerdijk Fungal Biodiversity Institute"
        in text
    ):
        return True
    if "Department" in text:
        return True
    if text == "REVISION OF ASPERGILLUS SECTION RESTRICTI":
        return True
    if "www.studiesinmycology.org" in text:
        return True
    if "ELSEVIER B.V" in text:
        return True
    if text.startswith("Abstract:"):
        return True
    if text.startswith("*Correspondence:"):
        return True
    if text.startswith("Key words:"):
        return True
    if text.startswith("Available online "):
        return True
    if text.startswith("Studies in Mycology"):
        return True
    if text.isdigit():
        return True
    return False


def clean_control_chars(text: str) -> str:
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)


# ---------------------------------------------------------------------------
# Figure detection
# ---------------------------------------------------------------------------

def is_figure_caption(block: dict) -> bool:
    if "lines" not in block or not block["lines"]:
        return False
    text = block["lines"][0]["spans"][0].get("text", "")
    if not text.startswith(("Fig.", "Figure ", "FIG.", "Fig ")):
        return False
    return is_first_word_bold(block)


def get_figure_regions(page: fitz.Page) -> List[fitz.Rect]:
    blocks = page.get_text("dict")["blocks"]
    return [fitz.Rect(b["bbox"]) for b in blocks if b.get("type") == 1]


def _expand_rect(rect: fitz.Rect, margin: float) -> fitz.Rect:
    return fitz.Rect(
        rect.x0 - margin,
        rect.y0 - margin,
        rect.x1 + margin,
        rect.y1 + margin,
    )


def block_in_figure(block, image_bboxes, margin=2) -> bool:
    rect = fitz.Rect(block["bbox"])
    for img in image_bboxes:
        if rect.intersects(_expand_rect(img, margin)):
            return True
    return False


def belongs_to_figure(block, image_bboxes) -> bool:
    if block.get("type") == 1:
        return True
    if is_figure_caption(block):
        return True
    if image_bboxes and block_in_figure(block, image_bboxes):
        return True
    return False


# ---------------------------------------------------------------------------
# Shared geometry helpers
# ---------------------------------------------------------------------------

def _sorted_text_blocks(page: fitz.Page) -> List[dict]:
    blocks = [
        b
        for b in page.get_text("dict")["blocks"]
        if b.get("type", 0) == 0 and b.get("lines")
    ]
    blocks.sort(key=lambda b: (b["bbox"][1], b["bbox"][0]))
    return blocks


def _first_span_size(block: dict) -> float:
    if not block.get("lines") or not block["lines"][0].get("spans"):
        return 10.0
    return block["lines"][0]["spans"][0].get("size", 10.0)


def _is_body_text(text: str, size: float) -> bool:
    if text.startswith("Additional materials examined: "):
        return True
    if size < 10:
        return False
    return True


def expand_region_downward(page: fitz.Page, seed: fitz.Rect) -> fitz.Rect:
    region = fitz.Rect(seed)
    y_bottom = seed.y1
    for b in _sorted_text_blocks(page):
        br = fitz.Rect(b["bbox"])
        if br.y1 <= seed.y0 + 1:
            continue
        text = block_text(b)
        size = _first_span_size(b)
        if br.y0 - y_bottom > 30 and size >= 10:
            break
        if _is_body_text(text, size):
            if not TABLE_CAPTION_RE.match(text.strip()):
                break
        region |= br
        y_bottom = br.y1
    return region


def get_table_regions(page: fitz.Page) -> List[fitz.Rect]:
    regions: List[fitz.Rect] = []
    for table in page.find_tables():
        r = fitz.Rect(table.bbox)
        if r.height < 60:
            r = expand_region_downward(page, r)
        regions.append(r)
    for b in _sorted_text_blocks(page):
        if TABLE_CAPTION_RE.match(block_text(b).strip()):
            cap = fitz.Rect(b["bbox"])
            expanded = expand_region_downward(page, cap)
            if not any(expanded.intersects(x) for x in regions):
                regions.append(expanded)
    return regions


def _line_text(line: dict) -> str:
    return "".join(
        span.get("text", "") for span in line.get("spans", [])
    ).rstrip()


def group_lines_into_table_rows(
    line_items: List[tuple],
    y_tolerance: float = 4.0,
    cell_sep: str = "\t",
) -> List[str]:
    if not line_items:
        return []

    line_items = sorted(line_items, key=lambda item: (item[0], item[1]))
    rows: List[str] = []
    row_y = None
    cells: List[tuple] = []

    for y0, x0, text in line_items:
        if row_y is None or abs(y0 - row_y) <= y_tolerance:
            cells.append((x0, text))
            if row_y is None:
                row_y = y0
        else:
            cells.sort(key=lambda c: c[0])
            rows.append(cell_sep.join(c[1] for c in cells))
            row_y = y0
            cells = [(x0, text)]

    if cells:
        cells.sort(key=lambda c: c[0])
        rows.append(cell_sep.join(c[1] for c in cells))
    return rows


def _collect_lines_in_bbox(
    page: fitz.Page, table_bbox, margin: float
) -> List[tuple]:
    tbl = (
        table_bbox if isinstance(table_bbox, fitz.Rect) else fitz.Rect(table_bbox)
    )
    expanded = _expand_rect(tbl, margin)
    items = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type", 0) != 0:
            continue
        for line in block.get("lines", []):
            if "bbox" not in line:
                continue
            lbbox = fitz.Rect(line["bbox"])
            if lbbox.intersects(expanded):
                text = _line_text(line)
                if text:
                    items.append((lbbox.y0, lbbox.x0, text))
    return items


def extract_text_from_table_bbox(
    page: fitz.Page,
    table_bbox,
    margin: float = 2,
    y_tolerance: float = 4.0,
    cell_sep: str = "\t",
) -> str:
    for table in page.find_tables():
        tb = fitz.Rect(table.bbox)
        region = (
            table_bbox
            if isinstance(table_bbox, fitz.Rect)
            else fitz.Rect(table_bbox)
        )
        if tb.intersects(region):
            rows = table.extract() or []
            if rows and any(any(c for c in row) for row in rows):
                return "\n".join(
                    cell_sep.join((c or "").strip() for c in row) for row in rows
                ).strip()

    line_items = _collect_lines_in_bbox(page, table_bbox, margin)
    table_rows = group_lines_into_table_rows(
        line_items, y_tolerance=y_tolerance, cell_sep=cell_sep
    )
    return "\n".join(table_rows)


def extract_text_in_table_regions(
    page: fitz.Page,
    table_bboxes: List[fitz.Rect],
    margin: float = 2,
    y_tolerance: float = 4.0,
    cell_sep: str = "\t",
) -> str:
    if not table_bboxes:
        return ""

    parts = []
    for bbox in table_bboxes:
        text = extract_text_from_table_bbox(
            page,
            bbox,
            margin=margin,
            y_tolerance=y_tolerance,
            cell_sep=cell_sep,
        ).strip()
        if text:
            parts.append(text)
    return "\n\n".join(parts)


def extract_tables_for_page(page: fitz.Page) -> str:
    table_bboxes = get_table_regions(page)
    return extract_text_in_table_regions(page, table_bboxes)


def block_in_table(block, table_bboxes, margin=8) -> bool:
    if not table_bboxes:
        return False
    rect = fitz.Rect(block["bbox"])
    for tbl in table_bboxes:
        tbl_rect = tbl if isinstance(tbl, fitz.Rect) else fitz.Rect(tbl)
        expanded = _expand_rect(tbl_rect, margin)
        if rect.intersects(expanded):
            return True
        for line in block.get("lines", []):
            if "bbox" in line and fitz.Rect(line["bbox"]).intersects(expanded):
                return True
    return False


# ---------------------------------------------------------------------------
# HTML table generation from positioned-text blocks
# ---------------------------------------------------------------------------

def _cluster_xs(xs: List[float], tol: float = 12.0) -> List[float]:
    """Merge x-values within `tol` of each other; return one representative per cluster."""
    out: List[float] = []
    for x in sorted(xs):
        if out and abs(x - out[-1]) <= tol:
            out[-1] = (out[-1] + x) / 2
        else:
            out.append(x)
    return out


def _col_of(x0: float, col_bounds: List[float]) -> int:
    """Map a span's x0 coordinate to a 0-based column index (5 px tolerance)."""
    adjusted = [b - 5.0 for b in col_bounds[1:]]
    return bisect.bisect_right(adjusted, x0)


def _cluster_ys(ys: List[float], tol: float = 8.0) -> List[float]:
    """Merge y-values within `tol` of each other; return one representative per cluster."""
    if not ys:
        return []
    out = [ys[0]]
    for y in ys[1:]:
        if y - out[-1] > tol:
            out.append(y)
    return out

# Assuming this is defined globally in your script
TABLE_CAPTION_RE = re.compile(r"^(Table\s+\d+|Tab\.\s+\d+)", re.IGNORECASE)

def _find_table_col_bounds(blocks: List[dict]) -> List[float]:
    """Infer column x-start positions from all rows in the top structural header zone.

    Looks at both bold and non-bold blocks in the early part of the table
    to avoid missing un-bolded non-spanning root columns (like 'Species').
    """
    # Safety Check: If this block sequence represents a continued table page, 
    # headers won't match up properly. Check early blocks for continuation signals.
    is_continuation = False
    for b in blocks[:3]:
        for line in b.get("lines", []):
            text = "".join(sp.get("text", "") for sp in line.get("spans", [])).strip()
            if "(Continued)" in text or "continued" in text.lower():
                is_continuation = True
                break

    xs: List[float] = []
    
    # Only try to parse dynamic columns from headers if it's not a continuation page
    for block in blocks:
        text=block_text(block)
    if not is_continuation:
        # Peek at the top structural rows to capture every column start
        for b in blocks[:5]:  
            for line in b.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue
                text = "".join(sp.get("text", "") for sp in spans).strip()
                if not text or TABLE_CAPTION_RE.match(text) or "(Continued)" in text:
                    continue
                
                # Sort spans left-to-right to accurately evaluate spacing
                sorted_spans = sorted(spans, key=lambda s: s["bbox"][0])
                # print(len(sorted_spans))
                # for span in sorted_spans:
                #     print(span.get("text",""))
            
                
                last_x0 = -999.0
                # A 15-point gap tolerance usually safely distinguishes separate columns 
                # from multi-word/multi-span cell text in PDF document scales
                COL_GAP_TOLERANCE = 15.0 

                for sp in sorted_spans:
                    txt = sp.get("text", "").strip()
                    if not txt:
                        continue
                        
                    x0 = sp["bbox"][0]
                    
                    # Only treat this span as a brand new column boundary 
                    # if it sits far enough away from the last processed span
                    if (x0 - last_x0) > COL_GAP_TOLERANCE:
                        xs.append(x0)
                        last_x0 = x0
                    else:
                        # It's part of the same text column cell, update our rightward baseline boundary tracking
                        last_x0 = max(last_x0, sp["bbox"][2])
                        
    if not xs:
        # Return a safe, standard multi-column structure default if header bounds can't be inferred
        return [40.0, 110.0, 200.0, 300.0, 420.0, 500.0, float("inf")]
    
    return _cluster_xs(xs) + [float("inf")]
    return _cluster_xs(xs) + [float("inf")]


def table_blocks_to_html(
    blocks: List[dict],
    col_bounds: List[float],
    carry_species: str = "",
) -> Tuple[str, str]:
    """Convert a collected sequence of table PDF blocks into a <table> HTML string."""
    n_cols = len(col_bounds) - 1

    # ── 1. Generic Framework Header Parsing ──────────────────────────────────
    header_items: List[Dict[str, Any]] = []

    # Check if this block collection is explicitly a continuation page
    is_continuation = False
    for b in blocks[:3]:
        for line in b.get("lines", []):
            text = "".join(sp.get("text", "") for sp in line.get("spans", [])).strip()
            if "(Continued)" in text or "continued" in text.lower():
                is_continuation = True

    # Identify lines belonging structurally to the table header (only if not a multi-page continuation)
    if not is_continuation:
        for b in blocks[:5]:
            for line in b.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue

                text = "".join(sp.get("text", "") for sp in spans).strip()
                if not text or TABLE_CAPTION_RE.match(text) or "(Continued)" in text:
                    continue

                x0 = min(sp["bbox"][0] for sp in spans)
                x1 = max(sp["bbox"][2] for sp in spans)
                y0 = line["bbox"][1]

                col_start = _col_of(x0, col_bounds)
                col_end = _col_of(x1, col_bounds)

                header_items.append({
                    # FIXED: Removed html.escape here to prevent double-escaping inside _td() / final render
                    "text": text, 
                    "y0": y0,
                    "col_start": col_start,
                    "col_end": col_end,
                    "is_spanning": col_end > col_start,
                })

    thead = ""
    sub_hdr_cols = set()

    if header_items:
        y_coords = sorted({round(item["y0"], 1) for item in header_items})
        flat_headers: Dict[int, str] = {}

        if len(y_coords) >= 2:
            mid_y = sum(y_coords) / len(y_coords)
            top_tier = [item for item in header_items if item["y0"] <= mid_y]
            bottom_tier = [item for item in header_items if item["y0"] > mid_y]

            # 1. Fill bottom tier items (e.g., ITS, benA, CaM, RPB2)
            for item in bottom_tier:
                flat_headers[item["col_start"]] = item["text"]
                sub_hdr_cols.add(item["col_start"])

            # 2. Backfill un-split standalone root columns (Species, Strain no.)
            for item in top_tier:
                if item["col_start"] not in flat_headers:
                    flat_headers[item["col_start"]] = item["text"]
                else:
                    # If text already exists, preserve hierarchy or append safely
                    if item["text"] not in flat_headers[item["col_start"]]:
                        flat_headers[item["col_start"]] = f"{item['text']} {flat_headers[item['col_start']]}"
        else:
            for item in header_items:
                flat_headers[item["col_start"]] = item["text"]

        # Build final flat row matching all structural grid indices
        row_cells = []
        for c in range(n_cols):
            cell_text = flat_headers.get(c, "")
            if not cell_text:
                # Default generic fallbacks if something layout-wise leaves an explicit blank slot
                if c == 0: cell_text = "Species"
                elif c == 1: cell_text = "Strain no."
                else: cell_text = f"Column {c+1}"
            
            safe_hdr_text = html.escape(" ".join(cell_text.split()))
            row_cells.append(f"<th>{safe_hdr_text}</th>")

        thead = f"<thead><tr>{''.join(row_cells)}</tr></thead>"

    # ── 2. Collect Data Lines (Non-header content blocks) ────────────────────
    items: List[Tuple[float, int, str]] = []
    header_y_limit = max([item["y0"] for item in header_items]) if header_items else 0

    for b in blocks:
        for line in b.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            y0 = line["bbox"][1]
            
            # If it's a continuation page, we don't drop items based on header coordinates
            if not is_continuation and y0 <= header_y_limit + 2:
                continue  # Skip header lines
                
            x0 = spans[0]["bbox"][0]
            text = "".join(sp.get("text", "") for sp in spans).strip()
            
            # Skip page tracking artifacts or metadata headers on continuation sequences
            if not text or "(Continued)" in text or "continued" in text.lower():
                continue
                
            col = _col_of(x0, col_bounds)
            items.append((y0, col, text))

    if not items:
        return (f"<table>{thead}</table>" if thead else "", carry_species)

    items.sort()

    # ── 3. Detect Row Anchors ───────────────────────────────────────────────
    _acc_cols = sub_hdr_cols if sub_hdr_cols else set(range(1, n_cols))
    acc_ys_raw = sorted(
        {round(y0, 1) for y0, col, _ in items if col in _acc_cols}
    )
    row_anchors = _cluster_ys(acc_ys_raw)

    if not row_anchors:
        # Fallback handling: if no row anchors found via sub-headers, cluster by all elements
        all_ys_raw = sorted({round(y0, 1) for y0, _, _ in items})
        row_anchors = _cluster_ys(all_ys_raw)
        if not row_anchors:
            return ("", carry_species)

    def _row_range(i: int) -> Tuple[float, float]:
        lo = (
            (row_anchors[i] + row_anchors[i - 1]) / 2
            if i > 0
            else row_anchors[i] - 30
        )
        hi = (
            (row_anchors[i] + row_anchors[i + 1]) / 2
            if i < len(row_anchors) - 1
            else row_anchors[i] + 30
        )
        return lo, hi

    ranges = [_row_range(i) for i in range(len(row_anchors))]

    # ── 4. Assign Items to Rows ──────────────────────────────────────────────
    row_cells: List[dict] = [{} for _ in row_anchors]

    for y0, col, text in items:
        ri = next(
            (i for i, (lo, hi) in enumerate(ranges) if lo <= y0 <= hi),
            min(
                range(len(row_anchors)), key=lambda i: abs(y0 - row_anchors[i])
            ),
        )
        row_cells[ri].setdefault(col, []).append(text)

    rows: List[List[str]] = []
    for rc in row_cells:
        rows.append([" ".join(rc.get(c, [])) for c in range(n_cols)])

    # ── 5. Compute Rowspan for Grouping Column (Column 0) ────────────────────
    groups: List[Tuple[int, int, str]] = []
    current = carry_species or None
    start = 0

    for ri, row in enumerate(rows):
        sp = row[0].strip()
        if sp:
            if current is not None:
                groups.append((start, ri - start, current))
            current = sp
            start = ri
    if current is not None:
        groups.append((start, len(rows) - start, current))

    species_cell: dict = {}
    for s, cnt, txt in groups:
        species_cell[s] = (txt, cnt)
        for i in range(1, cnt):
            species_cell[s + i] = None

    last_species = groups[-1][2] if groups else carry_species

    # ── 6. Render <tbody> ────────────────────────────────────────────────────
    def _td(text: str, **attrs) -> str:
        attr_str = "".join(
            f' {k}="{v}"' for k, v in attrs.items() if v not in (None, 1, "")
        )
        cleaned_text = " ".join(text.split())
        safe_text = html.escape(cleaned_text)
        return f"<td{attr_str}>{safe_text}</td>"

    tbody_rows: List[str] = []
    for ri, row in enumerate(rows):
        tds: List[str] = []
        sc = species_cell.get(ri, "MISSING")
        if sc is None:
            pass
        elif sc == "MISSING":
            tds.append(_td(""))
        else:
            txt, rs = sc
            tds.append(_td(txt, rowspan=rs if rs > 1 else None))

        for c in range(1, n_cols):
            tds.append(_td(row[c]))

        tbody_rows.append("<tr>" + "".join(tds) + "</tr>")

    tbody = "<tbody>" + "\n".join(tbody_rows) + "</tbody>"
    
    # If the head is missing (continuation blocks), return layout cleanly without standard components crashing
    if thead:
        html_out = "<table>\n" + thead + "\n" + tbody + "\n</table>"
    else:
        html_out = "<table>\n" + tbody + "\n</table>"
        
    return html_out, last_species

# ---------------------------------------------------------------------------
# Main extraction
# ---------------------------------------------------------------------------

def extract_text(doc, output_path) -> None:
    with open(output_path, "w", encoding="utf-8") as outputfile:
        text_parts: List[str] = []
        table_parts: List[str] = []
        col_bounds: List[float] = []  # reset per unique table section
        carry_species: str = ""

        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            image_bboxes = get_figure_regions(page)
            prev_had_figure = bool(image_bboxes)

            table_blocks: List[dict] = []
            in_table = False

            def _flush_table() -> None:
                nonlocal col_bounds, carry_species
                if not table_blocks:
                    return
                # Recalculate columns per table sequence rather than freezing globally
                col_bounds = _find_table_col_bounds(table_blocks)
                html_str, carry_species = table_blocks_to_html(
                    table_blocks, col_bounds, carry_species
                )
                if html_str:
                    table_parts.append(html_str)
                table_blocks.clear()

            for b in blocks:
                if "lines" not in b:
                    continue

                if belongs_to_figure(b, image_bboxes):
                    prev_had_figure = True
                    continue

                text = clean_control_chars(block_text(b).replace('"', ""))

                if is_caption(text):
                    continue

                if text.lower().startswith("references"):
                    _flush_table()
                    outputfile.write(
                        "".join(text_parts) + "\n\n" + "".join(table_parts)
                    )
                    return
                if TABLE_CAPTION_RE.match(text.strip()):
                    _flush_table()  # Flush any open table block before starting a new one
                    in_table = True
                    table_parts.append("\n\n" + text.strip() + "\n\n")
                    continue

                size = _first_span_size(b)

                if in_table and (size < 10 or is_first_word_bold(b)):
                    table_blocks.append(b)
                    continue

                if in_table:
                    _flush_table()
                    in_table = False

                if prev_had_figure and not _is_body_text(text, size):
                    continue

                text_parts.append(" " + text + "\n\n")

            _flush_table()

        outputfile.write("".join(text_parts) + "\n\n" + "".join(table_parts))


extract_text(doc, output_path)
print("The text extracted from the PDF is saved in " + output_path)