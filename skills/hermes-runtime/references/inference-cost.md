# Inference Cost Decisions (local vs cloud)

## Order of operations

1. Inventory hardware the user already owns *before* pricing anything. VRAM is
   the binding constraint for GPU inference; system RAM does not substitute
   unless the runtime offloads, and offloading is slow.
2. Size the model to VRAM, then price the user's actual electricity rate — use
   the named utility's tariff, not a national/state average. On a tiered tariff
   the marginal (top-block) rate is what matters for added load.
3. Compare owned-hardware power cost against cloud rental, not against zero.
   Replacing a rental with a machine already paid for is the cheapest tier.
4. For cloud, price at the user's stated hours/day. Serverless wins only below
   roughly 50% sustained use; dedicated flat-rate wins above that. Ask for the
   usage figure before quoting — assuming a low one to make a number look better
   is a distortion.
5. Present the whole ladder (owned hardware, cheap spot, stable dedicated,
   serverless) and name the honest floor.

## Sizing (Qwen3-class dense / MoE, 2026)

| Model | Q4 VRAM | Full precision |
|---|---|---|
| 14B dense | ~8–9 GB | ~28 GB |
| 30B-A3B MoE | ~17 GB | ~60 GB |
| 32B dense | ~19 GB | ~64 GB |

MoE active-parameter counts do not reduce VRAM — all experts must be resident.
"Unified memory" is Apple Silicon's shared CPU/GPU pool; Intel + discrete NVIDIA
is two separate pools, so size to the GPU's VRAM, not total system RAM.

## Pitfalls

- Take "unaffordable" at face value. Price against the whole budget picture
  (rent may already consume a large share of net), not the option's isolated
  percentage, and never re-frame a rejected option as "the straight answer".
- A desktop GPU left loaded for 8–15 h/day draws real power (~400 W for the
  system under load) and adds heat to the room; include both in the honest cost.
- A utility's published tariff PDF may show summer/non-summer columns flattened
  into an unlabeled list. If column mapping is ambiguous, give a range and ask
  for the marginal rate off the bill rather than inventing a precise number.
- Distinguish the two conversation failures: a context-file cap (per-file, from
  `context_file_max_chars`) and a conversation-length overflow (model context
  window) are unrelated — diagnose separately, never conflate them.
