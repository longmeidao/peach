#!/usr/bin/env bash
# macOS/Linux 的唯一测试入口，与 Windows 的 scripts/test.ps1 同一套契约：
# 从 Git common directory 定位主目录的 .venv，强制加载当前 worktree 的 src，
# 并核对 peach.__file__ 确实来自这个 worktree。worktree 不复制 .venv。
set -euo pipefail

SCOPE="${1:-auto}"
case "$SCOPE" in
    full|auto|follow|catalog|media|sync|metadata|tooling|web|checks) ;;
    *)
        echo "未知测试域：$SCOPE（可选 full、auto、follow、catalog、media、sync、metadata、tooling、web）" >&2
        exit 2
        ;;
esac
EXTRA=()
if [[ "${2:-}" = "--fresh" ]]; then
    EXTRA+=(--fresh)
elif [[ $# -gt 1 ]]; then
    echo '第二个参数只接受 --fresh' >&2
    exit 2
fi

WORKTREE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

GIT_COMMON_RAW="$(git -C "$WORKTREE_ROOT" rev-parse --git-common-dir)"
if [[ -z "$GIT_COMMON_RAW" ]]; then
    echo "无法定位 Peach 主工作树。" >&2
    exit 1
fi
if [[ "$GIT_COMMON_RAW" = /* ]]; then
    GIT_COMMON="$GIT_COMMON_RAW"
else
    GIT_COMMON="$WORKTREE_ROOT/$GIT_COMMON_RAW"
fi
GIT_COMMON="$(cd "$GIT_COMMON" && pwd)"
MAIN_ROOT="$(dirname "$GIT_COMMON")"

PYTHON="$MAIN_ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
    echo "Peach 主项目 venv 不存在：$PYTHON" >&2
    exit 1
fi

SOURCE_ROOT="$WORKTREE_ROOT/src"
export PYTHONPATH="$SOURCE_ROOT"
export PYTHONIOENCODING=utf-8

cd "$WORKTREE_ROOT"
LOADED_MODULE="$("$PYTHON" -c 'import peach; print(peach.__file__)')"
if [[ "$LOADED_MODULE" != "$SOURCE_ROOT/"* ]]; then
    echo "测试加载了错误源码：$LOADED_MODULE；预期位于 $SOURCE_ROOT" >&2
    exit 1
fi

echo "Peach source: $LOADED_MODULE"
if [[ $# -eq 0 && "$WORKTREE_ROOT" = "$(dirname "$GIT_COMMON")" ]]; then
    SCOPE=full
fi
exec "$PYTHON" scripts/test_runner.py --scope "$SCOPE" "${EXTRA[@]}"
