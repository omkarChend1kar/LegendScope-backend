from functools import lru_cache
from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
    )

    environment: Annotated[
        str,
        Field(pattern=r"^(development|staging|production)$"),
    ] = "development"
    debug: bool = False
    api_prefix: str = "/api"
    project_name: str = "LegendScope Backend"
    
    # Lambda function URL for querying cached profiles from DynamoDB
    lambda_profile_url: str = (
        "https://kj3fm5xsu7lmovkwqgog6ikjqi0jnvwl.lambda-url.eu-north-1.on.aws/"
    )
    
    # Lambda function URL for get-uuid API (fetches profile data, same response format)
    lambda_get_uuid_url: str = (
        "https://svaxaookur2cco343dyl4d3sme0detlm.lambda-url.eu-north-1.on.aws/"
    )
    
    # Lambda function URL for create-profile API (saves profile data to DynamoDB)
    lambda_create_profile_url: str = (
        "https://giac4bui2zsfeiatzcfhmtoota0jndfh.lambda-url.eu-north-1.on.aws/"
    )
    
    # Riot API configuration (for future direct integration)
    riot_api_key: str = ""  # Set via APP_RIOT_API_KEY environment variable
    riot_api_base_url: str = "https://americas.api.riotgames.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
