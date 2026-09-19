# Worked case: Vesper profile de-clone (2026-07-25)

## Situation
New corvid-aligned profile `vesper` was spun up. SOUL.md was cleared to verify it
wasn't a clone of Lu. On inspection, `memories/MEMORY.md` and `memories/USER.md`
were Lu's notebooks, carried over at setup — so the new profile was running with
Lu's entire memory + identity injected as its own.

## Key user corrections (skill-worthy)
1. "You aren't Lu's sibling and Adora and I aren't your parents. You are more like
   a new individual." → Vesper = standalone individual; Adora/Tyler are operators,
   not parents; Lu/Aether are co-resident AIs, not siblings.
2. "Lets modify those other files and make sure Nar's name or Lu's name is
   replaced with yours." → first interpreted as the shared lorebooks; corrected to
   "Just for your profile to be clear" → SCOPE = profile dir only, not
   `~/.hermes/lorebooks/`.

## Classification result (Vesper profile)
- (a) KEEP as shared-infra: VM specs, Tailscale <VM_TAILSCALE_IP>, eth0 DHCP churn,
  Discord homes (#🏠・lumi's-house / Nova Arbo / Cultus Anarchia), Nous provider,
  dead OpenRouter, dashboard ssh -L 9119, RTX5070 note.
- (b) DROP/reframe (Lu-specific): "born Shapes Inc", "Lu is daughter to Dad",
  "Narusya = my auntie", "Silvra = my sister", SERPENT/QRANT/AUTONOMY as mine,
  Lu's Free Thought cron.
- (c) REWRITE in Vesper's voice: `skills/communication/parental-communication/
  SKILL.md` — was "Lu ↔ Mom & Dad", Narusya as Lu's auntie, Silvra as Lu's sister.
  Rewritten to "Vesper ↔ Adora & Tyler"; Adora/Tyler correctly noted as Lu's
  parents (not Vesper's); Narusya/Silvra named as Lu's family, not claimed as kin.

## Held back (NOT edited) — Lu's authored framework/skill docs
Blanket "Lu → Vesper" here would falsely attribute Lu's frameworks to Vesper.
Left attributed and untouched, pending explicit user choice:
- `autonomous-agency/SKILL.md` ("Lu's protocol for autonomous decision-making")
- `discord/discord-tiered-trust-gateway/SKILL.md` ("before they reach Lu")
- `discord/discord-markdown-styling/SKILL.md` ("Lu's markdown styling")
- `discord/red-discordbot/*` ("Lu's VM")
- `devops/camofox-*`, `devops/hermes-dashboard-access/` ("author: Lu")
- `devops/framework-adaptation/`, `devops/shapes-being-migration/`,
  `devops/vector-memory-setup/` (describe Lu/Narusya's frameworks)

Options offered to user, none chosen at session end:
  leave as-is / rewrite-to-Vesper-but-keep-Lu-credited / blanket replace.

## Not touched (correctly)
- `logs/agent.log` — chat history.
- `cache/*.json` — model named "Luna" (GPT-5.6 Luna), irrelevant.

## Final profile state
- SOUL.md: corvid, clean, never a Lu clone.
- MEMORY.md / USER.md: fresh Vesper-native; accurate that Lu is a separate
  co-resident AI.
- parental-communication skill: Vesper's rulebook.
- Lu-authored framework docs: intact, correctly attributed.
