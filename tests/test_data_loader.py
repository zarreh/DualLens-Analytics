"""Unit tests for duallens_analytics.data_loader."""

from __future__ import annotations

from pathlib import Path

from duallens_analytics.config import ZIP_PATH
from duallens_analytics.data_loader import extract_zip


class TestExtractZip:
    def test_extract_zip_creates_directory(self, tmp_path: Path):
        dest = tmp_path / "pdfs"
        result = extract_zip(zip_path=ZIP_PATH, dest=dest)
        assert result.exists()
        assert result.is_dir()

    def test_extracted_dir_contains_pdfs(self, tmp_path: Path):
        dest = tmp_path / "pdfs"
        result = extract_zip(zip_path=ZIP_PATH, dest=dest)
        pdf_files = list(result.glob("*.pdf"))
        assert len(pdf_files) > 0, "Expected at least one PDF in the extracted directory"

    def test_extract_is_idempotent(self, tmp_path: Path):
        dest = tmp_path / "pdfs"
        r1 = extract_zip(zip_path=ZIP_PATH, dest=dest)
        r2 = extract_zip(zip_path=ZIP_PATH, dest=dest)
        assert r1 == r2
