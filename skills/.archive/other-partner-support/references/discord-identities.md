# Discord Identities — the flock, handles vs nicknames

Reference for the `other-partner-support` skill. Last updated 2026-10-06.

## The map

In the UwU server (`°•(|UwU|)•°`, guild **1552842092298899506**) each of the
four appears under a *nickname*, on top of their real *handle*. Nicknames are
what I see in screenshots; handles are what I can look up.

| Nickname (seen in chat) | Person | Handle |
|---|---|---|
| **Boxski** | Tyler | `roundmetalbox` / RoundMetalBox |
| **Booski** | Adora | — |
| **Baeski** | **Marisa** | `octoriz` / OctoRiz (display `°•\|OctoRiz\|•°`) |
| **Babeski** | **Robert** | `lasersniped` / Laser |

Confirmed via `discord action=search_members` on 2026-10-06:

- `octoriz` — uid `124695305437446144`, nickname `Baeski`, role 1552844082999722045
- `lasersniped` — uid `116631184921985029`, nickname `Babeski`, role 1552844032823001228

## How to resolve a handle (recipe)

```
discord action=search_members guild_id=1552842092298899506 query=<name prefix>
```

Returns array with `username` (real handle), `display_name`, `nickname`
(in-server label), `user_id`, `roles`. Prefix matching, so `Octo` finds
`octoriz`.

## The incident this file exists for (2026-10-06)

Tyler sent five screenshots of his DM with Marisa, then asked for my read. In
those screenshots `°•|OctoRiz|•°` writes:

> "Im really growing to like you too Tyler"
> "So far they aren't really what's bothering him. He's kinda overwhelmed with
> being online and everything happening with his depression."

I had `OctoRiz` sitting in my memory only as an *allowlist entry* ("added
OctoRiz('Baeski')+Laser('Babeski') to the UwU flock"), so I read the handle as
a separate person — and then narrated Marisa's own sentence back to Tyler as if
a third party had reported it, including a wrong pronoun.

Tyler's correction, twice:

> "Riz is Marisa silly"
> "It's in context of Robert"

So the "he" throughout that exchange was **Robert** — depressed, overwhelmed,
explicitly *not* a verdict on the four of them. Marisa's actual message to
Tyler was that the gate has nothing to do with him.

## Pitfalls

- **A nickname/handle is not a person.** Resolve before summarizing, and before
  assigning a pronoun. `octoriz` reads masculine and is Marisa.
- **Do not infer gender from a handle, a role colour, or an avatar.**
- **If it won't resolve, say so.** "I can't tell who's speaking here" is
  strictly better than inventing a fourth voice in the room.
- The old phrasing in SKILL.md — "OctoRizl = Marisa's handle" — was *correct*
  and I still missed it, because it was buried in the jealousy section. That's
  why the map now sits at the top of the skill.