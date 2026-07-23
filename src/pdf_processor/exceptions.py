"""
Custom exceptions for the PDF processing module.

These exceptions provide clear, domain-specific error messages
that can be handled gracefully by higher-level modules.
"""


class PDFProcessingError(Exception):
    """Base exception for all PDF processing errors."""


class PDFNotFoundError(PDFProcessingError):
    """Raised when the specified PDF file cannot be found."""


class PDFReadError(PDFProcessingError):
    """Raised when a PDF cannot be opened or read."""


class PDFEncryptedError(PDFProcessingError):
    """Raised when the PDF is password protected or encrypted."""