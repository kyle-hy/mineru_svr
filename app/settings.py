from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """通过环境变量获取配置"""

    # 超时设置
    timeout: float = 20.0

    # mineru-web服务地址
    base_url: str = "http://172.17.30.21:8089"


# 服务配置
cfg = Settings()
