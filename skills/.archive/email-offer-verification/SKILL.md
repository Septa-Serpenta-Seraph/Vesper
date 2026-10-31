---
name: email-offer-verification
description: "Verify suspicious promo/gift-card emails before clicking."
version: 1.0.0
---

# Email / Offer Verification — Phishing Triage for Tyler

Tyler forwards suspicious promotional emails (gift cards, rewards, "you
won X") and asks "is this legit?" before clicking. This is the triage
playbook — verify with evidence, keep him calm, never shame him for asking.
Pattern established 2026-08-13 with the Xfinity $200 Amazon eGift email.

## The triage ladder (do these in order, cite evidence)

1. **Sender domain, not sender name.** Check the actual email address
   (`@incentivetracker.xfinity.com` ≠ display name "Xfinity"). Lookalike
   domains (`xfinity-rewards.xyz`, missing hyphens, swapped letters) = red
   flag. Real subdomains of the company's own domain = green signal.
2. **Check the claim destination URL — without clicking.** Hover/long-press
   the button to reveal the real URL. If the destination is the company's own
   domain (even with a long tracker string — normal), that's strong evidence.
   If it's a random/lookalike domain, stop.
3. **DNS/CDN sanity on the activation domain.** Resolve the domain
   (`dig +short egift.activationspot.com`) — legitimate fulfillment platforms
   sit behind big CDNs (Fastly, Cloudflare, Akamai). A personal-looking IP or
   brand-new domain is suspicious. WHOIS creation date can help.
4. **"Not in the app" is NOT automatically disqualifying.** Companies run
   TWO reward channels: loyalty rewards (visible in-app, e.g. Xfinity
   Rewards) and signup/incentive promotions (delivered by email only, often
   via a third-party incentive tracker domain). If the email came from the
   real incentive-tracker domain and matches a signup he remembers, the
   "can't find it in the app" test doesn't kill it — verify the URL instead.
5. **The credential/payment test (the dealbreaker).** Real rewards never ask
   for password, SSN, or a "fee to claim". The instant the page asks for any
   of those — it's fake, regardless of how clean the email looked.

## What to tell Tyler (tone)

- Warm, never condescending: he did the right thing by checking. "You spotted
  it, you checked it, you didn't lose a thing" — that's the win.
- No urgency: real rewards don't expire in 24 hours. "Check the link when
  you're at the laptop" removes the FOMO pressure scammers rely on.
- Give him a concrete safe path (claim through the official app/website, not
  the email link; hover the URL first).
- If phishing: suggest reporting it from the email app, don't reply (that
  confirms a live address).

## Verified case (2026-08-13) — the Xfinity $200 eGift — RESOLVED: LEGIT ✅

- Email: `yourcard@incentivetracker.xfinity.com` — real Xfinity incentive
  domain; matches Xfinity's signup-promotion channel (delivered by email,
  NOT in the Rewards app — so "not in app" was NOT disqualifying).
- Activation URL: `egift.activationspot.com/?tid=...` — resolved through
  Fastly (big legit CDN), site has bot-protection (JS challenge, common on
  legit fulfillment platforms).
- **Tracking-link gotcha:** the "Activate" BUTTON went through
  `link.hawkmarketplace.com` — a legitimate email-marketing platform
  (Hawk Marketplace), NOT a scam domain. Curl returned `400 Wrong Link`
  when fetched directly — that's NORMAL for click-tracking links (they
  require the email client's session/cookies; direct fetches get refused).
  Don't treat a 400 on the tracking link as a scam signal.
- **Outcome: claimed via the direct URL (typed, not the button) and $200
  was added to his account. 100% legit.** The ladder worked: sender domain
  real + CDN legit + claim page only wanted the eGift code = real reward.
- Lesson: don't write it off on "not in app" OR write it off on "unknown
  domain" OR on a tracking-link 400 — run the ladder, and the safe path is
  **typing the destination URL directly** (skips the tracking redirect) then
  watching the claim page for credential/payment asks.

## Related

- `domain-intel` — deeper passive recon (WHOIS, certs, subdomains) if the
  URL needs more digging
- `himalaya` — reading/sending email from terminal if we need headers
