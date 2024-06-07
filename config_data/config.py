from pydantic import Field
from pydantic_settings import BaseSettings,SettingsConfigDict

class Config(BaseSettings):
    APIToken: str = Field(alias='APITOKEN')
    OpenAIToken: str = Field(alias='OPENAITOKEN')
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
