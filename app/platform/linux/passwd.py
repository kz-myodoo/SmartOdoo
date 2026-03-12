import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

ENCPASS_BUCKET = "smartodoo"
ALLOW_STDIN_PROMPTS_ENV = "SMARTODOO_ALLOW_STDIN_PROMPTS"


def get_secret(secret_name: str, encpass_path: Path) -> str:
    """Resolve a secret from encpass on Linux."""
    bash_path = shutil.which("bash")
    if encpass_path.exists() and bash_path:
        show_result = subprocess.run(
            [str(encpass_path), "show", ENCPASS_BUCKET, secret_name],
            text=True,
            capture_output=True,
            check=False,
        )
        if show_result.returncode == 0:
            value = show_result.stdout.strip()
            if value and value != "**Locked**":
                return value

        allow_stdin_prompts = os.getenv(ALLOW_STDIN_PROMPTS_ENV) == "1"
        if sys.stdin.isatty() or allow_stdin_prompts:
            add_result = _encpass_add_secret(secret_name, encpass_path)
            verify_result = subprocess.run(
                [str(encpass_path), "show", ENCPASS_BUCKET, secret_name],
                text=True,
                capture_output=True,
                check=False,
            )
            value = verify_result.stdout.strip()
            if verify_result.returncode == 0 and value and value != "**Locked**":
                return value

            add_stderr = (add_result.stderr or "").strip() if add_result.stderr is not None else ""
            add_stdout = (add_result.stdout or "").strip() if add_result.stdout is not None else ""
            details = add_stderr or add_stdout or "no details"
            raise RuntimeError(
                f"Failed to add secret '{secret_name}' to bucket '{ENCPASS_BUCKET}' "
                f"(encpass add exit code: {add_result.returncode}). Details: {details}"
            )

        error_details = show_result.stderr.strip() or "no details"
        raise RuntimeError(
            f"Missing secret '{secret_name}' in bucket '{ENCPASS_BUCKET}'. "
            f"Interactive add requires terminal input (TTY) or {ALLOW_STDIN_PROMPTS_ENV}=1. "
            f"Details: {error_details}"
        )

    raise RuntimeError(
        f"Missing secret '{secret_name}'. Configure encpass.sh (Linux/macOS)."
    )


def _prompt_secret_value(secret_name: str) -> Optional[str]:
    """Prompt user for a secret value and confirm it."""
    try:
        first = input(f"Enter value for {secret_name}: ").strip()
        second = input(f"Confirm value for {secret_name}: ").strip()
    except (EOFError, KeyboardInterrupt):
        return None

    if not first:
        return None
    if first != second:
        raise RuntimeError(f"Secret confirmation mismatch for '{secret_name}'.")
    return first


def _encpass_add_secret(secret_name: str, encpass_path: Path) -> subprocess.CompletedProcess:
    """Add or update secret in the encpass bucket."""
    prompted_value = _prompt_secret_value(secret_name)
    if prompted_value:
        add_input = f"{prompted_value}\n{prompted_value}\n"
        return subprocess.run(
            [str(encpass_path), "add", "-f", ENCPASS_BUCKET, secret_name],
            text=True,
            capture_output=True,
            check=False,
            input=add_input,
        )

    return subprocess.CompletedProcess(
        args=[str(encpass_path), "add", "-f", ENCPASS_BUCKET, secret_name],
        returncode=1,
        stdout="",
        stderr="Secret input canceled.",
    )
