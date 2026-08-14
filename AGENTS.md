# Peach agent contract

This file is the single cross-agent entry point for Codex and Claude.

Before changing the project, read these files in order:

1. `README.md`
2. `docs/STATUS.md`
3. `docs/ARCHITECTURE.md`
4. `docs/HANDOFF.md`
5. Relevant ADRs under `docs/adr/`

Working rules:

- `R:\peach-app` is code and documentation. `R:\peach-data`, `R:\media`, `A:\` and `B:\` are runtime data or mounted media and must never be copied into Git.
- `R:\peach-data\database\ledger.db` is the truth store. Tests use temporary databases only. A real migration requires a SQLite backup and before/after count checks.
- The project is an early personal project: aggressively remove obsolete code and compatibility layers when the replacement is tested. Do not preserve dead interfaces merely for history; Git is the archive.
- Preserve real media, ledger rows, behavior history, credentials, network/firewall state, and unrelated long-running jobs.
- Inspect `git status` and the active listeners/processes before work. Never claim candidate code is production until the service has actually been switched and checked.
- Keep the architecture a FastAPI modular monolith with a separate web surface. Do not introduce microservices, PostgreSQL, a React rewrite, or a full multi-account system without a new ADR.
- Ledger remains the core truth. Stash is a replaceable Media Engine adapter. AI results are candidates with provenance/confidence, not direct truth-field mutations.
- Do not create dated handoff documents. Update `docs/STATUS.md` for current runtime/next work and `docs/HANDOFF.md` for durable operating knowledge as part of the same change.
- Run the verification commands in `README.md` before committing relevant changes.
