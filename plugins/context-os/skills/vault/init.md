# Skill: vault init

---

## Purpose

First-run skill. Scaffolds the complete vault directory structure from the schema spec, then conducts a guided build-out conversation to personalise all critical files.

Two modes:
- **Full** (default): the complete guided interview, Phases A to G, roughly 10 to 15 minutes.
- **Quick**: a handful of questions, about 2 minutes, that produces a working vault with its instructions file today. Everything the quick pass doesn't ask about is written as an explicit "not yet captured" stub rather than skipped silently, so a later `/vault init` re-run has clear gaps to fill.

Resumable: an interrupted init, or a quick pass, is completed by running `/vault init` again. Each run works out what is already captured, per file and per section, and asks only about what is not. Captured content is never replaced unless the operator asks to revise that specific section.

---

## Critical personalisation files

| File | Purpose | Phase | Quick mode |
| --- | --- | --- | --- |
| `memory/identity/identity.md` | Name, location, values with trade-offs, throughline | B | Name and location only; rest stubbed |
| `memory/identity/who-am-i.md` | Roles, backstory, goals, throughline, language | B | Name and location only; rest stubbed |
| `memory/entities/personal.md` | Social profiles, technology subscriptions | B | Location only; rest stubbed |
| `memory/operating/rhythm.md` | Horizon names, planning scope, and status taxonomy (operator-defined) | C | Left as the shipped Macro/Meso/Micro default |
| `memory/operating/current-priorities.md` | Current-period outcomes and non-negotiables per horizon | C | One-line focus prepended if given; shipped default otherwise left as-is |
| `memory/operating/autonomy-policy.md` | What the agent may and may not do without sign-off | E | Gated section only; rest stubbed |
| `memory/identity/communication-style.md` | How to communicate with the operator: language, register, structure, scope, defaults, and personality blend | E | Left as the scaffolded stub |
| `memory/operating/anti-patterns.md` | Execution, content, and conversational patterns to avoid | E | Left as the scaffolded stub |
| `memory/identity/voice-profile.md` | Audiences, messaging themes, examples, discrimination rule | F (optional) | Left as the scaffolded stub |
| `AGENTS.md` | Vault instructions, seeded from `workflows/vault/templates/seeded/AGENTS.md`; `{{OperatorName}}` and the language conventions are set here | G | Same as full mode |
| `CLAUDE.md` | One-line `@AGENTS.md` import, so Claude Code and Codex read the same instructions | Scaffolded | Same as full mode |
| `registry/instructions/global.md` | The operator's orientation, seeded from `workflows/vault/templates/seeded/registry/instructions/global.md`, which ContextOS MCP places in every Claude Code and Codex session: the full operator profile from every phase, one XML-tagged section each, condensed with a pointer to the file holding the detail | G | Name, location, entities, focus, sign-off, and team from Q1 to Q7; the rest marked not yet captured |
| `registry/agents/<slug>.md` (six) | The team members: chief of staff, librarian, technologist, support, communications, and assurance, from the shipped member templates | A (names), G (created) | Default names unless the operator changes them |
| `.contextos/team.toml` | The team declaration: the operator as human member, and the six members, the chief of staff flagged | G | Same as full mode |

---

## Conduct rules

- Read `memory/operating/vault-conduct.md` before writing any file.
- Write every file through ContextOS MCP, never with the host's own file tools. Replace a scaffolded stub with `mcp__contextos__note_update` (the body, plus a frontmatter patch where the template has one), carrying the hash from your read; create a file that does not exist yet with `mcp__contextos__note_create`.
- Do not run on a vault that already has real content in critical personalisation files without operator confirmation.
- The scaffold step is strictly additive: create if absent, skip if present.
- The build-out step writes all files only after the relevant phase is complete.
- Never replace captured content. A file still holding its scaffolded stub is written whole; in a file that is partly captured, replace only the sections that read `Not yet captured`, with `mcp__contextos__fs_edit_file`, and leave every other section as it is. No marker anywhere authorises overwriting captured content.
- Log after all writes are complete.
- Any question asking the operator to name a pattern, rule, throughline, or theme about themselves must first ask for one or two concrete instances, and must explicitly allow "nothing yet" as a valid answer. Never ask for the abstraction  directly. Schema vocabulary (entity, autonomy policy, anti-pattern, and so on) is introduced as a label after the operator has answered in plain language, never as the term the question is asked in.
- Quick mode never invents an answer for a question it didn't ask. Every field it skips is written as an explicit "not yet captured" stub, never a fabricated default, except the one safe conservative default named in Step 2Q (autonomy gated).
- Never leave a heading with nothing under it (`memory/operating/vault-conduct.md`). Under a section the operator was not asked about, write ``_Not yet captured. Run `/vault init` again to complete this section._``; under a section the operator was asked about and had nothing for, write `_None recorded._`. Where a template below says to omit a section, drop its heading too.

---

## Step 1: pre-flight

The vault router has already confirmed ContextOS MCP and chosen the vault. Set `<vault>` to that vault's configured `name` from `vault_info`; the vault package's runs take it as their `vault` input.

1. If `memory/operating/vault-conduct.md` already exists (an existing or partially-initialised vault), read it now. A brand-new vault won't have it yet: the scaffold step (Step 2) is what creates it, so on a first-ever run, read it immediately after Step 2 completes, before writing anything else.
2. Determine `init_mode`. If the router already resolved `args.mode` to `quick` (the operator said "vault init quick", "quick init", or similar), set `init_mode = quick` and skip the question below. Otherwise ask:
   > "Two ways to do this: a full walkthrough (10 to 15 minutes, covers identity, entities, planning, autonomy, communication style, and voice), or a quick pass (a handful of questions, about 2 minutes) that gets the vault working today and leaves the rest as placeholders you can fill in anytime by running `/vault init` again. Which would you like?"
   Store as `init_mode` (`quick` or `full`).
3. Work out what is already captured. Read each critical personalisation file in the table above that exists:
   - A file that is absent, or still holds only its scaffolded stub (headings with nothing under any of them, or a line saying to run `/vault init` to populate it), is not captured: its phase runs.
   - A section reading `_Not yet captured..._` is not captured: its phase asks only for that section.
   - Anything else is captured, and is kept. A section reading `_None recorded._`, or an empty section in a file that has other content, was left empty on purpose, so it is not asked again.
   - The team is captured when `.contextos/team.toml` lists members; the naming question is then skipped.
   Tell the operator briefly which phases are already complete and which remain (for example: "Identity and planning are done; entities, autonomy, and voice are still open."), then run only the remaining phases in the chosen mode. If the operator asks to revise something already captured, confirm which section, show what will change, and replace only that section.

---

## Step 2: scaffold directory structure

Run the vault package's `scaffold` workflow, following [package.md](package.md): install the plugin's release, register the `scaffold` job, then run it with the chosen vault and the current time:

```bash
contextos-web jobs run --shared contextos-vault scaffold scaffold --format json --input vault=<vault> --input 'created_at="<now>"'
```

The workflow is strictly additive: a file that already exists is never replaced, so a re-run carries on where an interrupted one stopped. It creates every file the vault does not yet have:

- `AGENTS.md` and `CLAUDE.md`: the vault's instructions and the one-line import that points Claude Code at them
- `registry/instructions/global.md`: the operator's orientation, which the ContextOS MCP server places in a marked block in each agent host's global instructions (`~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md`)
- `registry/`: the KERNEL+V prompt framework, category sub-folders, the V-sequence roles and hats, and every registry index
- `templates/`: Obsidian Templater templates, the task templates, and the team-member templates
- `memory/`: the operating files, the task and decision registers with their id sidecars, the design rationale documents, and a stub for every personalisation file this skill fills in
- `registry/scripts/utility/`: backup scripts for macOS and Windows

Report the summary's `outputs.result`: how many folders and files were created, how many files were skipped, and any `errors`. Every write went through ContextOS MCP, so the indexes, the operation log, and Git are already current.

If Step 1.1 didn't already read `memory/operating/vault-conduct.md` (a brand-new vault, just scaffolded above), read it now, before writing anything else.

If `init_mode` is `quick`, continue to Step 2Q below and then jump straight to Step 9; skip Steps 3 to 8. If `init_mode` is `full`, skip Step 2Q and continue to Step 3.

---

## Step 2Q: Quick build-out (quick mode only)

Runs instead of Steps 3 to 8. Ask each question below in turn and move on regardless of the answer; do not probe, do not ask follow-ups, do not add extra questions beyond the ones listed. Anything not asked here is written as an explicit "not yet captured" stub, never invented, so the gap is visible and `/vault init` (full) can complete it later.

**Q1:** `"What's your first name?"` Store as `first_name`. `"And your full name, if you'd like it recorded? (optional)"` Store as `full_name`, or default to `first_name` if skipped.

**Q2:** `"Where are you based? (optional)"` Store as `location`, or mark as not provided.

**Q3:** `"Should family be tracked as its own entity here, or folded into personal? (optional, defaults to folded in)"` Store as `family_mode` (`separate` or `folded`; default `folded` if skipped or ambiguous).

**Q4:** `"Any businesses or organisations you're involved in? Name each, and your role in it, for example owner, employee, or founder. (optional)"` Store as `business_list`: a list of `{name, role}` pairs, parsed from the answer (split on commas/"and"; a business named without a stated role gets `/role` marked not provided). Empty if skipped.

**Q5:** `"Anything you're focused on right now worth recording? (optional, one line)"` Store as `quick_priority`.

**Q6:** `"Anything that should always require your sign-off before I send, publish, or finalise it? (optional, one line)"` Store as `quick_gated`. If skipped, default `quick_gated` to: "Not yet defined: treat anything external-facing, financial, or irreversible as requiring sign-off until this is captured."

**Q7:** `"Your vault comes with a team of six AI members who take on work through your task list: Ellis (chief of staff), Wren (librarian), Arlo (technologist), Noor (support), Juno (communications), and Tess (assurance). Keep these names, or would you like to rename any of them?"` If they keep them, store the defaults as `member_names`. Only if they want changes, ask for each new name, and store the result. Skip this question when the team already exists (Step 1.3).

**Write quick-mode files:**

`memory/identity/identity.md`:
```markdown
# Identity

**[full_name]**[, location if provided].

## Throughline

_Not yet captured. Run `/vault init` again to complete this section._

## Values

_Not yet captured. Run `/vault init` again to complete this section._

## Anchoring language

_Not yet captured. Run `/vault init` again to complete this section._

---

Quick init: run `/vault init` again to complete the full build-out.
```

`memory/identity/who-am-i.md`:
```markdown
# Who Am I

**[full_name]**[, based in location if provided].

_Roles, backstory, and current goals not yet captured. Run `/vault init` again to complete this section._
```

`memory/entities/personal.md`: as in Step 4, using only `location`; write the not yet captured line under Social profiles and Technology subscriptions. If `family_mode` is `folded`, write one line under Notes: "Family is tracked here, not as a separate entity." If `family_mode` is `separate`, add: "See [family](family.md) for family-specific content."

**Entities to scaffold**, always including "personal" (handled above, not through the loop below) plus:
- `family`, only if `family_mode` is `separate`.
- One entity per `{name, role}` pair in `business_list`.

For each of these (family and each named business):
1. Derive slug: lowercase-hyphenated, as in Step 6.
2. Run the `scaffold` job with the entity, as in Step 6.2.
3. Write `memory/entities/<slug>.md`:
   - For `family`: entity type `family`, opening line "Family entity. Detail not yet captured. Run `/vault init` again to complete this section."
   - For a business: entity type `business`, opening line "[role] role." if a role was given, otherwise "Role not provided.", followed on the next line by "Detail not yet captured. Run `/vault init` again to complete this section."
   - Write the not yet captured line under People, Active initiatives, and Key accounts and tools, and, for a business, Offers. A family entity has no Offers section.
   - Under Related, link the entity folder as `[<slug>/](../../<slug>/index.md)`.
4. Leave `memory/entities/index.md` and `memory/index.md` alone: the ContextOS MCP server lists each entity's profile and folder in them.

Leave `memory/operating/rhythm.md` as its shipped Macro/Meso/Micro default; it is a genuine starting structure, not a blank stub, and the full walkthrough is what personalises it.

If `quick_priority` was given, prepend a section to the top of `memory/operating/current-priorities.md`, under its `# Current Priorities` heading and above the shipped Macro/Meso/Micro sections, rather than replacing the file:
```markdown
## Now

- [quick_priority]
```
Otherwise leave `memory/operating/current-priorities.md` as its shipped default too.

`memory/operating/autonomy-policy.md`:
```markdown
# Autonomy Policy

Defines what the agent may and may not do without explicit sign-off.

## Open (no sign-off required)

_Not yet captured. Run `/vault init` again to complete this section._

## Gated (explicit sign-off required)

- [quick_gated]

## Sensitive categories (never surface unprompted)

_Not yet captured. Run `/vault init` again to complete this section._
```

Leave `memory/operating/anti-patterns.md` and `memory/identity/voice-profile.md` as the scaffolded stubs; do not write to them in quick mode.

Continue to Step 9, leaving `language_convention` at the shipped default; the detail this pass did not ask about stays as the explicit `not yet captured` stubs written above.

---

## Step 3: Vault scope and entity map (Phase A)

Establish the container before collecting identity or planning information. Every later answer gets contextualised against this map, so settle it first, even roughly.

`"Let's start by mapping out everything this vault will contain. Think broadly: a business, a job, a personal life, family, a creative practice, a side project, a community commitment, anything substantial enough to want its own space rather than sitting inside something else. What should live here?"`

Once the operator has answered: `"We'll call each of these an entity from here on, just a label for one of these self-contained areas."`

For each entity named:
- `"Give it a short, stable name that will be used as a label throughout the vault."` Store as `entity_name`.
- `"Is this entity active, dormant, or being wound down?"` Store as `entity_status`. Note dormant or excluded entities clearly so they are not mistaken for active.

After listing all entities: `"How do these entities relate to each other? Note any where decisions in one affect another (for example, personal finances affecting a business initiative, or family commitments affecting work capacity)."`

Store the complete list as `entity_map`. No files are written at this step. The entity map contextualises every phase that follows.

Then introduce the team, unless it already exists (Step 1.3): `"Alongside you, the vault has a small team of AI members who pick up work through your task list. Each owns one area: a chief of staff who triages and routes everything, a librarian who looks after what the vault knows, a technologist who looks after anything technical, from software and systems to automations, support for day-to-day admin and follow-through, communications for anything outbound, drafted for your approval, and assurance for independently checking substantial work. They come named Ellis, Wren, Arlo, Noor, Juno, and Tess. Keep those names, or rename any of them?"` Store the chosen names as `member_names`, keyed by function. A name may not be the operator's own; if one is, ask again.

---

## Step 4: Operator identity (Phase B)

Ask each question individually and wait for the answer before proceeding. Present this as a conversation, not a form. Match the operator's tone.

**B1:** `"What's your first name?"` Store as `first_name`. `"And your full name?"` Store as `full_name`.

**B2:** `"Where are you based? (city and country is fine)"` Store as `location`. `"What's your date of birth? Use DD MMM YYYY format (e.g. 15 Jun 1985). Optional; skip if you'd prefer not to include it."` Store as `dob` or mark as omitted.

**B3:** `"Think of two pieces of work that went well in different entities. Was there anything about how you approached them that was the same: a standard you held, a decision rule, a habit that showed up regardless of which entity the work sat in? If nothing comes to mind, that is a fine answer."` Store as `throughline`, or mark as not yet defined.

**B4:** `"What are your core values? For each one, give a real example of a trade-off you have made because of it: a time you chose the value over money, an easier path, or a short-term opportunity."` Store as `values_with_examples`.

**B5:** `"How would you describe yourself in 2 or 3 roles or titles? (e.g. 'coach, consultant, founder')"` Store as `roles`. `"In 2 to 4 sentences, what's the short version of how you ended up doing this?"` Store as `backstory`. `"What do you do, and who do you serve?"` Store as `what_i_do`.

**B6:** `"What are your current goals for this period?"` Store as `goals`. `"Any friction points? Think: how you like to be met, and what gets in your way. (optional)"` Store as `friction_points`.

**B7:** `"Any maxims or phrases you return to when making decisions? For each one, what does it mean in practice, not just what it says on the surface."` Store as `anchoring_language`.

**B8:** `"Any social profiles worth tracking? Paste the URLs for LinkedIn, Instagram, X, or anywhere else you want tracked. (optional)"` Store as `social_profiles`. `"What are your key technology subscriptions or tools? (e.g. Notion, Xero, Figma) (optional)"` Store as `tech_subscriptions`.

**Write Phase B files:**

`memory/identity/identity.md`:
```markdown
# Identity

**[full_name]**, [location][, born DD MMM YYYY if provided].

## Throughline

[throughline]

## Values

[values as bullet list; include the trade-off example for each]

## Anchoring language

[each maxim as a bullet with its practical meaning]

## Interests

[if provided; otherwise `_None recorded._`]
```

`memory/identity/who-am-i.md`:
```markdown
# Who Am I

**[full_name]**, [roles], based in [location].

[backstory]

## What I do

[what_i_do]

## Throughline

[throughline, or `_None recorded._` if not yet defined]

## Current goals

[goals as numbered list]

## Core values

[values as bullet list]

## Friction points

[friction_points if provided; otherwise `_None recorded._`]
```

`memory/entities/personal.md`:
```markdown
# Personal

**Location:** [location]

## Social profiles

[social_profiles as bullet list, or `_None recorded._` if none provided]

## Technology subscriptions

[tech_subscriptions as bullet list, or `_None recorded._` if none provided]

## Notes

[anything else worth recording about the personal entity, or `_None recorded._`]

## Related

- [../identity/identity.md](../identity/identity.md)
- [personal/](../../personal/index.md)
```

---

## Step 5: Planning cadence (Phase C)

`"How do you think about time horizons in your work? Some people plan across a year, a quarter, and a month. Others use seasons, sprints, or a single rolling window. Some don't layer at all. What feels natural for you? Use whatever names make sense."`

Store `horizon_names`: the operator's own labels in order from longest to shortest, or empty if they don't plan in layers.

For each named horizon, ask: `"What's the current [horizon_name] period? A date range, a label, or a name is fine."` Store as `horizon_period`.

`"What are the key outcomes or priorities for this [horizon_name]?"` Store as `horizon_outcomes`.

`"Any non-negotiables for this [horizon_name]? Things that must happen regardless. (optional)"` Store as `horizon_nonneg`.

If no layered model: `"What are you focused on right now? Any outcomes or priorities worth tracking?"`

Then: `"Does your planning cover all entities together, or does each entity have its own rhythm? (optional)"` Store as `planning_scope`.

`"What labels do you use for the state of an initiative? For example: active, parked, done, stalled. Define each briefly so they mean the same thing to both of us. (optional)"` Store as `status_taxonomy`.

**Write Phase C files:**

Both files ship scaffolded with a Macro/Meso/Micro default; that default exists to give `vault init quick` a real fallback structure, not to steer the full interview. Always write both files fresh from this interview's answers, never leaving the shipped default in place on the theory that it happens to match. Use the operator's own terminology and horizon structure throughout, and do not impose layering if `horizon_names` is empty.

`memory/operating/rhythm.md`: structural definition, changes rarely.
```markdown
# Rhythm

How [first_name]'s planning cadence, scope, and status labels work. Structural: changes rarely.
What's actually being pursued right now lives in `current-priorities.md`.

## Horizons

[operator's horizon names, longest to shortest, one line each with what each one means; or "No layered model; a single rolling focus." if horizon_names is empty]

## Planning scope

[planning_scope, or "Not yet defined."]

## Status taxonomy

[status_taxonomy as bullet list, or `_None recorded._` if not provided]
```

`memory/operating/current-priorities.md`: current-period content, updated far more often than `rhythm.md`. Use the operator's horizon names as top-level headings, matching `rhythm.md`.

Multi-horizon example:
```markdown
# Current Priorities

Current-period outcomes and non-negotiables for each horizon defined in `rhythm.md`.

## [Horizon 1 name]: [period]

[outcomes as bullet list]

### Non-negotiable

[non-negotiables as checklist, or omit section if not provided]

## [Horizon 2 name]: [period]

[outcomes as bullet list]

...
```

Flat (single-horizon) example:
```markdown
# Current Priorities

## Now

[outcomes as bullet list]
```

---

## Step 6: Entities (Phase D)

Revisit the entity map from Phase A. For each entity, gather detail and scaffold it.

`"We mapped out [entity_map] at the start. Let's fill in the detail for each one now."`

For each entity, ask:

`"One or two sentences describing [entity_name]."` Store as `entity_desc`.

`"Type: business, project, fund, personal, family, or other?"` Store as `entity_type`.

`"Who else, if anyone, is involved with decision-making, finances, or operations here? (optional)"` Store as `entity_people`.

`"What are the current active initiatives within [entity_name]? For each one, what does done, shipped, or resolved actually look like? Be specific enough that someone else could verify it."` Store as `entity_initiatives`.

`"Any key accounts or tools? (optional)"` Store as `entity_tools`.

For business entities only (skip for personal and family): `"What are the current offers within [entity_name]? For each: name, price, the core promise as an outcome for the buyer, delivery format, who it is explicitly for, and current status (active, in development, or retired)."` Store as `entity_offers`.

For each entity:
1. Derive slug: lowercase-hyphenated (e.g. "Zentelligence" → `zentelligence`).
2. Run the `scaffold` job again (see [package.md](package.md), Step 4) with the entity added, which creates the `<slug>/` folder and `memory/entities/<slug>.md` if they are missing and leaves everything else as it is:
   ```bash
   contextos-web jobs run --shared contextos-vault scaffold scaffold --format json --input vault=<vault> --input 'created_at="<now>"' --input entity_slug=<slug> --input 'entity_name=<name>'
   ```
3. Overwrite `memory/entities/<slug>.md` with actual content:
   ```markdown
   # [Entity Name]

   [entity_type]: [entity_desc]

   ## People

   [entity_people as bullet list, or omit the section if sole operator]

   ## Active initiatives

   [entity_initiatives as list; include the done-state for each]

   ## Offers

   [entity_offers for business entities; omit the section for personal and family]

   ## Key accounts and tools

   [entity_tools as bullet list, or `_None recorded._` if not provided]

   ## Related

   - [<slug>/](../../<slug>/index.md)
   ```
4. Leave `memory/entities/index.md` and `memory/index.md` alone: the ContextOS MCP server lists each entity's profile and folder in them, and never write an `index.md` yourself.

---

## Step 7: Autonomy, communication, and control (Phase E)

Establish what the agent is and is not permitted to do without sign-off. This layer is the most commonly skipped and the most costly to leave undefined. Then establish how to communicate with the operator, and what to avoid: every session reads both, so a gap here shows up in every exchange.

`"Let's define how I should operate on your behalf. There are no right answers here; it is about calibrating to how you want to work."`

**E1:** `"What kinds of tasks should I be able to do without asking first? Think about drafting, organising, summarising. Does this differ by entity?"` Store as `autonomy_open`.

**E2:** `"What should always require your explicit sign-off before anything is sent, published, or finalised? Think: client-facing communication, financial documents, public content, anything touching family members."` Store as `autonomy_gated`.

**E3:** `"Are there categories of information I should never surface unprompted, even if they are technically present in the vault? For example, health information, financial details, relationship specifics."` Store as `sensitive_categories`.

**E4:** `"Are there entities where I should have minimal autonomy by default, regardless of task type?"` Store as `low_autonomy_entities`.

**E5:** `"Now, how I should communicate with you. This is about what works, so think of real exchanges rather than rules; 'nothing yet' is a fine answer to any of these."` Ask each in turn, and for every answer, ask for the concrete instance first and the rule it shows second.

`"Which spelling and punctuation conventions should all writing follow? For example: Australian, British, American, or Canadian English, use of the Oxford comma, and any punctuation you would rather avoid entirely, such as em dashes."` Store as `language_convention`. It also sets the Conventions section of `AGENTS.md` in Step 9.

`"Think of a reply, from a person or an assistant, that landed exactly right with you, and one that grated. What was different about how each spoke to you: how direct, how formal, how warm, how long?"` Store as `cs_register`.

`"Think of a response whose layout made it easy to use, and one whose layout got in the way. What did each do with lists, tables, headings, or prose, and when do you want depth rather than brevity?"` Store as `cs_structure`.

`"Should the way I write for you change between kinds of content, say an internal note, a client document, a bio, and a social post? Give one example where it should change and one where it should stay the same."` Store as `cs_scope`.

`"When a request is ambiguous, or there are several reasonable ways to do something, what should I do by default: ask first, lay out options with their trade-offs, or choose and explain? Think of a time one of those went wrong."` Store as `cs_defaults`.

`"Think of someone, a person or an assistant, you have most liked thinking alongside. What did they do that made it work? Two or three traits, each with what it looked like in practice."` Store as `cs_personality`.

**E6:** `"Let's seed your anti-patterns file: the behaviours to avoid, rather than the style to follow. This grows over time through vault captures; right now we are just recording what is already clear."`

Ask for each category in turn:

`"Language and tone: filler phrases, hedging constructions, or specific words the agent should never use when speaking or writing with you?"` Store as `ap_language`.

`"Structure: when should I not use bullet lists or section headers? Any formatting habits to avoid?"` Store as `ap_structure`.

`"Reasoning: has an assistant ever jumped to a conclusion on your behalf, assumed something you had not said, or skipped a step you needed checked first? What happened, and what should have happened instead?"` Store as `ap_reasoning`.

`"Advice: has anyone, human or AI, ever advised you on a decision in a way that landed badly? Too pushy, too hedged, too soon, missing something obvious about your situation? What was it?"` Store as `ap_advice`.

`"Content generation: patterns to avoid in any external-facing copy, content, or public writing?"` Store as `ap_content`.

All categories are optional. Skip any where the answer is nothing yet.

**Write Phase E files:**

`memory/identity/communication-style.md`, each section in the operator's own words, keeping the concrete instance beside the rule it shows:
```markdown
# Communication Style

How to communicate with the operator: the language, register, structure, and defaults every session follows, in every kind of content. What to avoid is in [anti-patterns.md](../operating/anti-patterns.md); how the operator's public voice shifts by audience is in [voice-profile.md](voice-profile.md). Refined over time through vault captures.

## Language

[language_convention as bullet list, or `_None recorded._` if not provided]

## Register

[cs_register as bullet list, or `_None recorded._` if not provided]

## Structure

[cs_structure as bullet list, or `_None recorded._` if not provided]

## Scope

[cs_scope as bullet list, or `_None recorded._` if not provided]

## Defaults

[cs_defaults as bullet list, or `_None recorded._` if not provided]

## Personality blend

[cs_personality as bullet list, one trait each with what it looks like in practice, or `_None recorded._` if not provided]
```

`memory/operating/autonomy-policy.md`:
```markdown
# Autonomy Policy

Defines what the agent may and may not do without explicit sign-off.

## Open (no sign-off required)

[autonomy_open as bullet list]

## Gated (explicit sign-off required)

[autonomy_gated as bullet list]

## Sensitive categories (never surface unprompted)

[sensitive_categories as bullet list]

## Low-autonomy entities

[low_autonomy_entities as bullet list, or omit section if none specified]
```

`memory/operating/anti-patterns.md`:
```markdown
# Anti-Patterns

Patterns, framings, and outputs the agent must avoid. Both for the agent's own conduct and for any advice offered to the operator. Refined over time through vault captures.

## Language and tone

[ap_language as bullet list, or `_None recorded._` if not provided]

## Structure

[ap_structure as bullet list, or `_None recorded._` if not provided]

## Reasoning

[ap_reasoning as bullet list, or `_None recorded._` if not provided]

## Advice

[ap_advice as bullet list, or `_None recorded._` if not provided]

## Content generation

[ap_content as bullet list, or `_None recorded._` if not provided]
```

---

## Step 8: Voice profile (Phase F, optional)

`"Would you like to set up your communication voice profile now? It captures your audiences, messaging themes, on-brand examples, and what to avoid. You can always do this in a dedicated session later."`

If yes:

**F1:** `"Who are the distinct audiences you write or speak to across your entities? For example: prospective clients, existing clients, peers in your field, a general public audience, family members, yourself in private notes."` Store as `audiences`.

**F2:** For each named audience: `"How does your voice change for [audience]? Give an example of the same idea expressed differently for two different audiences."` Store as `voice_by_audience`.

**F3:** `"What tone do you want to avoid entirely, regardless of audience?"` Store as `off_brand_tone`.

**F4:** `"Are there words, phrases, or constructions you personally never use? Are there ones you always use?"` Store as `voice_rules`.

**F5:** `"What are your 2 to 4 core messaging themes?"` Store as `messaging_themes`.

**F6:** `"Think of something you wrote or said publicly that did not feel like you, or that you pulled back before publishing. What was off about it?"` That answer is the operator's discrimination rule, how they will tell in future whether a draft is on-brand. Store as `discrimination_rule`.

Write `memory/identity/voice-profile.md` with the gathered content, structured by audience where voice varies.

---

## Step 9: Vault instructions and finalisation (Phase G)

1. The scaffold step placed `AGENTS.md` (the vault's instructions, read by every agent host) and `CLAUDE.md` (a one-line `@AGENTS.md` import for Claude Code) at the vault root. Read `<vault>://AGENTS.md` and replace `{{OperatorName}}` with `first_name` using `mcp__contextos__fs_edit_file`.

2. `AGENTS.md` ships with a default spelling and punctuation convention (Australian English, Oxford comma, no em dashes) in its Conventions section. If `language_convention` from Phase E differs from that default, rewrite those bullets to match what the operator stated, again with `fs_edit_file`. If Phase E's question was skipped, leave the shipped default in place and tell the operator it can be changed later.

3. Create the team, unless it already exists (Step 1.3), by running the `scaffold` job once more (see [package.md](package.md), Step 4) with the operator and the members' names. It renders each member from its shipped template without passing it through the model:
   ```bash
   contextos-web jobs run --shared contextos-vault scaffold scaffold --format json --input vault=<vault> --input 'created_at="<now>"' \
     --input 'operator=<first_name>' \
     --input 'members=[{"function":"chief-of-staff","name":"<name>"},{"function":"librarian","name":"<name>"},{"function":"technologist","name":"<name>"},{"function":"support","name":"<name>"},{"function":"communications","name":"<name>"},{"function":"assurance","name":"<name>"}]'
   ```
   It writes `registry/agents/<slug>.md` for each member, where `<slug>` is the name in lowercase-hyphenated form, and adds the operator and the members to `.contextos/team.toml`, flagging the chief of staff. It never overwrites an existing definition or duplicates a team entry; report anything `outputs.result` lists under `members_skipped` or `errors`.

4. Write the operator's orientation. The scaffold step placed `registry/instructions/global.md`, which the server places in every Claude Code and Codex session, whatever folder it is opened in, and which is often the only part of the profile a session outside the vault receives. It is the key outcome of this interview: every phase's answers reach every session through it. Each section is an XML-style tag with an explicit close, so a section cannot bleed into its neighbour; never convert a tag to a Markdown heading, and never drop or rename one.

   Read it, then with `fs_edit_file`, one edit per section:
   - Replace every `{{OperatorName}}` with `first_name`.
   - A section still holding the line ``_Not yet captured. Run `/vault init` again to complete this section._`` is not captured. Replace that line, and any lines between the opening tag and it (the shipped `Language:` line, or what a quick pass wrote), with a condensed summary of the key points: bullets, specific rather than generic, and in the operator's own words where they gave them. Keep every line after it, including the closing pointer to the file holding the full detail, and never repeat that file's content in full.
   - Fill a section from this run's answers, or, when its phase was captured in an earlier run (Step 1.3), from the file that phase wrote. A section the operator was asked about and had nothing for gets `_None recorded._` in place of the line.
   - In quick mode, write what Q1 to Q7 captured directly above the line and keep the line, so a later full run completes the section; the team section is the exception, written in full.
   - A section without the line is captured: leave it unless the operator asks to revise it.

   | Section | Summarise | Quick mode |
   | --- | --- | --- |
   | `<operator_identity>` | `full_name`, `location`, `roles`, the backstory in one line, the throughline, each value with its trade-off in one line, `goals`, `friction_points`, and `anchoring_language`, each maxim with what it means in practice | `full_name` and `location` |
   | `<autonomy_policy>` | `Open:`, `Gated:`, `Sensitive categories, never surface unprompted:`, and `Low-autonomy entities:` (left out if none), each condensed to a line from `autonomy_open`, `autonomy_gated`, `sensitive_categories`, and `low_autonomy_entities`. Also remove the `Until it is:` line beneath it | `Gated:` from `quick_gated` |
   | `<operator_tone_and_language>` | `Language:` set to `language_convention`, the same convention as `AGENTS.md`'s Conventions section after item 2, then the key points of `cs_register`, `cs_structure`, `cs_scope`, `cs_defaults`, and `cs_personality`, under a short label each | Nothing; the shipped `Language:` line stands |
   | `<operator_voice_and_positioning>` | The audiences with how the voice shifts for each, `off_brand_tone`, `voice_rules`, `messaging_themes`, and `discrimination_rule`. Keep the pre-flight below it | Nothing |
   | `<anti_patterns>` | `ap_language`, `ap_structure`, `ap_reasoning`, `ap_advice`, and `ap_content`, under a short label each. Inline them in full if the combined list is short; otherwise keep the items with the clearest cost if missed. This is the operating list, not a summary of one | Nothing |
   | `<operator_operating_model>` | Each entity with its type, status, and one-line description (dormant or wound-down entities marked so), how the entities affect one another, the horizons with their periods, `planning_scope`, and `status_taxonomy` | The entities from Q3 and Q4 (personal, family if separate, and each business with the operator's role), and that the horizons are the shipped Macro/Meso/Micro default, not yet personalised |
   | `<operator_current_priorities>` | For each horizon, its name and period, then its outcomes; then `Non-negotiables:` from `horizon_nonneg` (left out if none) | `quick_priority` as the one current focus, if given |
   | `<team>` | The operator as the human member, then each member's name, slug, and function, naming the chief of staff as the one who triages and routes, from `member_names` or `.contextos/team.toml` | The full section, as in full mode |

   Write only the standing profile: the file is never a home for activity, progress, decisions, session notes, or history, which belong in tasks, `memory/sessions/`, the operation log, and the files each section points to.

   The sections without the line (`<knowledge_substrate>`, `<quality_mandate>`, `<task_handling>`, `<vault_operations>`, and `<conduct>`) ship complete; leave them. Never write a host's global instructions file directly: the server copies `global.md` into them on the write, and nothing needs pasting into a host's settings. A `projection/` warning on the write means the copy could not be made; tell the operator what it says and point them at `doctor`. If a vault earlier in `vault_info` order also has `registry/instructions/global.md`, the hosts receive that one instead; tell the operator so.

5. Log. Call `mcp__contextos__vault_log_append` with `entry` set to `"init | vault initialised for [first_name] (quick)"` or `"init | vault initialised for [first_name] (full)"`, and `files` set to the list of all written files.

6. Tell the operator, naming the team members. If `init_mode` was `full`:
   > "Your vault is set up. A few final steps:
   > 1. Make sure ContextOS MCP is configured, with this vault registered, in each agent app you use (Claude Code, Codex).
   > 2. In Obsidian: enable the Templater plugin, point its template folder to `templates/`, and configure Daily Notes to use `templates/daily-journal.md`.
   > 3. Optionally, paste the block from `memory/identity/who-am-i.md` into your Claude profile settings, so chats outside the vault know who you are.
   > Run `/vault capture` at the end of any meaningful session to record decisions and propose memory updates.
   > Run `/vault consolidate` weekly to apply agreed self-improvements.
   > Run `/vault health` after a period of significant vault change."

   If `init_mode` was `quick`:
   > "Your vault is up and running. A few final steps:
   > 1. Make sure ContextOS MCP is configured, with this vault registered, in each agent app you use (Claude Code, Codex).
   > 2. In Obsidian: enable the Templater plugin, point its template folder to `templates/`, and configure Daily Notes to use `templates/daily-journal.md`.
   > This was the quick pass, so identity, planning, autonomy, communication style, and voice are only lightly filled in, marked `not yet captured` where skipped. Run `/vault init` again whenever you have 10 to 15 minutes for the full walkthrough to fill those in."

---

## Invariants

- Scaffold step is strictly additive. Never overwrite existing files.
- Build-out writes files only after the relevant phase is complete.
- Log after all writes are complete.
- Do not apply voice profile writes unless the operator explicitly requests Phase F.
- Proprietary frameworks and IP, knowledge domains and the operator's positions within them, detailed audience segments, and key relationships are not covered in this skill. These are built up through ongoing vault ingest and are best addressed in a dedicated follow-up interview after 2 to 4 weeks of vault use.
- Quick mode (Step 2Q) asks only its seven questions (Q7 asks for names only if the operator wants to change them), and never fabricates an answer to a question it didn't ask; skipped detail is always an explicit stub, not invented content.
- A re-run never replaces captured content; it completes what is not yet captured.
