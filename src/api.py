"""
FastAPI bridge for the existing SAE Case Summary pipeline.

This module adds no pipeline behaviour of its own. It accepts an
uploaded PDF over HTTP, calls the existing `SAEPipeline` from
`main.py` exactly as that module's own CLI entry point does, and
returns the resulting `CaseSummary` as JSON. `python src/main.py`
is untouched and continues to work independently of this file.

Run with (from the project root):
    uvicorn src.api:app --reload
"""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
from pathlib import Path

# Every module in `src/` uses flat imports (e.g. `from extractor
# import Extractor`), which resolve correctly when `src/` itself is
# on sys.path — true for `python src/main.py`, but not when this
# module is imported as `src.api` by uvicorn from the project root.
# Adding it here (isolated to this new file) lets the existing
# pipeline modules be imported completely unchanged.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, File, HTTPException, UploadFile  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402

from main import SAEPipeline  # noqa: E402  (existing pipeline, unmodified)

app = FastAPI(title="SAE Report Automation API")

# The Vite dev server from the frontend foundation phase.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# SAEPipeline.run() already knows how to generate a DOCX; it just
# needs an output directory. This reuses the project's existing
# `outputs/` directory so no new storage concept is introduced, and
# keeps generated DOCX files around so the separate GET endpoint can
# serve them after the synchronous POST /api/reports request returns.
_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs" / "api"
_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# SAEPipeline() itself only wires up the extractor/validator/builder
# objects; the actual PDF reader (and its OCR model) is constructed
# fresh inside run() on every call, exactly as it is for the CLI.
# Reusing one instance here just mirrors main()'s own
# `pipeline = SAEPipeline()` usage.
_pipeline = SAEPipeline()


def _safe_case_id(case_id: str) -> str:
    """
    `case_id` comes from extracted document data (a REDCap record ID
    or the PDF's filename stem) and is used to build a filesystem
    path. Restrict it to characters safe for a filename/URL segment
    so it can never be used for path traversal.
    """

    return re.sub(r"[^A-Za-z0-9_.-]", "_", case_id) or "case"


@app.post("/api/reports")
def create_report(file: UploadFile = File(...)) -> dict:
    """
    Accept a PDF upload, run it through the existing SAEPipeline
    synchronously, and return the resulting structured CaseSummary.
    """

    filename = file.filename or "upload.pdf"

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted.",
        )

    with tempfile.TemporaryDirectory() as tmp_dir:

        upload_path = Path(tmp_dir) / filename

        with upload_path.open("wb") as destination:
            shutil.copyfileobj(file.file, destination)

        # Validate the actual file content, not just the filename —
        # a PDF always begins with this magic header.
        with upload_path.open("rb") as uploaded:
            header = uploaded.read(5)

        if header != b"%PDF-":
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is not a valid PDF.",
            )

        try:
            summary = _pipeline.run(upload_path)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Pipeline failed: {exc}",
            ) from exc

        # With no explicit output_path, SAEPipeline.run() writes the
        # DOCX next to the input PDF (see main.py) as
        # "<case_id>_SAE_Case_Summary.docx" — i.e. into this temp
        # directory. Move it into the persistent output directory
        # before the temp directory is cleaned up below.
        case_id = _safe_case_id(summary.case_id or upload_path.stem)

        generated_docx = (
            upload_path.parent / f"{summary.case_id}_SAE_Case_Summary.docx"
        )

        docx_url = None

        if generated_docx.exists():
            destination = _OUTPUT_DIR / f"{case_id}_SAE_Case_Summary.docx"
            shutil.move(str(generated_docx), str(destination))
            docx_url = f"/api/reports/{case_id}/docx"

    return {
        "caseSummary": summary.model_dump(),
        "docxUrl": docx_url,
    }


@app.get("/api/reports/{case_id}/docx")
def download_docx(case_id: str) -> FileResponse:
    """
    Serve the DOCX generated for a previous /api/reports request.
    There is no separate "report" concept in the existing pipeline —
    this reuses the same `case_id` the pipeline itself already
    computes (SAEPipeline.run(), see main.py).
    """

    safe_id = _safe_case_id(case_id)
    path = _OUTPUT_DIR / f"{safe_id}_SAE_Case_Summary.docx"

    if not path.is_file() or path.parent != _OUTPUT_DIR:
        raise HTTPException(status_code=404, detail="Report not found.")

    return FileResponse(
        path,
        media_type=(
            "application/vnd.openxmlformats-officedocument"
            ".wordprocessingml.document"
        ),
        filename=path.name,
    )
