#!/usr/bin/env bash
set -u
export PATH=/nix/store/9r02ykx9y35lf4gk6gc30gnag1y8ncp7-python3-3.13.15/bin:/nix/store/m908x0pw1400073whn4bsvsswp5rj9yg-herdr-0.9.1/bin:$PATH
export NIX_BUILD_CORES=2 NIX_MAX_JOBS=1
export NIX_CONFIG="max-jobs = 1
cores = 2"
exec > >(tee /mnt/exchange/guest-integration.log) 2>&1
printf 'NixOS graphical Test: committed head 70da969a01cef42325d881b6d4aa3f37aa35f28c\n'
cat /etc/os-release
nproc; free -m
printf '%s  /mnt/exchange/source.tar\n' de95554145d596a655088bce95d0b46ff4a99bad7b084bbbeb8016852f40f3b4 | sha256sum -c - || exit 1
mkdir -p /tmp/workforce-source
tar xf /mnt/exchange/source.tar -C /tmp/workforce-source
cd /tmp/workforce-source
export FM_HERDR_LAB_STATE_DIR=/tmp/workforce-herdr-lab
session=$(bash bin/fm-herdr-lab.sh name workforce-test)
printf '%s\n' "$session" | tee /mnt/exchange/lab-name.txt
prepared=0
cleanup() {
 if [ "$prepared" = 1 ]; then
  bash bin/fm-herdr-lab.sh teardown "$session"
  echo "Herdr teardown exit: $?"
 fi
}
trap cleanup EXIT
bash bin/fm-herdr-lab.sh prepare "$session"
prepare_exit=$?
echo "Herdr prepare exit: $prepare_exit"
if [ "$prepare_exit" = 0 ]; then
 prepared=1
 cp "$FM_HERDR_LAB_STATE_DIR/$session.fleet-state.json" /mnt/exchange/fleet-tripwire-before.json
 bash bin/fm-herdr-lab.sh provision "$session"
 provision_exit=$?
 echo "Herdr provision exit: $provision_exit"
 if [ "$provision_exit" = 0 ]; then
  bash bin/fm-herdr-lab.sh run "$session" session list --json | tee /mnt/exchange/lab-session.json
  export FM_WORKFORCE_LAB_SESSION="$session"
 fi
fi
bin/fm-test-run.sh tests/fm-workforce.test.sh tests/fm-inbox.test.sh --jobs 1 --json /mnt/exchange/guest-targeted-tests.json
focused=$?
echo "Focused tests exit: $focused"
python3 /mnt/exchange/drive-workforce.py
cli=$?
echo "CLI integration exit: $cli"
printf '{"focused_exit":%s,"cli_exit":%s,"herdr_prepare_exit":%s}\n' "$focused" "$cli" "$prepare_exit" > /mnt/exchange/guest-result.json
echo 'Graphical guest integration completed; see recorded exit codes.'
