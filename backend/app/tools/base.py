"""Base abstractions for planner tools."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar, Type

from pydantic import BaseModel


class BasePlanningTool(ABC):
    """Common interface so tools can be registered quickly."""

    name: ClassVar[str]
    description: ClassVar[str]
    args_schema: ClassVar[Type[BaseModel]]
    return_model: ClassVar[Type[BaseModel]]

    @abstractmethod
    async def _arun(self, **kwargs) -> BaseModel:
        """Perform the tool's core async logic and return its Pydantic payload."""

