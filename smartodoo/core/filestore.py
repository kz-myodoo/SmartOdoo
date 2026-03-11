from pathlib import Path
from smartodoo.core.docker_ops import DockerOps, DockerOpsError

class FilestoreError(Exception):
    pass

class FilestoreManager:
    """Odpowiada za kopiowanie i naprawę uprawnień do katalogu filestore."""
    
    def __init__(self, docker_ops: DockerOps, odoo_container: str):
        self.docker_ops = docker_ops
        self.odoo_container = odoo_container

    def restore_filestore(self, local_path: Path, db_name: str) -> str:
        """Kopiuje filestore i nadaje prawa chown wew. kontenera odoo."""
        if not local_path.exists() or not local_path.is_dir():
            raise FilestoreError(f"Folder filestore nie istnieje: {local_path}")
            
        remote_dest_dir = f"/var/lib/odoo/filestore/{db_name}"
        
        try:
            # Utworzenie lokalizacji docelowej gdyby nie istniała
            self.docker_ops.exec_run(self.odoo_container, ["mkdir", "-p", remote_dest_dir], user="root")
            
            # Kopiujemy z wnetrza folderu local_path/. do remote_dest_dir
            # cp w dockerze na 15k plikach na Windowsie jest bardzo wolne, lepiej uzyc tar:
            import subprocess
            cmd = f'tar -c -C "{local_path}" . | docker exec -i --user root {self.odoo_container} tar -x -C "{remote_dest_dir}"'
            subprocess.run(cmd, shell=True, check=True)
            
            # Prawa odoo:odoo (uid/gid Odoo to zazwyczaj odoo user, UID=100/1000 - chown username)
            self.docker_ops.exec_run(self.odoo_container, ["chown", "-R", "odoo:odoo", remote_dest_dir], user="root")
            self.docker_ops.exec_run(self.odoo_container, ["chmod", "-R", "755", remote_dest_dir], user="root")
            
        except DockerOpsError as e:
            raise FilestoreError(f"Przywracanie filestore nie powiodło się: {e}")
            
        return f"Przywrócono i nadpisano uprawnienia dla {db_name} wewnątrz kontenera {self.odoo_container}"
