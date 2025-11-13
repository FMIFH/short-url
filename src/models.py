import re

from pydantic import BaseModel, Field, model_validator


class ShortenURLRequest(BaseModel):
    original_url: str = Field(..., alias="originalUrl")

    @model_validator(mode="before")
    def validate_original_url(cls, values):
        url = values.get("originalUrl")
        # Regex pattern to validate URL structure
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if not url_pattern.match(url):
            raise ValueError("originalUrl is not a valid URL")

        return values
