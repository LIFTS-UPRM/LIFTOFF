## Ambiguity Score: **7.5 / 10**
## Feasibility Score: **4.5 / 10**

The architecture and data models are solid — that work is good. The scores are dragged down by a small number of high-impact gaps that affect almost every other decision. Here's what's driving them.

---

### What's driving the ambiguity

| # | Gap | Impact |
|---|-----|--------|
| 1 | **Hermes is never defined technically** — "Hermes Agent Runtime" appears dozens of times but nowhere says: is this Claude? GPT-4? A custom agent framework? The current codebase uses OpenAI via `/chat`. The TDD lists "Browser Access" and "Terminal Access" for Hermes — that's a completely different class of system than a chat endpoint. | Blocks Phases 3–7 |
| 2 | **Auth is unresolved** — 3 options listed (simple login, institutional OAuth, Supabase Auth). The frontend already has a Microsoft SSO button that currently does nothing. | Blocks every role-gated feature |
| 3 | **Telemetry source is undefined** — What hardware sends data during a live flight? APRS? Raspberry Pi over cellular? LoRa? The telemetry schema fields are defined but nothing says where they come from in real operations. | Blocks Phase 2 |
| 4 | **Obsidian vault access model** — "local vault sync" — who runs the sync, from what machine, how often? For a web platform this needs a concrete answer. | Blocks Phase 4 |
| 5 | **Skill execution format** — Skills have "Execution Logic" listed as a field but what is it stored as? A prompt template? Python code? JSON workflow steps? | Blocks Phase 7 |

---

### What's driving the feasibility risk

The biggest feasibility risk isn't technical — it's scope. The MVP as written includes mission CRUD, live telemetry WebSockets, knowledge ingestion from two sources, vector search, a full data cleaning pipeline, 7 artifact types, role-based auth, Hermes tool permission enforcement, skill execution, AND a learned skill system. For most student teams that's 18–24 months of work, not a semester MVP.

The second risk: if "Hermes" means a full agentic runtime with browser + terminal tools, the security and sandboxing requirements alone become a major sub-project.

---

### Questions (highest impact first)

**About Hermes:**

1. What is Hermes, technically? Is it the current OpenAI `/chat` endpoint with more tools added, or is it a separate agent framework (e.g., Claude Code, a LangGraph agent, something custom)? The "Browser Access" and "Terminal Access" in the TDD suggest something much larger than what exists today.

2. Does Hermes need browser and terminal access for MVP, or is that Phase 2+? If it's MVP, what's the concrete use case that requires it?

**About scope and team:**

3. How many people are actively building STRATOS (not using it — building it), and what's the target delivery timeline for the MVP?

4. If you had to ship ONE pillar first — Pre-Flight, Flight Operations, Post-Flight, or Knowledge/Hermes — which one delivers the most value to LIFTS right now?

**About telemetry:**

5. What hardware does LIFTS currently use during a live flight to send position/sensor data? (e.g., APRS tracker, Raspberry Pi + cellular, LoRa radio, something else?) This determines the entire telemetry ingestion design.

6. Do you have an example of actual telemetry data from a past LIFTS flight — even a CSV — so the schema can be validated against real data?

**About knowledge sources:**

7. Is the Obsidian vault on someone's personal machine, a shared network drive, or already synced somewhere accessible? How does the backend reach it?

8. For SharePoint: is this UPRM institutional SharePoint, or a LIFTS-managed SharePoint? Do you have API access today, or is manual export the only option right now?

**About auth:**

9. Should login use the Microsoft SSO button already in the UI (institutional UPRM accounts via Azure AD), or is simpler email/password auth acceptable for MVP?

**About the skills system:**

10. Can you describe one concrete skill that Hermes should be able to execute and reuse today — what triggers it, what it does, what it outputs? This will anchor the skill format decision.