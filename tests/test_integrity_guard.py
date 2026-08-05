"""Phase 8 regression tests for the sample-data integrity guard."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import pytest

import integrity_guard as guard


def test_calculate_known_sha256_and_chunked_input(tmp_path):
    payload = (b"CyberRisk360\x00" * 10000) + b"end"
    target = tmp_path / "large.bin"
    target.write_bytes(payload)
    assert guard.calculate_file_sha256(target) == hashlib.sha256(payload).hexdigest()


def test_calculate_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        guard.calculate_file_sha256(tmp_path / "missing")


def test_calculate_directory_raises(tmp_path):
    with pytest.raises(ValueError):
        guard.calculate_file_sha256(tmp_path)


def test_real_manifest_loads_and_is_independent():
    first = guard.load_integrity_manifest()
    assert list(first) == ["project", "algorithm", "files"]
    first["files"].clear()
    assert len(guard.load_integrity_manifest()["files"]) == 5


@pytest.mark.parametrize("manifest,error", [
    ([], TypeError),
    ({"project": "CyberRisk360", "algorithm": "SHA-256"}, ValueError),
    ({"project": "CyberRisk360", "algorithm": "SHA-256", "files": {"x": "0" * 64}, "extra": 1}, ValueError),
    ({"project": "Wrong", "algorithm": "SHA-256", "files": {"x": "0" * 64}}, ValueError),
    ({"project": "CyberRisk360", "algorithm": "sha256", "files": {"x": "0" * 64}}, ValueError),
    ({"project": "CyberRisk360", "algorithm": "SHA-256", "files": {}}, ValueError),
])
def test_invalid_manifest_structures(manifest, error):
    with pytest.raises(error):
        guard.validate_integrity_manifest(manifest)


@pytest.mark.parametrize("path", ["../outside.csv", "/absolute.csv", "data\\file.csv"])
def test_unsafe_manifest_paths_are_rejected(path):
    manifest = {"project": "CyberRisk360", "algorithm": "SHA-256", "files": {path: "0" * 64}}
    with pytest.raises(ValueError):
        guard.validate_integrity_manifest(manifest)


@pytest.mark.parametrize("digest", ["A" * 64, "0" * 63, "0" * 65, "g" * 64])
def test_invalid_hashes_are_rejected(digest):
    manifest = {"project": "CyberRisk360", "algorithm": "SHA-256", "files": {"data/file.csv": digest}}
    with pytest.raises(ValueError):
        guard.validate_integrity_manifest(manifest)


def test_all_current_samples_pass_and_inputs_do_not_change():
    before = guard.load_integrity_manifest()
    snapshot = copy.deepcopy(before)
    report = guard.verify_sample_data_integrity()
    assert report["status"] == "Pass"
    assert report["verified_files"] == report["total_files"] == 5
    assert before == snapshot


def test_tampered_and_missing_file_results(tmp_path):
    expected = hashlib.sha256(b"original").hexdigest()
    target = tmp_path / "sample.csv"
    target.write_bytes(b"changed")
    tampered = guard.verify_file_integrity(target, expected, "data/sample.csv")
    missing = guard.verify_file_integrity(tmp_path / "missing.csv", expected)
    assert tampered["exists"] and not tampered["matches"]
    assert not missing["exists"] and missing["actual_sha256"] == ""


def test_failed_result_helper_preserves_order_and_returns_copies():
    results = [{"file": name, "exists": True, "expected_sha256": "0" * 64,
                "actual_sha256": "1" * 64, "matches": matches}
               for name, matches in (("a", False), ("b", True), ("c", False))]
    report = {"results": results}
    failed = guard.get_failed_integrity_results(report)
    assert [item["file"] for item in failed] == ["a", "c"]
    failed[0]["file"] = "changed"
    assert report["results"][0]["file"] == "a"


def test_sample_hashes_match_manifest():
    manifest = guard.load_integrity_manifest()
    for name, digest in manifest["files"].items():
        assert guard.calculate_file_sha256(guard.PROJECT_ROOT / name) == digest
