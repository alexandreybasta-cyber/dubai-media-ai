from pydantic_settings import BaseSettings
from pydantic import model_validator


class Settings(BaseSettings):
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_VIDEO_API_KEY: str = ""
    DASHSCOPE_BASE_URL: str = "https://ws-gk4cdiq85mzbjrvp.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
    DASHSCOPE_API_URL: str = "https://ws-gk4cdiq85mzbjrvp.ap-southeast-1.maas.aliyuncs.com/api/v1"
    MODEL_VIDEO: str = "qwen-vl-max"
    MODEL_ASR: str = "paraformer-v2"
    MODEL_TEXT: str = "qwen-max"
    MODEL_EMBEDDING: str = "text-embedding-v3"
    UPLOAD_DIR: str = "./uploads"
    BASE_URL: str = "http://localhost:8000"

    model_config = {
        "env_file": "../.env",
        "env_file_encoding": "utf-8",
    }

    @model_validator(mode="after")
    def _default_video_key(self):
        if not self.DASHSCOPE_VIDEO_API_KEY:
            self.DASHSCOPE_VIDEO_API_KEY = self.DASHSCOPE_API_KEY
        return self


settings = Settings()
