import requests
import logging
import asyncio
import io
import time


async def mu_parse_files(files, user_id):
    """解析文件列表"""
    data = []
    for file in files:
        file_data = await file.read()
        cnt, err = upload_parse(file.filename, file_data, user_id)
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


async def upload_parse(file_name, file_data, user_id):
    """上传文件并等待解析内容结果返回"""

    # mineru-web backend的相关URL
    URL_ADDR = "http://172.17.30.21:8089"
    URL_UPLOAD = URL_ADDR + "/api/upload"
    URL_CRUD = URL_ADDR + "/api/files/{file_id}"
    URL_PARSE = URL_ADDR + "/api/files/{file_id}/parse"
    URL_CONTENT = URL_ADDR + "/api/files/{file_id}/parsed_content"

    # 获取对应的 MIME type，默认为 application/octet-stream
    mime_types = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "bmp": "image/bmp",
        "gif": "image/gif",
        "tiff": "image/tiff",
        "tif": "image/tiff",
        "webp": "image/webp",
        "svg": "image/svg+xml",
        "ico": "image/x-icon",
    }
    file_extension = file_name.split(".")[-1].lower()
    content_type = mime_types.get(file_extension, "application/octet-stream")

    # 上传文件至MinerU
    headers = {"x-user-id": user_id}
    files = {"files": (file_name, io.BytesIO(file_data), content_type)}
    response = requests.post(URL_UPLOAD, headers=headers, files=files, timeout=60)
    if response.status_code != 200:
        logging.error(f"文件：{file_name} MinerU上传异常: {response}")
        return "", response
    # 解析上传返回的文件ID
    res = response.json()
    file_id = res["files"][0]["id"]

    # 训练结果
    status = ""
    err_msg = ""
    retry_count = 0
    while retry_count < 300:
        retry_count += 1
        await asyncio.sleep(1)
        try:
            response = requests.get(
                URL_CRUD.format(file_id=file_id), headers=headers, timeout=3
            )
            response_data = response.json()
            status = response_data["status"]
            # 解析完成，请求获取文本内容
            if status == "parsed":
                content_res = requests.get(
                    URL_CONTENT.format(file_id=file_id), headers=headers, timeout=3
                )
                if content_res.status_code == 200:
                    content = content_res.content.decode()
                    if content[0] == '"' and content[-1] == '"' and len(content) > 1:
                        content = content[1:-1]

                    # 删除留存在MinerU服务器上的文件
                    result = requests.delete(
                        URL_CRUD.format(file_id=file_id), headers=headers, timeout=10
                    )
                    if result.status_code == 200:
                        logging.info(
                            f"{file_name}:{file_id} 文档解析完成，并从MinerU中移除"
                        )
                        pass
                    return content, None

            elif status == "pending":
                try:
                    logging.info(
                        f"文件队列阻塞，执行插队解析文件：{file_name}:{file_id}"
                    )
                    response_status = requests.post(
                        URL_PARSE.format(file_id=file_id), headers=headers, timeout=10
                    )
                except requests.exceptions.Timeout:
                    logging.info(
                        f'{time.strftime("[%d/%b/%Y %H:%M:%S]")}, {file_name}:{file_id}大文件解析中···'
                    )

            elif status == "parsing":
                continue
            else:
                logging.warning(f"{file_name}:{file_id} 异常状态: {status}")
                err_msg = status
                break

        except Exception as e:
            logging.error(f"{file_name}:{file_id}: 解析失败: {e}")
            err_msg = e
            break
    return "", err_msg
