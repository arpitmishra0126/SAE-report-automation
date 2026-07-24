"""
Neonatal Sepsis Surveillance extractor.
"""

from __future__ import annotations

from form_segmenter.form import Form
from models.nss import NSSData
from utils.parser import TextParser

from .base import BaseExtractor


class NSSExtractor(BaseExtractor[NSSData]):

    def __init__(self) -> None:
        self._parser = TextParser()

    def extract(self, form: Form) -> NSSData:

        text = "\n".join(page.text for page in form.pages)

        data = NSSData()

        return data