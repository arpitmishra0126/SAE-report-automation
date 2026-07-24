"""
Maternal History extractor.
"""

from __future__ import annotations

from form_segmenter.form import Form
from models.maternal import MaternalData
from utils.parser import TextParser

from .base import BaseExtractor


class MaternalExtractor(BaseExtractor[MaternalData]):

    def __init__(self) -> None:
        self._parser = TextParser()

    def extract(self, form: Form) -> MaternalData:

        text = "\n".join(page.text for page in form.pages)

        data = MaternalData()

        return data