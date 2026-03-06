import subprocess
from pathlib import Path
from typing import Optional

class GitManager:
    """Odizolowany menedżer do zadań gita, gotowy do zastosowania Dependency Injection
    i mockowania w testach w taki sam sposób jak DockerManager"""

    def clone(self, target_path: Path, url: str, branch: Optional[str] = None, depth: int = 1) -> bool:
        """Klonuje repozytorium z określoną głębokością w celu optymalizacji przestrzeni"""
        if not url:
            return False
            
        cmd = ["git", "-C", str(target_path.parent), "clone"]
        if depth:
            cmd.extend(["--depth", str(depth)])
        if branch:
            cmd.extend(["--branch", branch])
            
        cmd.extend([url, target_path.name])
        return subprocess.run(cmd, text=True).returncode == 0

    def pull(self, repo_path: Path) -> bool:
        """Odświeża repozytorium (fast-forward)"""
        cmd = ["git", "-C", str(repo_path), "pull", "--ff-only"]
        return subprocess.run(cmd, text=True).returncode == 0
