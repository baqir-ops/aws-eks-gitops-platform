#!/usr/bin/env python3

"""Restore the ledger namespace and report verified recovery time."""

from argparse import ArgumentParser
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Sequence


def run_command(command: Sequence[str], timeout: int) -> str:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(
            f"Command timed out after {timeout} seconds: "
            f"{' '.join(command)}"
        ) from error

    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}"
            + (f"\n{details}" if details else "")
        )

    return result.stdout.strip()


def main() -> int:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backup",
        required=True,
        help="Name of the completed Velero backup to restore",
    )
    parser.add_argument(
        "--expected-sha256",
        required=True,
        help="SHA-256 recorded from /data/important.txt before deletion",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the JSON report (default: stdout)",
    )
    args = parser.parse_args()

    if not re.fullmatch(r"[0-9a-fA-F]{64}", args.expected_sha256):
        parser.error("--expected-sha256 must contain exactly 64 hex digits")

    for executable in ("velero", "kubectl"):
        if shutil.which(executable) is None:
            parser.error(f"required executable not found on PATH: {executable}")

    started_at = datetime.now(timezone.utc)
    restore_name = f"rto-{started_at:%Y%m%d%H%M%S%f}"
    report: dict[str, object] = {
        "backup": args.backup,
        "restore": restore_name,
        "started_at_utc": started_at.isoformat(),
        "status": "failed",
    }
    error_message: str | None = None

    try:
        run_command(
            [
                "velero",
                "restore",
                "create",
                restore_name,
                "--from-backup",
                args.backup,
                "--wait",
            ],
            timeout=600,
        )
        run_command(
            [
                "kubectl",
                "wait",
                "--namespace",
                "ledger",
                "--for=condition=Available",
                "deployment/ledger",
                "--timeout=180s",
            ],
            timeout=200,
        )
        checksum_output = run_command(
            [
                "kubectl",
                "exec",
                "--namespace",
                "ledger",
                "deployment/ledger",
                "--",
                "sha256sum",
                "/data/important.txt",
            ],
            timeout=30,
        )
        checksum_parts = checksum_output.split(maxsplit=1)
        if not checksum_parts or not re.fullmatch(
            r"[0-9a-fA-F]{64}",
            checksum_parts[0],
        ):
            raise RuntimeError(
                "Could not parse the restored file SHA-256 from kubectl output"
            )
        actual_sha256 = checksum_parts[0]
        actual_sha256 = actual_sha256.lower()
        expected_sha256 = args.expected_sha256.lower()
        report["expected_sha256"] = expected_sha256
        report["actual_sha256"] = actual_sha256

        if actual_sha256 != expected_sha256:
            raise RuntimeError(
                "Restored file checksum does not match the pre-incident "
                f"value (expected {expected_sha256}, got {actual_sha256})"
            )
        report["status"] = "succeeded"
    except RuntimeError as error:
        error_message = str(error)
        report["error"] = error_message

    completed_at = datetime.now(timezone.utc)
    report["completed_at_utc"] = completed_at.isoformat()
    report["recovery_time_seconds"] = round(
        (completed_at - started_at).total_seconds(),
        3,
    )
    serialized_report = json.dumps(report, indent=2) + "\n"

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized_report, encoding="utf-8")
        print(f"RTO report written to {args.output}")
    else:
        print(serialized_report, end="")

    if error_message:
        print(error_message, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
