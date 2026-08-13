from pydantic import BaseModel, Field


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., description="The ID token returned by Google Sign-In on the frontend")
