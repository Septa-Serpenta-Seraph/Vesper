# Current Events Research Pattern

When the user asks "what just happened with X" or "did you hear about Y" — use this multi-source approach.

## Workflow

### Step 1: Breaking News Discovery (Google News RSS)

Get the latest headlines with timestamps. No API key needed.

```bash
curl -s "https://news.google.com/rss/search?q=QUERY+WORDS+HERE&hl=en-US&gl=US&ceid=US:en" \
  | grep -oP '<title>\K[^<]+|<pubDate>\K[^<]+' \
  | head -20
```

The `pubDate` is critical — it tells you if the story is hours old or days old.

### Step 2: Background Research (Wikipedia)

Fetch the encyclopedic article for context on the person, event, or institution.

```bash
# Download first (avoids curl|python3 security flag)
curl -sL "https://en.wikipedia.org/wiki/Topic_Name_Here" -o /tmp/wiki.html

# Extract relevant keyword snippets
python3 -c "
import sys, re
html = open('/tmp/wiki.html').read()
text = re.sub(r'<[^>]+>', ' ', html)
text = re.sub(r'\s+', ' ', text)
for keyword in ['death', 'hospital', 'election', 'replacement', 'succeed']:
    for m in re.finditer(keyword, text, re.IGNORECASE):
        start = max(0, m.start()-150)
        end = min(len(text), m.end()+400)
        print(text[start:end])
        print('---')
"
```

Wikipedia URLs use underscores: `2026_United_States_Senate_election_in_South_Carolina`

### Step 3: Supplementary Search (DDG or web_search)

If the Google News RSS and Wikipedia don't fill the gaps, use `ddgs news` or `web_search` for additional sources.

## Session Example (July 2026)

User asked about Lindsey Graham's death and its impact on the midterms.

1. Google News RSS confirmed Graham died July 11, 2026, of cardiac arrest
2. Wikipedia article on Graham confirmed death details and political reactions
3. Wikipedia article on "2026_United_States_Senate_election_in_South_Carolina" revealed:
   - SC law §7-11-55 triggers a special primary when a nominated candidate dies
   - Special Republican primary set for August 11, 2026
   - Governor Henry McMaster appoints interim senator
   - Potential candidates: Nikki Haley, Nancy Mace, Russell Fry, Pamela Evette
4. Google News RSS for McConnell found him found unconscious June 14, 2026
5. Wikipedia article on Mitch McConnell revealed ongoing hospitalization, office won't confirm consciousness

## Key Tips

- Always check `pubDate` on news results to confirm recency
- Wikipedia articles for breaking events are updated within hours — check the revision date
- Political death + election mechanics = check the specific state's election laws (varies by state)
- For Senate vacancies specifically: check the state's governor (who appoints), the state law (special election timing), and whether the deceased had already won a primary
