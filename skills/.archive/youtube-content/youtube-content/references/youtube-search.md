# YouTube Search Without a Browser

Techniques for discovering YouTube videos from the terminal when no browser/Camofox is available.

## Method 1: curl title scrape (zero dependencies)

Scrapes YouTube's search results page HTML and extracts video titles. Fast, no install needed.

```bash
curl -s "https://www.youtube.com/results?search_query=QUERY+WITH+PLUS+SIGNS" \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  | grep -oP '"title":{"runs":\[{"text":"[^"]*"' \
  | sed 's/"title":{"runs":\[{"text":"//;s/"$//'
```

**Limitations**: titles only — no durations, no video IDs, no channel info. Good for a quick "what exists" scan before committing to deeper metadata lookup.

## Method 2: yt-dlp search (full metadata)

Uses yt-dlp's `ytsearch` pseudo-playlist to fetch metadata for search results without downloading any video.

```bash
yt-dlp --flat-playlist --print "%(duration)s|%(id)s|%(title)s" "ytsearch5:QUERY HERE"
```

- `ytsearch5:` — returns top 5 results. Change the number to get more/fewer.
- `--flat-playlist` — reads metadata only, does not download video content.
- `%(duration)s` — in seconds. Convert: `mins=$((dur/60))`.
- `%(id)s` — video ID. Construct URL: `https://youtube.com/watch?v=ID`.
- `%(title)s` — video title.
- Can combine multiple format fields with `|` separator for easy parsing.

**Multi-query batch** (search several topics at once):
```bash
for q in "query one" "query two" "query three"; do
  echo "=== $q ==="
  yt-dlp --flat-playlist --print "%(duration)s|%(id)s|%(title)s" "ytsearch5:$q" 2>/dev/null
  echo
done
```

**Filter for length** (find videos over N minutes):
```bash
yt-dlp --flat-playlist --print "%(duration)s|%(title)s" "ytsearch10:QUERY" 2>/dev/null \
  | while IFS='|' read -r dur title; do
      mins=$((dur/60))
      [ "$mins" -ge 60 ] && echo "${mins}min | $title"
    done
```

## Install note

On PEP 668-protected systems (Debian/Ubuntu), `pip install yt-dlp` fails with an externally-managed-environment error. Fix:
```bash
pip install --break-system-packages yt-dlp
```
Or use a venv / `uv tool install yt-dlp` as alternatives.

## Workflow: discovery → selection → transcript

1. **Scout** with curl title scan (Method 1) to see what's out there.
2. **Get metadata** with yt-dlp search (Method 2) for durations and video IDs.
3. **Present** results to the user with durations and direct URLs.
4. **Fetch transcript** of the selected video using `scripts/fetch_transcript.py`.
5. **Transform** transcript into the requested format (summary, chapters, thread, etc.).
