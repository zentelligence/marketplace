# Skill: vault init

---

## Purpose

First-run skill. Scaffolds the complete vault directory structure from the schema spec, then conducts a guided build-out conversation to personalise all critical files.

Idempotent: existing files are never overwritten by the scaffold step. The build-out always writes content to section-stub files regardless of prior state, so `vault init` can be re-run to complete an interrupted build-out.

---

## Triggers

```
vault init | initialise vault | initialize vault | init vault
```

---

## Tools required

`Read`, `Write`, `Edit`, `Bash`

---

## Critical personalisation files

| File | Purpose | Phase |
| --- | --- | --- |
| `memory/identity/identity.md` | Name, location, values with trade-offs, throughline | B |
| `memory/identity/who-am-i.md` | Roles, backstory, goals, throughline, language | B |
| `memory/entities/personal.md` | Social profiles, technology subscriptions | B |
| `memory/operating/current-priorities.md` | Planning horizons and priorities (operator-defined) | C |
| `memory/entities/index.md` | Entity registry (updated with real entity names) | D |
| `memory/index.md` | Memory master index (updated with real entity names) | D |
| `memory/operating/autonomy-policy.md` | What the agent may and may not do without sign-off | E |
| `memory/operating/anti-patterns.md` | Execution, content, and conversational patterns to avoid | E |
| `memory/identity/voice-profile.md` | Audiences, messaging themes, examples, discrimination rule | F (optional) |
| `memory/operating/global-instructions.md` | Comprehensive, self-contained Cowork paste block: structure, tone, autonomy, anti-patterns, priorities | G |
| `CLAUDE.md` | Copied from `scaffold/COWORK.md`, then `{{OperatorName}}` replaced with operator's first name | G |

---

## Conduct rules

- Read `memory/operating/vault-conduct.md` before writing any file.
- Do not run on a vault that already has real content in critical personalisation files without operator confirmation.
- The scaffold step is strictly additive: create if absent, skip if present.
- The build-out step writes all files only after the relevant phase is complete.
- Log after all writes are complete.
- Any question asking the operator to name a pattern, rule, throughline, or theme about themselves must first ask for one or two concrete instances, and must explicitly allow "nothing yet" as a valid answer. Never ask for the abstraction  directly. Schema vocabulary (entity, autonomy policy, anti-pattern, and so on) is introduced as a label after the operator has answered in plain language, never as the term the question is asked in.

---

## Step 1: pre-flight

1. Read `memory/operating/vault-conduct.md`.
2. Check whether the vault has already been initialised by inspecting `memory/identity/identity.md`. If it contains real content (not section stubs), warn the operator and ask for confirmation before proceeding.
3. Confirm the vault's absolute path. Ask:
   > "What is the absolute path to this vault on your machine? (e.g. `/home/name/vault`
   > or `C:\Users\Name\Obsidian\MyVault`)"
   Store as `vault_path`.

---

## Step 2: scaffold directory structure

Run the scaffold script to create all required directories and stub files. This step always runs as a script: its idempotent, interview-driven scaffolding logic has no MCP equivalent.

```bash
session-start >/dev/null 2>&1
source "${TMPDIR:-/tmp}/plugin-data.env" 2>/dev/null
python $CONTEXT_OS_PLUGIN_ROOT/scripts/vault_scaffold.py --vault-root <vault_path>
```

The script is idempotent: existing files are not overwritten. In addition to creating directory structure and stub indexes, it seeds the vault with plugin-provided files:

- `registry/` — KERNEL+V prompt framework, category sub-folders, and role and skills indexes
- `templates/` — Obsidian Templater templates (daily journal, unique note)
- `memory/designs/` — design rationale documents
- `scripts/utility/` — backup scripts for macOS and Windows

Review the output to confirm what was created or skipped.

---

## Step 3: Vault scope and entity map (Phase A)

Establish the container before collecting identity or planning information. Every later answer gets contextualised against this map, so settle it first, even roughly.

`"Let's start by mapping out everything this vault will contain. Think broadly: a business, a job, a personal life, family, a creative practice, a side project, a community commitment, anything substantial enough to want its own space rather than sitting inside something else. What should live here?"`

Once the operator has answered: `"We'll call each of these an entity from here on, just a label for one of these self-contained areas."`

For each entity named:
- `"Give it a short, stable name that will be used as a label throughout the vault."` Store as `entity_name`.
- `"Is this entity active, dormant, or being wound down?"` Store as `entity_status`. Note dormant or excluded entities clearly so they are not mistaken for active.
- `"Is this entity more sensitive than the others by default? For example, a family entity may warrant more caution than a business one."` Store as `entity_sensitivity`.

After listing all entities: `"How do these entities relate to each other? Note any where decisions in one affect another (for example, personal finances affecting a business initiative, or family commitments affecting work capacity)."`

Store the complete list as `entity_map`. No files are written at this step. The entity map contextualises every phase that follows.

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

[if provided; otherwise omit section body]
```

`memory/identity/who-am-i.md`:
```markdown
# Who Am I

**[full_name]**, [roles], based in [location].

[backstory]

## What I do

[what_i_do]

## Throughline

[throughline, or omit section body if not yet defined]

## Current goals

[goals as numbered list]

## Core values

[values as bullet list]

## Friction points

[friction_points if provided; otherwise omit section body]
```

`memory/entities/personal.md`:
```markdown
# Personal

**Location:** [location]

## Social profiles

[social_profiles as bullet list, or omit section body if none provided]

## Technology subscriptions

[tech_subscriptions as bullet list, or omit section body if none provided]

## Notes

## Related

- [../identity/identity.md](../identity/identity.md)
- [personal/](personal/index.md)
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

`memory/operating/current-priorities.md`: Write using the operator's own terminology and horizon structure. Do not impose a fixed template. Use their horizon names as top-level headings.

Multi-horizon example:
```markdown
# Current Priorities

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

If a status taxonomy was provided, append:
```markdown
## Status taxonomy

[status labels and definitions as bullet list]
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
2. Run scaffold script with entity args:
   ```bash
   python scripts/vault_scaffold.py --vault-root <vault_path> --entity-slug <slug> --entity-name "<name>"
   ```
3. Overwrite `memory/entities/<slug>.md` with actual content:
   ```markdown
   # [Entity Name]

   [entity_type]: [entity_desc]

   ## People

   [entity_people as bullet list, or omit if sole operator]

   ## Active initiatives

   [entity_initiatives as list; include the done-state for each]

   ## Offers

   [entity_offers for business entities; omit for personal and family]

   ## Key accounts and tools

   [entity_tools as bullet list, or omit if not provided]

   ## Related

   - [<entity>/](<entity>/index.md)
   ```
4. Rewrite `memory/entities/index.md` with a row for each entity (including self).
5. Rewrite `memory/index.md` with the entities row updated to list actual entity names.

---

## Step 7: Autonomy and control (Phase E)

Establish what the agent is and is not permitted to do without sign-off. This layer is the most commonly skipped and the most costly to leave undefined.

`"Let's define how I should operate on your behalf. There are no right answers here; it is about calibrating to how you want to work."`

**E1:** `"What kinds of tasks should I be able to do without asking first? Think about drafting, organising, summarising, updating internal logs. Does this differ by entity?"` Store as `autonomy_open`.

**E2:** `"What should always require your explicit sign-off before anything is sent, published, or finalised? Think: client-facing communication, financial documents, public content, anything touching family members."` Store as `autonomy_gated`.

**E3:** `"Are there categories of information I should never surface unprompted, even if they are technically present in the vault? For example, health information, financial details, relationship specifics."` Store as `sensitive_categories`.

**E4:** `"Are there entities where I should have minimal autonomy by default, regardless of task type?"` Store as `low_autonomy_entities`.

**E5:** `"Let's seed your anti-patterns file. This grows over time through vault captures;  right now we are just recording what is already clear."`

`"Which spelling and punctuation conventions should vault writing follow? For example: Australian, British, American, or Canadian English, use of the Oxford comma, and any punctuation you would rather avoid entirely, such as em dashes."` Store as `language_convention`. This is not written to a file at this step; it is used directly in Step 9 to template `CLAUDE.md`'s Conventions section and the Global Instructions tone section.

Ask for each remaining category in turn:

`"Language and tone: filler phrases, hedging constructions, or specific words the agent should never use when speaking or writing with you?"` Store as `ap_language`.

`"Structure: when should I not use bullet lists or section headers? Any formatting habits to avoid?"` Store as `ap_structure`.

`"Reasoning: has an assistant ever jumped to a conclusion on your behalf, assumed something you had not said, or skipped a step you needed checked first? What happened, and what should have happened instead?"` Store as `ap_reasoning`.

`"Advice: has anyone, human or AI, ever advised you on a decision in a way that landed badly? Too pushy, too hedged, too soon, missing something obvious about your situation? What was it?"` Store as `ap_advice`.

`"Content generation: patterns to avoid in any external-facing copy, content, or public writing?"` Store as `ap_content`.

All categories are optional. Skip any where the answer is nothing yet.

**Write Phase E files:**

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

[ap_language as bullet list, or omit section body if not provided]

## Structure

[ap_structure as bullet list, or omit section body if not provided]

## Reasoning

[ap_reasoning as bullet list, or omit section body if not provided]

## Advice

[ap_advice as bullet list, or omit section body if not provided]

## Content generation

[ap_content as bullet list, or omit section body if not provided]
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

## Step 9: Path binding and finalisation (Phase G)

1. If `<vault_path>/CLAUDE.md` does not already exist, copy it from `$CONTEXT_OS_PLUGIN_ROOT/scaffold/COWORK.md`. Replace `{{OperatorName}}` with `first_name`.

2. `CLAUDE.md` ships with a default spelling and punctuation convention (Australian English, Oxford comma, no em dashes) in its Conventions section. If `language_convention` from Phase E differs from that default, rewrite those two bullets to match what the operator stated. If Phase E's question was skipped, leave the shipped default in place and tell the operator it can be changed later.

3. Generate the Global Instructions paste block. Cowork has no automatic equivalent of Claude Code's project `CLAUDE.md` load: a Cowork session's only guaranteed startup context is whatever is pasted into Global Instructions. Treat this block as self-contained.

   Do not use `@`-prefixed file references anywhere in it; Cowork does not expand them. An explicit "read this file first" instruction is not a reliable substitute either, recent changes mean that kind of directive is often not honoured until specifically re-prompted mid-session, by which point a response has usually already been given    without the missing context. File paths in this block are soft references for elaboration only, never the delivery mechanism for anything the block depends on. The field has a practical ceiling of roughly 200 lines; a few extra lines of tone or autonomy content is worth it against the cost of a silent gap discovered mid-session and the rework it causes, but stay condensed within that ceiling.

   Assemble the block from every phase of this interview, not autonomy alone. Where a phase was skipped, say so explicitly in that section rather than omitting it silently, so the gap stays visible in the block itself.

   Wrap each major section in an XML-style tag rather than a markdown header. A header opens a section but never closes it, the next header is the only signal that the previous one ended; a tag has an explicit close, which gives the model a bounded unit to hold onto rather than an open-ended stream. This block has no fallback if a section's content is misread or bleeds into its neighbour, so use the more explicit structure:

   ```
   ContextOS vault. Root: <vault_path>. All paths below are relative to this root.
   Areas tracked: [entity_name (entity_status), entity_name (entity_status), ...].

   <vault_structure>
   memory/ is agent-owned content, start at memory/index.md. 
   memory/wiki/ is compiled and cited knowledge. 
   memory/raw/ and memory/research/ are immutable once written.
   memory/log/ is an append-only operations log. 
   inbox/, processed/, and outbox/ are operator material, never cite it directly. 
   registry/ holds prompt, role, hat, agent and skill definitions. Naming is lowercase-hyphenated; every folder has an index.md.
   Full schema: CLAUDE.md and memory/operating/vault-conduct.md.
   </vault_structure>

   <tone_and_language>
   [language_convention, condensed. ap_language, as a bullet list. If both were skipped: "No language or tone constraints captured yet; ask before assuming any."]
   </tone_and_language>

   <autonomy_policy>
   Open (no sign-off required): [autonomy_open, condensed to one line]
   Gated (sign-off required): [autonomy_gated, condensed to one line]
   Sensitive categories, never surface unprompted: [sensitive_categories, condensed]
   Low-autonomy areas: [low_autonomy_entities, condensed, or omit]
   Edge cases beyond this summary: memory/operating/autonomy-policy.md
   </autonomy_policy>

   <anti_patterns>
   [ap_language, ap_structure, ap_reasoning, ap_advice, ap_content: inline in full if the combined list is short, otherwise condense to the items with the clearest cost if missed. This is the operating list, not a summary of one.]
   </anti_patterns>

   <current_priorities>
   [top horizon name and period]: [outcomes, condensed]
   Non-negotiables: [horizon_nonneg, condensed, or omit if none]
   </current_priorities>

   <operations>
   vault ingest | vault research | vault query | vault capture | vault consolidate |
   vault lint | vault distil-transcript | vault log <entry> | vault update
   </operations>

   <session_start>
   Handled automatically by `scripts/session-start` which scans `$HOME/mnt/.remote-plugins/` and adds the resulting plugin name-to-path map to context. No manual lookup needed. 
   </session_start>

   <working_conduct>
   If a file or folder cannot be read due to missing access, request access immediately before retrying. Do not proceed on partial context. Use `vault query` for content questions rather than walking memory/wiki/ directly.
   </working_conduct>
   ```

   Write to `memory/operating/global-instructions.md`.

4. Log. If MCP is available (see the vault router's MCP awareness section), call `mcp__contextos__vault_log_append` with `entry: "init | vault initialised for [first_name]"` and `files` set to the list of all written files. Otherwise,    append to `memory/log/YYYY/MM/YYYY-MM-DD.md`:
   ```
  HH:MM | agent | init | vault initialised for [first_name] | files: [list of all written files]
   ```

5. Tell the operator:
   > "Your vault is set up. A few final steps:
   > 1. Paste the block from `memory/identity/who-am-i.md` into Claude Settings, General, Instructions for Claude.
   > 2. Paste the block from `memory/operating/global-instructions.md` into Cowork Settings, Edit Global Instructions on each device.
   > 3. In Obsidian: enable the Templater plugin, point its template folder to `templates/`, and configure Daily Notes to use `templates/daily-journal.md`.
   > Run `vault capture` at the end of any meaningful session to record decisions
   > and propose memory updates.
   > Run `vault consolidate` weekly to apply agreed self-improvements.
   > Run `vault lint` after a period of significant vault change as a health check"

---

## Invariants

- Scaffold step is strictly additive. Never overwrite existing files.
- Build-out writes files only after the relevant phase is complete.
- Log after all writes are complete.
- Do not apply voice profile writes unless the operator explicitly requests Phase F.
- Proprietary frameworks and IP, knowledge domains and the operator's positions within them, detailed audience segments, and key relationships are not covered in this skill. These are built up through ongoing vault ingest and are best addressed in a dedicated follow-up interview after 2 to 4 weeks of vault use.
