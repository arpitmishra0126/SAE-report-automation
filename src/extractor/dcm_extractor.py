"""
Daily Clinical Monitoring extractor.
"""

from __future__ import annotations

from form_segmenter.form import Form
from models.dcm import DCMData
from utils.parser import TextParser

from .base import BaseExtractor


class DCMExtractor(BaseExtractor[DCMData]):

    def __init__(self) -> None:
        self._parser = TextParser()

    def extract(self, form: Form) -> DCMData:

        text = "\n".join(page.text for page in form.pages)

        data = DCMData()

        return data