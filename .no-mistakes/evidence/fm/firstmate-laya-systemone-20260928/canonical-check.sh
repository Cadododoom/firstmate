set -eu
export FM_HOME=/tmp/laya-home
mkdir -p "$FM_HOME/config"
export PATH=/mnt/.validation-laya/guest-bin:$PATH
export DISPATCH_SYSTEMONE_PROVIDER=laya LAYA_SYSTEMONE_BASE_URL=http://127.0.0.1:8000 TYPESAFE_API_KEY='' LAYA_API_KEY="${LAYA_API_KEY-}"
cat /mnt/.validation-laya/source-head.txt
printf 'Canonical Laya health:\n'
curl -fsS http://127.0.0.1:8000/health; echo
printf '%s\n' '{"rules":[{"when":"Fix a pager bug with a known root cause","min_confidence":0.01,"use":{"harness":"codex","model":"gpt-6.1-sol","effort":"medium"}}],"default":{"harness":"codex","model":"gpt-6.1-sol","effort":"medium"}}' > "$FM_HOME/config/crew-dispatch.json"
printf '\nCanonical Laya resolver result:\n'
/mnt/bin/fm-dispatch-resolve.sh /mnt/.validation-laya/brief.md --project isolated-pager
