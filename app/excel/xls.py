import os
import re
import xlrd
import subprocess
from pathlib import Path
from html import escape


def format_cell(cell):
    """避免整数变成小数，如 1.0 → 1"""
    if cell.ctype == 2:  # number
        val = cell.value
        if val == int(val):
            return str(int(val))
        return str(val)

    value = escape(str(cell.value)) if cell.value else ""
    value = re.sub(r"\r\n|\r|\n", "<br>", value)
    return value


def find_trim_ranges(sheet):
    """找到首部全空的行数与列数"""
    nrows, ncols = sheet.nrows, sheet.ncols

    # 前置空行
    trim_top = 0
    for r in range(nrows):
        if all(sheet.cell(r, c).ctype == 0 for c in range(ncols)):
            trim_top += 1
        else:
            break

    # 前置空列
    trim_left = 0
    for c in range(ncols):
        if all(sheet.cell(r, c).ctype == 0 for r in range(nrows)):
            trim_left += 1
        else:
            break
    return trim_top, trim_left


def sheet_to_html(sheet_title, sheet, book):
    """把单个 sheet 转 HTML 表格"""

    font_list = book.font_list  # 所有字体对象
    xf_list = book.xf_list  # 所有格式对象

    # 去掉首部空行/列
    trim_top, trim_left = find_trim_ranges(sheet)
    nrows = sheet.nrows - trim_top
    ncols = sheet.ncols - trim_left

    # 处理合并单元格
    merged = []
    for r1, r2, c1, c2 in sheet.merged_cells:
        if r2 <= trim_top or c2 <= trim_left:
            continue
        merged.append(
            (
                max(0, r1 - trim_top),
                max(0, r2 - trim_top),
                max(0, c1 - trim_left),
                max(0, c2 - trim_left),
            )
        )

    skip = set()
    html = [f"<table><caption>{sheet_title}</caption>"]
    for r in range(trim_top, sheet.nrows):
        rr = r - trim_top
        if rr >= nrows:
            break

        html.append("<tr>")
        for c in range(trim_left, sheet.ncols):
            cc = c - trim_left
            if cc >= ncols:
                break

            if (rr, cc) in skip:
                continue

            # 合并单元格处理
            rowspan = 1
            colspan = 1
            for r1, r2, c1, c2 in merged:
                if r1 == rr and c1 == cc:
                    rowspan = r2 - r1
                    colspan = c2 - c1
                    for rr2 in range(r1, r2):
                        for cc2 in range(c1, c2):
                            if not (rr2 == r1 and cc2 == c1):
                                skip.add((rr2, cc2))
                    break

            cell = sheet.cell(r, c)
            text = format_cell(cell)

            # 粗体 → th
            xf = xf_list[cell.xf_index]
            font = font_list[xf.font_index]
            tag = "th" if font.bold == 1 else "td"

            attrs = ""
            if rowspan > 1:
                attrs += f' rowspan="{rowspan}"'
            if colspan > 1:
                attrs += f' colspan="{colspan}"'
            html.append(f"<{tag}{attrs}>{text}</{tag}>")
        html.append("</tr>")
    html.append("</table>")

    # 只有<table></table>的空表
    if len(html) == 2:
        return ""
    return "".join(html)


def xls_to_html(xls_path):
    """遍历所有 sheet，生成完整 HTML 字符串"""
    book = xlrd.open_workbook(xls_path, formatting_info=True)

    output = []
    for i in range(book.nsheets):
        sheet = book.sheet_by_index(i)
        title = escape(sheet.name)
        # 该 sheet 的 HTML 表格
        output.append(sheet_to_html(title, sheet, book))

    return "\n".join(output)


def xls_to_xlsx(xls_path, output_dir=None):
    xls_path = Path(xls_path)
    suffix = xls_path.suffix.lower()
    if suffix != ".xls":
        return ""

    if output_dir is None:
        output_dir = xls_path.parent

    # LibreOffice / OpenOffice 可执行程序
    # https://www.libreoffice.org/download/download-libreoffice/
    cmd = [
        "soffice",
        "--headless",
        "--convert-to",
        "xlsx",
        "--outdir",
        output_dir,
        xls_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    xlsx_path = os.path.join(output_dir, xls_path.stem + ".xlsx")
    return xlsx_path


if __name__ == "__main__":
    # 使用示例
    print("-----")
    html_table = xls_to_html("data/input/xls/test.xls")
    # 写入文件
    with open("test.md", "w", encoding="utf-8") as f:
        f.write(html_table)
