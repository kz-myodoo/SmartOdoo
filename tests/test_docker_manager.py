import pytest
import subprocess
from unittest.mock import MagicMock
from pathlib import Path
from smartodoo.core.docker_manager import DockerManager

@pytest.fixture
def fake_docker_manager(mocker):
    # Mocking in-class subprocess requirements
    mocker.patch("shutil.which", return_value="/usr/bin/docker")
    mocker.patch("subprocess.run", return_value=MagicMock(returncode=0))
    return DockerManager()

def test_execute_auto_resolution(mocker, fake_docker_manager):
    """Sprawdza czy rzut błędem 'Permission denied' w konsoli uruchomi mechanizm naprawy"""
    # Pierwszy strzał - wywala Permission Denied, Drugi strzał przechodzi.
    mock_fail = MagicMock(returncode=1, stderr="Error: Permission denied /var/lib/odoo")
    mock_success = MagicMock(returncode=0, stderr="")
    
    mock_run = mocker.patch("subprocess.run", side_effect=[mock_fail, MagicMock(returncode=0), mock_success])
    mocker.patch("os.name", "posix")

    project_path = Path("/tmp/fake_project")
    result = fake_docker_manager.execute(project_path, ["up", "-d"], check=True)
    
    assert result.returncode == 0
    # Test powinnien wykonac się 3 razy: Próba up -> Chmod 777 sudo -> Powtórna Próba up
    assert mock_run.call_count == 3
    
    chmod_call = mock_run.call_args_list[1]
    assert "sudo" in chmod_call[0][0]
    assert "chmod" in chmod_call[0][0]

def test_execute_normal_failure(mocker, fake_docker_manager):
    """Sprawdza czy inny błąd (np. brak dockerfile) natychmiast rzuci prawowity wyjątek"""
    mock_run = mocker.patch("subprocess.run", return_value=MagicMock(returncode=1, stderr="no configuration file provided"))
    
    with pytest.raises(subprocess.CalledProcessError):
        fake_docker_manager.execute(Path("/tmp/"), ["up", "-d"], check=True)
        
    assert mock_run.call_count == 1  # Brak próby naprawy chmod
