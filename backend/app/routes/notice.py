import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from ..models.notice import NoticeScanResult
from ..services.notice_service import NoticeScannerService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notice", tags=["Notice Scanner"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".txt", ".md"}

@router.post("/scan", response_model=NoticeScanResult)
async def scan_notice_endpoint(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    language: str = Form("kn"),
):
    """
    Scans a photographed or uploaded government notice (PDF, image, or pasted text)
    and returns a structured citizen breakdown with deadlines, urgency, obligations, and next steps.
    """
    file_bytes: Optional[bytes] = None
    filename: Optional[str] = None
    mime_type: Optional[str] = None

    if file:
        filename = file.filename or "uploaded_notice"
        mime_type = file.content_type
        # Validate extension
        from pathlib import Path
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        try:
            file_bytes = await file.read()
            if len(file_bytes) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Uploaded file exceeds maximum limit of 10MB."
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to read uploaded file: %s", e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not read uploaded file: {str(e)}"
            )

    if not file_bytes and not (text and text.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide an uploaded notice file (image/PDF) or paste notice text."
        )

    try:
        result = await NoticeScannerService.scan_notice(
            file_bytes=file_bytes,
            filename=filename,
            mime_type=mime_type,
            text_content=text,
            language=language,
        )
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error("Error processing notice scan: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scan government notice: {str(e)}"
        )
