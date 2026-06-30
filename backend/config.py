from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
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


settings = Settings()
