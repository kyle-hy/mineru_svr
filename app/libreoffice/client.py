import io
import httpx
import uuid
from fastapi import UploadFile
from typing import Optional, Tuple
from app.utils.log import log


# Gotenberg容器LibreOffice格式转换接口调用封装类
class LOClient:
    def __init__(self, addr: str, timeout: float = 10.0):
        self.addr = addr.rstrip("/")
        self.timeout = timeout

    async def __aenter__(self):
        """async with 开始时申请资源"""
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(self.timeout))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """async with 结束时释放资源"""
        await self.client.aclose()

    async def convert_pdf(self, file: UploadFile) -> tuple[bytes | None, str]:
        """代理上传文档到libreoffice转为PDF格式"""
        files = {
            "file": (
                str(uuid.uuid4().hex) + ".pdf",
                file.file,
                file.content_type,
            )
        }
        try:
            # 异步httpx流式请求
            async with self.client.stream(
                "POST",
                url=f"{self.addr}/forms/libreoffice/convert",
                files=files,
                timeout=60.0,
            ) as resp:
                status = resp.status_code
                if status != 200:
                    detail = await resp.aread()
                    msg = detail.decode("utf-8", errors="replace")
                    msg = f"convert failed: {status} {file.filename} {msg}"
                    log.warning(msg)
                    return None, msg

                # 流式读取 PDF 内容 100KB/chunk
                pdf_bytes = bytearray()
                async for chunk in resp.aiter_bytes(chunk_size=102400):
                    if chunk:
                        pdf_bytes.extend(chunk)
                return bytes(pdf_bytes), ""

        except httpx.TimeoutException as e:
            msg = f"timeout : {e} {file.filename}"
            log.warning(msg)
            return None, msg
        except Exception as e:
            msg = f"exception: {type(e).__name__}: {e} {file.filename}"
            log.warning(msg)
            return None, msg
