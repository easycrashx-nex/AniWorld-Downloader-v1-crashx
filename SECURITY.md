# Security Policy

## Supported Build Scope

This repository contains a customized AniWorld Downloader build with a heavily extended Web UI, multi-user support, Auto-Sync, diagnostics, provider health, and server-oriented deployment options.

Security reports should focus on issues that affect:

- authentication and authorization
- user/session handling
- Web UI routes and API endpoints
- database handling
- file and path handling
- Docker or server deployment defaults
- remote exposure / reverse proxy usage

## Reporting a Vulnerability

Please do not open public issues for security-sensitive problems.

Instead, report them privately to the repository owner / maintainer first.

A useful report should include:

- affected version or commit
- affected deployment type
  - local source install
  - Docker / Docker Compose
  - Linux systemd / server install
- exact reproduction steps
- impact
- proof of concept if available
- logs, screenshots, or request samples if relevant

## Response Expectations

When a valid security issue is confirmed, the maintainer should aim to:

1. acknowledge the report
2. reproduce and scope the issue
3. prepare a fix or mitigation
4. publish the fix in a normal code update

Timing depends on severity, available maintainers, and whether the issue is actively exploitable.

## What Counts as Sensitive

Examples of sensitive issues:

- auth bypass
- privilege escalation
- remote code execution
- path traversal
- insecure file deletion or overwrite
- exposed secrets or tokens
- unsafe defaults for public server deployments
- cross-user data leaks

## Safe Disclosure Rules

Please avoid:

- publishing proof-of-concept exploits before a fix exists
- posting active attack payloads in public issues
- disclosing secrets, session values, or personal user data

If you are unsure whether something is security-sensitive, treat it as private first.

## Hardening Notes for Operators

For server deployments, the current recommended baseline is:

- enable Web Auth
- keep `.aniworld` persistent and private
- avoid exposing the app publicly without authentication
- prefer a reverse proxy if the service is reachable outside a trusted LAN
- back up both downloads and `.aniworld`
- monitor free disk space and runtime diagnostics

## Third-Party Targets

This build interacts with external content/provider sites. Reports about those third-party services themselves are out of scope for this repository unless the issue is caused by code in this repository.
