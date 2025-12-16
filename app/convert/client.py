import io
import httpx
import uuid
from typing import Optional, Tuple


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

    async def convert_pdf(
        self, file_name: str, file_data: bytes
    ) -> Tuple[Optional[bytes], str]:
        """上传文档到mineru解析服务器进行异步解析"""
        files = {
            "file": (
                str(uuid.uuid4().hex) + ".pdf",
                io.BytesIO(file_data),
                file_name.rsplit(".", 1)[-1].lower(),
            )
        }
        try:
            async with self.client.stream(
                "POST",
                url=f"{self.addr}/forms/libreoffice/convert",
                files=files,
                timeout=60.0,
            ) as response:
                status = response.status_code
                if status != 200:
                    # 尝试读取错误信息（可能是 JSON 或 text）
                    try:
                        error_detail = await response.aread()
                        error_msg = error_detail.decode("utf-8", errors="replace")
                    except Exception as e:
                        error_msg = "unknown error"
                    return None, f"convert failed: {status} {error_msg}"

                # 流式读取 PDF 内容 100KB/chunk
                pdf_bytes = bytearray()
                async for chunk in response.aiter_bytes(chunk_size=102400):
                    if chunk:
                        pdf_bytes.extend(chunk)
                return bytes(pdf_bytes), ""
        except httpx.TimeoutException as e:
            return None, f"Timeout during conversion: {str(e)}"
        except httpx.HTTPError as e:
            return None, f"HTTP error: {str(e)}"
        except Exception as e:
            return None, f"Unexpected error: {type(e).__name__}: {str(e)}"
