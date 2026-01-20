from fastapi.responses import Response
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Header, Query
from . import convert_tmp as ch


# 初始化业务模块路由
router = APIRouter()


async def check_uid(x_user_id: str | None = Header(None)):
    """校验user_id参数"""
    if not x_user_id:
        raise HTTPException(status_code=400, detail="Missing X-User-Id header")
    return x_user_id


@router.post(
    "/upload",
    summary="上传md文档，返回文档ID列表",
)
async def upload(
    files: list[UploadFile] = File(...),
    user_id: str = Depends(check_uid),
):
    cnt, msg = await ch.to_tmps(files, user_id)
    if msg:
        return {"data": "", "msg": msg, "code": -1}
    return {"data": cnt, "msg": "ok", "code": 1}


@router.get(
    "/content",
    summary="根据文档ID获取文件内容",
)
async def get_content(
    file_id: int = Query(..., description="文件ID"),
    user_id: str = Depends(check_uid),
):
    cnt, msg = await ch.tmp_content(file_id, user_id)
    if msg:
        return {"data": "", "msg": msg, "code": -1}
    return {"data": cnt, "msg": "ok", "code": 1}


@router.get(
    "/contents",
    summary="根据文档ID列表，获取文件内容",
)
async def get_contents(
    file_ids: list[int] = Query(..., description="文件ID列表"),
    user_id: str = Depends(check_uid),
):
    cnt, msg = await ch.tmp_contents(file_ids, user_id)
    if msg:
        return {"data": cnt, "msg": msg, "code": -1}
    return {"data": cnt, "msg": "ok", "code": 1}
