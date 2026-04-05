from pydantic import BaseModel


class Recording(BaseModel):
    id: str
    filename: str
    genus: str | None = None
    species: str | None = None
    english_name: str | None = None
    duration_seconds: float | None = None


class RecordingList(BaseModel):
    recordings: list[Recording]
