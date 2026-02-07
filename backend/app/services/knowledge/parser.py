"""Document parsing service.

Extracts text content from various file formats.
"""

import hashlib
from pathlib import Path
from typing import Optional

import structlog


logger = structlog.get_logger()


class DocumentParser:
    """Parses documents and extracts text content.

    Supports PDF, TXT, DOCX, and Markdown files.
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx", ".md", ".markdown"}

    @staticmethod
    def is_supported(filename: str) -> bool:
        """Check if file type is supported.

        Args:
            filename: Name or path of the file.

        Returns:
            True if file type is supported.
        """
        ext = Path(filename).suffix.lower()
        return ext in DocumentParser.SUPPORTED_EXTENSIONS

    @staticmethod
    async def parse(file_path: str) -> str:
        """Parse a document and extract text.

        Args:
            file_path: Path to the document file.

        Returns:
            Extracted text content.

        Raises:
            ValueError: If file type is not supported.
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        logger.info("document_parse_start", file=path.name, extension=ext)

        if ext == ".pdf":
            text = await DocumentParser._parse_pdf(file_path)
        elif ext in {".txt", ".md", ".markdown"}:
            text = await DocumentParser._parse_text(file_path)
        elif ext == ".docx":
            text = await DocumentParser._parse_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        logger.info(
            "document_parse_complete",
            file=path.name,
            text_length=len(text),
        )
        return text

    @staticmethod
    async def _parse_pdf(file_path: str) -> str:
        """Parse PDF file using pypdf."""
        from pypdf import PdfReader

        reader = PdfReader(file_path)
        text_parts = []

        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)

        return "\n\n".join(text_parts)

    @staticmethod
    async def _parse_text(file_path: str) -> str:
        """Parse plain text or markdown file."""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    async def _parse_docx(file_path: str) -> str:
        """Parse Word document using python-docx."""
        from docx import Document

        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)

    @staticmethod
    def compute_hash(content: str) -> str:
        """Compute SHA-256 hash of content.

        Args:
            content: Text content.

        Returns:
            Hex-encoded SHA-256 hash.
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    async def parse_bytes(content: bytes, filename: str) -> str:
        """Parse document from bytes.

        Args:
            content: File content as bytes.
            filename: Original filename (for extension detection).

        Returns:
            Extracted text content.
        """
        import tempfile
        import os

        ext = Path(filename).suffix.lower()

        # Write to temp file
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            text = await DocumentParser.parse(temp_path)
        finally:
            os.unlink(temp_path)

        return text
