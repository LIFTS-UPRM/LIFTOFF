# Stratos Chat Continuation Roadmap

Date: 2026-05-15

## Executive Recommendation

Do not start with a full OpenAI Agents SDK rewrite. The best tradeoff for Stratos is a staged path:

1. Add server-owned Stratos conversation state first, modeled as a runtime-neutral event ledger.
2. Add context assembly, rolling summaries, trusted tool-result summaries, and persisted chat UI/search.
3. Migrate the model primitive from Chat Completions to Responses API when state assembly is testable.
4. Pilot the OpenAI Agents SDK only after Stratos has durable sessions, evals, and clear tool-continuity rules.

This gets the biggest user-visible win quickly: chats can continue after the frontend session or prompt window is too large. It also avoids throwing away the current safety work around untrusted client history before there is a replacement state model. The key architectural guardrail is that local Stratos events remain authoritative while OpenAI runtime IDs, traces, conversations, and SDK sessions are linked projections.

## Current Stratos Architecture

Stratos currently uses a manual chat runtime:

- The frontend stores messages in React state in `frontend/src/app/chat/page.tsx` and sends prior messages to the backend on each turn.
- `frontend/src/lib/chatApi.ts` serializes `message` plus mapped `history`.
- `backend/app/schemas.py` caps history to 30 items, with 8,000 characters per message and 512 KiB per request body.
- `backend/app/main.py` constructs a Chat Completions message list, injects sanitized client history, calls `client.chat.completions.create(...)`, then manually loops over tool calls.
- `backend/llm.py` owns OpenAI tool schemas, the STRATOS system prompt, and direct dispatch to weather, airspace, and SondeHub tools.
- `README.md` explicitly says client-supplied history is untrusted and that future trusted tool continuity must come from server-owned state.

That design is healthy for the current scale. It is intentionally defensive. The context-limit problem appears because the only conversation memory is client replay plus recent request payloads. Once the conversation grows, Stratos either sends too much, truncates too much, or loses details.

## What The Agents SDK Would Change

OpenAI describes the Agents SDK as the right path when the application owns orchestration, tool execution, approvals, and state. It supports code-first agents, tool use, handoffs, streaming, sessions, and tracing. Official docs also show four continuation strategies: app-owned history, SDK session, OpenAI Conversation ID, or `previous_response_id`.

Changing Stratos to the Agents SDK would require:

- Add `openai-agents` to backend dependencies.
- Create a STRATOS mission agent with the current system prompt from `backend/llm.py`.
- Convert the current tool schemas into SDK function tools or connect the existing MCP servers through SDK-managed MCP.
- Replace the manual loop in `backend/app/main.py` with `Runner.run(...)` / `Runner.run_streamed(...)`.
- Persist a session or continuation key per Stratos conversation.
- Extract tool-call records, final output, usage, trace IDs, and trajectory artifacts from SDK run results.
- Preserve current prompt-injection boundaries: client history, retrieved docs, and tool outputs must remain untrusted unless created by server state.
- Add tests around SDK tool routing, duplicate tool prevention, timeouts, and server-owned tool history.

## Benefits Over Current Setup

The SDK would give Stratos:

- A maintained runner loop instead of hand-written model/tool iteration.
- Built-in continuation surfaces: `history`, sessions, Conversation IDs, and `previous_response_id`.
- Handoffs for future specialists such as Weather Analyst, Trajectory Analyst, Airspace Reviewer, and Mission Checklist Agent.
- Tracing for model calls, tool calls, handoffs, guardrails, and custom spans.
- Streaming and resumable state for interrupted or approval-gated runs.
- Cleaner integration with SDK-managed MCP if Stratos expands its tool system.

The SDK does not automatically solve all context problems:

- Context windows still apply.
- OpenAI docs say previous inputs in a chained `previous_response_id` conversation are still billed as input tokens.
- If Stratos uses OpenAI Conversations, those items may persist without the same 30-day response TTL, so data governance must be a conscious decision.
- Stratos still needs local search, UI history, mission scoping, audit records, and trusted tool ledgers.

## OpenAI API/SDK Findings

Official documentation says Responses is the recommended API primitive for new projects and supports stateful, tool-using interactions. It also notes that Chat Completions remains supported, but conversation state is managed manually there.

Useful continuation mechanisms:

- Responses with `previous_response_id`: lightest server-managed continuation, but still bills previous input tokens.
- Conversations API: durable server-managed conversation object that stores messages, tool calls, tool outputs, and other items.
- Responses `context_management`: can trigger compaction at a token threshold.
- `/responses/compact`: returns compacted items, including opaque encrypted compaction content.
- Agents SDK sessions: app-controlled persistent chat state and resumable runs.
- Agents SDK tracing: structured visibility into model calls, tool calls, handoffs, guardrails, and custom spans.

Important cost notes:

- As of the current OpenAI pricing page, `gpt-5.5` standard pricing is listed at $5 input / $0.50 cached input / $30 output per 1M short-context tokens, while `gpt-5.4-mini` is much cheaper at $0.75 input / $0.075 cached input / $4.50 output per 1M tokens.
- OpenAI cost guidance recommends reducing requests, minimizing tokens, and selecting smaller models where quality remains acceptable.
- For Stratos, the biggest cost lever is not only model choice; it is reducing repeated history, summarizing large tool outputs, and keeping full artifacts out of the model prompt.

## Staged Roadmap

### Stage 0: Baseline And Token Budget

Effort: 0.5-1 day.

Add durable metrics before changing runtime:

- Prompt/input token estimate per turn.
- Number of history messages sent.
- Tool schema payload size.
- Tool result payload size.
- Model latency and total request latency.
- Tool-call count and selected tool group.
- Whether a trajectory artifact was produced.

Why first: Stratos already optimized normal chat by routing tool schemas only when needed. Keep that discipline and make future changes measurable.

### Stage 1: Server-Owned Conversation Store

Effort: 3-5 days for an MVP.

Add backend-owned persistence as an append-only event ledger plus read models:

- Conversation read model: id, mission_id, title, created_at, updated_at.
- Message read model: conversation_id, role, content, created_at, source/trust metadata.
- Trusted tool-call read model: server-observed calls with args, status, latency, and result reference.
- Tool result summaries: compact model-facing summaries.
- Memory snapshots: rolling mission summary, pinned facts, decisions, unresolved questions.
- Event ledger: `user_message_received`, `assistant_message_created`, `model_tool_call_requested`, `tool_call_started`, `tool_call_completed`, `tool_call_failed`, `artifact_created`, `summary_created`, `fact_pinned`, `fact_retracted`, and `runtime_trace_linked`.

Change `/chat` to accept `conversation_id` plus the current message. Keep `history` temporarily for compatibility, but stop relying on it as the primary source of truth.

Also add turn ordering and retry safety:

- `turn_id`.
- `client_request_id`.
- Append sequence.
- Idempotency key for tool jobs.
- Stale conversation handling.
- Duplicate-send and reload behavior.

Frontend changes:

- Sidebar shows persisted chats instead of "No chats".
- New chat creates a server conversation.
- Search uses persisted messages/summaries.
- Reloading the page restores the conversation.

This stage solves the immediate user problem without changing the model API.

Important split: persisted transcript, audit ledger, model context, search index, and pinned mission facts should be separate projections. A saved assistant message is not automatically safe or useful memory for the next model call.

### Stage 2: Context Assembly And Memory Policy

Effort: 4-7 days.

Create a deterministic context builder:

- Recent N messages.
- Rolling mission summary.
- Pinned operational facts.
- Active mission configuration.
- Trusted tool-call summaries.
- Retrieved mission docs using the existing untrusted envelope style.
- Current user message.

Add a token budget:

- Reserve output tokens.
- Reserve tool schema/tool result space.
- Drop oldest raw turns first.
- Keep pinned facts and structured mission data ahead of prose.

Key optimization: do not send full trajectory artifacts to the model when a compact summary will do. Keep the full artifact for the UI map and audit trail.

Make summaries derived and disposable:

- Store summary source event range.
- Store summary policy version.
- Store model/runtime used to create it.
- Store token budget assumptions.
- Regenerate summaries when facts are retracted or tool outputs are superseded.
- Never make a prose summary the only home of mission-critical facts.

Trust labels should exist below the message level, not only around entire messages. Useful classes include `client_claim`, `server_observed_tool_result`, `derived_summary`, `operator_pinned`, and `retrieved_document`.

### Stage 3: Responses API Migration

Effort: 5-10 days.

Build a provider adapter next to the current `OpenAIProvider`:

- Convert `messages` to Responses `input` and `instructions`.
- Port function-call handling from Chat Completions to Responses item handling.
- Keep the current provider behind a feature flag.
- Test `previous_response_id`, Conversations API, and compaction against Stratos' local store.

Recommendation: keep Stratos' local store authoritative even when using OpenAI-managed state. Use OpenAI state as a runtime accelerator, not as the only mission record.

The migration spike should answer more than "can the API call work?" It should produce a compatibility matrix for:

- Tool-call representation.
- Retry and idempotency behavior.
- Trace/run linkage.
- Compaction semantics.
- Cost accounting.
- Failure recovery.
- How to reconstruct the Stratos event ledger from runtime outputs.

### Stage 4: Compaction And Retrieval

Effort: 3-7 days after Stage 3.

Add two kinds of compression:

- Human-readable Stratos summaries for UI/search/audit.
- Model-facing compaction for long-running Responses workflows.

Add retrieval:

- Search prior conversation decisions and mission facts.
- Retrieve mission documents with the existing untrusted-context envelope.
- Optionally add embeddings/vector search later, once basic persistence and keyword search prove useful.

### Stage 5: Agents SDK Pilot

Effort: 1-2 weeks for a serious pilot.

Start with one agent, not a multi-agent redesign:

- STRATOS Mission Copilot agent.
- Existing weather, airspace, and trajectory tools wrapped as SDK function tools.
- Session mapped to local `conversation_id`.
- Trace ID recorded with each run.
- Streaming enabled only after non-streaming parity is solid.

Then test specialists:

- Weather Analyst.
- Trajectory Analyst.
- Airspace Reviewer.
- Mission Readiness Reviewer.

Only keep specialists if evals show better tool selection, safer recommendations, or clearer mission output.

Out of scope for the MVP: shipping multi-agent specialists during Stage 1 or Stage 2. The first implementation should prove durable conversations, context assembly, and trusted tool summaries before adding specialist handoffs.

## Recommended Architecture

Use three layers:

1. Local Stratos state layer:
   - Source of truth for conversations, messages, trusted tool calls, summaries, mission facts, and UI search.

2. Model runtime adapter:
   - Starts as current Chat Completions provider.
   - Evolves into Responses provider.
   - Later can run Agents SDK behind the same app-level contract.

3. Context policy layer:
   - Owns what goes into the model prompt.
   - Enforces token budget.
   - Keeps untrusted data wrapped.
   - Summarizes heavy tool outputs.

This separation is the main reason not to jump directly to Agents SDK. If Stratos first defines its own conversation contract, each runtime becomes a replaceable implementation detail.

The local contract should be event-first. That avoids three competing state machines later: a Stratos ledger, a Responses conversation, and an Agents SDK session. Stratos owns the mission record; the runtime adapter stores upstream IDs and trace references as links.

## Other Project Optimizations

High-impact backend optimizations:

- Summarize tool outputs before adding them to model context.
- Store full map/trajectory artifacts outside the prompt.
- Add async/background job handling for long SondeHub/no-flight-zone runs instead of holding one request for up to 120 seconds.
- Add token counting in tests for representative prompts.
- Add model routing: cheaper model for casual chat, stronger model for launch recommendation or multi-tool risk analysis.
- Add eval fixtures for tool selection and GO/CAUTION/NO-GO output.
- Keep intent routing, but make tool-group selection observable and overrideable.

Frontend optimizations:

- Replace placeholder chat history with persisted conversations.
- Make search real once messages are stored.
- Show accurate loading states instead of always cycling through weather/simulation messages.
- Add a "context carried forward" indicator when old turns are summarized.
- Show tool result cards from trusted server records, not client-supplied history.

Safety and reliability optimizations:

- Keep the current untrusted envelope pattern.
- Add tests for prompt injection inside retrieved summaries.
- Add structured mission fact extraction with source references.
- Keep manual restriction/TFR review language pinned in memory and tested.
- Add audit export for a mission conversation.
- Promote long SondeHub/no-flight-zone work into resumable tool jobs with status records and artifact references.
- Add idempotency tests for duplicate sends, retries, and reloads.
- Ensure "restriction lookup unavailable" and similar uncertainty survives summarization with the same operational force as the original tool result.
- Add a token-budget fixture with 100 prior turns plus a large trajectory artifact; the model-facing prompt must stay under the configured budget while the full artifact remains available to the UI/audit trail.
- Add summary-regeneration tests for `fact_retracted` and superseded tool-output events.

## Decision Matrix

| Path | Continuity value | Migration risk | Cost control | UI/search value | Long-term agent fit |
| --- | ---: | ---: | ---: | ---: | ---: |
| Current client replay only | Low | Low | Low | Low | Low |
| Local store + summaries | High | Low-Medium | High | High | Medium |
| Responses + local store | High | Medium | High | Medium | High |
| Agents SDK immediately | Medium | High | Medium | Low initially | High |
| Staged hybrid | High | Medium | High | High | High |

## Final Recommendation

Build the local conversation/memory layer first, then migrate to Responses, then pilot Agents SDK. The local layer is not wasted work; it is the product contract Stratos needs no matter which OpenAI runtime wins.

Architect-review refinement: make that local layer an append-only, trust-labeled event ledger with separate projections for transcript, audit, model memory, summaries, search, and mission facts. That turns "local memory" from temporary glue into the stable architecture that makes later Responses and Agents SDK adoption safer.

## Sources

- OpenAI, [Agents SDK overview](https://developers.openai.com/api/docs/guides/agents)
- OpenAI, [Agents SDK quickstart](https://developers.openai.com/api/docs/guides/agents/quickstart)
- OpenAI, [Running agents](https://developers.openai.com/api/docs/guides/agents/running-agents)
- OpenAI, [Agents results and state](https://developers.openai.com/api/docs/guides/agents/results)
- OpenAI, [Agents integrations and observability](https://developers.openai.com/api/docs/guides/agents/integrations-observability)
- OpenAI, [Migrate to Responses](https://developers.openai.com/api/docs/guides/migrate-to-responses)
- OpenAI, [Conversation state](https://developers.openai.com/api/docs/guides/conversation-state)
- OpenAI, [Responses create API reference](https://developers.openai.com/api/reference/resources/responses/methods/create)
- OpenAI, [Responses compact API reference](https://developers.openai.com/api/reference/resources/responses/methods/compact)
- OpenAI, [Models](https://developers.openai.com/api/docs/models)
- OpenAI, [Pricing](https://developers.openai.com/api/docs/pricing)
- OpenAI, [Cost optimization](https://developers.openai.com/api/docs/guides/cost-optimization)
- OpenAI, [Counting tokens](https://developers.openai.com/api/docs/guides/token-counting)
