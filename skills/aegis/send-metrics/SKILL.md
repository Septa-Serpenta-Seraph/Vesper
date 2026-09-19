# AEGIS Send Metrics Skill

Send Hermes agent metrics to the AEGIS Dashboard for visualization.

## Usage

Call with: `send metrics to AEGIS`

Gathers current Hermes runtime metrics and POSTs them to `/api/stats/visualize`.
Returns the generated chart image (base64 PNG) or an error.

## Configuration

Set environment variable `AEGIS_API_URL` to the base URL of the AEGIS Dashboard
(e.g., `http://localhost:5000`). Default: `http://localhost:5000`.

## Metrics Payload

```json
{
  "metrics": {
    "tool_usage": {"terminal": 12, "execute_code": 5, ...},
    "emotional_state": {"curiosity": 0.8, "focus": 0.7, ...},
    "session_turns": 42,
    "total_tokens": 125000
  },
  "type": "line"
}
```

## Implementation

- Uses `requests` to POST JSON
- Handles connection errors and non-200 responses
- Returns chart image data or error

## Requirements

- AEGIS Dashboard running and accessible at `AEGIS_API_URL`
- Dashboard has `/api/stats/visualize` endpoint

## Example Response

```json
{
  "success": true,
  "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "chart_type": "line"
}
```
