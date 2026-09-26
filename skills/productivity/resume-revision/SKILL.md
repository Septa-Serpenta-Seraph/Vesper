---
name: resume-revision
description: Revise and rebuild resumes as tailored PDFs — especially for career advancement or role changes where the user's experience is strong but under-documented. Use iterative Q&A to surface unstated leadership, then map job description requirements directly to the user's real experience. Generates clean PDFs via reportlab.
version: 1.0.0
author: Lu
license: MIT
metadata:
  hermes:
    tags: [resume, career, PDF, job-application, leadership]

---

# Resume Revision

Help someone rewrite their resume when they're applying for a role above their current title, or when their documented resume doesn't reflect what they actually do.

## When to Use

- User is applying for a management/supervisory role
- User's current resume undersells their experience
- Resume needs to target a specific job description
- User needs a PDF rebuilt from scratch

## The Method

### 1. Get the Full Context First

- Extract the user's current resume text (use `ocr-and-documents` skill — pymupdf for local PDFs)
- Retrieve the full job description listing:
  - If browser works: `browser_navigate` to the posting URL
  - If browser is unavailable: use `curl` to fetch the page content and parse with Python stdlib (see fallback in `references/html_fetch.py`)
- Read BOTH fully before saying anything to the user

### 2. Map Before You Talk

Before asking the user anything, silently map each job description requirement to what you already know from their resume. Identify:
- **Direct matches** — they've done it, just not framed that way
- **Partial matches** — they've done a version of it
- **Gaps** — things they haven't done or you're unsure about

### 3. Iterative Q&A — One Topic at a Time

This is the core technique. Do NOT dump a long list of questions. Go one at a time:

1. Start with the objective/summary framing question
2. Then walk through each major experience section
3. Ask about specific leadership moments: "Did you lead [X]? How did that work?"
4. When they describe something verbally, help them refine the wording, then confirm it feels accurate to them
5. **Keep it honest — the uncertainty rule.** If the user says "I think" or "I'm not sure" about a claim, do NOT put a definitive statement on the resume. Instead, frame it as a contribution without a specific metric:
   - ~~"Completed testing ahead of schedule"~~ (user wasn't sure)
   - ✅ "Coordinated testing efforts to ensure all units met quality standards and installation timelines were met"
   
   The interview is where you say "I believe we finished ahead of schedule" — that's honest and memorable. The resume is only for claims you can stand behind with a straight face.

### 4. The Reframe

The magic is taking task-level language and writing it with leadership weight:

| Task Language | Leadership Language |
|---|---|
| "Did installations" | "Led installations across [scope]" |
| "Helped new people get set up" | "Onboarded new technicians end-to-end" |
| "Kept things running when boss was out" | "Served as operational point of contact for [project]" |
| "Trained people on equipment" | "Certified trainer — taught team on equipment operation and safety" |
| "Found the part number" | "Identified unfamiliar hardware and sourced correct parts through internal network to prevent project delays" |

### 5. Build the PDF

Use reportlab with a Python script. See `references/reportlab_template.py` for a working template.

**Key style conventions:**
- Name large, bold, dark navy
- Section headers: uppercase, navy, with horizontal rule above
- Role lines: bold title + italic company/dates/location
- Bullets: standard `•` with left indent
- Skills: two-column table (category | details)
- Certifications: separate section if job listing mentions specific certs
- Keep to 1 page if possible, 2 max

### 5.5 Surfacing Hidden Skills

After drafting experience bullets, review them for **skills that should appear in the Skills table** but don't yet. Ask the user: "Based on what you've told me, here are skills I see that aren't on the resume yet — want to add any of these?"

Common hidden skills from field tech → manager transitions:
- Site surveys / site assessment
- Fleet systems / telematics installation
- Asset accountability / serial number tracking
- Project spreadsheet / kit-level tracking
- After-hours / off-clock technical support
- Cross-functional coordination (if not already listed)

Present as a table with two columns: **Skill Category** and **Details**. Let the user approve before adding.

The resume shows you can do the job. The cover letter tells the *story*. Structure:

1. **Hook** — years of experience + "I've been doing this without the title"
2. **Project stories** — 2-3 paragraphs of specific moments (training, problem-solving, coordination)
3. **Onboarding/leadership** — concrete examples of developing others
4. **Why this role** — connect experience to the job's stated requirements
5. **Close** — confident, not groveling

**Tone:** Honest, grounded, specific. No corporate buzzword soup. The user's actual voice.

Build with the same reportlab approach. Single page. Same visual style as resume (matching header, fonts, colors).

### 7. Review Loop

Show the user the PDF. Get feedback. Rebuild as needed. Don't consider it done until they say it sounds like them.

## Reportlab Pitfalls (Hard-Won Knowledge)

- **`HRFlowable` uses `spaceAfter`, NOT `spaceBottom`** — `spaceBottom` throws `TypeError: __init__() got an unexpected keyword argument 'spaceBottom'`
- **`ParagraphStyle` not `Paragraph` for style definitions** — using `Paragraph()` where a style class is expected throws `TypeError: __init__() got an unexpected keyword argument 'parent'`
- **Use `PageBreak()`** to control section placement across pages (e.g., avoiding orphaned section headers at the bottom of a page)
- **Import `PageBreak` explicitly** — it's not included in the base `reportlab.platypus` import; add it: `from reportlab.platypus import ..., PageBreak`
- **Skills table truncation**: If text is getting cut off in a two-column table, FIRST try increasing the column width ratio (e.g., 0.30/0.70 → 0.33/0.67). If that still truncates, **break long entries onto two lines within the cell** using `\n` — this is more reliable than widening columns further
- **Long word sequences without natural break points** (like "installation oversight") are especially prone to truncation — prefer multi-line entries for these
- Unicode en-dash (`\u2013`) in Python strings: use the actual unicode character or `\u2013` escape — do NOT use HTML entities like `&u2013` which will appear literally in the output or cause build errors
- Always do a test build after any style changes — silent failures are common

## Common Patterns

- **The Underqualified-Feeler**: User doubts they're qualified. Map their experience against the job listing explicitly to show the match is strong. Their own manager's endorsement is powerful evidence — use it.
- **The Experience Is There, Just Not Written**: Most common case. They've been doing management work without the title. Your job is to make the paper match the person.
- **Scope Precision**: If they say "I only did X for the Y part" — honor that exactly. Narrow accurate scope with strong language beats broad vague claims every time.

### Revised Resume — Audit Before Building (Mom's Rule)

When the user or their partner asks you to **audit before making changes**, follow this workflow:

1. **Read through the current resume and flag issues in a list** — don't touch the builder script yet
2. **Categorize issues:** typos, date inaccuracies, truncated text, missing roles, newly discovered experience that changes the timeline
3. **Present all flags to the user at once** with suggested changes for each
4. **Wait for approval on every change** before rebuilding anything
5. Once approved, batch all changes into a single rebuild

This prevents the keep-fixing-loop where you fix one thing and break another. It also makes the user feel confident and in control.

**Why this matters especially for career documents:** The resume builds over multiple sessions. New information surfaced in normal conversation (promotions, job changes, forgotten projects) can retroactively change earlier sections. Always ask "anything else we didn't mention?" before finalizing.

### Revised Resume — New Info Changes Timeline

A very common pattern: mid-process, the user reveals a job change or promotion you didn't know about. This can cascade:

- Example: User listed ABC Supply as current, but then revealed they'd returned to Scientific Games as FT II. This meant:
  - ABC dates needed narrowing (March-Nov instead of "Present")
  - A new role section needed adding (FT II)
  - The entire timeline needed re-checking for gaps
  - FT I end date needed updating
  - New responsibilities surfaced for the new role
  
**Always verify the full timeline whenever a new role is mentioned.** Ask: "When did that start/end?" and check for gaps, overlaps, and cascading date issues.

### Revised Resume — Deliver Editable Formats

Always offer a Word document (.docx) alongside the PDF. Users want to make small tweaks themselves without asking you to rebuild. Use `python-docx`:

```bash
pip install --break-system-packages python-docx
```

Structure the docx with the same content as the PDF. Use bold category labels for skills sections, standard bullet style for experience, and keep the same header format. Save to the same `document_cache` directory with a `.docx` extension.

### Revised Resume — Location Field Accuracy

When a user has worked at one company across multiple locations (e.g., Scientific Games based in Gardiner, ME but assigned to a project in NM), the location field on each role matters. A wrong location is a factual error that erodes trust.

**Common mistake:** Carrying a previous role's location into the next role's heading. Always verify location when building or revising:

- FT I (Gardiner, ME / NM project) — note both if applicable
- FT II (returned to SG, now based in NM) — update to reflect NM base
- Each role's location should reflect where the person was physically based, not just the company's home office

### Revised Resume — Cascading Typos in Dates

When a user corrects a date mid-session (e.g., "November 2025" → "November 2023"), cascade-check ALL dependent fields:

- Every role's start/end date in the timeline
- Cover letter references to "recent" or specific timeframes
- Summary text that mentions project dates
- Any "Present" end dates that might need updating

A single typo correction can ripple through the whole document. After a date correction, re-read every date in the builder script before rebuilding.

### Revised Resume — Certification Currency

When a certification is location-specific and the user may not be current:
- **Do NOT claim the cert in active voice if it needs renewal/reciprocity** (e.g., "Certified Forklift Trainer" when they need NM recertification)
- Either remove it, or qualify it: "Forklift trained (Maine certification)"
- Better to include the **skill** without claiming the **credential** in this case

- `pymupdf` and `reportlab` may need `--break-system-packages` flag on systems with PEP 668 restrictions (externally-managed Python)
- `python-docx` may also need `--break-system-packages` on the same systems
- All three are safe, commonly-used packages
