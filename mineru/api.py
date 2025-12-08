from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Header
from .parse_file import upload_parse


async def get_user_id(x_user_id: Optional[str] = Header(None)):
    if not x_user_id:
        raise HTTPException(status_code=400, detail="Missing X-User-Id header")
    return x_user_id


# 初始化业务模块
router = APIRouter()


@router.post("/parse_file", summary="上传文档，返回MinerU解析后的文本内容")
async def parse_file(
    files: List[UploadFile] = File(...),
    user_id: str = Depends(get_user_id),
):

    content = upload_parse(file_name="finename", file_data="", user_id="user_id")
    return {"data": content, "msg": "ok", "code": 1}
