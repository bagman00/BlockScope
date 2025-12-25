"""
Integration tests: Verify full end-to-end flows
"""
import json
from pathlib import Path
from click.testing import CliRunner
from fastapi.testclient import TestClient
from backend.cli.main import cli
from backend.app.main import app
from backend.analysis import AnalysisOrchestrator, ScanRequest

cli_runner = CliRunner()
api_client = TestClient(app)

# Test fixture: Simple Solidity contract
SAMPLE_CONTRACT = """
pragma solidity ^0.8.0;
contract SimpleStorage {
    uint256 storedData;

    function set(uint256 x) public {
        storedData = x;
    }

    function get() public view returns (uint256) {
        return storedData;
    }
}
"""


def test_cli_to_orchestrator():
    """Test: CLI → Orchestrator → Analysis Engine"""

    # 1. Create temp contract file
    with cli_runner.isolated_filesystem():
        with open('test.sol', 'w') as f:
            f.write(SAMPLE_CONTRACT)

        # 2. Run CLI scan
        result = cli_runner.invoke(cli, ['scan', 'test.sol'])

        # 3. Verify output
        assert result.exit_code == 0
        assert 'CONTRACT:' in result.output
        assert 'Score:' in result.output


def test_cli_json_output():
    """Test: CLI JSON output is valid JSON"""

    with cli_runner.isolated_filesystem():
        with open('test.sol', 'w') as f:
            f.write(SAMPLE_CONTRACT)

        result = cli_runner.invoke(cli, ['scan', 'test.sol', '-o', 'json'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert 'contract_name' in data
        assert 'overall_score' in data
        assert 'vulnerabilities_count' in data


def test_fastapi_scan_endpoint():
    """Test: FastAPI /api/v1/scan endpoint"""

    response = api_client.post('/api/v1/scan', json={
        'source_code': SAMPLE_CONTRACT,
        'contract_name': 'SimpleStorage'
    })

    assert response.status_code == 200
    data = response.json()
    assert data['contract_name'] == 'SimpleStorage'
    assert 'overall_score' in data
    assert 'scan_id' in data


def test_fastapi_list_scans():
    """Test: FastAPI GET /api/v1/scans"""

    # First, create a scan
    api_client.post('/api/v1/scan', json={
        'source_code': SAMPLE_CONTRACT,
        'contract_name': 'Test1'
    })

    # Then list scans
    response = api_client.get('/api/v1/scans')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_fastapi_get_scan_by_id():
    """Test: FastAPI GET /api/v1/scans/{id}"""

    # Create a scan
    create_response = api_client.post('/api/v1/scan', json={
        'source_code': SAMPLE_CONTRACT,
        'contract_name': 'Test2'
    })
    scan_id = create_response.json()['scan_id']

    # Get by ID
    response = api_client.get(f'/api/v1/scans/{scan_id}')
    assert response.status_code == 200
    data = response.json()
    assert data['contract_name'] == 'Test2'


def test_orchestrator_direct():
    """Test: AnalysisOrchestrator directly"""

    from backend.analysis import ScanRequest

    orchestrator = AnalysisOrchestrator(rules=[])
    request = ScanRequest(
        source_code=SAMPLE_CONTRACT,
        contract_name='Direct'
    )

    result = orchestrator.analyze(request)

    assert result.contract_name == 'Direct'
    assert result.overall_score >= 0
    assert result.overall_score <= 100
