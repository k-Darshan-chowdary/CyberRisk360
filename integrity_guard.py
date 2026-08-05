"""Read-only SHA-256 integrity verification for CyberRisk360 sample data."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_MANIFEST_PATH = DATA_DIR / "integrity_manifest.json"
_HEX = frozenset("0123456789abcdef")


def _validate_hash(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("SHA-256 values must be strings.")
    if len(value) != 64 or any(character not in _HEX for character in value):
        raise ValueError("SHA-256 values must be 64 lowercase hexadecimal characters.")
    return value


def calculate_file_sha256(file_path: str | Path) -> str:
    """Return a file's SHA-256 digest while reading it in small binary chunks."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(path)
    if not path.is_file():
        raise ValueError("The supplied path is not a regular file.")
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_integrity_manifest(manifest: object) -> bool:
    """Validate the manifest without changing the caller-owned dictionary."""
    if not isinstance(manifest, dict):
        raise TypeError("The integrity manifest must be a dictionary.")
    required = {"project", "algorithm", "files"}
    if set(manifest) != required:
        raise ValueError("The integrity manifest must contain exactly project, algorithm, and files.")
    if not isinstance(manifest["project"], str) or not isinstance(manifest["algorithm"], str):
        raise TypeError("Manifest project and algorithm values must be strings.")
    if manifest["project"] != "CyberRisk360" or manifest["algorithm"] != "SHA-256":
        raise ValueError("The manifest project or algorithm is invalid.")
    files = manifest["files"]
    if not isinstance(files, dict):
        raise TypeError("Manifest files must be a dictionary.")
    if not files:
        raise ValueError("Manifest files must not be empty.")
    for relative_path, expected_hash in files.items():
        if not isinstance(relative_path, str):
            raise TypeError("Manifest file paths must be strings.")
        parsed = PurePosixPath(relative_path)
        if (not relative_path or parsed.is_absolute() or Path(relative_path).is_absolute()
                or ":" in parsed.parts[0] or "\\" in relative_path or ".." in parsed.parts):
            raise ValueError("Manifest paths must be safe project-relative forward-slash paths.")
        _validate_hash(expected_hash)
    return True


def load_integrity_manifest(manifest_path: str | Path = DEFAULT_MANIFEST_PATH) -> dict[str, Any]:
    """Load, validate, and return an independent integrity manifest."""
    path = Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("The integrity manifest is not valid JSON.") from error
    try:
        validate_integrity_manifest(value)
    except (TypeError, ValueError) as error:
        raise ValueError("The integrity manifest has an invalid structure.") from error
    return copy.deepcopy(value)


def verify_file_integrity(
    file_path: str | Path, expected_sha256: str, display_path: str | None = None
) -> dict[str, object]:
    """Compare one file with an expected digest and return a safe result."""
    expected = _validate_hash(expected_sha256)
    path = Path(file_path)
    shown = display_path if display_path is not None else path.name
    if not path.exists():
        return {"file": shown, "exists": False, "expected_sha256": expected,
                "actual_sha256": "", "matches": False}
    actual = calculate_file_sha256(path)
    return {"file": shown, "exists": True, "expected_sha256": expected,
            "actual_sha256": actual, "matches": actual == expected}


def verify_sample_data_integrity(
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    project_root: str | Path = PROJECT_ROOT,
) -> dict[str, object]:
    """Verify every safely resolved file in the integrity manifest."""
    manifest = load_integrity_manifest(manifest_path)
    root = Path(project_root).resolve()
    results: list[dict[str, object]] = []
    for relative_path, expected_hash in manifest["files"].items():
        target = (root / Path(*PurePosixPath(relative_path).parts)).resolve()
        try:
            target.relative_to(root)
        except ValueError as error:
            raise ValueError("A manifest path escapes the project root.") from error
        results.append(verify_file_integrity(target, expected_hash, relative_path))
    verified = sum(bool(result["matches"]) for result in results)
    return {"status": "Pass" if verified == len(results) else "Fail",
            "total_files": len(results), "verified_files": verified,
            "failed_files": len(results) - verified, "results": copy.deepcopy(results)}


def get_failed_integrity_results(integrity_report: object) -> list[dict[str, object]]:
    """Return independent copies of failed file results in their original order."""
    if not isinstance(integrity_report, dict):
        raise TypeError("The integrity report must be a dictionary.")
    results = integrity_report.get("results")
    if not isinstance(results, list):
        raise ValueError("The integrity report must contain a results list.")
    required = {"file", "exists", "expected_sha256", "actual_sha256", "matches"}
    for result in results:
        if not isinstance(result, dict):
            raise TypeError("Each integrity result must be a dictionary.")
        if set(result) != required or not isinstance(result["matches"], bool):
            raise ValueError("An integrity result has an invalid structure.")
    return [copy.deepcopy(result) for result in results if not result["matches"]]


def _main() -> int:
    try:
        report = verify_sample_data_integrity()
        print(f"CyberRisk360 sample-data integrity: {report['status']}")
        for result in report["results"]:
            print(f"- {result['file']}: {'Pass' if result['matches'] else 'Fail'}")
        return 0 if report["status"] == "Pass" else 1
    except (FileNotFoundError, TypeError, ValueError, OSError) as error:
        print(f"CyberRisk360 sample-data integrity: Fail\n- {error}")
        return 1


if __name__ == "__main__":
    sys.exit(_main())
