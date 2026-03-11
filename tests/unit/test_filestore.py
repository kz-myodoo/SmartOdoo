import pytest
from pathlib import Path
from smartodoo.core.filestore import FilestoreManager, FilestoreError
from smartodoo.core.docker_ops import DockerOps

def test_restore_filestore(tmp_path, monkeypatch):
    """Sprawdza wywołanie funkcji kopiującej drzewo na platformie kontenera."""
    local_fs = tmp_path / "filestore_src"
    local_fs.mkdir()
    
    commands_run = []
    
    class FakeDockerOps:
        def cp(self, src, dest):
            commands_run.append(f"cp {src} {dest}")
            return ""
            
        def exec_run(self, container, cmd):
            commands_run.append(f"exec {container} {' '.join(cmd)}")
            return ""
            
    manager = FilestoreManager(FakeDockerOps(), odoo_container="odoo_cont")
    
    manager.restore_filestore(local_fs, "mojabaza")
    
    # Kopiowanie musi konczyć się na "/." by chwytało zjawisko recursive zawartości wg dockera
    expected_cp = f"cp {local_fs}/. odoo_cont:/var/lib/odoo/filestore/mojabaza/"
    assert expected_cp in commands_run
    
    assert "exec odoo_cont mkdir -p /var/lib/odoo/filestore/mojabaza" in commands_run
    assert "exec odoo_cont chown -R odoo:odoo /var/lib/odoo/filestore/mojabaza" in commands_run
    assert "exec odoo_cont chmod -R 755 /var/lib/odoo/filestore/mojabaza" in commands_run

def test_filestore_not_exists(tmp_path):
    manager = FilestoreManager(None, "cont")
    with pytest.raises(FilestoreError) as exc:
        manager.restore_filestore(Path("/nieistnieje"), "test_db")
    assert "nie istnieje" in str(exc.value)
