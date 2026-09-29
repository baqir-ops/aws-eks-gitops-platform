#!/usr/bin/env python3

"""Validate the secure GitOps desired-state repository."""

from pathlib import Path
import re
import sys
from typing import Any

import yaml


ENVIRONMENTS = ("dev", "staging", "production")

IMAGE_REPOSITORY_PATTERN = re.compile(
    r"^\d{12}\.dkr\.ecr\.ap-south-1\.amazonaws\.com/"
    r"secure-gitops-app$"
)

IMAGE_TAG_PATTERN = re.compile(r"^sha-[0-9a-f]{40}$")
IMAGE_DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")

errors: list[str] = []
environment_summaries: list[str] = []
repositories: set[str] = set()


def fail(message: str) -> None:
    errors.append(message)


def require_mapping(
    parent: dict[str, Any],
    key: str,
    location: str,
) -> dict[str, Any]:
    value = parent.get(key)

    if not isinstance(value, dict):
        fail(f"{location}: '{key}' must be a mapping")
        return {}

    return value


for environment in ENVIRONMENTS:
    path = Path("environments") / environment / "values.yaml"

    if not path.is_file():
        fail(f"{path}: required values file is missing")
        continue

    try:
        values = yaml.safe_load(path.read_text())
    except yaml.YAMLError as error:
        fail(f"{path}: invalid YAML: {error}")
        continue

    if not isinstance(values, dict):
        fail(f"{path}: document root must be a mapping")
        continue

    replica_count = values.get("replicaCount")

    if (
        not isinstance(replica_count, int)
        or isinstance(replica_count, bool)
        or replica_count < 1
    ):
        fail(f"{path}: replicaCount must be a positive integer")

    image = require_mapping(values, "image", str(path))
    repository = image.get("repository")
    tag = image.get("tag")
    digest = image.get("digest", "")
    pull_policy = image.get("pullPolicy")

    if not isinstance(repository, str):
        fail(f"{path}: image.repository must be a string")
    elif not IMAGE_REPOSITORY_PATTERN.fullmatch(repository):
        fail(
            f"{path}: image.repository is not the expected "
            "private ECR repository"
        )
    else:
        repositories.add(repository)

    if not isinstance(tag, str) or not IMAGE_TAG_PATTERN.fullmatch(tag):
        fail(
            f"{path}: image.tag must use immutable format "
            "'sha-' followed by 40 lowercase hexadecimal characters"
        )

    if digest not in ("", None):
        if (
            not isinstance(digest, str)
            or not IMAGE_DIGEST_PATTERN.fullmatch(digest)
        ):
            fail(
                f"{path}: image.digest must be empty or a valid "
                "sha256 digest"
            )

    if pull_policy not in {"IfNotPresent", "Always", "Never"}:
        fail(f"{path}: image.pullPolicy is invalid")

    config = require_mapping(values, "config", str(path))

    if config.get("environment") != environment:
        fail(
            f"{path}: config.environment must be exactly "
            f"'{environment}'"
        )

    if config.get("forceFailure") not in {"true", "false"}:
        fail(
            f"{path}: config.forceFailure must be quoted "
            "'true' or 'false'"
        )

    autoscaling = require_mapping(values, "autoscaling", str(path))

    if not isinstance(autoscaling.get("enabled"), bool):
        fail(f"{path}: autoscaling.enabled must be a boolean")

    minimum = autoscaling.get("minReplicas")
    maximum = autoscaling.get("maxReplicas")
    target_cpu = autoscaling.get("targetCPUUtilizationPercentage")

    if (
        not isinstance(minimum, int)
        or isinstance(minimum, bool)
        or minimum < 1
    ):
        fail(f"{path}: autoscaling.minReplicas must be positive")

    if (
        not isinstance(maximum, int)
        or isinstance(maximum, bool)
        or maximum < 1
    ):
        fail(f"{path}: autoscaling.maxReplicas must be positive")

    if (
        isinstance(minimum, int)
        and isinstance(maximum, int)
        and not isinstance(minimum, bool)
        and not isinstance(maximum, bool)
        and maximum < minimum
    ):
        fail(
            f"{path}: autoscaling.maxReplicas cannot be less "
            "than minReplicas"
        )

    if (
        not isinstance(target_cpu, int)
        or isinstance(target_cpu, bool)
        or not 1 <= target_cpu <= 100
    ):
        fail(
            f"{path}: targetCPUUtilizationPercentage must be "
            "between 1 and 100"
        )

    service_monitor = require_mapping(
        values,
        "serviceMonitor",
        str(path),
    )

    if not isinstance(service_monitor.get("enabled"), bool):
        fail(f"{path}: serviceMonitor.enabled must be a boolean")

    ingress = require_mapping(values, "ingress", str(path))

    if not isinstance(ingress.get("enabled"), bool):
        fail(f"{path}: ingress.enabled must be a boolean")

    environment_summaries.append(
        f"{environment}: replicas={replica_count}, tag={tag}, "
        f"autoscaling={autoscaling.get('enabled')}"
    )


if len(repositories) > 1:
    fail("Environment files reference different image repositories")


for path in sorted(Path(".").rglob("*.yaml")):
    if any(
        part in {".git", ".venv", "docs"}
        for part in path.parts
    ):
        continue

    try:
        documents = list(yaml.safe_load_all(path.read_text()))
    except yaml.YAMLError as error:
        fail(f"{path}: invalid YAML: {error}")
        continue

    for index, document in enumerate(documents, start=1):
        if not isinstance(document, dict):
            continue

        kind = document.get("kind")

        if kind == "Secret":
            fail(
                f"{path}, document {index}: plain Kubernetes Secret "
                "manifests are prohibited"
            )

        if kind in {"Application", "ApplicationSet"}:
            serialized = yaml.safe_dump(document)

            if "targetRevision: '*'" in serialized:
                fail(
                    f"{path}, document {index}: wildcard "
                    "targetRevision is prohibited"
                )

            if "targetRevision: latest" in serialized:
                fail(
                    f"{path}, document {index}: unpinned latest "
                    "revision is prohibited"
                )


if errors:
    print("GitOps validation failed:\n")

    for error in errors:
        print(f"- {error}")

    sys.exit(1)


print("GitOps validation passed.\n")

for summary in environment_summaries:
    print(f"- {summary}")
