"""Run Peach's unittest suite by a documented product scope."""
from __future__ import annotations

import argparse
import importlib
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"

COMMON_PATTERNS = ("test_context_budget.py", "test_test_collection.py")
SCOPES: dict[str, tuple[str, ...]] = {
    "follow": ("test_follow*.py", "test_http.py", "test_migrations.py"),
    "catalog": ("test_ad_judgement.py", "test_duplicate_identity_merge.py",
                "test_entity_merge.py", "test_fastapi_api.py", "test_migrations.py",
                "test_review_mirror.py", "test_rm_ledger.py", "test_rm_web.py",
                "test_entity_link_install.py", "test_web_links.py",
                "test_link_marks.py",
                "test_review_csv.py", "test_related.py",
                "test_taste_history.py", "test_web_ui.py", "test_web_resource_sync.py",
                "test_web_review.py", "test_web_settings.py"),
    "media": ("test_endcard.py", "test_fastapi_api.py", "test_jobs.py",
              "test_interaction.py", "test_media.py", "test_previews.py",
              "test_providers.py", "test_segments.py", "test_streaming.py",
              "test_transcodes.py"),
    "sync": ("test_sync*.py", "test_platform.py", "test_mount.py", "test_tray.py",
             "test_mdns.py", "test_netwatch.py", "test_certs.py",
             "test_review_mirror.py"),
    "metadata": ("test_metadata*.py", "test_fc2*.py", "test_babepedia_match.py",
                 "test_jav*.py", "test_code_creators.py", "test_logo_provider.py",
                 "test_avatar_provider.py", "test_performer*.py",
                 "test_series_localization.py",
                 "test_duplicate_identity_merge.py", "test_entity_merge.py",
                 "test_stash_entity_import.py", "test_migrations.py",
                 "test_entity_link_install.py", "test_studio_site_harvest.py",
                 "test_performer_link_harvest.py",
                 "test_link_rediscovery.py"),
    "tooling": ("test_scripts.py", "test_agent_worktree.py", "test_dependency_policy.py",
                "test_restart_windows_tray.py",
                "test_versioning.py",
                "test_windows_update.py", "test_certs.py", "test_config.py",
                "test_job_status.py", "test_jobs.py", "test_reference_updates.py",
                "test_repo_hygiene.py",
                "test_review_csv.py",
                "test_subprocess_encoding.py", "test_module_layering.py"),
}

SCOPE_TEST_IDS: dict[str, tuple[str, ...]] = {
    "follow": (
        "test_rm_web.WebDataTests.test_contract_handler_registries_are_complete_and_unknown_routes_fail",
        "test_rm_web.WebDataTests.test_read_only_post_routes_are_declared_and_all_exist",
        "test_scripts.OperationalScriptTests.test_test_entrypoint_enforces_worktree_source_and_unittest",
    ),
}


def selected_files(scope: str) -> tuple[Path, ...]:
    if scope == "full":
        return tuple(sorted(TESTS.glob("test_*.py")))
    found: set[Path] = set()
    for pattern in (*COMMON_PATTERNS, *SCOPES[scope]):
        found.update(TESTS.glob(pattern))
    return tuple(sorted(found))


def unclassified_files() -> tuple[Path, ...]:
    classified = set()
    for scope in SCOPES:
        classified.update(selected_files(scope))
    return tuple(sorted(set(TESTS.glob("test_*.py")) - classified))


def build_suite(scope: str) -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    sys.path[:0] = [str(ROOT), str(TESTS)]
    try:
        for path in selected_files(scope):
            suite.addTests(loader.loadTestsFromModule(importlib.import_module(path.stem)))
        for test_id in SCOPE_TEST_IDS.get(scope, ()):
            suite.addTests(loader.loadTestsFromName(test_id))
    finally:
        del sys.path[:2]
    return suite


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=("full", *SCOPES), default="full")
    parser.add_argument("--list-scopes", action="store_true")
    args = parser.parse_args(argv)
    if args.list_scopes:
        print("\n".join(("full", *SCOPES)))
        return 0
    files = selected_files(args.scope)
    print(f"Peach test scope: {args.scope} ({len(files)} files)", flush=True)
    result = unittest.TextTestRunner(verbosity=2).run(build_suite(args.scope))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
