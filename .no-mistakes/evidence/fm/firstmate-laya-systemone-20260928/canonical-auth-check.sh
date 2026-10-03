set -eu
export FM_HOME=/tmp/laya-home PATH=/mnt/.validation-laya/guest-bin:$PATH DISPATCH_SYSTEMONE_PROVIDER=laya LAYA_SYSTEMONE_BASE_URL=http://127.0.0.1:8000 TYPESAFE_API_KEY=''
for mode in missing wrong; do
  echo "Canonical required auth, $mode key:"
  if [ "$mode" = missing ]; then export LAYA_API_KEY=''; else export LAYA_API_KEY=lab-wrong-key; fi
  output=$(/mnt/bin/fm-dispatch-resolve.sh /mnt/.validation-laya/brief.md --project isolated-pager)
  echo "$output"
  echo "$output" | grep -q 'status: error'
  echo "$output" | grep -q 'http 401'
done
export LAYA_API_KEY=lab-auth-required
bash /mnt/.validation-laya/canonical-check.sh
