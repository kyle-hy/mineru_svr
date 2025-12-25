from fastapi.responses import Response
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Header, Query

from .convert_pdf import to_pdf


# 初始化业务模块路由
router = APIRouter()


async def check_uid(x_user_id: str | None = Header(None)):
    """校验user_id参数"""
    if not x_user_id:
        raise HTTPException(status_code=400, detail="Missing X-User-Id header")
    return x_user_id


@router.post(
    "/convert_pdf",
    summary="上传文档，返回转格式后的PDF二进制内容",
)
async def convert_pdf(
    file: UploadFile = File(...),
):
    pdf_bytes, msg = await to_pdf(file)
    if msg:
        raise HTTPException(502, "Failed to fetch PDF")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",  # 必须
        headers={
            "Content-Disposition": "inline; filename=sample.pdf"  # inline=浏览器预览，attachment=强制下载
        },
    )
