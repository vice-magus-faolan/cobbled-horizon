#!/usr/bin/env python3
"""Exact-pin distribution decisions and deterministic recipient notices.

Integrity validators are intentionally separate from permission decisions. A
successful structural check never grants permission to upload an archive.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import tomllib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHANNELS = {"github", "curseforge", "private"}
STATES = {"allowed", "conditional", "unknown", "denied"}


def load(path: pathlib.Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def https(value: str) -> bool:
    return isinstance(value, str) and value.startswith("https://")


def check_record(record: dict) -> None:
    for field in ("project", "version", "name", "license", "credit", "conditions"):
        require(isinstance(record.get(field), str) and bool(record[field]), f"permission record requires {field}")
    require(re.fullmatch(r"[0-9a-f]{64}", record.get("metafile_sha256", "")) is not None, "permission must bind original metafile bytes, including download URL and side")
    require(re.fullmatch(r"[0-9a-f]{128}", record.get("sha512", "")) is not None, "permission record requires exact SHA-512")
    require(record.get("side") == "server", "permission record must bind server side")
    require(set(record.get("channels", {})) == CHANNELS, "permission record must name every distribution channel")
    require(all(value in STATES for value in record["channels"].values()), "invalid permission state")
    require(record.get("lines") and set(record["lines"]) <= {"26.2", "26.3", "prospective"}, "permission record requires exact version lines")
    require(record.get("evidence") and all(https(item["url"]) and re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) and item.get("at") for item in record["evidence"]), "permission evidence requires URL, digest and capture date")
    require(isinstance(record.get("texts"), list) and isinstance(record.get("pending"), list), "permission record requires texts and pending obligations")
    require(record.get("nested") in {"verified", "unknown"}, "nested/shaded coverage must be explicit")
    require(isinstance(record.get("source"), dict), "permission record requires source disposition")
    source = record["source"]
    require(source.get("status") in {"unknown", "not-required", "equivalent-access"}, "invalid source disposition")
    require(isinstance(source.get("basis"), str) and bool(source["basis"]), "source disposition needs a basis")
    require(all(isinstance(item, str) and item for item in record["pending"]), "invalid pending obligation")
    if source["status"] != "unknown":
        check_source(source)


def records(root: pathlib.Path) -> list[dict]:
    data = load(root / "distribution/permissions.toml")
    require(data.get("schema") == 1, "unsupported distribution schema")
    rules = data.get("rules", {})
    obligations = data.get("obligations", {})
    result = [{**obligations, **rules.get(item["project"], {}), **item} for item in data.get("components", [])]
    require(bool(result), "permission inventory is empty")
    seen = set()
    for record in result:
        check_record(record)
        key = (record["project"], record["version"], record["sha512"])
        require(key not in seen, "duplicate exact permission identity")
        seen.add(key)
        for digest in record["texts"]:
            require(re.fullmatch(r"[0-9a-f]{64}", digest) is not None, "unsafe license-text identity")
            path = root / "distribution/texts" / (digest + ".txt")
            require(path.is_file() and not path.is_symlink(), f"missing regular license text: {digest}")
            require(hashlib.sha256(path.read_bytes()).hexdigest() == digest, f"changed license text: {digest}")
            provenance = record.get("text_provenance", [])
            require(any(https(item.get("url")) and item.get("sha256") == digest and item.get("at") for item in provenance), f"missing license-text provenance: {digest}")
    return result


def selected(root: pathlib.Path) -> list[tuple[dict, dict]]:
    """Bind every indexed active mod to original download and updater identity."""
    inventory = records(root)
    by_identity = {(item["project"], item["version"], item["sha512"]): item for item in inventory}
    line = load(root / "pack.toml")["versions"]["minecraft"]
    result = []
    targets = set()
    references = set()
    for entry in load(root / "index.toml")["files"]:
        if not entry.get("metafile"):
            continue
        relative = pathlib.PurePosixPath(entry["file"])
        require(relative.parent == pathlib.PurePosixPath("mods"), "unexpected active metadata path")
        mod = load(root / relative)
        pin = mod["update"]["modrinth"]
        key = (pin["mod-id"], pin["version"], mod["download"]["hash"])
        require(key in by_identity, f"new or changed pin lacks exact permission record: {relative}")
        record = by_identity[key]
        require(line in record["lines"], f"permission line mismatch: {relative}")
        require(mod["side"] == record["side"] and mod["download"]["hash-format"] == "sha512" and hashlib.sha256((root / relative).read_bytes()).hexdigest() == record["metafile_sha256"], f"stale permission download identity: {relative}")
        hosted = mod.get("update", {}).get("curseforge")
        require(hosted == record.get("hosted"), f"unverified hosted mapping: {relative}")
        filename = mod["filename"]
        require(isinstance(filename, str) and bool(filename) and
                not any(char in filename for char in "/\\:\x00") and filename not in {".", ".."},
                f"unsafe mod filename: {relative}")
        require(filename not in targets, f"duplicate selected target: {filename}")
        targets.add(filename)
        if hosted is not None:
            require(isinstance(hosted, dict) and set(hosted) == {"project-id", "file-id"} and
                    all(type(value) is int and value > 0 for value in hosted.values()), "invalid native CurseForge mapping")
            reference = (hosted["project-id"], hosted["file-id"])
            require(reference not in references, "duplicate native CurseForge reference")
            references.add(reference)
            check_hosted_evidence(mod, record)
        result.append((mod, record))
    require(bool(result), "no selected distribution components")
    return result


def check_source(source: dict) -> None:
    status = source.get("status")
    require(status in {"not-required", "equivalent-access"}, "unfulfilled source-delivery obligation")
    require(bool(source.get("basis")), "source disposition needs an applicability/completeness basis")
    if status == "equivalent-access":
        revision = source.get("revision", "")
        require(re.fullmatch(r"[0-9a-f]{40}", revision) is not None, "source must bind an exact revision")
        require(https(source.get("url")) and revision in source["url"], "source must use an immutable exact-revision download, not a homepage")
        require(re.fullmatch(r"[0-9a-f]{64}", source.get("sha256", "")) is not None, "source download requires verified digest")
        require(bool(source.get("directions")) and bool(source.get("verified_at")), "source requires equivalent-access directions and availability verification")


def check_hosted_evidence(mod: dict, record: dict) -> None:
    evidence = record.get("hosted_evidence")
    require(isinstance(evidence, dict), f"missing structured hosted mapping evidence: {record['name']}")
    hosted = mod["update"]["curseforge"]
    url = f"https://www.curseforge.com/api/v1/mods/{hosted['project-id']}/files/{hosted['file-id']}/download"
    require(evidence.get("url") == url and evidence.get("at") and
            re.fullmatch(r"[0-9a-f]{64}", evidence.get("sha256", "")) and
            evidence.get("sha512") == mod["download"]["hash"],
            f"hosted mapping evidence must bind selected download SHA-512: {record['name']}")


def uncleared_components(items: list[tuple[dict, dict]], channel: str) -> list[dict]:
    """Separate valid unresolved obligations from corrupt policy/identity evidence.

    Validate every component, then assess redistribution only for conveyed JARs.
    References do not convey binaries, but never bypass identity/evidence checks.
    """
    require(channel in CHANNELS, f"unknown distribution channel: {channel}")
    failures = []
    for mod, record in items:
        source = record["source"]
        if "curseforge" in mod.get("update", {}):
            continue  # Native CF exporter conveys this exact verified reference.
        unresolved = (record["channels"][channel] != "allowed" or record["pending"] or
                      record["nested"] != "verified" or source["status"] == "unknown" or not record["texts"])
        if unresolved or (channel == "curseforge" and record.get("platform") != "verified"):
            failures.append(record)
    return failures


def clearance(root: pathlib.Path, channel: str) -> list[tuple[dict, dict]]:
    items = selected(root)
    failures = uncleared_components(items, channel)
    require(not failures, "distribution not cleared for " + channel + ":\n" + "\n".join(
        f"{record['name']} {record['version']}: {record['channels'][channel]}; {record['conditions']}" for record in failures))
    return items


def release_plan(root: pathlib.Path, tag: str | None = None) -> dict:
    """The single public asset contract; policy errors are never a fallback."""
    from release_metadata import metadata
    identity = metadata(load(root / "pack.toml"), tag)
    blockers = uncleared_components(selected(root), "github")
    basename = identity["basename"]
    suffixes = (".mrpack", ".mrpack.sha256") if blockers else (".mrpack", ".zip", ".sha256")
    notes = ("Distribution obligations are fulfilled for the JARs actually bundled in the CurseForge ZIP. "
             "Exact hosted references do not grant binary redistribution rights. No server ZIP is published.")
    if blockers:
        names = sorted(f"{item['name']} ({item['project']}/{item['version']})" for item in blockers)
        notes = ("Metadata-only release: the CurseForge ZIP is withheld because "
                 "binary redistribution obligations remain unresolved for these bundled mods:\n\n" +
                 "\n".join("- " + name for name in names) +
                 "\n\nThe no-JAR .mrpack contains upstream download references, configuration and recipient notices; "
                 "it does not grant redistribution permission for the referenced binaries. No server ZIP is published.")
    return {"schema": 1, "tag": identity["tag"], "mode": "metadata" if blockers else "full",
            "assets": [basename + suffix for suffix in suffixes], "checksum": basename + suffixes[-1],
            "policy_sha256": hashlib.sha256((root / "distribution/permissions.toml").read_bytes()).hexdigest(),
            "notes": notes}


def verify_release(root: pathlib.Path, plan: dict, directory: pathlib.Path, tag: str | None = None) -> None:
    """Reassess policy, then require exactly the selected nonempty checksum set.

    Archive semantics remain in Make's existing check-metadata/check-upload
    consumers. In particular a failing ZIP check must not select another mode.
    """
    require(plan == release_plan(root, tag), "release plan differs from current source/policy/tag")
    require({path.name for path in directory.iterdir()} == set(plan["assets"]), "unexpected release file set")
    for name in plan["assets"]:
        path = directory / name
        require(path.is_file() and not path.is_symlink() and path.stat().st_size > 0, "missing regular nonempty asset: " + name)
    expected = []
    for name in plan["assets"][:-1]:
        with (directory / name).open("rb") as stream:
            expected.append(hashlib.file_digest(stream, "sha256").hexdigest() + "  " + name + "\n")
    require((directory / plan["checksum"]).read_text(encoding="utf-8") == "".join(expected),
            "release checksum content/membership differs from selected archives")


def notice_members(root: pathlib.Path) -> dict[str, bytes]:
    """Use a finite member contract; never copy the policy directory wholesale.

    Structural-only fixtures without policy intentionally have no notice members.
    Binary publication entrypoints also call clearance. Metadata-only exports
    and ephemeral verification retain unresolved notices without granting rights.
    """
    if not (root / "distribution/permissions.toml").exists():
        return {}
    credits = ["# Component credits", "", "Unmodified upstream binaries; pack configuration changes only.", ""]
    sources = ["# Component source access", "", "These directions do not relicense independent pack components.", ""]
    members = {}
    for _, record in sorted(selected(root), key=lambda item: (item[1]["project"], item[1]["version"])):
        identity = f"{record['name']} ({record['project']}/{record['version']})"
        credits.extend([f"## {identity}", "", record["credit"], "", f"License/permission: {record['license']}", "",
                        "Distribution conditions (not a grant): " + record["conditions"], ""])
        source = record["source"]
        sources.extend([f"## {identity}", "", source.get("directions", source.get("basis", "Source delivery unresolved; not redistribution clearance.")), ""])
        if source.get("status") == "equivalent-access":
            check_source(source)
            sources.extend(["Source download: " + source["url"], "", "Revision: " + source["revision"], ""])
        for digest in record["texts"]:
            members["LICENSES/" + digest + ".txt"] = (root / "distribution/texts" / (digest + ".txt")).read_bytes()
    members["CREDITS.md"] = ("\n".join(credits) + "\n").encode()
    members["SOURCES.md"] = ("\n".join(sources) + "\n").encode()
    return members


def add_notices(path: pathlib.Path, root: pathlib.Path, channel: str) -> None:
    clearance(root, channel)
    write_notices(path, root)


def write_notices(path: pathlib.Path, root: pathlib.Path) -> None:
    """Write finite notices for integrity-only preparation, not upload clearance."""
    members = notice_members(root)
    with zipfile.ZipFile(path, "a", compression=zipfile.ZIP_DEFLATED) as archive:
        require(not any("overrides/" + name in archive.namelist() for name in members), "archive already contains notice members")
        for name, data in sorted(members.items()):
            info = zipfile.ZipInfo("overrides/" + name, (1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("schema", "check", "notices", "status", "verification-notices", "metadata-notices", "release-plan", "verify-release"))
    parser.add_argument("--channel", choices=sorted(CHANNELS))
    parser.add_argument("--archive", type=pathlib.Path)
    parser.add_argument("--tag")
    parser.add_argument("--plan", type=pathlib.Path)
    parser.add_argument("--directory", type=pathlib.Path, default=ROOT / "dist")
    args = parser.parse_args()
    try:
        if args.command == "release-plan":
            print(json.dumps(release_plan(ROOT, args.tag), sort_keys=True))
            return 0
        elif args.command == "verify-release":
            require(args.plan is not None, "release plan is required")
            verify_release(ROOT, json.loads(args.plan.read_text(encoding="utf-8")), args.directory, args.tag)
        elif args.command == "schema":
            selected(ROOT)
        elif args.command == "status":
            items = selected(ROOT)
            for channel in sorted(CHANNELS):
                print(f"{channel}: {sum(item['channels'][channel] == 'allowed' for _, item in items)}/{len(items)} records allowed (all obligations still required)")
        elif args.command in {"verification-notices", "metadata-notices"}:
            require(args.archive is not None, "archive is required")
            if args.command == "metadata-notices":
                require(args.archive.suffix.lower() == ".mrpack", "metadata-only notices require a .mrpack")
            write_notices(args.archive, ROOT)
            if args.command == "metadata-notices":
                import validate_mrpack
                index, contents = validate_mrpack.read_index(args.archive)
                minecraft = load(ROOT / "pack.toml")["versions"]["minecraft"]
                errors, _, _ = validate_mrpack.validate_index(index, contents, minecraft, "fabric", ROOT)
                require(not errors, "invalid metadata-only archive: " + "; ".join(errors))
        else:
            require(args.channel is not None, "explicit distribution channel is required")
            if args.command == "check":
                clearance(ROOT, args.channel)
            else:
                require(args.archive is not None, "archive is required")
                add_notices(args.archive, ROOT, args.channel)
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        print(f"ERROR: distribution: {exc}")
        return 1
    print("PASS: distribution " + args.command + " (not platform moderation or runtime acceptance)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
