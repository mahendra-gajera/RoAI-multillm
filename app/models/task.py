"""
Task Model for Multi-LLM Risk Intelligence Platform
Defines task structure and attributes for intelligent routing
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class TaskType(str, Enum):
    """Enumeration of supported task types"""
    RISK_SCORING = "risk_scoring"
    FRAUD_DETECTION = "fraud_detection"
    COMPLIANCE_CHECK = "compliance_check"
    DOCUMENT_ANALYSIS = "document_analysis"
    GENERAL = "general"


class Task(BaseModel):
    """
    Task model representing a single analysis request.

    Attributes:
        task_id: Unique identifier for the task
        description: Detailed task description/prompt
        requires_strict_json: Flag indicating need for structured JSON output
        context_length: Estimated token count for the task
        multi_document: Flag indicating multi-document analysis requirement
        business_impact: Risk score from 0-1 (0=low, 1=critical)
        task_type: Category of the task
    """
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str = Field(..., min_length=1, description="Task description or prompt")
    requires_strict_json: bool = Field(default=False, description="Requires structured JSON output")
    context_length: int = Field(default=0, ge=0, description="Estimated token count")
    multi_document: bool = Field(default=False, description="Multi-document analysis required")
    business_impact: float = Field(default=0.5, ge=0.0, le=1.0, description="Business criticality (0-1)")
    task_type: TaskType = Field(default=TaskType.GENERAL, description="Task category")

    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "description": "Analyze transaction for fraud indicators",
                "requires_strict_json": True,
                "context_length": 1500,
                "multi_document": False,
                "business_impact": 0.7,
                "task_type": "fraud_detection"
            }
        }

    def to_dict(self) -> dict:
        """Convert task to dictionary for serialization"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create task from dictionary"""
        return cls(**data)
