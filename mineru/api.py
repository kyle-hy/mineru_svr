from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Header
from .parse_file import mu_parse_file, mu_parse_files

# 初始化业务模块路由
router = APIRouter()


async def get_user_id(x_user_id: Optional[str] = Header(None)):
    if not x_user_id:
        raise HTTPException(status_code=400, detail="Missing X-User-Id header")
    return x_user_id


@router.post(
    "/parse_files",
    summary="上传文档列表，返回MinerU解析后的文本内容",
)
async def parse_files(
    files: List[UploadFile] = File(...),
    user_id: str = Depends(get_user_id),
):

    data, msg = await mu_parse_files(files, user_id)
    if msg:
        return {"data": "", "msg": msg, "code": -1}

    return {"data": data, "msg": "ok", "code": 1}


@router.post(
    "/parse_file",
    summary="上传文档，返回MinerU解析后的文本内容",
)
async def parse_file(
    file: UploadFile = File(...),
    user_id: str = Depends(get_user_id),
):

    cnt, msg = await mu_parse_file(file, user_id)
    if msg:
        return {"data": "", "msg": msg, "code": -1}
    return {"data": cnt, "msg": "ok", "code": -1}
