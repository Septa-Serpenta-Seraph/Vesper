#!/bin/bash
# watch-remote-task.sh — Poll a long-running Windows task over SSH until completion.
#
# PATTERN: launch the heavy task detached on Windows (wmic process call create,
# or the download .bat pattern in remote-comfyui-models), then run THIS poller in
# the background with notify_on_complete=true. It survives SSH drops and pings you
# exactly once when the task finishes (or errors).
#
# Usage: edit the vars below, then:
#   terminal(background=true, notify_on_complete=true, command=".../watch-remote-task.sh")
#
# Two modes:
#   MODE=log    — poll a log file for marker strings (downloads: watch C:\minimax_dl.log for "ALL DONE")
#   MODE=comfy  — poll ComfyUI /history/<PROMPT_ID> for "completed" / error status

KEY=~/.ssh/windows_desktop
PORT=1237              # reverse-tunnel port (find with the port-scan loop in comfyui-ssh-tunnel)
MODE=comfy             # log | comfy
LOG_PATH="C:\\minimax_dl.log"          # MODE=log: Windows path to the log file
SUCCESS_MARKER="ALL DONE"              # MODE=log: string that means success
FAIL_MARKER="FAIL"                     # MODE=log: string that means failure
PROMPT_ID="00000000-0000-0000-0000-000000000000"  # MODE=comfy: prompt id from POST /prompt
TIMEOUT_MIN=90         # how long to poll before giving up

for i in $(seq 1 $((TIMEOUT_MIN * 2))); do
  if [ "$MODE" = "log" ]; then
    RESULT=$(timeout 15 ssh -i "$KEY" -p "$PORT" tyler@127.0.0.1 cmd /c "type $LOG_PATH" 2>/dev/null)
    if echo "$RESULT" | grep -q "$SUCCESS_MARKER"; then
      echo "=== TASK COMPLETE ==="; echo "$RESULT" | tail -20; exit 0
    fi
    if echo "$RESULT" | grep -q "$FAIL_MARKER"; then
      echo "=== TASK FAILED ==="; echo "$RESULT" | tail -20; exit 1
    fi
  else
    RESULT=$(timeout 15 ssh -i "$KEY" -p "$PORT" tyler@127.0.0.1 cmd /c "curl -s -m 10 http://127.0.0.1:8188/history/$PROMPT_ID" 2>/dev/null)
    if echo "$RESULT" | grep -q "\"completed\""; then
      echo "=== GENERATION COMPLETE ==="; echo "$RESULT" | head -c 3000; exit 0
    fi
    if echo "$RESULT" | grep -q "\"status_str\": \"error\""; then
      echo "=== GENERATION ERROR ==="; echo "$RESULT" | head -c 3000; exit 1
    fi
  fi
  sleep 30
done
echo "=== WATCHER TIMED OUT (${TIMEOUT_MIN} min) — check manually ==="
