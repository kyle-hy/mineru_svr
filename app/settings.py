from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """通过环境变量获取配置"""

    # mineru-web服务地址
    mineru_url: str = "http://172.17.30.21:8089"

    # Gotenberg容器LibreOffice服务地址
    office_url: str = "http://172.17.30.110:45505"
    # office_url: str = "http://localhost:3000"


# 服务配置
cfg = Settings()
