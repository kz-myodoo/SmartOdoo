import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_subprocess_run(mocker):
    """Izoluje środowisko developerskie testującego. Żaden proces systemowy nie zostanie wyrzucony z palca."""
    mock = mocker.patch('subprocess.run')
    mock.return_value.returncode = 0
    mock.return_value.stdout = "mocked stdout"
    mock.return_value.stderr = ""
    return mock

@pytest.fixture
def mock_docker_manager(mocker):
    """Mock zastępujący menedżera kontenerów tak by nie obudzić prawdziwego dockera Odoo z testów"""
    mock = MagicMock()
    mocker.patch('smartodoo.core.docker_manager.DockerManager', return_value=mock)
    return mock
