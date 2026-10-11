"""Data contracts for the code review agent.

These models define the exact shape of data the model must return
Pydantic validates it at run time, so bad data never reaches our logic
"""

from typing import Literal

from pydantic import BaseModel, Field


class ReviewComment(BaseModel):
    """A single finding about one place in the code."""

    file: str = Field(description="Path of the file the comment refers to")
    line: int = Field(description="Line number in the new version of the file")
    severity: Literal["low", "medium", "high"]
    category: Literal["bug", "security", "performance", "style"]
    message: str = Field(description="What is wrong and why it matters")
    suggestion: str | None = Field(
        default=None, description="Concrete fix, if there is one"
    )


class ReviewResult(BaseModel):
    """The complete review of one diff."""

    summary: str = Field(description="One or two sentences with the overall verdict")
    comments: list[ReviewComment]
