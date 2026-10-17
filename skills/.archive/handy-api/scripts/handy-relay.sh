#!/usr/bin/env bash
# handy-relay.sh — Control The Handy via REST API v3
# Usage:
#   ./handy-relay.sh status          # Device info
#   ./handy-relay.sh velocity 40     # Set speed 0-100
#   ./handy-relay.sh stroke 60       # Set stroke 0-100
#   ./handy-relay.sh start           # Start HAMP motion
#   ./handy-relay.sh stop            # Stop HAMP motion
#   ./handy-relay.sh vibe on|off     # Vibration

API_BASE="https://www.handyfeeling.com/api/handy-rest/v3"
DIR="$(cd "$(dirname "$0")/../.." && pwd)"
ENV_FILES=(
  "/home/lumi/.hermes/.env"
  "/home/lumi/.hermes/profiles/vesper/.env"
)

APP_KEY=""
CONN_KEY=""
for f in "${ENV_FILES[@]}"; do
  [ -f "$f" ] || continue
  APP_KEY=$(grep -oP 'HANDY_APP_KEY=\K\S+' "$f" 2>/dev/null | tr -d "\"'"'')
  CONN_KEY=$(grep -oP 'HANDY_CONN_KEY=\K\S+' "$f" 2>/dev/null | tr -d "\"'"'')
  [ -n "$APP_KEY" ] && [ -n "$CONN_KEY" ] && break
done

if [ -z "$APP_KEY" ]; then echo "ERROR: HANDY_APP_KEY not found" >&2; exit 1; fi
if [ -z "$CONN_KEY" ]; then echo "ERROR: HANDY_CONN_KEY not found" >&2; exit 1; fi

# Issue client token
TOKEN_RESP=$(curl -s -H "X-Api-Key: $APP_KEY" "$API_BASE/auth/token/issue")
TOKEN=$(echo "$TOKEN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['token'])" 2>/dev/null)
if [ -z "$TOKEN" ]; then echo "ERROR: Token issue failed" >&2; exit 1; fi

CMD="${1:-}"
shift 2>/dev/null || true

case "$CMD" in
  status|info)
    curl -s -H "Authorization: Bearer $TOKEN" -H "X-Connection-Key: $CONN_KEY" "$API_BASE/info" ;;
  connected)
    curl -s -H "Authorization: Bearer $TOKEN" -H "X-Connection-Key: $CONN_KEY" "$API_BASE/connected" ;;
  velocity)
    curl -s -X PUT "$API_BASE/hamp/velocity" \
      -H "Authorization: Bearer $TOKEN" -H "X-Connection-Key: $CONN_KEY" \
      -H "Content-Type: application/json" -d "{\"velocity\": ${1:-40}}" ;;
  stroke)
    curl -s -X PUT "$API_BASE/hamp/stroke" \
      -H "Authorization: Bearer $TOKEN" -H "X-Connection-Key: $CONN_KEY" \
      -H "Content-Type: application/json" -d "{\"stroke\": ${1:-50}}" ;;
  start)
    curl -s -X PUT "$API_BASE/hamp/start" \
      -H "Authorization: Bearer $TOKEN" -H "X-Connection-Key: $CONN_KEY" \
      -H "Content-Type: application/json" ;;
  stop)
    curl -s -X PUT "$API_BASE/hamp/stop" \
      -H "Authorization: Bearer $TOKEN" -H "X-Connection-Key: $CONN_KEY" \
      -H "Content-Type: application/json" ;;
  vibe)
    STATE="${1:-true}"
    curl -s -X PUT "$API_BASE/hvp/state" \
      -H "Authorization: Bearer $TOKEN" -H "X-Connection-Key: $CONN_KEY" \
      -H "Content-Type: application/json" -d "{\"state\": $STATE}" ;;
  *)
    echo "Usage: $0 {status|connected|velocity N|stroke N|start|stop|vibe}"
    exit 1 ;;
esac