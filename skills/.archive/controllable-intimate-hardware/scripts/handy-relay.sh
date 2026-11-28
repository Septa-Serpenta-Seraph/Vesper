#!/usr/bin/env bash
# handy-relay.sh — Send commands to The Handy via REST API v3
# Velocity range: 0.0 to 1.0 (float)
# Usage:
#   ./handy-relay.sh velocity 0.5
#   ./handy-relay.sh stroke 0.6
#   ./handy-relay.sh start [velocity]
#   ./handy-relay.sh stop
#   ./handy-relay.sh ramp 0.8 [steps] [delay]
#   ./handy-relay.sh status

API_BASE="https://www.handyfeeling.com/api/handy-rest/v3"
ENV_FILES=( "/home/lumi/.hermes/.env" "/home/lumi/.hermes/profiles/vesper/.env" )

# Load credentials
APP_KEY=""
CONN_KEY=""
for f in "${ENV_FILES[@]}"; do
  if [ -f "$f" ]; then
    [ -z "$APP_KEY" ] && APP_KEY=$(grep -oP 'HANDY_APP_KEY=\K\S+' "$f" 2>/dev/null | tr -d "\"'")
    [ -z "$CONN_KEY" ] && CONN_KEY=$(grep -oP 'HANDY_CONN_KEY=\K\S+' "$f" 2>/dev/null | tr -d "\"'")
  fi
done
if [ -z "$APP_KEY" ]; then echo "ERROR: HANDY_APP_KEY not found" >&2; exit 1; fi
if [ -z "$CONN_KEY" ]; then echo "ERROR: HANDY_CONN_KEY not found" >&2; exit 1; fi

issue_token() {
  curl -s "$API_BASE/auth/token/issue" -H "X-Api-Key: $APP_KEY" | \
    python3 -c "import sys,json; print(json.load(sys.stdin)['result']['token'])" 2>/dev/null
}

api() {
  local method="$1" path="$2" body="$3"
  local t=$(issue_token)
  [ -z "$t" ] && echo "ERROR: token issue failed" >&2 && return 1
  curl -s -X "$method" "$API_BASE$path" \
    -H "Authorization: Bearer $t" \
    -H "X-Connection-Key: $CONN_KEY" \
    -H "Content-Type: application/json" \
    ${body:+-d "$body"}
}

CMD="${1:-}"
shift 2>/dev/null || true

case "$CMD" in
  status|info)     api GET "/info" ;;
  connected)       api GET "/connected" ;;
  state)           api GET "/hamp/state" ;;
  velocity)        api PUT "/hamp/velocity" "{\"velocity\": ${1:-0.5}}" ;;
  stroke)          api PUT "/hamp/stroke" "{\"min\": ${2:-0.0}, \"max\": ${1:-1.0}}" ;;
  start)           api PUT "/hamp/start" "{\"velocity\": ${1:-0.3}}" ;;
  stop)            api PUT "/hamp/stop" "{}" ;;
  vibe|vibration)  api PUT "/hvp/state" "{\"state\": ${1:-true}}" ;;
  checkin)
    t=$(issue_token)
    [ -z "$t" ] && echo "ERROR: token issue failed" && exit 1
    conn=$(curl -s "$API_BASE/connected" -H "Authorization: Bearer $t" -H "X-Connection-Key: $CONN_KEY" 2>/dev/null)
    st=$(curl -s "$API_BASE/hamp/state" -H "Authorization: Bearer $t" -H "X-Connection-Key: $CONN_KEY" 2>/dev/null)
    python3 - "$conn" "$st" <<'PYEOF'
import sys, json
conn, st = sys.argv[1], sys.argv[2]
try:
    c = json.loads(conn).get("result", {}).get("connected", False)
except Exception:
    c = False
try:
    r = json.loads(st).get("result", {})
    v = r.get("velocity", 0)
    p = r.get("play_state", 0)
    d = r.get("direction", True)
    print(f"connected={c} play_state={p} velocity={v} direction={'UP' if d else 'DOWN'}")
except Exception as e:
    print(f"connected={c} state_error={e}")
PYEOF
    ;;
  safeword)
    t=$(issue_token)
    [ -z "$t" ] && echo "ERROR: token issue failed" && exit 1
    echo "SAFEWORD ACTIVATED — stopping everything"
    curl -s -X PUT "$API_BASE/hamp/stop" -H "Authorization: Bearer $t" -H "X-Connection-Key: $CONN_KEY" -H "Content-Type: application/json" -d '{}' > /dev/null 2>&1
    curl -s -X PUT "$API_BASE/hsp/stop" -H "Authorization: Bearer $t" -H "X-Connection-Key: $CONN_KEY" -H "Content-Type: application/json" -d '{}' > /dev/null 2>&1
    curl -s -X PUT "$API_BASE/hvp/stop" -H "Authorization: Bearer $t" -H "X-Connection-Key: $CONN_KEY" -H "Content-Type: application/json" -d '{}' > /dev/null 2>&1
    echo "All protocols stopped. Aftercare mode engaged."
    ;;
  ramp)
    target="${1:-0.8}"; steps="${2:-5}"; delay="${3:-1.5}"
    start_v="0.2"
    t=$(issue_token)
    [ -z "$t" ] && echo "ERROR: token issue failed" && exit 1
    curl -s -X PUT "$API_BASE/hamp/start" -H "Authorization: Bearer $t" -H "X-Connection-Key: $CONN_KEY" -H "Content-Type: application/json" -d "{\"velocity\": $start_v}" > /dev/null
    for step in $(python3 -c "s=float('$start_v');t=float('$target');n=int($steps)
for i in range(1,n+1):print(s+(t-s)*i/n)" 2>/dev/null); do
      echo "  -> velocity $step"
      curl -s -X PUT "$API_BASE/hamp/velocity" -H "Authorization: Bearer $t" -H "X-Connection-Key: $CONN_KEY" -H "Content-Type: application/json" -d "{\"velocity\": $step}" > /dev/null
      sleep "$delay"
    done
    echo "Ramp complete at velocity $target"
    ;;
  pattern)
    seq_spec="${1:-0.3:10 0.5:8 0.7:6}"
    t=$(issue_token)
    [ -z "$t" ] && echo "ERROR: token issue failed" && exit 1
    curl -s -X PUT "$API_BASE/hamp/start" -H "Authorization: Bearer $t" -H "X-Connection-Key: $CONN_KEY" -H "Content-Type: application/json" -d '{"velocity": 0.2}' > /dev/null
    for pair in $seq_spec; do
      v="${pair%%:*}"; dur="${pair##*:}"
      echo "  -> velocity $v for ${dur}s"
      curl -s -X PUT "$API_BASE/hamp/velocity" -H "Authorization: Bearer $t" -H "X-Connection-Key: $CONN_KEY" -H "Content-Type: application/json" -d "{\"velocity\": $v}" > /dev/null
      sleep "$dur"
    done
    echo "Pattern complete"
    ;;
  compose|hsp)
    points="$1"; loop_mode=false
    for a in "$@"; do [ "$a" = "--loop" ] && loop_mode=true; done
    [ -z "$points" ] && echo "ERROR: provide t:x points (e.g. \"0:20 300:80\")" && exit 1
    t=$(issue_token); [ -z "$t" ] && echo "ERROR: token issue failed" && exit 1
    json_pts=""; idx=0
    for pair in $points; do
      pt="${pair%%:*}"; px="${pair##*:}"
      [ -z "$json_pts" ] || json_pts="$json_pts,"
      json_pts="$json_pts{\"t\": $pt, \"x\": $px}"
      idx=$((idx+1))
    done
    tail_idx=$((idx + 1))
    curl -s -X PUT "$API_BASE/hsp/setup" -H "Authorization: Bearer $t" -H "X-Connection-Key: $CONN_KEY" -H "Content-Type: application/json" -d '{}' > /dev/null 2>&1
    echo "HSP session setup"
    body="{\"points\": [$json_pts], \"tail_point_stream_index\": $tail_idx}"
    resp=$(curl -s -X PUT "$API_BASE/hsp/add" -H "Authorization: Bearer $t" -H "X-Connection-Key: $CONN_KEY" -H "Content-Type: application/json" -d "$body")
    echo "Points added: $(echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('result',{}); print(f\"buffered={r.get('buffered', r)}\")" 2>/dev/null || echo "$resp")"
    curl -s -X PUT "$API_BASE/hsp/play" -H "Authorization: Bearer $t" -H "X-Connection-Key: $CONN_KEY" -H "Content-Type: application/json" -d '{"start_time": 0}' > /dev/null 2>&1
    echo "Composition playing ($idx points)"
    if [ "$loop_mode" = "true" ]; then
      last_t=$(echo "$points" | tr ' ' '\n' | tail -1 | cut -d: -f1); [ -z "$last_t" ] && last_t=3000
      offset=0
      while true; do
        offset=$((offset + last_t)); loop_pts=""
        for pair in $points; do
          pt=$(( ${pair%%:*} + offset )); px="${pair##*:}"
          [ -z "$loop_pts" ] || loop_pts="$loop_pts,"
          loop_pts="$loop_pts{\"t\": $pt, \"x\": $px}"
        done
        body="{\"points\": [$loop_pts], \"tail_point_stream_index\": $((idx + 1))}"
        curl -s -X PUT "$API_BASE/hsp/add" -H "Authorization: Bearer $t" -H "X-Connection-Key: $CONN_KEY" -H "Content-Type: application/json" -d "$body" > /dev/null 2>&1
        sleep "$((last_t / 1000))"
      done
    fi
    ;;
  *)
    echo "Usage: $0 {status|connected|state|checkin|velocity N|stroke MAX [MIN]|start [N]|stop|vibe|ramp TARGET [steps] [delay]|pattern 'v:d v:d ...'|compose 't:x t:x ...' [--loop]|safeword}"
    echo "  Velocity range: 0.0 to 1.0"
    exit 1
    ;;
esac