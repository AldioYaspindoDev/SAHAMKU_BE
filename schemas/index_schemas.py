from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel


class UploadResponse(BaseModel):
    index_name: str
    evaluation_type: Optional[str]
    effective_start: date
    effective_end: Optional[date]
    n_constituents: int
    has_weight_data: bool
    is_update: bool  # True kalau periode ini sudah ada sebelumnya (di-replace)
    message: str


class PeriodOut(BaseModel):
    id: int
    evaluation_type: Optional[str]
    effective_start: date
    effective_end: Optional[date]
    source_filename: Optional[str]
    has_weight_data: bool

    class Config:
        from_attributes = True


class ConsistencyOut(BaseModel):
    stock_code: str
    frequency: int
    longest_streak: int
    is_perfect_member: bool
    simple_consistency_score: float
    average_weight: Optional[float] = None
    weight_std: Optional[float] = None
    consistency_score: Optional[float] = None
    last_computed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
