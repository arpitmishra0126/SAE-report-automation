"""
Base extractor interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from form_segmenter.form import Form

T = TypeVar("T")


class BaseExtractor(ABC, Generic[T]):
    """
    Base class for all form extractors.
    """

    @abstractmethod
    def extract(self, form: Form) -> T:
        """
        Extract structured information from a REDCap form.
        """
        raise NotImplementedError