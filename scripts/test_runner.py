"""Run Peach's unittest suite by a documented product scope."""
from __future__ import annotations

import argparse
import fnmatch
import importlib
import re
import subprocess
import sys
import time
import tomllib
import unittest
from collections.abc import Iterable
from contextlib import nullcontext
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"

if not __package__:
    sys.path.insert(0, str(ROOT))
    __package__ = "scripts"
from . import test_evidence

COMMON_PATTERNS = ("test_context_budget.py", "test_test_collection.py")
SCOPES: dict[str, tuple[str, ...]] = {
    "checks": ("test_copy_final_state.py", "test_dependency_policy.py", "test_repo_hygiene.py", "test_test_planning.py"),
    "follow": ("test_follow*.py", "test_http.py", "test_migrations.py"),
    "catalog": ("test_ad_judgement.py", "test_composite_name_split.py", "test_media_libraries.py",
                "test_duplicate_identity_merge.py",
                "test_entity_merge.py", "test_fastapi_api.py", "test_migrations.py",
                "test_review_mirror.py", "test_rm_web.py",
                "test_entity_link_install.py", "test_web_links.py",
                "test_link_marks.py", "test_site_icons.py", "test_site_logos.py",
                "test_avatar_face.py",
                "test_brand_marks.py", "test_studio_icon_variants.py",
                "test_review_csv.py", "test_related.py",
                "test_search_suggest.py",
                "test_jav_code_domain.py",
                "test_taste_history.py", "test_web_ui.py", "test_web_js.py",
                "test_web_perf.py", "test_web_resource_sync.py",
                "test_web_review.py", "test_web_settings.py"),
    "media": ("test_runtime_consistency.py", "test_endcard.py", "test_fastapi_api.py", "test_jobs.py",
              "test_interaction.py", "test_media.py", "test_previews.py",
              "test_providers.py", "test_segments.py", "test_streaming.py",
              "test_transcodes.py"),
    "sync": ("test_sync*.py", "test_platform.py", "test_mount.py", "test_tray.py", "test_log_retention.py",
             "test_mdns.py", "test_netwatch.py", "test_certs.py",
             "test_review_mirror.py"),
    "metadata": ("test_scraping_access.py", "test_metadata*.py", "test_genre_taxonomy.py", "test_fc2*.py",
                 "test_babepedia_match.py",
                 "test_jav*.py", "test_code_creators.py", "test_logo_provider.py",
                 "test_avatar_provider.py", "test_avatar_face.py",
                 "test_face_detect.py", "test_performer*.py",
                 "test_avatar_watermark.py",
                 "test_social_avatar_harvest.py",
                 "test_series_localization.py",
                 "test_duplicate_identity_merge.py", "test_entity_merge.py",
                 "test_migrations.py",
                 "test_entity_link_install.py", "test_studio_site_harvest.py",
                 "test_performer_link_harvest.py", "test_directory_link_harvest.py",
                 "test_minnano_av.py", "test_agency_roster_harvest.py",
                 "test_performer_agency_resync.py",
                 "test_studio_name_localization.py", "test_studio_icon_variants.py",
                 "test_mgstage_maker_harvest.py", "test_studio_name_variant_merge.py",
                 "test_javdb_cn_names.py",
                 "test_link_rediscovery.py", "test_link_label_owner.py",
                 "test_resource_identification.py",
                 "test_agency_entity.py"),
    "tooling": ("test_scripts.py", "test_trash_junk.py", "test_auth.py", "test_access.py", "test_cli.py", "test_script_policy.py",
                "test_scan.py", "test_onboarding.py", "test_configuration_sources.py", "test_folder_picker.py", "test_ledger_backups.py",
                "test_agent_worktree.py", "test_test_evidence.py", "test_dependency_policy.py",
                "test_version_bump.py", "test_changelog.py", "test_release_due.py",
                "test_restart_windows_tray.py", "test_deploy_windows_tray.py",
                "test_buildinfo.py", "test_versioning.py",
                "test_windows_update.py", "test_release_updates.py", "test_automatic_updates.py", "test_standalone_update.py", "test_certs.py", "test_config.py",
                "test_fsutil.py", "test_desktop_settings.py",
                "test_job_status.py", "test_jobs.py", "test_reference_updates.py",
                "test_repo_hygiene.py",
                "test_review_csv.py", "test_jav_code_domain.py",
                "test_subprocess_encoding.py", "test_module_layering.py",
                "test_copy_final_state.py"),
    # 前端 island 层（ADR-0022）。产物与源码的断言不需要 Node；vitest 那部分在没有
    # npm 时自己跳过，所以这个域在任何机器上都能跑，`full` 也就自动包含它。
    # `test_web_perf.py` 两个域都登记：压缩与 ETag 是 API 交付（catalog），
    # 播放器按需加载的断言读 `web/app.js`（web），改任一侧都该被本域拦住。
    # `test_copy_final_state.py` 两个域都登记：它扫全树，而界面字串是它最常拦到的
    # 一面，改 `web/` 的人必须在本域就撞上它。
    # 后面七个文件的主体不在这一层，但各有一段断言读 `web/` 或 `frontend/` 的源码，
    # 所以本域也要登记它们：改了 `web/app.js` 却漏跑读它的测试，`test_test_planning.py`
    # 的域映射门槛会在本地就红。
    "web": ("test_frontend_build.py", "test_web_ui.py", "test_web_js.py",
            "test_web_perf.py", "test_copy_final_state.py",
            "test_agency_entity.py", "test_dependency_policy.py", "test_desktop_settings.py",
            "test_fastapi_api.py", "test_follow_assets.py", "test_follow_web.py",
            "test_metadata_library.py", "test_studio_icon_variants.py", "test_web_settings.py"),
    "core": ("test_access.py", "test_auth.py", "test_config.py", "test_migrations.py",
             "test_platform.py", "test_mount.py", "test_tray.py", "test_certs.py",
             "test_folder_picker.py", "test_fsutil.py", "test_runtime_consistency.py",
             "test_subprocess_encoding.py", "test_windows_update.py", "test_buildinfo.py"),
    "packaging": ("test_dependency_policy.py", "test_buildinfo.py", "test_onboarding.py",
                  "test_cli.py", "test_versioning.py", "test_frontend_build.py"),
}

SCOPE_TEST_IDS: dict[str, tuple[str, ...]] = {
    "follow": (
        "test_rm_web.WebDataTests.test_contract_handler_registries_are_complete_and_unknown_routes_fail",
        "test_rm_web.WebDataTests.test_read_only_post_routes_are_declared_and_all_exist",
        "test_scripts.OperationalScriptTests.test_test_entrypoint_enforces_worktree_source_and_unittest",
    ),
}

# `auto` 域按改动文件选域：每个文件按下面这张「路径前缀 → 域」表取第一个命中的前缀，
# 多个文件取并集。表里没有的 `tests/test_*.py` 直接按文件名归域，`src/peach/` 下的
# 其余模块按「模块名 ↔ 测试文件名」推断（`media.py` → `test_media.py` → media）。
# 仓库根的 Markdown 归 tooling：入口文件、README 与待办的门槛都在那个域里。
AUTO_SCOPE_PREFIXES: tuple[tuple[str, str], ...] = (
    ("src/peach/media.py", "media"),
    ("src/peach/desktop_startup.py", "tooling"),
    ("src/peach/desktop_uninstall.py", "tooling"),
    ("src/peach/peach_proxy.py", "tooling"),
    ("scripts/localize_performer_names.py", "metadata"),
    ("scripts/localize_series_names.py", "metadata"),
    ("src/peach/follow", "follow"),
    ("src/peach/fanbox.py", "follow"),
    ("src/peach/web_follow.py", "follow"),
    ("src/peach/sync", "sync"),
    ("src/peach/platform.py", "sync"),
    ("src/peach/mount.py", "sync"),
    ("src/peach/tray.py", "sync"),
    ("src/peach/mdns.py", "sync"),
    ("src/peach/netwatch.py", "sync"),
    ("src/peach/certs.py", "sync"),
    ("src/peach/web_", "catalog"),
    ("src/peach/routes_", "catalog"),
    ("web/", "web"),
    ("frontend/", "web"),
    ("scripts/", "tooling"),
    ("pyproject.toml", "tooling"),
    (".github/", "tooling"),
    ("docs/", "tooling"),
    (".claude/", "tooling"),
)

# AGENTS.md 规定必须跑 `full` 的面：迁移、共享测试设施、依赖清单。命中任一个就不再选域。
FULL_ONLY_PREFIXES: tuple[str, ...] = (
    "pyproject.toml",
    "scripts/test_runner.py", "scripts/test_evidence.py", "scripts/test.ps1", "scripts/test.sh",
    "scripts/ci_plan.py", "uv.lock",
    "migrations/",
    "tests/support/",
    "package.json",
    "package-lock.json",
    "frontend/package.json",
    "frontend/package-lock.json",
)


def selected_files(scope: str) -> tuple[Path, ...]:
    if scope == "full":
        return tuple(sorted(TESTS.glob("test_*.py")))
    found: set[Path] = set()
    for pattern in (*COMMON_PATTERNS, *SCOPES[scope]):
        found.update(TESTS.glob(pattern))
    return tuple(sorted(found))


def scopes_of_test_file(name: str) -> tuple[str, ...]:
    """一个 `tests/test_*.py` 文件名登记在哪些域里；公共门槛文件归 tooling。"""
    scopes = tuple(scope for scope, patterns in SCOPES.items() if scope not in {"core", "packaging"}
                   if any(fnmatch.fnmatch(name, pattern) for pattern in patterns))
    if not scopes and any(fnmatch.fnmatch(name, pattern) for pattern in COMMON_PATTERNS):
        return ("tooling",)
    return scopes


def scopes_of_module(stem: str) -> tuple[str, ...]:
    """`src/peach/<stem>.py` 按测试文件名推断域：`test_<stem>.py` 或 `test_<stem>_*.py`。"""
    exact, prefix = f"test_{stem}.py", f"test_{stem}_"
    return tuple(scope for scope, patterns in SCOPES.items() if scope not in {"core", "packaging"}
                 if any(fnmatch.fnmatch(exact, pattern) or pattern.startswith(prefix)
                        for pattern in patterns))


#: `<某个 Path> / "a" / "b/c.js"` 这种拼接。要求左边有个 `/`，是为了把「路径当字符串
#: 参数传进去」的写法排除掉：`scopes_for_changes(["web/app.js"])` 喂的是假清单，
#: 不读真文件，不该因为字面量长得像路径就被算成读了它。
_PATH_CHAIN = re.compile(r"""/\s*((?:["'][^"'\n]+["']\s*/\s*)*["'][^"'\n]+["'])""")
_SEGMENT = re.compile(r"""["']([^"'\n]+)["']""")
#: 测试文件顶上的 `FRONTEND = ROOT / "frontend"` 这类别名，用来还原下面链式拼接的前缀。
_ROOT_ALIAS = re.compile(r"""^\w+\s*=\s*\w+(?:\[\d+\])?\s*/\s*["']([\w./-]+)["']\s*$""", re.M)


def repository_paths_read_by(source: str) -> tuple[str, ...]:
    """一段测试源码实际读到的仓库文件，仓库相对路径。

    只认拼在某个 Path 后面、且在仓库里真的存在的那一档。判据是「文件存在」而不是
    「长得像路径」：不存在的字面量是别的东西，存在的才是这个测试真正依赖的输入。
    """
    prefixes = {"", *(alias.strip("/") for alias in _ROOT_ALIAS.findall(source))}
    found: set[str] = set()
    for chain in _PATH_CHAIN.findall(source):
        joined = "/".join(segment.strip("/") for segment in _SEGMENT.findall(chain))
        for prefix in prefixes:
            candidate = f"{prefix}/{joined}".strip("/")
            if (ROOT / candidate).is_file():
                found.add(candidate)
    return tuple(sorted(found))


def dependency_inputs(source: str) -> dict:
    """只忽略不改变依赖图的 uv 工具版本和项目展示字段。"""
    data = tomllib.loads(source)
    project = data.get("project", {})
    uv = dict(data.get("tool", {}).get("uv", {}))
    uv.pop("required-version", None)
    return {"build": data.get("build-system"), "requires-python": project.get("requires-python"),
            "dependencies": project.get("dependencies"), "extras": project.get("optional-dependencies"),
            "groups": data.get("dependency-groups"), "uv": uv}


def changed_contents(root: Path, base: str, paths: Iterable[str]) -> dict:
    result = {}
    if "pyproject.toml" in paths:
        try:
            result["pyproject.toml"] = (test_evidence.git(root, "show", f"{base}:pyproject.toml"),
                                        (root / "pyproject.toml").read_text(encoding="utf-8"))
        except (OSError, subprocess.CalledProcessError):
            pass
    return result


def scopes_for_changes(paths: Iterable[str], *, contents: dict | None = None) -> tuple[tuple[str, ...], str]:
    """纯函数：改动文件清单 → (要跑的域, 一行说明)。

    退化为 `full` 的条件只有两个：某个文件映射不到任何域，或改动触及必须 full 的面。
    """
    picked: dict[str, list[str]] = {}
    full_reasons: list[str] = []
    for raw in paths:
        path = raw.replace("\\", "/").strip("/")
        if not path:
            continue
        name = path.rsplit("/", 1)[-1]
        if path == "pyproject.toml" and contents and path in contents:
            try:
                before, after = contents[path]
                if dependency_inputs(before) == dependency_inputs(after):
                    picked.setdefault("packaging", []).append(path)
                    continue
            except (ValueError, TypeError):
                pass
        if path.startswith(("scripts/build_", "scripts/release_", ".github/workflows/")):
            picked.setdefault("packaging", []).append(path)
            picked.setdefault("tooling", []).append(path)
            continue
        if name == "conftest.py" or any(path.startswith(p) for p in FULL_ONLY_PREFIXES):
            full_reasons.append(f"{path} 属于必须 full 的面")
            continue
        scopes: tuple[str, ...] = ()
        if path.startswith("tests/test_") and path.endswith(".py"):
            scopes = scopes_of_test_file(name)
        elif path.endswith(".md"):
            scopes = ("checks",)
        elif path == "src/peach/routes_pages.py":
            scopes = ("catalog", "tooling", "web")
        else:
            for prefix, scope in AUTO_SCOPE_PREFIXES:
                if path.startswith(prefix):
                    scopes = (scope,)
                    break
            if not scopes and path.startswith("src/peach/") and path.endswith(".py"):
                scopes = scopes_of_module(name.removesuffix(".py"))
        if not scopes:
            full_reasons.append(f"{path} 映射不到任何域")
            continue
        for scope in scopes:
            picked.setdefault(scope, []).append(path)
    if full_reasons:
        return ("full",), "Peach auto scope: full <- " + "; ".join(full_reasons)
    if not picked:
        return ("checks",), "Peach auto scope: checks <- 没有改动文件，检查公共门槛"
    ordered = tuple(scope for scope in SCOPES if scope in picked)
    detail = "; ".join(f"{scope}: {', '.join(picked[scope])}" for scope in ordered)
    return ordered, f"Peach auto scope: {', '.join(ordered)} <- {detail}"


def changed_files(root: Path = ROOT, base: str = "master") -> list[str]:
    """分支相对 `base` 的提交、工作区已改动的文件和未跟踪文件，三者并集。"""
    commands = (
        ("git", "diff", "--name-only", "-z", f"{base}...HEAD"),
        ("git", "diff", "--name-only", "-z", "HEAD"),
        ("git", "ls-files", "--others", "--exclude-standard", "-z"),
    )
    found: set[str] = set()
    for command in commands:
        command = ("git", "-c", f"safe.directory={root.as_posix()}", *command[1:])
        output = subprocess.run(command, cwd=root, capture_output=True, text=True,
                                encoding="utf-8", check=True).stdout
        found.update(part for part in output.split("\0") if part)
    return sorted(found)


def resolve_auto_scope() -> tuple[tuple[str, ...], str]:
    try:
        paths = changed_files()
    except (OSError, subprocess.CalledProcessError) as error:
        return ("full",), f"Peach auto scope: full <- git 不可用（{error}）"
    return scopes_for_changes(paths, contents=changed_contents(ROOT, "master", paths))


def build_suite(*scopes: str, shard_index: int = 0, shard_count: int = 1) -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    files = sorted({path for scope in scopes for path in selected_files(scope)})
    assigned = set(files[shard_index::shard_count])
    sys.path[:0] = [str(ROOT), str(TESTS)]
    try:
        for path in sorted(assigned):
            suite.addTests(loader.loadTestsFromModule(importlib.import_module(path.stem)))
        for scope in scopes:
            for test_id in SCOPE_TEST_IDS.get(scope, ()):
                # 补充用例以模块名稳定分配；每个 shard 只运行自己的一份。
                module = TESTS / (test_id.split(".", 1)[0] + ".py")
                if module not in files and sum(test_id.split(".", 1)[0].encode()) % shard_count == shard_index:
                    suite.addTests(loader.loadTestsFromName(test_id))
    finally:
        del sys.path[:2]
    return suite


class TimedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timings = []

    def startTest(self, test):
        self.started = time.monotonic()
        super().startTest(test)

    def stopTest(self, test):
        self.timings.append((round(time.monotonic() - self.started, 3), test.id()))
        super().stopTest(test)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=("full", "auto", *SCOPES), default="auto")
    parser.add_argument("--fresh", action="store_true", help="实际重跑，不复用本机记录")
    parser.add_argument("--base", default="master", help="CI 选测的已验证 Git 基线")
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--list-scopes", action="store_true")
    args = parser.parse_args(argv)
    if not 1 <= args.shard_count <= 4 or not 0 <= args.shard_index < args.shard_count:
        parser.error("分片总数为 1～4，编号从 0 开始且小于总数")
    if args.list_scopes:
        print("\n".join(("full", "auto", *SCOPES)))
        return 0
    scopes: tuple[str, ...] = (args.scope,)
    if args.scope == "auto":
        if args.base == "master":
            scopes, explanation = resolve_auto_scope()
        else:
            paths = changed_files(ROOT, args.base)
            scopes, explanation = scopes_for_changes(paths, contents=changed_contents(ROOT, args.base, paths))
        print(explanation, flush=True)
    files = {path for scope in scopes for path in selected_files(scope)}
    print(f"Peach test scope: {' '.join(scopes)} ({len(files)} files)", flush=True)
    if args.shard_count > 1:
        # CI 的每片独立 runner；局部分片绝不签发本机全量证明。
        result = unittest.TextTestRunner(verbosity=2, resultclass=TimedResult).run(
            build_suite(*scopes, shard_index=args.shard_index, shard_count=args.shard_count))
        return 0 if result.wasSuccessful() and result.testsRun > 0 else 1
    context = test_evidence.inputs(ROOT)
    state = context["state"]
    try:
        with test_evidence.run_lock(ROOT, state, scope=" ".join(scopes), root=str(ROOT)):
            if not args.fresh and args.scope != "full" and test_evidence.covers(
                    test_evidence.read(ROOT, state), scopes):
                print("复用本机测试记录：代码、依赖环境和范围匹配（24 小时内）。", flush=True)
                return 0
            previous = test_evidence.read(ROOT, state)
            baseline = None
            if args.scope == "auto" and not args.fresh and not previous:
                choices = []
                for record, delta, version_only in test_evidence.baselines(ROOT, context):
                    needed, _ = scopes_for_changes(delta)
                    if version_only and "full" not in needed:
                        needed = tuple(dict.fromkeys((*needed, "tooling")))
                    if "full" not in needed:
                        weight = len({p for scope in needed for p in selected_files(scope)})
                        if weight <= len(files):
                            choices.append((weight, record, needed))
                if choices:
                    _, baseline, scopes = min(choices, key=lambda item: item[0])
                    print(f"复用全量基线 {baseline['state'][:12]}；新增差异补测：{' '.join(scopes)}", flush=True)
            folder = test_evidence.evidence_dir(ROOT)
            full_lock = test_evidence.held(folder / "full-suite.lock",
                                           scope=" ".join(scopes), root=str(ROOT)) \
                if "full" in scopes else nullcontext()
            with full_lock:
                (folder / f"{state}.json").unlink(missing_ok=True)
                started = time.monotonic()
                result = unittest.TextTestRunner(verbosity=2, resultclass=TimedResult).run(build_suite(*scopes))
            stable = state == test_evidence.key(ROOT)
            success = result.wasSuccessful() and stable and result.testsRun > 0
            slowest = sorted(result.timings, reverse=True)[:20]
            test_evidence.write(ROOT, state, scopes, success=success, previous=previous,
                                context=context, baseline=baseline,
                                elapsed=time.monotonic() - started, slowest=slowest, count=result.testsRun)
            for seconds, name in slowest[:5]:
                print(f"慢测试 {seconds:.3f}s：{name}", flush=True)
            if not stable:
                print("验证期间代码或依赖环境改变，本次记录无效。", flush=True)
            return 0 if success else 1
    except test_evidence.Timeout as error:
        lock = Path(error.lock_file)
        what = "本仓库全量测试" if lock.name == "full-suite.lock" else "相同状态的验证"
        print(f"{what}正在运行（{test_evidence.describe_holder(lock)}），请等待该次结果。",
              flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
