import os
import re
from typing import Tuple
from pathlib import Path
from .xls import xls_to_html
from .xlsx import xlsx_to_html
from .html import align_table
from app.utils.batch import batch_async
from app.utils import aiofile as af
from app.utils.autoid import next_id


async def to_html(file) -> Tuple[str, str]:
    # 检查文件类型
    fpath = Path(file.filename)
    ext = fpath.suffix.lower()
    if ext not in [".xls", ".xlsx"]:
        return "", f"unsupported {ext}"

    # 存临时文件
    tmp_name = f"{next_id()}{ext}"
    tmp_path = os.path.join("tmp", "all", tmp_name)
    tmp_path = Path(tmp_path)
    content = await file.read()
    await af.write_bin(tmp_path, content)

    # 格式转换
    if ext == ".xls":
        html_cnt = xls_to_html(tmp_path)
    if ext == ".xlsx":
        html_cnt = xlsx_to_html(tmp_path)

    # 清理并对齐单元格
    html_cnt = align_table(html_cnt)

    # 清理资源
    await af.unlink(tmp_path)  # 删除临时文件

    return html_cnt, ""


def extract_filename(ss):
    """
    提取<html>之前的文件名
    内容：filename<html>...
    """
    pattern = r"([^<]*?\.(?i:xlsx?))(?=\s*<html\b)"
    match = re.search(pattern, ss)
    if match:
        filename = match.group(1)
        content = re.sub(pattern, "", ss, count=1)
        return filename, content
    return "", ss


async def to_htmls(files, user_id) -> Tuple[str, str]:
    # 触发批处理获取结果
    results = await batch_async(to_html, files)

    # 提取批量结果
    files_msg = []
    for status, idx, file, (cnt, msg) in results:
        if status and not msg:
            # 临时文件名
            id = next_id()
            tmp_name = f"{user_id}_{id}.md"

            # 临时文件头部写入文件名

            cnt = file.filename + cnt

            # 写文件
            await af.write_file(os.path.join("tmp", tmp_name), cnt)

            # 文件信息
            files_msg.append(
                {
                    "id": id,
                    "user_id": user_id,
                    "filename": file.filename,
                }
            )
    output = {
        "total": len(files),
        "files": files_msg,
    }
    return output, ""


async def html_content(file_id, user_id) -> Tuple[dict, str]:
    # 触发批处理获取结果
    tmp_name = f"{user_id}_{file_id}.md"
    fpath = os.path.join("tmp", tmp_name)
    fpath = Path(fpath)
    if not await af.file_exists(fpath):
        return {}, f"file not found of id: {file_id}"

    # 读取临时存储的文件内容
    cnt = await af.read_file(fpath)
    filename, cnt = extract_filename(cnt)

    # 删除临时文件
    await af.unlink(fpath)

    data = {
        "id": file_id,
        "user_id": user_id,
        "content": cnt,
        "filename": filename,
    }
    return data, ""


async def html_contents(file_ids, user_id) -> Tuple[list, str]:
    async def worker(param):
        file_id, user_id = param
        return await html_content(file_id, user_id)

    # 批量读取文件
    params = [(file_id, user_id) for file_id in file_ids]
    results = await batch_async(worker, params)

    # 提取批量结果
    files_data = []
    err_msg = []
    for status, idx, param, (cnt, msg) in results:
        if status:
            if msg:
                err_msg.append(msg)
                continue
            else:
                files_data.append(cnt)

    return files_data, " | ".join(err_msg)
