from pathlib import Path
from smartodoo.core.docker_ops import DockerOps, DockerOpsError

class DbOpsError(Exception):
    pass

class DbOps:
    """Moduł do rządzania bazą z perspektywy dewelopera Odoo. Wywołuje psql/pg_restore."""
    
    def __init__(self, docker_ops: DockerOps, db_container: str):
        self.docker_ops = docker_ops
        self.db_container = db_container
        
    def restore_database(self, dump_path: Path, db_name: str, db_user: str):
        """Kopiuje plik SQL do kontenera i rekreuje bazę danych omijając locki klienta."""
        if not dump_path.exists():
            raise DbOpsError(f"Nie znaleziono pliku dump: {dump_path}")
            
        remote_tmp = "/tmp/dump.sql"
        
        try:
            # 1. Kopiuj dump na kontener
            self.docker_ops.cp(str(dump_path), f"{self.db_container}:{remote_tmp}")
            
            # 2. Usuń i stwórz bazę ponownie
            self.docker_ops.exec_run(self.db_container, ["dropdb", "-U", db_user, "--if-exists", "--force", db_name])
            self.docker_ops.exec_run(self.db_container, ["createdb", "-U", db_user, "-O", db_user, db_name])
            
            # 3. Importuj
            # Używamy formatu psql (złożony skrypt lub plik wykonywalny SQL tekstowy)
            self.docker_ops.exec_run(self.db_container, ["psql", "-q", "-U", db_user, "-d", db_name, "-f", remote_tmp], env={"PGPAGER": ""})
            
        except DockerOpsError as e:
            raise DbOpsError(f"Operacja na bazie nie powiodła się: {e}")
            
        return f"Przywrócono bazę {db_name} z pliku {dump_path.name}"
