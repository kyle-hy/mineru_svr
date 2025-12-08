import requests
import logging
import time


def upload_parse(file_name, file_data, user_id):
    return "你好呀"
    url_mineru_upload = "http://10.244.12.108:18088/api/upload"
    headers = {"x-user-id": user_id}

    file_extension = file_name.split(".")[-1].lower()

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

    # 获取对应的 MIME type，默认为 application/octet-stream
    content_type = mime_types.get(file_extension, "application/octet-stream")

    files = {
        "files": (file_name, file_data, content_type),
    }

    # 上传文件至MinerU
    response = requests.post(
        url_mineru_upload, headers=headers, files=files, timeout=60
    )

    # logging.info(response)
    if response.status_code != 200:
        logging.error(f"MinerU解析异常: {response}")
        return ""
    res = response.json()
    mineru_file_id = res["files"][0]["id"]
    result_url = "http://10.244.12.108:18088/api/files" + f"/{mineru_file_id}"
    status = ""
    retry_count = 0
    while True:
        retry_count += 1
        time.sleep(1)

        try:
            response = requests.get(result_url, headers=headers, timeout=3)
            response_data = response.json()
            status = response_data["status"]

            if status == "parsed":
                content_url = (
                    "http://10.244.12.108:18088/api/files"
                    + f"/{mineru_file_id}/parsed_content"
                )
                content_res = requests.get(content_url, headers=headers, timeout=3)
                if content_res.status_code == 200:
                    content = content_res.content.decode()

                    if content[0] == '"' and content[-1] == '"' and len(content) > 1:
                        content = content[1:-1]

                    # 删除留存在MinerU服务器上的文件，节省服务器空间
                    delete_url = (
                        "http://10.244.12.108:18088/api/files" + f"/{mineru_file_id}"
                    )
                    result = requests.delete(
                        url=delete_url, headers=headers, timeout=10
                    )
                    if result.status_code == 200:
                        logging.info(f"{mineru_file_id}文档解析完成，并从MinerU中移除")
                        pass

                    return content
            elif status == "pending":
                try:
                    logging.info("文件队列阻塞，执行插队解析。")
                    response_status = requests.post(
                        result_url + "/parse", headers=headers, timeout=10
                    )
                except requests.exceptions.Timeout:
                    logging.info(
                        f'{time.strftime("[%d/%b/%Y %H:%M:%S]")}, 大文件解析中···'
                    )

            elif status == "parsing":
                continue
            else:
                logging.warning(f"文件 {file_name} 异常状态: {status}")
                break

        except Exception as e:
            logging.error(f"文件 {file_name} 解析失败: {e}")
            break
    return ""
