#!/usr/bin/env bash
set -eu
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PYTHONDONTWRITEBYTECODE=1 python3 - "$ROOT" <<'PY'
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

root = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("runner", root / "bin/fm-openshell-codex.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

with tempfile.TemporaryDirectory(dir=root / "tests", prefix="openshell-test-") as tmp:
    base = Path(tmp)
    fake = base / "openshell"
    log = base / "commands.jsonl"
    identity = base / "identity"
    identity.write_text("workspace-original")
    fake.write_text('''#!/usr/bin/env python3
import json, os, pathlib, sys
args = sys.argv[1:]
with open(os.environ["COMMAND_LOG"], "a") as f:
    f.write(json.dumps(args) + "\\n")
workspace = args[args.index("--workspace") + 1] if "--workspace" in args else os.environ.get("OPENSHELL_WORKSPACE", "default")
if "workspace" in args and "get" in args:
    print("Workspace:\\n\\n  Name: " + workspace + "\\n  Id: " + pathlib.Path(os.environ["WORKSPACE_ID_FILE"]).read_text())
''')
    fake.chmod(0o755)
    env = dict(os.environ, PATH=str(base) + os.pathsep + os.environ["PATH"],
               COMMAND_LOG=str(log), WORKSPACE_ID_FILE=str(identity), OPENSHELL_WORKSPACE="other")
    ctx = dict(id="task", home=base, state=base, gateway="local", workspace="team",
               workspace_id="workspace-original", journal=base / "journal.json", worktree=base,
               sandbox="task-sandbox", values={})
    def commands():
        return [json.loads(line) for line in log.read_text().splitlines()]
    def refuses(call):
        try:
            call()
        except runner.Refusal:
            return
        raise AssertionError("expected a closed refusal")
    with patch.dict(os.environ, env):
        result = subprocess.run([sys.executable, str(root / "bin/fm-openshell-codex.py"),
                                 "workspace-id", "local", "team"], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "workspace-original"
        for command in [("sandbox", "create"), ("sandbox", "get"), ("sandbox", "delete"),
                        ("sandbox", "stop"), ("sandbox", "start"), ("sandbox", "upload"),
                        ("sandbox", "download"), ("sandbox", "exec"), ("policy", "list")]:
            runner.openshell_run(ctx, *command)
            assert commands()[-1][:4] == ["--gateway", "local", "--workspace", "team"]
        runner.write_journal(ctx, {"phase": "agent-exited"})
        assert runner.read_journal(ctx)["workspace_id"] == "workspace-original"
        refuses(lambda: runner.read_journal(dict(ctx, workspace_id="replacement")))
        refuses(lambda: runner.read_journal(dict(ctx, workspace="other")))
        count = len(commands())
        refuses(lambda: runner.openshell_run(dict(ctx, workspace_id=""), "sandbox", "delete"))
        assert len(commands()) == count
        identity.write_text("workspace-recreated")
        refuses(lambda: runner.delete_sandbox(ctx))
        assert commands()[-1][-3:] == ["workspace", "get", "team"]
        identity.write_text("workspace-original")
        for model, effort, expected_model, expected_effort in [
            ("default", "default", "gpt-6.1-sol", "medium"),
            ("", "", "gpt-6.1-sol", "medium"),
            ("custom-model", "high", "custom-model", "high"),
            ("gpt-5.6-luna", "max", "gpt-5.6-luna", "max")]:
            with patch.object(runner, "sync_channels", lambda ctx: None):
                assert runner.run_codex(ctx, {}, "task brief", model, effort) == 0
            args = commands()[-1]
            codex = args[args.index("--") + 1:]
            assert codex[codex.index("--model") + 1] == expected_model
            assert 'model_reasoning_effort="' + expected_effort + '"' in codex
            assert "--dangerously-bypass-approvals-and-sandbox" in codex
            assert "CODEX_HOME=/tmp/fm-codex-home" in args
        for options, expected in [([], ("gpt-6.1-sol", "medium")),
                                  (["--model", "custom", "--effort", "high"], ("custom", "high"))]:
            with patch.object(sys, "argv", ["runner", "run", "task", "brief", *options]), patch.object(runner, "run_task", return_value=0) as launch:
                assert runner.main() == 0
                assert launch.call_args.args == ("task", "brief", *expected)
        old_journal = json.loads(ctx["journal"].read_text())
        old_journal.pop("workspace_id")
        ctx["journal"].write_text(json.dumps(old_journal))
        refuses(lambda: runner.read_journal(ctx))
        state = base / "state"
        state.mkdir()
        sandbox = "fm-codex-" + hashlib.sha256(os.fsencode(str(base)) + b"\0task").hexdigest()[:24]
        metadata = dict(openshell="codex-v1", harness="codex", backend="herdr", kind="ship",
                        mode="no-mistakes", openshell_providers="codex", openshell_gateway="local",
                        openshell_name=sandbox, worktree=str(base), tasktmp="/tmp/fm-task", branch="task")
        for fields in [{}, {"openshell_workspace": "team"},
                       {"openshell_workspace": "team", "openshell_workspace_id": ""}]:
            (state / "task.meta").write_text("".join(k + "=" + v + "\n" for k, v in {**metadata, **fields}.items()))
            with patch.dict(os.environ, FM_HOME=str(base), FM_STATE_OVERRIDE=str(state)):
                refuses(lambda: runner.load_context("task"))
print("ok - workspace identity binds commands and recovery; Codex defaults preserve overrides")
PY
