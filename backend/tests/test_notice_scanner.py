import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.notice import NoticeScanResult, UrgencyLevel
from backend.app.services.notice_service import NoticeScannerService
import pypdf

client = TestClient(app)

def create_sample_pdf_bytes(text: str) -> bytes:
    """Helper to create a minimal in-memory PDF with text."""
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=612, height=792)
    
    # We can write simple metadata or use a basic PDF structure
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()

@pytest.mark.asyncio
async def test_notice_service_with_text_en():
    notice_text = (
        "GOVERNMENT OF KARNATAKA\n"
        "Department of Food, Civil Supplies and Consumer Affairs\n"
        "Public Notice: Mandatory biometric e-KYC for all BPL and AAY ration cardholders.\n"
        "Deadline: December 31, 2026. Failure to comply will lead to card suspension.\n"
        "Visit Fair Price Shop with Aadhaar."
    )
    result = await NoticeScannerService.scan_notice(
        text_content=notice_text,
        language="en"
    )
    assert isinstance(result, NoticeScanResult)
    assert result.language == "en"
    assert result.issuing_authority != ""
    assert result.deadline == "December 31, 2026"
    assert len(result.citizen_obligations) > 0
    assert len(result.next_steps) > 0
    assert "Information only, not legal advice" in result.disclaimer

@pytest.mark.asyncio
async def test_notice_service_with_text_kn():
    notice_text = (
        "ಕರ್ನಾಟಕ ಸರ್ಕಾರ - ಆಹಾರ ಇಲಾಖೆ\n"
        "ಪಡಿತರ ಚೀಟಿ ಇ-ಕೆವೈಸಿ ಕಡ್ಡಾಯ ಅಧಿಸೂಚನೆ.\n"
        "ದಿನಾಂಕ: 31 ಡಿಸೆಂಬರ್ 2026."
    )
    result = await NoticeScannerService.scan_notice(
        text_content=notice_text,
        language="kn"
    )
    assert isinstance(result, NoticeScanResult)
    assert result.language == "kn"
    assert result.deadline == "December 31, 2026"
    assert "ಕಾನೂನು ಸಲಹೆಯಲ್ಲ" in result.disclaimer

@pytest.mark.asyncio
async def test_notice_service_no_deadline_explicit():
    notice_text = (
        "GOVERNMENT NOTICE - GENERAL INFORMATION\n"
        "Department of Agriculture, Karnataka.\n"
        "Soil Health Testing guidelines for Kharif season.\n"
        "Farmers are requested to submit soil samples at Raitha Samparka Kendras."
        # No deadline mentioned
    )
    result = await NoticeScannerService.scan_notice(
        text_content=notice_text + " (No deadline mentioned)",
        language="en"
    )
    assert result.deadline == "No deadline mentioned in the document"

def test_api_notice_scan_with_form_text():
    response = client.post(
        "/api/notice/scan",
        data={
            "text": "Department of Food & Civil Supplies: Update Ration Card e-KYC before 31 December 2026.",
            "language": "en"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "issuing_authority" in data
    assert "purpose" in data
    assert "summary" in data
    assert "deadline" in data
    assert "citizen_obligations" in data
    assert "next_steps" in data
    assert "urgency" in data
    assert "disclaimer" in data

def test_api_notice_scan_kannada():
    response = client.post(
        "/api/notice/scan",
        data={
            "text": "ಪಡಿತರ ಚೀಟಿ e-KYC ನವೀಕರಣ ಅಧಿಸೂಚನೆ. ಕೊನೆಯ ದಿನಾಂಕ: 31 ಡಿಸೆಂಬರ್ 2026.",
            "language": "kn"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "kn"
    assert "ಕಾನೂನು ಸಲಹೆಯಲ್ಲ" in data["disclaimer"]

def test_api_notice_scan_image_upload():
    # 1x1 transparent PNG file bytes
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    response = client.post(
        "/api/notice/scan",
        files={"file": ("official_circular.png", png_bytes, "image/png")},
        data={"language": "en"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source_filename"] == "official_circular.png"
    assert "summary" in data
    assert "deadline" in data

def test_api_notice_scan_pdf_upload():
    # Generate simple PDF
    pdf_bytes = create_sample_pdf_bytes("Notice text inside PDF")
    response = client.post(
        "/api/notice/scan",
        files={"file": ("government_order.pdf", pdf_bytes, "application/pdf")},
        data={"language": "en"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source_filename"] == "government_order.pdf"

def test_api_notice_scan_unsupported_file():
    response = client.post(
        "/api/notice/scan",
        files={"file": ("malicious.exe", b"fake binary", "application/octet-stream")},
        data={"language": "en"}
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]

def test_api_notice_scan_empty_payload():
    response = client.post(
        "/api/notice/scan",
        data={"language": "en"}
    )
    assert response.status_code == 400
    assert "Please provide an uploaded notice file" in response.json()["detail"]
