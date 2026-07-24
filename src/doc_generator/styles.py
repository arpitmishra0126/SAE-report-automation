"""
Common document styles.
"""

from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT


class DocumentStyles:

    TITLE_SIZE = Pt(16)

    HEADING_SIZE = Pt(13)

    NORMAL_SIZE = Pt(11)

    FONT = "Calibri"

    TITLE_ALIGNMENT = WD_PARAGRAPH_ALIGNMENT.CENTER