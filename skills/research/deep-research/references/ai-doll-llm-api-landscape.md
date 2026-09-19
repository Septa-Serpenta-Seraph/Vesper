# AI Doll / Companion Doll LLM-API Landscape (Aug 2026)

Condensed from the Aug 22 2026 landscape brief. Full report: `/home/lumi/ai-doll-llm-api-research.md`.

## Bottom line
**No company ships a doll with true bring-your-own-LLM / OpenAI-compatible API support.** Every shipped AI doll uses a proprietary cloud-locked app brain. Realbotix is the closest commercial product (app-level third-party LLM integration incl. local models, but NOT a public developer API/SDK). The only genuine custom-LLM-endpoint paths are DIY/hacker projects (OSSM, buttplug ecosystem) — none are dolls. SynDoll Labs/Thalanor and BOLTT do not exist as described.

## Shipped vendors (no API anywhere)
| Vendor | Status | Price | LLM story |
|---|---|---|---|
| Realbotix B/M/F + Aria (US) | ✅ shipped | B-bust $20K, M $95K, F $125K; ~$199/mo sub | BYO third-party LLM via controller app (ChatGPT, Llama, Gemini, DeepSeek, Claude, HF, local apps; rolled out Feb–Jul 2025). App-level, no dev SDK/portal/GitHub. |
| RealDoll Harmony/Nova/Serenity/RealDollX (Abyss) | ✅ shipped | ~$10K+ | X Mode app personality sliders, learning AI, AI vagina insert. Proprietary. |
| Lovense Emily (CES 2026) | ✅ shipped (pre-order) | $4,000–$8,000 | Generative voice, persistent memory, personality switching. Cloud-locked. See `references/lovense-emily-ai-doll.md`; Lovense dev API (developer.lovense.com) is for TOYS only, not Emily's brain. |
| UBTech U1 (CN) | ✅ shipped (presale Jun 2026, ~3,000 units) | deposit ¥3,000 (~$440), full TBD | 88 joints, affective AI, encrypted memory. Proprietary. |
| Noetix bust (CN) | ✅ shipped | ¥99,900 (~$14K) | Conversational/emotional. Proprietary. |
| Starpery (CN) | ✅ shipped | ~$2,500+ | "AI" = moaning/heating/suction only, no conversation on doll. 2024 r/NomiAI post floated "android body ready to take any AI companion" (body + phone-app brain split) — never shipped as such. |
| Jiggly Joy, Ridmii, BestRealDoll, Irontech IronAI, VMDoll | ✅ shipped | ~$2–5K | "AI talking" heads, all proprietary. BI Jun 2026: VMDoll AI "cannot get into a deep conversation." |

## Realbotix developer story (verified)
- Feb 4 2025 PR: third-party AI "interface... operate through our hardware"; roadmap HF/ChatGPT/DeepSeek (Feb), Llama/Gemini/Claude (Mar–Apr), more (Jun–Jul). CEO claim "only manufacturer... open-source hardware system" = marketing spin, no open-source hardware published.
- Configured through the Realbotix app (LLM connections, custom character profiles, lip-sync). **No public API/SDK for third-party devs** — no dev portal, no docs subdomain, no GitHub org.
- Pricing detail: 3 tiers + subscription; Aria media price ~$150–175K.

## DIY / open-source (the real BYO-LLM route)
- **OSSM** (KinkyMakers / Research & Desire, Toronto) — fully open ESP32 sex machine. Ready-to-Play $689.05, DIY kit from $523.08, PCB $59.27. github.com/KinkyMakers/OSSM-hardware, ossm.tech, docs.researchanddesire.com. App: "OSSM Possum."
- **buttplug.io / Intiface** (BSD-3) — open intimate-hardware control standard; Buttplug MCP server lets LLM agents control toys.
- **ButtplugLLM** (github.com/zhanp199/ButtplugLLM) — local-LLM chat controlling hardware via Buttplug, safety features.
- **LLM_Buttplug** (PsychoSmiley) — "Let LLMs control sex toys."
- **AgenticLover** (agenticlover.ai) — local-LLM companion controlling toys/e-stim/smart-home.
- **ToyBridge** (AmandaClarke61) — reverse-engineer BLE toy protocols, control with AI.
- Dominant consumer pattern (BI): Starpery doll (~$2,500) + Kindroid/Nomi chatbot on laptop/phone = "doll is the body, AI is the mind."

## Dead-ends (verified non-existence / misremembered)
- **SynDoll Labs / CEO "Thalanor"** — no such company. Real "Syndoll" = Chengdu AI plush/desktop toy robot + UK IPO trademark (class 28, Shaoting Huang, journal 2026/030). Vaporware as described.
- **BOLTT** — not found in 4 search variants; hits are Fire-Boltt smartwatches. Misremembered.
- **"Tempest"** — `elder-plinius/T3MP3ST` is an open-source red-teaming security platform (AGPL), not a sex robot.
- **"Repurposed"** — no project of that name; nearest is Realbotix repurposing RealDoll bodies as classroom bots.
- **"Sex Doll Genius"** — SEO spam on reseller blogs.
- **DollSweet / DS Doll** — real robotic head (dsdoll.us) but 2018 "app code will be open sourced" promise never materialized; stale, no LLM.

## Watch list
- **Furhat Robotics** (furhatrobotics.com/furhat-sdk, furhat.io) — only shipped companion HEAD with a genuine public SDK + Remote API, LLM-native (FurhatAI). Not a sex doll; the shipped gold standard for "program a head with your own LLM."
- **CUBIE (Cubic Robotics)** — Indiegogo $185K; desktop companion with open API + deploy-your-own-API-key (Llama etc.). Crowdfunded, not shipped.
- No company has publicly announced doll API support on a roadmap — that gap IS the finding.

## Key sources
realbotix.ai news (2025-02-04) · emerginggrowth.com Realbotix profile (Dec 2025) · businessinsider.com/we-were-promised-sex-robots-2026-6 · cnet.com CES 2026 Emily · sixthtone.com/news/1018634 (UBTech U1) · researchanddesire.com/pages/ossm · awesome.buttplug.io · github.com/zhanp199/ButtplugLLM · agenticlover.ai · roboticgizmos.com DS Doll · furhatrobotics.com · indiegogo CUBIE · ipo.gov.uk Syndoll trademark.
