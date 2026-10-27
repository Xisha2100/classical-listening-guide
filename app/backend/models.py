from typing import Literal
from pydantic import BaseModel, Field

class Route(BaseModel):
    start: float
    end: float
    staff: str
    voice: str | None = None

class Segment(BaseModel):
    id: str = ''
    label: str = '片段'
    score_version: str
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    staffs: list[str] = []
    voices: list[str] = []
    routes: list[Route] = []
    note_ids: list[str] = []
    start_measure: int = 0
    end_measure: int = 0

class Source(BaseModel):
    id: str
    kind: Literal['book','web','score','personal'] = 'book'
    title: str = ''
    author: str = ''
    edition: str = ''
    pages: str = ''
    url: str = ''
    accessed_at: str = ''
    excerpt: str = ''
    extracted: bool = False

class Analysis(BaseModel):
    id: str = ''
    work_id: str
    title: str = Field(min_length=1, max_length=200)
    body: str = ''
    kind: Literal['动机','主题','变奏','曲式','和声'] = '主题'
    origin: Literal['manual','model','seed'] = 'manual'
    status: Literal['unlocated','suggested','confirmed'] = 'unlocated'
    sources: list[Source] = []
    segments: list[Segment] = []
    created_at: str = ''
    updated_at: str = ''
    verification: str = ''

class ResearchRequest(BaseModel):
    work_id: str
    question: str = Field(min_length=1,max_length=1000)

class ExtractRequest(BaseModel):
    work_id: str
    urls: list[str] = Field(max_length=5)

class ModelRequest(BaseModel):
    work_id: str
    mode: Literal['sources','segment']
    question: str = Field(min_length=1,max_length=3000)
    sources: list[Source] = Field(default_factory=list,max_length=10)
    segments: list[Segment] = Field(default_factory=list,max_length=2)

class ModelCard(BaseModel):
    title: str = Field(min_length=1,max_length=200)
    body: str = Field(min_length=1)
    kind: Literal['动机','主题','变奏','曲式','和声']
    source_ids: list[str] = []
    segment_ids: list[str] = []

class ModelOutput(BaseModel):
    cards: list[ModelCard] = Field(min_length=1,max_length=5)
