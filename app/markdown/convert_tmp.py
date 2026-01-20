import os
from pathlib import Path
import aiofiles.os as aos
import aiofiles.ospath as aop
from app.utils.batch import batch_async
from app.utils import aiofile as af
from app.utils.autoid import next_id


def extract_filename(fcnt):
    """
    提取第一行为文件名,后续为内容
    fcnt格式：filename\ncontent
    """
    parts = fcnt.split("\n", 1)  # 只分割一次，最多分成两部分
    if len(parts) == 2:
        filename, content = parts
    else:
        # 如果没有 \n，说明只有 filename，content 为空
        filename = parts[0]
        content = ""
    return filename, content


async def to_tmps(files, user_id) -> tuple[str, str]:
    # 提取批量结果
    files_msg = []
    for file in files:
        # 临时文件名
        id = next_id()
        tmp_name = f"{user_id}_{id}.md"

        # 临时文件头部写入文件名
        content = await file.read()
        cnt = file.filename + "\n" + content.decode("utf-8")

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


async def tmp_content(file_id, user_id) -> tuple[dict, str]:
    # 触发批处理获取结果
    tmp_name = f"{user_id}_{file_id}.md"
    fpath = os.path.join("tmp", tmp_name)
    fpath = Path(fpath)
    if not await aop.isfile(fpath):
        return {}, f"file not found of id: {file_id}"

    # 读取临时存储的文件内容
    cnt = await af.read_file(fpath)
    filename, cnt = extract_filename(cnt)

    # 删除临时文件
    await aos.unlink(fpath)

    data = {
        "id": file_id,
        "user_id": user_id,
        "content": cnt,
        "filename": filename,
    }
    return data, ""


async def tmp_contents(file_ids, user_id) -> tuple[list, str]:
    async def worker(param):
        file_id, user_id = param
        return await tmp_content(file_id, user_id)

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
