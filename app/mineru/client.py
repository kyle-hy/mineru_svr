import io
import httpx
from typing import Optional, Tuple

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

    async def upload_file(
        self, file_name: str, file_data: bytes, content_type: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """上传文档到mineru解析服务器进行异步解析"""
        files = {
            "files": (file_name, io.BytesIO(file_data), content_type),
        }
        try:
            resp = await self.client.post(
                f"{self.addr}/api/upload",
                headers=self.headers,
                files=files,
            )
            if resp.status_code != 200:
                return None, f"upload failed: {resp.status_code} {resp.text}"
            data = resp.json()
            return data["files"][0]["id"], None
        except Exception as e:
            return None, str(e)

    async def get_status(self, file_id: str) -> Tuple[Optional[str], Optional[str]]:
        """根据文档id查询异步解析结果"""
        try:
            resp = await self.client.get(
                f"{self.addr}/api/files/{file_id}",
                headers=self.headers,
            )
            if resp.status_code != 200:
                return None, f"get_status failed: {resp.text}"
            return resp.json().get("status"), None
        except Exception as e:
            return None, str(e)

    async def trigger_parse(self, file_id: str) -> Optional[str]:
        """触发插队解析"""
        try:
            resp = await self.client.post(
                f"{self.addr}/api/files/{file_id}/parse",
                headers=self.headers,
            )
            if resp.status_code not in (200, 204):
                return f"trigger_parse failed: {resp.text}"
            return None
        except Exception as e:
            return str(e)

    async def get_content(self, file_id: str) -> Tuple[Optional[str], Optional[str]]:
        """获取解析结果内容"""
        try:
            resp = await self.client.get(
                f"{self.addr}/api/files/{file_id}/parsed_content",
                headers=self.headers,
            )
            if resp.status_code != 200:
                return None, f"get_content failed: {resp.text}"
            content = resp.text
            if content.startswith('"') and content.endswith('"'):
                content = content[1:-1]
            return content, None
        except Exception as e:
            return None, str(e)

    async def delete_file(self, file_id: str) -> Optional[str]:
        try:
            resp = await self.client.delete(
                f"{self.addr}/api/files/{file_id}",
                headers=self.headers,
            )
            if resp.status_code not in (200, 204):
                return f"delete_file failed: {resp.text}"
            return None
        except Exception as e:
            return str(e)
