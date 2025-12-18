import io
import httpx
from fastapi import UploadFile
from app.utils.log import log

MIME_TYPES = {
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


# mineru-web接口调用封装类
class MUClient:
    def __init__(self, addr: str, uid: str, timeout: float = 20.0):
        self.addr = addr.rstrip("/")
        self.headers = {"x-user-id": uid}
        self.timeout = timeout

    async def __aenter__(self):
        """async with 开始时申请资源"""
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(self.timeout))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """async with 结束时释放资源"""
        await self.client.aclose()

    async def proxy_upload(
        self,
        file: UploadFile | list[UploadFile],
    ) -> tuple[list[str], str | None]:
        """中转文件到mineru解析服务器进行异步解析"""
        try:
            # 上传对象
            names = []
            multipart_files = []  # 多个同名字段上传使用 list[tuple]
            file_list = file if isinstance(file, list) else [file]
            for f in file_list:
                names.append(f.filename)
                multipart_files.append(("files", (f.filename, f.file, f.content_type)))

            # 异步上传
            resp = await self.client.post(
                f"{self.addr}/api/upload",
                headers=self.headers,
                files=multipart_files,
            )

            # 异常状态
            if resp.status_code != 200:
                msg = f"upload failed: {resp.status_code} : {names}"
                log.warning(msg)
                return [], msg

            # 解析结果
            data = resp.json()
            id_list = [
                (item.get("id"), item.get("filename")) for item in data.get("files", [])
            ]

            # 数量是否对齐
            if len(id_list) != len(file_list):
                msg = f"got:{len(id_list)}, expected:{len(file_list)} {names}"
                log.warning(msg)
                # 依然部分返回
                return id_list, msg

            return id_list, None
        except Exception as e:
            msg = f"exception: {type(e).__name__}: {str(e)} {names}"
            log.warning(msg)
            return None, msg

    async def upload_file(
        self,
        file_name: str,
        file_data: bytes,
        content_type: str,
    ) -> tuple[str | None, str | None]:
        """上传文档到mineru解析服务器进行异步解析"""
        try:
            # 单文件或明确不同字段名使用 dict
            files = {
                "files": (
                    file_name,
                    io.BytesIO(file_data),
                    content_type,
                ),
            }
            resp = await self.client.post(
                f"{self.addr}/api/upload",
                headers=self.headers,
                files=files,
            )
            if resp.status_code != 200:
                msg = f"upload failed: {resp.status_code} {file_name}"
                log.warning(msg)
                return None, msg
            data = resp.json()
            return data["files"][0]["id"], None
        except Exception as e:
            msg = f"exception: {type(e).__name__}: {str(e)} {file_name}"
            log.warning(msg)
            return None, msg

    async def get_status(self, file_id: str) -> tuple[str | None, str | None]:
        """根据文档id查询异步解析结果"""
        try:
            resp = await self.client.get(
                f"{self.addr}/api/files/{file_id}",
                headers=self.headers,
            )
            if resp.status_code != 200:
                msg = f"get_status failed: {resp.text} {file_id}"
                log.warning(msg)
                return None, msg
            return resp.json().get("status"), None
        except Exception as e:
            msg = f"exception: {type(e).__name__}: {str(e)} {file_id}"
            log.warning(msg)
            return None, msg

    async def trigger_parse(self, file_id: str) -> str | None:
        """触发插队解析"""
        try:
            resp = await self.client.post(
                f"{self.addr}/api/files/{file_id}/parse",
                headers=self.headers,
            )
            if resp.status_code not in (200, 204):
                msg = f"trigger_parse failed: {resp.text}"
                log.warning(msg)
                return msg
            return None
        except Exception as e:
            msg = f"exception: {type(e).__name__}: {str(e)} {file_id}"
            log.warning(msg)
            return msg

    async def get_content(self, file_id: str) -> tuple[str | None, str | None]:
        """获取解析结果内容"""
        try:
            resp = await self.client.get(
                f"{self.addr}/api/files/{file_id}/parsed_content",
                headers=self.headers,
            )
            if resp.status_code != 200:
                msg = f"get_content failed: {resp.text}"
                log.warning(msg)
                return None, msg
            content = resp.text
            if content.startswith('"') and content.endswith('"'):
                content = content[1:-1]
            return content, None
        except Exception as e:
            msg = f"exception: {type(e).__name__}: {str(e)} {file_id}"
            log.warning(msg)
            return None, msg

    async def delete_file(self, file_id: str) -> str | None:
        try:
            resp = await self.client.delete(
                f"{self.addr}/api/files/{file_id}",
                headers=self.headers,
            )
            if resp.status_code not in (200, 204):
                msg = f"delete file failed: {resp.text}"
                return msg
            return None
        except Exception as e:
            msg = f"exception: {type(e).__name__}: {str(e)} {file_id}"
            log.warning(msg)
            return msg
