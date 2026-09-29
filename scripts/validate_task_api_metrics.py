#!/usr/bin/env python3
"""Validate task API ServiceMonitor configuration."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


def load_resources(
    path: Path,
    kind: str,
) -> list[dict[str, Any]]:
    """Load Kubernetes resources of the requested kind."""

    if not path.is_file():
        raise SystemExit(f"FAIL: Rendered file not found: {path}")

    resources: list[dict[str, Any]] = []

    with path.open(encoding="utf-8") as stream:
        for document in yaml.safe_load_all(stream):
            if (
                isinstance(document, dict)
                and document.get("kind") == kind
            ):
                resources.append(document)

    return resources


def resource_name(resource: dict[str, Any]) -> str:
    """Return metadata.name from a Kubernetes resource."""

    name = resource.get("metadata", {}).get("name")

    if not isinstance(name, str) or not name:
        raise SystemExit(
            "FAIL: Kubernetes resource has no metadata.name"
        )

    return name


def validate_enabled(
    environment: str,
    rendered_file: Path,
) -> None:
    """Verify that an environment renders a ServiceMonitor."""

    monitors = load_resources(
        rendered_file,
        "ServiceMonitor",
    )

    if not monitors:
        raise SystemExit(
            f"FAIL: {environment} did not render a ServiceMonitor"
        )

    names = [resource_name(item) for item in monitors]

    print(
        f"PASS: {environment} ServiceMonitor enabled: {names}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dev",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--staging",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--production",
        type=Path,
        required=True,
    )

    args = parser.parse_args()

    validate_enabled("Dev", args.dev)
    validate_enabled("Staging", args.staging)
    validate_enabled("Production", args.production)

    print(
        "\nTask API metrics configuration validated."
    )


if __name__ == "__main__":
    main()
