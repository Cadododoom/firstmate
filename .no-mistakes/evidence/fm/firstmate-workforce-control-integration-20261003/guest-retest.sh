#!/usr/bin/env bash
set -u
export PATH=/nix/store/myzwgd3ylpl3d8zrl7kl3l97i7zl8mw6-perl-5.42.0/bin:/nix/store/9r02ykx9y35lf4gk6gc30gnag1y8ncp7-python3-3.13.15/bin:/nix/store/m908x0pw1400073whn4bsvsswp5rj9yg-herdr-0.9.1/bin:$PATH
export NIX_CONFIG="max-jobs = 1
cores = 2"
cd /tmp/workforce-source
bin/fm-test-run.sh tests/fm-inbox.test.sh --jobs 1 --json /mnt/exchange/guest-inbox-retest.json 2>&1 | tee /mnt/exchange/guest-inbox-retest.log
rc=${PIPESTATUS[0]}
printf '{"inbox_retest_exit":%s}\n' "$rc" > /mnt/exchange/guest-inbox-retest-result.json
