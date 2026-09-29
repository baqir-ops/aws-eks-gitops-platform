#!/usr/bin/env python3
"""Validate Argo CD metrics Service and ServiceMonitor contracts."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


EXPECTED_MONITORS = {
    "argocd-application-controller",
    "argocd-applicationset-controller",
    "argocd-repo-server",
    "argocd-server",
}


def load_resources(path: Path, kind: str) -> list[dict[str, Any]]:
    """Load all resources of a requested Kubernetes kind."""

    if not path.is_file():
        raise SystemExit(f"FAIL: File does not exist: {path}")

    resources: list[dict[str, Any]] = []

    with path.open(encoding="utf-8") as stream:
        for document in yaml.safe_load_all(stream):
            if isinstance(document, dict) and document.get("kind") == kind:
                resources.append(document)

    return resources


def resource_name(resource: dict[str, Any]) -> str:
    """Return the Kubernetes resource name."""

    metadata = resource.get("metadata", {})
    name = metadata.get("name")

    if not isinstance(name, str) or not name:
        raise SystemExit("FAIL: Kubernetes resource has no metadata.name")

    return name


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--services",
        type=Path,
        required=True,
        help="Helm-rendered Argo CD manifests",
    )
    parser.add_argument(
        "--monitors",
        type=Path,
        required=True,
        help="Git-managed Argo CD ServiceMonitor manifests",
    )
    args = parser.parse_args()

    services = load_resources(args.services, "Service")
    monitors = load_resources(args.monitors, "ServiceMonitor")

    monitor_names = {resource_name(monitor) for monitor in monitors}

    if monitor_names != EXPECTED_MONITORS:
        missing = sorted(EXPECTED_MONITORS - monitor_names)
        unexpected = sorted(monitor_names - EXPECTED_MONITORS)

        raise SystemExit(
            "FAIL: Unexpected Argo CD ServiceMonitor set. "
            f"Missing={missing}, Unexpected={unexpected}"
        )

    for monitor in monitors:
        monitor_name = resource_name(monitor)
        metadata = monitor.get("metadata", {})
        spec = monitor.get("spec", {})

        if metadata.get("namespace") != "argocd":
            raise SystemExit(
                f"FAIL: {monitor_name} must be created in namespace argocd"
            )

        namespace_selector = spec.get("namespaceSelector", {})
        match_names = namespace_selector.get("matchNames", [])

        if match_names != ["argocd"]:
            raise SystemExit(
                f"FAIL: {monitor_name} namespaceSelector must contain only argocd"
            )

        selector = spec.get("selector", {}).get("matchLabels", {})

        if not isinstance(selector, dict) or not selector:
            raise SystemExit(
                f"FAIL: {monitor_name} has no selector.matchLabels"
            )

        endpoints = spec.get("endpoints", [])

        if len(endpoints) != 1:
            raise SystemExit(
                f"FAIL: {monitor_name} must have exactly one endpoint"
            )

        endpoint = endpoints[0]
        endpoint_port = endpoint.get("port")
        endpoint_path = endpoint.get("path")
        scrape_timeout = endpoint.get("scrapeTimeout")

        if endpoint_port != "http-metrics":
            raise SystemExit(
                f"FAIL: {monitor_name} must scrape port http-metrics"
            )

        if endpoint_path != "/metrics":
            raise SystemExit(
                f"FAIL: {monitor_name} must scrape path /metrics"
            )

        if scrape_timeout != "10s":
            raise SystemExit(
                f"FAIL: {monitor_name} must use scrapeTimeout 10s"
            )

        matching_services: list[dict[str, Any]] = []

        for service in services:
            labels = service.get("metadata", {}).get("labels", {})

            if all(labels.get(key) == value for key, value in selector.items()):
                matching_services.append(service)

        if len(matching_services) != 1:
            matched_names = [
                resource_name(service)
                for service in matching_services
            ]

            raise SystemExit(
                f"FAIL: {monitor_name} matched "
                f"{len(matching_services)} Services: {matched_names}"
            )

        service = matching_services[0]
        service_name = resource_name(service)

        port_names = {
            port.get("name")
            for port in service.get("spec", {}).get("ports", [])
        }

        if endpoint_port not in port_names:
            raise SystemExit(
                f"FAIL: {monitor_name} expects port {endpoint_port}, "
                f"but {service_name} exposes {sorted(port_names)}"
            )

        print(
            f"PASS: {monitor_name} -> "
            f"{service_name}:{endpoint_port}{endpoint_path}"
        )

    print(
        "\nAll four Argo CD ServiceMonitor contracts passed."
    )


if __name__ == "__main__":
    main()
