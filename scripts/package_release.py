#!/usr/bin/env python3
"""Package sources and persisted full-flow evidence, with a verified manifest."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def included(path):
    rel = path.relative_to(ROOT)
    return ("__pycache__" not in rel.parts and path.suffix not in (".pyc", ".vvp")
            and not str(rel.as_posix()).startswith(("verification/evidence_check/", "verification/wrapper_evidence_check/"))
            and rel.as_posix() != "release_manifest.json" and ".git" not in rel.parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        parser.error("Output already exists; choose a new archive path")
    if output.is_relative_to(ROOT):
        parser.error("Write the ZIP beside the project, not inside it")
    summary = json.loads((ROOT / "evidence/full_flow_final/summary.json").read_text(encoding="utf-8"))
    if summary["status"] != "PASS":
        raise RuntimeError("Full-flow evidence must be PASS before packaging")
    for name, expected in summary["source_sha256"].items():
        if sha256(ROOT / name) != expected:
            raise RuntimeError("Source differs from tested snapshot: " + name)
    paths = sorted(p for p in ROOT.rglob("*") if p.is_file() and included(p))
    entries = [{"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size,
                "sha256": sha256(p)} for p in paths]
    manifest_path = ROOT / "release_manifest.json"
    manifest_path.write_text(json.dumps({"schema": 1, "full_flow_status": "PASS",
        "exclusions": ["simulation binaries .vvp", "Python caches", "duplicate development test outputs", "Git metadata"],
        "files": entries}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in paths + [manifest_path]:
            archive.write(path, ROOT.name + "/" + path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(output) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError("ZIP CRC failure: " + bad)
        for entry in entries:
            data = archive.read(ROOT.name + "/" + entry["path"])
            if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise RuntimeError("Archived hash mismatch: " + entry["path"])
    digest = sha256(output)
    output.with_suffix(output.suffix + ".sha256").write_text(digest + "  " + output.name + "\n", encoding="ascii")
    print(json.dumps({"archive": str(output), "files": len(entries) + 1,
                      "bytes": output.stat().st_size, "sha256": digest,
                      "crc_and_all_file_hashes": "PASS"}, indent=2))


if __name__ == "__main__":
    main()
