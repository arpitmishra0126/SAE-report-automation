"""
Document template.
"""

from docx import Document
from docx.document import Document as DocxDocument
from docx.shared import Inches


def create_document() -> DocxDocument:
    """
    Create a new Word document with standard margins.
    """

    document = Document()

    section = document.sections[0]

    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)

    return document