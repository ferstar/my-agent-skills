---
name: artifact-verify
description: Verify an existing build artifact itself: metadata, complete download, checksum or size, archive integrity, unpacked contents, and source or lock provenance. Use when artifact contents or completeness must be proven; do not use to trigger builds, releases, deploys, or health checks.
argument-hint: "[artifact path or URL]"
---

# Artifact Verify

Treat workflow status and artifact presence as insufficient evidence. Prove the artifact that a consumer would receive.

## Inputs

Record:

- artifact path or authenticated download URL
- expected filename, size, checksum, platform, and format when known
- exact source SHA or build identifier
- expected metadata, manifest, lock file, binaries, resources, or package entries

## Verification

1. Read artifact metadata and bind it to the exact run and source SHA.
2. Download the complete artifact to a temporary path; do not inspect a partial response or UI preview.
3. Record byte size and a cryptographic checksum when no trusted checksum is supplied.
4. Test archive or installer integrity with the format's native listing/test command before extraction.
5. Extract into a new temporary directory and inspect the required paths and manifests.
6. Verify embedded version, source, dependency lock, runtime lock, or provenance fields against expectations.
7. Report exact commands, observed values, missing entries, and whether the artifact is fit for its intended consumer.

Use format-appropriate tools such as `unzip -t`, `tar -tf`, `7z t`, platform package inspectors, `file`, and checksum utilities. Never execute an untrusted binary merely to inspect it.

## Boundary

- Use `release-deploy-preflight` to resolve or trigger the workflow that produces an artifact.
- Use `ci-first-failure` if that workflow is red.
- This skill is read-only with respect to release systems and deployed environments.
