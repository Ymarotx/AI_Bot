from pydantic import Field
from pydantic_settings import BaseSettings,SettingsConfigDict



class Settings(BaseSettings):
    bot_token: str = Field(alias='APITOKEN')
    ope_ai_token: str = Field(alias='OPENAITOKEN')
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

class Config:
    settings = Settings()
    APIToken = settings.bot_token
    OpenAIToken = settings.ope_ai_token