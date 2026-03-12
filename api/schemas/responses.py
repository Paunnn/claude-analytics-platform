"""
Pydantic response schemas for API endpoints.

Defines the structure of API responses for validation and documentation.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MetricResponse(BaseModel):
    """Generic metric response schema."""
    metric_name: str
    value: float
    unit: str
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class TokenUsageResponse(BaseModel):
    """Token usage metrics response."""
    total_input_tokens: int
    total_output_tokens: int
    total_cache_read_tokens: int
    total_cache_creation_tokens: int
    average_tokens_per_request: float
    cache_hit_rate: float


class CostMetricsResponse(BaseModel):
    """Cost metrics response."""
    total_cost: float
    average_cost_per_request: float
    cost_breakdown: Dict[str, float]
    top_cost_drivers: List[Dict[str, Any]]


class InsightResponse(BaseModel):
    """Insight object schema."""
    insight_id: str
    type: str  # cost, performance, usage, trend
    severity: str  # high, medium, low
    title: str
    description: str
    recommendation: str
    potential_impact: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserResponse(BaseModel):
    """User information response."""
    user_id: str
    email: str
    full_name: str
    practice: str
    level: str
    location: str


class SessionResponse(BaseModel):
    """Session information response."""
    session_id: str
    user_id: str
    terminal_type: str
    session_start: datetime
    session_end: Optional[datetime] = None
    total_requests: Optional[int] = None
    total_cost: Optional[float] = None


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""
    data: List[Any]
    total: int
    limit: int
    offset: int
    has_more: bool


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
