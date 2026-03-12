import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

ALLOW_STDIN_PROMPTS_ENV = "SMARTODOO_ALLOW_STDIN_PROMPTS"
GUI_MODE_ENV = "SMARTODOO_GUI_MODE"


def _windows_hidden_subprocess_kwargs() -> dict[str, Any]:
    """Hide subprocess windows while running from GUI mode."""
    if os.getenv(GUI_MODE_ENV) != "1":
        return {}

    kwargs: dict[str, Any] = {}
    create_no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    if create_no_window:
        kwargs["creationflags"] = create_no_window

    startupinfo_cls = getattr(subprocess, "STARTUPINFO", None)
    if startupinfo_cls is not None:
        startupinfo = startupinfo_cls()
        startupinfo.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 0)
        startupinfo.wShowWindow = getattr(subprocess, "SW_HIDE", 0)
        kwargs["startupinfo"] = startupinfo
    return kwargs


def get_secret(secret_name: str, windows_secret_dir: Path) -> str:
    """Resolve secret from Windows credential store or environment variable."""
    env_key = secret_name.upper()
    env_value = os.getenv(env_key)

    windows_value = get_windows_secret(secret_name, env_value, windows_secret_dir)
    if windows_value:
        return windows_value

    if env_value:
        return env_value

    raise RuntimeError(
        f"Missing secret '{secret_name}'. Set env var '{env_key}' or configure Windows secret files in '{windows_secret_dir}'."
    )


def get_windows_secret(secret_name: str, env_value: Optional[str], windows_secret_dir: Path) -> Optional[str]:
    """Resolve secret from legacy CliXml files or create it via Get-Credential."""
    secret_specs: dict[str, tuple[str, str]] = {
        "github_addons_token": ("git_addons.xml", "Provide login and token for YOUR github account."),
        "github_enterprise_token": ("git_ent.xml", "Provide login and token for COMPANY github account."),
    }
    spec = secret_specs.get(secret_name)
    if not spec:
        return env_value

    file_name, prompt_message = spec
    secret_file = windows_secret_dir / file_name

    loaded_value = load_windows_credential_token(secret_file)
    if loaded_value:
        return loaded_value

    if env_value:
        save_windows_credential_token(secret_file, env_value, username="token", windows_secret_dir=windows_secret_dir)
        return env_value

    allow_stdin_prompts = os.getenv(ALLOW_STDIN_PROMPTS_ENV) == "1"
    if not (sys.stdin.isatty() or allow_stdin_prompts):
        return None

    return prompt_windows_credential_token(secret_file, prompt_message, windows_secret_dir=windows_secret_dir)


def find_powershell() -> Optional[str]:
    """Find a PowerShell executable."""
    return shutil.which("pwsh") or shutil.which("powershell")


def _escape_ps_single_quoted(value: str) -> str:
    """Escape a value for PowerShell single-quoted string."""
    return value.replace("'", "''")


def _ensure_hidden_secret_dir(windows_secret_dir: Path) -> None:
    """Create Windows secret directory and mark it hidden."""
    windows_secret_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["attrib", "+h", str(windows_secret_dir)], text=True, check=False)


def load_windows_credential_token(secret_file: Path) -> Optional[str]:
    """Read token from a PowerShell CliXml credential file."""
    if not secret_file.exists():
        return None

    powershell = find_powershell()
    if not powershell:
        return None

    path_escaped = _escape_ps_single_quoted(str(secret_file))
    script = (
        f"$cred = Import-Clixml -Path '{path_escaped}'; "
        "if ($null -eq $cred) { exit 1 }; "
        "$pwd = $cred.GetNetworkCredential().Password; "
        "if ([string]::IsNullOrWhiteSpace($pwd)) { exit 1 }; "
        "Write-Output $pwd"
    )
    result = subprocess.run(
        [powershell, "-NoProfile", "-Command", script],
        text=True,
        capture_output=True,
        check=False,
        **_windows_hidden_subprocess_kwargs(),
    )
    if result.returncode != 0:
        return None

    value = result.stdout.strip()
    return value or None


def save_windows_credential_token(
    secret_file: Path,
    token: str,
    username: str,
    windows_secret_dir: Path,
) -> None:
    """Persist token into a PowerShell CliXml credential file."""
    powershell = find_powershell()
    if not powershell:
        return

    _ensure_hidden_secret_dir(windows_secret_dir)
    token_escaped = _escape_ps_single_quoted(token)
    username_escaped = _escape_ps_single_quoted(username)
    path_escaped = _escape_ps_single_quoted(str(secret_file))
    script = (
        f"$secure = ConvertTo-SecureString '{token_escaped}' -AsPlainText -Force; "
        f"$cred = New-Object System.Management.Automation.PSCredential('{username_escaped}', $secure); "
        f"$cred | Export-Clixml -Path '{path_escaped}'"
    )
    subprocess.run([powershell, "-NoProfile", "-Command", script], text=True,
                   check=False, **_windows_hidden_subprocess_kwargs())


def prompt_windows_credential_token(secret_file: Path, prompt_message: str, windows_secret_dir: Path) -> str:
    """Prompt for credentials on Windows and persist token to CliXml file."""
    powershell = find_powershell()
    if not powershell:
        raise RuntimeError("PowerShell is required to manage secrets on Windows.")

    _ensure_hidden_secret_dir(windows_secret_dir)
    path_escaped = _escape_ps_single_quoted(str(secret_file))
    prompt_escaped = _escape_ps_single_quoted(prompt_message)
    script = (
        f"$cred = Get-Credential -Message '{prompt_escaped}'; "
        "if ($null -eq $cred) { exit 1 }; "
        "$pwd = $cred.GetNetworkCredential().Password; "
        "if ([string]::IsNullOrWhiteSpace($pwd)) { exit 1 }; "
        f"$cred | Export-Clixml -Path '{path_escaped}'; "
        "Write-Output $pwd"
    )
    result = subprocess.run(
        [powershell, "-NoProfile", "-Command", script],
        text=True,
        capture_output=True,
        check=False,
        **_windows_hidden_subprocess_kwargs(),
    )
    if result.returncode != 0:
        error_details = result.stderr.strip() or "no details"
        raise RuntimeError(f"Failed to capture Windows credential secret. Details: {error_details}")

    token = result.stdout.strip()
    if not token:
        raise RuntimeError("Failed to capture Windows credential secret (empty value).")
    return token
