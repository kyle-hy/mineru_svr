import logging
import asyncio
from typing import Optional, Tuple
from .client import MIME_TYPES, MUClient
from app.settings import cfg


async def mu_parse_files(files, user_id):
    """解析文件列表"""
    data = []
    for file in files:
        file_data = await file.read()
        cnt, err = await upload_parse(file.filename, file_data, user_id)
        if err:
            return [], err
        data.append({"filename": file.filename, "content": cnt})
    return data, None


async def mu_parse_file(file, user_id):
    """解析单个文件"""
    file_data = await file.read()
    cnt, err = await upload_parse(file.filename, file_data, user_id)
    if err:
        return "", err
    return cnt, None


async def upload_parse(
    file_name: str, file_data: bytes, user_id: str
) -> Tuple[str, Optional[str]]:
    """上传并解析文档，并清理服务器留存的数据"""

    ext = file_name.rsplit(".", 1)[-1].lower()
    content_type = MIME_TYPES.get(ext, "application/octet-stream")
    async with MUClient(cfg.base_url, user_id, timeout=cfg.timeout) as client:
        # 上传
        file_id, err = await client.upload_file(file_name, file_data, content_type)
        if err:
            logging.info(f"{file_name}:{file_id} 获取状态异常：{err}")
            return "", err

        # 轮询解析
        for _ in range(300):
            await asyncio.sleep(1)
            status, err = await client.get_status(file_id)
            if err:
                logging.info(f"{file_name}:{file_id} 获取状态异常：{err}")
                return "", err

            # 解析完成
            if status == "parsed":
                content, err = await client.get_content(file_id)
                if err:
                    logging.info(f"{file_name}:{file_id} 获取内容异常：{err}")
                    return "", err
                await client.delete_file(file_id)
                return content, None

            # 排队等待
            if status == "pending":
                await client.trigger_parse(file_id)

            # 正则解析
            elif status == "parsing":
                continue
            else:
                return "", f"unknown status: {status}"

        return "", "timeout"
