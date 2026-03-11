import pytest
from pathlib import Path
from smartodoo.core.db_ops import DbOps
from smartodoo.core.docker_ops import DockerOps

def test_restore_database(tmp_path, monkeypatch):
    """Test sprawdza przywracanie dump.sql poprzez mock DockerOps"""
    # Create fake dump
    dump_file = tmp_path / "dump.sql"
    dump_file.write_text("SELECT 1;")
    
    commands_run = []
    
    class FakeDockerOps:
        def cp(self, src, dest):
            commands_run.append(f"cp {src} {dest}")
            return ""
            
        def exec_run(self, container, cmd):
            commands_run.append(f"exec {container} {' '.join(cmd)}")
            return ""
    
    db_ops = DbOps(FakeDockerOps(), db_container="cont_db")
    db_ops.restore_database(
        dump_path=dump_file,
        db_name="test_db",
        db_user="odoo"
    )
    
    expected_cp = f"cp {str(dump_file)} cont_db:/tmp/dump.sql"
    assert expected_cp in commands_run
    assert "exec cont_db dropdb -U odoo --if-exists test_db" in commands_run
    assert "exec cont_db createdb -U odoo -O odoo test_db" in commands_run
    assert "exec cont_db psql -U odoo -d test_db -f /tmp/dump.sql" in commands_run
