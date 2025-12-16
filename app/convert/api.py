from fastapi.responses import Response
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.convert.convert_html import to_html
from .convert_pdf import to_pdf


# 初始化业务模块路由
router = APIRouter()


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


@router.post(
    "/convert_html",
    summary="上传Excel文档，返回HTML表格内容",
)
async def convert_html(
    file: UploadFile = File(...),
):
    cnt, msg = await to_html(file)
    if msg:
        return {"data": "", "msg": msg, "code": -1}
    return {"data": cnt, "msg": "ok", "code": 1}
