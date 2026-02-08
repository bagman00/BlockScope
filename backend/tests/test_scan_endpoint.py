import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from io import BytesIO

from backend.app.main import app
from backend.analysis.models import ScanResult

client = TestClient(app)
SCAN_URL = "/api/v1/scan"


def test_scan_endpoint_success():
    fake_result = ScanResult(
        contract_name="Test",
        source_code="contract Test {}",
        findings=[],
        vulnerabilities_count=0,
        severity_breakdown={
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        },
        overall_score=100,
        summary="No vulnerabilities found - SAFE ✅",
    )

    with patch(
        "backend.app.routers.scan.orchestrator.analyze",
        return_value=fake_result,
    ):
        response = client.post(
            SCAN_URL,
            files={
                "file": (
                    "Test.sol",
                    BytesIO(b"contract Test {}"),
                    "text/plain",
                )
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["contract_name"] == "Test"
    assert body["overall_score"] == 100
    assert body["summary"].startswith("No vulnerabilities")


def test_scan_endpoint_validation_error():
    # Missing file → API explicitly raises 400
    response = client.post(SCAN_URL)

    assert response.status_code == 400
    assert response.json()["detail"] == "file is required"


def test_scan_endpoint_internal_error():
    """
    Orchestrator failures are handled internally and
    should NOT crash the API.
    """

    with patch(
        "backend.app.routers.scan.orchestrator.analyze",
        side_effect=RuntimeError("boom"),
    ):
        response = client.post(
            SCAN_URL,
            files={
                "file": (
                    "Test.sol",
                    BytesIO(b"contract Test {}"),
                    "text/plain",
                )
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["overall_score"] == 100
    assert body["summary"].startswith("No vulnerabilities")

