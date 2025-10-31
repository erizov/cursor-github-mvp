from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    prompt: str = Field(..., min_length=3)


class RecommendationItem(BaseModel):
    algorithm: str
    score: float
    rationale: str
    when_to_use: str
    pros: List[str]
    cons: List[str]
    typical_steps: List[str]
    resources: List[str]


class RecommendResponse(BaseModel):
    recommendations: List[RecommendationItem]


class SelectionRecord(BaseModel):
    algorithm: str
    prompt: str
    created_at: datetime


class UsageCount(BaseModel):
    algorithm: str
    count: int


class UsageReportResponse(BaseModel):
    total: int
    counts: List[UsageCount]


class SelectionDetail(BaseModel):
    algorithm: str
    prompt: str
    created_at: datetime


class AlgorithmGroup(BaseModel):
    algorithm: str
    count: int
    items: List[SelectionDetail]


class DetailedReportResponse(BaseModel):
    total: int
    groups: List[AlgorithmGroup]


class UserRequest(BaseModel):
    prompt: str
    algorithm_type: str
    created_at: datetime


