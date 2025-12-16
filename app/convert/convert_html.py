import os
from typing import Tuple
import tempfile
from pathlib import Path
from .xls import xls_to_html
from .xlsx import xlsx_to_html
from .html import align_table


async def to_html(file) -> Tuple[str, str]:
    fpath = Path(file.filename)
    ext = fpath.suffix.lower()
    if ext not in [".xls", ".xlsx"]:
        return "", f"unsupported {ext}"

    # 存临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        temp_file = tmp.name
        content = await file.read()
        tmp.write(content)

    # 格式转换
    if ext == ".xls":
        html_cnt = xls_to_html(temp_file)
    if ext == ".xlsx":
        html_cnt = xlsx_to_html(temp_file)

    # 清理并对齐单元格
    html_cnt = align_table(html_cnt)

    # 清理资源
    await file.close()
    if temp_file and os.path.exists(temp_file):
        os.unlink(temp_file)  # 删除临时文件

    return html_cnt, ""
