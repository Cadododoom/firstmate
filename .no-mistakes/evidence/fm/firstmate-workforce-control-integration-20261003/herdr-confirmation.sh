#!/usr/bin/env bash
set -uo pipefail
HERDR_LAB_HELPER='/home/cadodolap_works/Projects/firstmate/bin/fm-herdr-lab.sh'
LAB_HOME_HELPER='/home/cadodolap_works/Projects/firstmate/bin/fm-lab-home.sh'
ROOT='/home/cadodolap_works/.no-mistakes/worktrees/e57655a07a4e/01M41CD8B6K3EEA20MPMVZMWPB'
EVIDENCE='/home/cadodolap_works/.no-mistakes/evidence/01M41CD8B6K3EEA20MPMVZMWPB'
HERDR_LAB_SESSION=$("$HERDR_LAB_HELPER" name firstmate-workforce-control-integration-20261003) || exit
export FM_HOME="$ROOT/.herdr-test-$HERDR_LAB_SESSION"
export FM_HERDR_LAB_STATE_DIR="$ROOT/.herdr-tripwire-$HERDR_LAB_SESSION"
export HERDR_LAB_HELPER HERDR_LAB_SESSION
LAB_TMUX_DIR=''
cleanup() {
  local rc=$?
  trap - EXIT
  if [ -n "$LAB_TMUX_DIR" ]; then
    TMUX_TMPDIR="$LAB_TMUX_DIR" tmux kill-server 2>/dev/null || true
  fi
  "$LAB_HOME_HELPER" teardown "$FM_HOME"
  printf 'lab-home teardown exit=%s\n' "$?"
  "$HERDR_LAB_HELPER" teardown "$HERDR_LAB_SESSION"
  printf 'herdr teardown exit=%s\n' "$?"
  if [ -f "$FM_HOME/.fm-lab-home" ]; then rm -rf "$FM_HOME"; fi
  if [ -d "$FM_HERDR_LAB_STATE_DIR" ]; then
    rmdir "$FM_HERDR_LAB_STATE_DIR" 2>/dev/null || true
  fi
  printf 'FINAL attempt exit=%s; lab=%s; no tmux server started\n' "$rc" "$HERDR_LAB_SESSION"
  exit "$rc"
}
trap cleanup EXIT
printf 'UTC='; date -u +%FT%TZ
printf 'HEAD='; git -C "$ROOT" rev-parse HEAD
printf 'session=%s\nFM_HOME=%s\nhelper_records=%s\nHOME=%s\nXDG_RUNTIME_DIR=%s\n' "$HERDR_LAB_SESSION" "$FM_HOME" "$FM_HERDR_LAB_STATE_DIR" "$HOME" "${XDG_RUNTIME_DIR:-<unset>}"
command -v herdr jq
"$LAB_HOME_HELPER" create "$FM_HOME" || exit
printf 'COMMAND: %s provision %s\n' "$HERDR_LAB_HELPER" "$HERDR_LAB_SESSION"
"$HERDR_LAB_HELPER" provision "$HERDR_LAB_SESSION"
provision_rc=$?
printf 'provision exit=%s\n' "$provision_rc"
if [ "$provision_rc" -ne 0 ]; then
  for args in 'version' 'help' 'session list --json' 'session --help'; do
    printf '\nCOMMAND: %s run %s %s\n' "$HERDR_LAB_HELPER" "$HERDR_LAB_SESSION" "$args"
    read -r -a fields <<< "$args"
    "$HERDR_LAB_HELPER" run "$HERDR_LAB_SESSION" "${fields[@]}"
    printf 'command exit=%s\n' "$?"
  done
  exit "$provision_rc"
fi
printf 'PROVISION SUCCEEDED: retain tripwire\n'
cp "$FM_HERDR_LAB_STATE_DIR/$HERDR_LAB_SESSION.fleet-state.json" "$EVIDENCE/herdr-default-before-confirmation.json"
"$HERDR_LAB_HELPER" run "$HERDR_LAB_SESSION" pane list > "$EVIDENCE/herdr-owned-before-confirmation.json" || exit
python3 "$EVIDENCE/herdr-typed-scenario.py" || exit
"$HERDR_LAB_HELPER" run "$HERDR_LAB_SESSION" session list --json > "$EVIDENCE/herdr-sessions-after-confirmation.json" || exit
jq -c '[.sessions[]? | select(.default == true)] | .[0] | {name, default, running, socket_path}' "$EVIDENCE/herdr-sessions-after-confirmation.json" > "$EVIDENCE/herdr-default-after-confirmation.json"
cmp "$EVIDENCE/herdr-default-before-confirmation.json" "$EVIDENCE/herdr-default-after-confirmation.json" || exit
printf 'PASS: default fleet tripwire unchanged before/after typed requests\n' 
