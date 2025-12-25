from fastapi import FastAPI

# 引入业务模块进行功能路由注册
from .mineru.api import router as mrouter
from .libreoffice.api import router as lorouter
from .excel.api import router as erouter

# 添加业务模块路由,
app = FastAPI()
app.include_router(mrouter, prefix="/api", tags=["MinerU"])
app.include_router(lorouter, prefix="/api", tags=["LibreOffice"])
app.include_router(erouter, prefix="/api/excel", tags=["Excel"])

if __name__ == "__main__":
    import uvicorn

    # 启动服务
    uvicorn.run(app, host="0.0.0.0", port=8091)
