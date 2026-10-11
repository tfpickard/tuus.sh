"""Shared curation and runtime contracts."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Function = Literal[
    "requesting", "thanking", "praising", "deferring", "scheduling",
    "declining", "hyping", "apologizing", "informing", "greeting",
]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Signature(Record):
    onset: float = Field(ge=1970, le=2030)
    peak: float = Field(ge=1970, le=2030)
    fade: float = Field(ge=1970, le=2030)
    fade_status: Literal["observed", "estimated"]
    confidence: Literal["high", "medium", "low"]

    @model_validator(mode="after")
    def ordered(self):
        if not self.onset < self.peak < self.fade:
            raise ValueError("Temporal signature requires onset < peak < fade")
        return self


class Source(Record):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    title: str = Field(min_length=3)
    url: str = Field(pattern=r"^https?://")
    published: str = Field(min_length=4)
    accessed: str
    note: str = Field(min_length=12)


class Example(Record):
    text: str = Field(min_length=3)
    kind: Literal["attested", "constructed"]
    source_id: str | None = None

    @model_validator(mode="after")
    def attestation(self):
        if self.kind == "attested" and not self.source_id:
            raise ValueError("Attested examples require a source")
        return self


class Entry(Record):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    surface: str = Field(min_length=2)
    variants: list[str]
    kairolexica: list[str] = Field(min_length=1)
    signature: Signature
    gloss: str = Field(min_length=10)
    functions: list[Function] = Field(min_length=1)
    examples: list[Example] = Field(min_length=1)
    rationale: str = Field(min_length=30)
    source_ids: list[str] = Field(min_length=1)
    review_status: Literal["accepted", "candidate"]


class Window(Record):
    start: float = Field(ge=1970, le=2030)
    end: float = Field(ge=1970, le=2030)

    @model_validator(mode="after")
    def ordered(self):
        if self.start >= self.end:
            raise ValueError("Window requires start < end")
        return self


class Kairolexicon(Record):
    schema_version: Literal[1] = 1
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    name: str
    window: Window
    description: str = Field(min_length=20)
    cause_of_death: str | None
    sources: list[Source] = Field(min_length=1)
    entries: list[Entry] = Field(min_length=1)
