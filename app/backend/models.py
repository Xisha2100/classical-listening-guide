from typing import Literal
from pydantic import BaseModel, Field

Dimension = Literal['动机','主题','变奏','曲式','和声','调性／调式','节奏／节拍','织体／复调','配器','力度／奏法']
DIMENSIONS = ['动机','主题','变奏','曲式','和声','调性／调式','节奏／节拍','织体／复调','配器','力度／奏法']

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
    role: Literal['excerpt','theme','phrase','evidence'] = 'excerpt'
    boundary_note: str = ''
    boundary_status: Literal['candidate','supported'] = 'candidate'
    source_ids: list[str] = Field(default_factory=list)

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
    summary: str = ''

class Claim(BaseModel):
    id: str = ''
    statement: str = Field(min_length=1, max_length=4000)
    evidence_type: Literal['source','score','hypothesis'] = 'hypothesis'
    source_ids: list[str] = Field(default_factory=list)
    segment_ids: list[str] = Field(default_factory=list)
    listening_cue: str = ''

class Analysis(BaseModel):
    id: str = ''
    work_id: str
    title: str = Field(min_length=1, max_length=200)
    body: str = ''
    kind: Dimension = '主题'
    dimensions: list[Dimension] = Field(default_factory=list)
    scope: Literal['overview','movement','section','segment'] = 'segment'
    section_id: str = ''
    listen_for: str = ''
    claims: list[Claim] = Field(default_factory=list)
    origin: Literal['manual','model','seed'] = 'manual'
    status: Literal['unlocated','suggested','confirmed','not_applicable'] = 'unlocated'
    review_status: Literal['unreviewed','checked'] = 'unreviewed'
    listening_status: Literal['pending','checked'] = 'pending'
    sources: list[Source] = []
    segments: list[Segment] = []
    created_at: str = ''
    updated_at: str = ''
    verification: str = ''
    analysis_model: str = ''
    analysis_run_id: str = ''

class GuideSection(BaseModel):
    id: str
    parent_id: str = ''
    title: str
    start_measure: int = Field(ge=0)
    end_measure: int = Field(ge=0)
    description: str = ''
    source_ids: list[str] = Field(default_factory=list)

class Guide(BaseModel):
    work_id: str
    overview: str = ''
    sections: list[GuideSection] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
