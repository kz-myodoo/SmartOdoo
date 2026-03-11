import subprocess
import pytest
from pathlib import Path
from smartodoo.core.docker_ops import DockerOps, DockerOpsError

@pytest.fixture
def mock_run_success(monkeypatch):
    def _mock_run(cmd, *args, **kwargs):
        class MockProc:
            stdout = f"Sukces dla {cmd[1]}"
            stderr = ""
            returncode = 0
            def check_returncode(self): pass
        return MockProc()
    monkeypatch.setattr(subprocess, "run", _mock_run)

@pytest.fixture
def mock_run_fail(monkeypatch):
    def _mock_run(cmd, *args, **kwargs):
        proc = subprocess.CompletedProcess(
            args=cmd,
            returncode=1,
            stdout="Porażka",
            stderr="Błąd krytyczny demona!"
        )
        raise subprocess.CalledProcessError(1, cmd, output="Porażka", stderr="Błąd krytyczny demona!")
    monkeypatch.setattr(subprocess, "run", _mock_run)

def test_compose_up_success(tmp_path, mock_run_success):
    ops = DockerOps(project_dir=tmp_path)
    res = ops.compose_up()
    assert "Sukces dla compose" in res

def test_compose_up_failure(tmp_path, mock_run_fail):
    ops = DockerOps(project_dir=tmp_path)
    with pytest.raises(DockerOpsError) as exc:
        ops.compose_up()
    assert "Błąd krytyczny demona!" in str(exc.value)

def test_exec_run_success(tmp_path, mock_run_success, monkeypatch):
    ops = DockerOps(project_dir=tmp_path)
    
    called_cmd = []
    def _mock_run(cmd, *args, **kwargs):
        called_cmd.extend(cmd)
        class MockProc:
            stdout = "Exec stdout"
            stderr = ""
            returncode = 0
            def check_returncode(self): pass
        return MockProc()
        
    monkeypatch.setattr(subprocess, "run", _mock_run)
    
    res = ops.exec_run("odoo", ["psql", "-U", "odoo"])
    assert res == "Exec stdout"
    assert called_cmd == ["docker", "exec", "-t", "odoo", "psql", "-U", "odoo"]
