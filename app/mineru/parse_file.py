import asyncio
from typing import Any
from .client import MUClient
from app.settings import cfg
from app.utils.batch import batch_async
from fastapi import UploadFile


async def mu_parse_files(files, user_id):
    """解析文件列表"""
    return await upload_parse(files, user_id)


async def mu_parse_file(file, user_id):
    """解析单个文件"""
    cnts, err = await upload_parse(file, user_id)
    if len(cnts) > 0:
        return cnts[0]["content"], None
    return "", err


async def upload_parse(
    file: UploadFile | list[UploadFile],
    user_id: str,
) -> tuple[list[Any], str | None]:
    """代理上传并解析文档，并清理服务器留存的数据"""
    async with MUClient(cfg.mineru_url, user_id) as client:
        # 上传文件获取文件ID列表
        file_items, err = await client.proxy_upload(file)
        if err:
            return "", err

        # 定义批处理函数
        async def check_content(file_item) -> tuple[str, str]:
            # 轮询解析
            file_id, file_name = file_item
            for _ in range(300):
                await asyncio.sleep(1)
                status, err = await client.get_status(file_id)
                if err:
                    return "", err

                # 解析完成
                if status == "parsed":
                    content, err = await client.get_content(file_id)
                    if err:
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

        # 触发批处理获取结果
        results = await batch_async(check_content, file_items)

        # 提取正常请求的结果
        parse_cnts = []
        err_msgs = []
        for status, idx, (file_id, file_name), result in results:
            if status:
                # 逻辑函数正常返回
                cnt, msg = result
                parse_cnts.append({"filename": file_name, "content": cnt})
            else:
                # 批处理函数异常返回
                err_msgs.append(f"{file_name}：{result}")
        return parse_cnts, "\n".join(err_msgs)
