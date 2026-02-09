"""Tests for document processor service."""

import tempfile
from pathlib import Path

import pytest

from app.models.knowledge import FileType
from app.services.document_processor import extract_text, _extract_csv


class TestTxtExtraction:
    """Tests for TXT file extraction."""

    def test_extract_txt(self, tmp_path):
        """Test extracting text from a TXT file."""
        file_path = tmp_path / "test.txt"
        content = "Hello, this is test content.\nWith multiple lines."
        file_path.write_text(content, encoding="utf-8")

        result = extract_text(str(file_path), FileType.txt)

        assert result == content

    def test_extract_empty_txt(self, tmp_path):
        """Test extracting from an empty TXT file."""
        file_path = tmp_path / "empty.txt"
        file_path.write_text("", encoding="utf-8")

        result = extract_text(str(file_path), FileType.txt)

        assert result == ""


class TestCsvExtraction:
    """Tests for CSV file extraction."""

    def test_extract_csv(self, tmp_path):
        """Test extracting text from a CSV file."""
        file_path = tmp_path / "test.csv"
        content = "Name,Age,City\nAlice,30,NYC\nBob,25,LA"
        file_path.write_text(content, encoding="utf-8")

        result = extract_text(str(file_path), FileType.csv)

        assert "Headers: Name, Age, City" in result
        assert "Name: Alice" in result
        assert "Age: 30" in result

    def test_extract_empty_csv(self, tmp_path):
        """Test extracting from an empty CSV file."""
        file_path = tmp_path / "empty.csv"
        file_path.write_text("", encoding="utf-8")

        result = extract_text(str(file_path), FileType.csv)

        assert result == ""


class TestJsonExtraction:
    """Tests for JSON file extraction."""

    def test_extract_json(self, tmp_path):
        """Test extracting from a JSON file (treated as plain text)."""
        file_path = tmp_path / "test.json"
        content = '{"name": "Test", "value": 123}'
        file_path.write_text(content, encoding="utf-8")

        result = extract_text(str(file_path), FileType.json)

        assert result == content


class TestUnsupportedType:
    """Tests for unsupported file types."""

    def test_unsupported_raises_error(self, tmp_path):
        """Test that unsupported types raise an error."""
        file_path = tmp_path / "test.xyz"
        file_path.write_text("content", encoding="utf-8")

        with pytest.raises(ValueError, match="Unsupported file type"):
            # Use a fake file type for testing
            extract_text(str(file_path), "xyz")


class TestPdfExtraction:
    """Tests for PDF extraction (requires pdfplumber)."""

    def test_pdf_import_error(self, tmp_path, monkeypatch):
        """Test proper error when pdfplumber is not installed."""
        # This test verifies the ImportError path
        file_path = tmp_path / "test.pdf"
        file_path.write_bytes(b"%PDF-1.4 fake pdf content")

        # Mock the import to fail
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "pdfplumber":
                raise ImportError("No module named 'pdfplumber'")
            return original_import(name, *args, **kwargs)

        # Only run this if pdfplumber is not installed
        try:
            import pdfplumber
            pytest.skip("pdfplumber is installed, skipping import error test")
        except ImportError:
            with pytest.raises(ImportError, match="pdfplumber is required"):
                extract_text(str(file_path), FileType.pdf)


class TestDocxExtraction:
    """Tests for DOCX extraction (requires python-docx)."""

    def test_docx_import_error(self, tmp_path, monkeypatch):
        """Test proper error when python-docx is not installed."""
        file_path = tmp_path / "test.docx"
        file_path.write_bytes(b"fake docx content")

        # Only run this if python-docx is not installed
        try:
            from docx import Document
            pytest.skip("python-docx is installed, skipping import error test")
        except ImportError:
            with pytest.raises(ImportError, match="python-docx is required"):
                extract_text(str(file_path), FileType.docx)
