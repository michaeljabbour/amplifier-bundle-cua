# amplifier-bundle-cua Design

## Goal

Build an Amplifier-native bundle for computer-use automation that provides universal desktop control, semantic UI understanding, and safe bounded operation — usable by Amplifier apps broadly (especially amplifier-app-cli) and later consumable by Kepler and other ecosystems via adapters.

## Background

Computer-use automation (CUA) is an emerging capability where AI agents observe and interact with desktop environments the way a human would — through screenshots, mouse/keyboard input, and UI element inspection. No existing solution is Amplifier-native. Current options are either framework-specific SDKs, MCP servers, or standalone tools that embed their own orchestration. `amplifier-bundle-cua` fills this gap: a clean-room Amplifier bundle that treats computer use as a first-class capability composed of tools, agents, and recipes, not a foreign runtime bolted onto Amplifier.

Kepler is a consumer of this bundle, not its center. The bundle's native contract is Amplifier-first. MCP adapters, Kepler integration, and Claude/Codex compatibility sit outside or beneath the core contract.

## Constraints and Explicit Decisions

| Decision | Choice | Rationale |
|---|---|---|
| **Repo identity** | New clean-room repo `amplifier-bundle-cua` | Fresh start; study donors but never copy donor code |
| **Native contract** | Amplifier-first (bundle, behaviors, modules, agents, context, recipes) | Not MCP-first, not Tauri-plugin-first, not framework-SDK-first |
| **Observation model** | Dual-world: visual state + semantic state as co-equal first-class inputs | Agent fuses both rather than forcing screenshot-only or accessibility-only |
| **Target architecture** | Host-agnostic abstract target model (host desktop + future sandbox/VM) | v1 implements host-desktop first; abstraction allows future targets cleanly |
| **Implementation language** | Polyglot allowed internally (Python modules + optional Rust helpers) | Python for the Amplifier-facing tool layer; Rust helpers only when justified |
| **Install/distribution** | UX feels like A (lightweight, normal bundle install); architecture permits B internally (prebuilt helpers later) | No local native compilation required for typical users |
| **Donor strategy** | Composite: study multiple donors, implement clean-room | Steal mental models and lessons, not source code |
| **Priority ranking** | 1) Universal control, 2) Semantic control, 3) Safety, 4) Interop | Drives donor evaluation and architectural trade-offs |

## Donor Comparison Summary

| Candidate | Universal Control | Semantic Control | Safety | Interop | Assessment |
|---|---|---|---|---|---|
| **trycua/cua** | High | Medium | High | Medium | Best single-repo donor — thinks in terms of computer use, strong screenshot+action model, better sandbox/VM future |
| **mediar-ai MCP desktop SDK** | Medium | High | Medium | High | Strongest semantic/interop donor, but too MCP/server-shaped for primary architecture |
| **screenpipe** | Low/Medium | High | Medium | Medium | Excellent "eyes + context" donor (screen + OCR + accessibility), not enough "hands" |
| **nut.js** | High | Low | Low/Medium | Medium | Strong primitive donor (screenshots/input/image matching), wrong abstraction level for primary architecture |
| **PyAutoGUI** | Medium | Low | Low | Medium | Baseline primitive donor only |
| **Rust/Tauri-adjacent lane** | Medium/High | Low | Medium | Medium | Strong Rust-native building blocks exist (enigo + xcap, screenpipe as reference), but no real Tauri 2 CUA plugin |

### Donor Role Assignments

- **Primary conceptual donor:** `trycua/cua` — supplies the overall computer-use mental model, universal screenshot+action patterns, and sandbox/VM thinking.
- **Primary semantic/perception donors:** `screenpipe` and secondarily `mediar-ai` — inform the perception layer, accessibility tree handling, and dual-world observation design.
- **Optional internal helper lane:** Rust primitives (`enigo` + `xcap`, etc.) — available as an implementation escape hatch for performance-critical backends, but never the bundle's public identity.
- **Reference donors for primitives:** `nut.js` and `PyAutoGUI` — inform low-level input/screenshot lessons only.

This is not a code merge. It is a clean-room donor map.

## Chosen Approach

Use a composite donor strategy to build an Amplifier-native bundle from scratch. The bundle's identity is **tools + agents + recipes for computer use**. The `cua` project supplies the overall mental model for how an agent should think about computer use. The `screenpipe` and `mediar-ai` projects inform how perception and semantic layers should work. Rust primitives remain an optional internal helper path for future performance needs. The result is a bundle that looks and installs like any normal Amplifier bundle, but internally draws lessons from the best available computer-use projects.

## Architecture

### Core Identity

`amplifier-bundle-cua` is an Amplifier-first bundle repo. Its native identity is tools + agents + recipes for computer use. It is not an MCP server, not a Tauri plugin, and not a framework-specific SDK. The repo is structured like a normal Amplifier bundle: a thin root bundle, one or more behaviors, context files, specialist agents, recipes, and one primary `tool-cua` module. That module is the center of gravity. It exposes the stable Amplifier tool surface, while everything else — MCP adapters, Kepler usage, Claude/Codex integration, native helpers — sits outside or beneath that contract.

### Dual-World Model

The operator agent reasons over two first-class inputs:

- **Visual state:** screenshots, screen geometry, cursor position, window captures.
- **Semantic state:** accessibility tree, window metadata, element hints, focused app/window, role/label/actionability when available.

Neither world is treated as secondary. The agent can act with screenshots alone, semantics alone, or both combined. This avoids the trap of forcing a screenshot-only worldview (brittle to visual changes) or an accessibility-only worldview (incomplete on many real desktops).

### Host-Agnostic Target Model

The internal implementation is host-agnostic even though v1 may only fully implement host-desktop backends first. Internal abstractions distinguish between **target** and **transport**:

- **Target:** what the agent is controlling (host desktop, sandbox, VM, container).
- **Transport:** how the control is implemented (Python-native code, subprocess helpers, prebuilt Rust helpers, network protocols).

This separation means adding a new target (e.g., a Linux VM via VNC) does not require rewriting the tool interface or agent logic.

### Composite Donor Architecture

```
┌─────────────────────────────────────────────────────┐
│  amplifier-bundle-cua (Amplifier-native surface)    │
│  ┌───────────────────────────────────────────────┐  │
│  │  Agents: cua-operator, cua-planner/reviewer   │  │
│  │  Context: dual-world reasoning guides         │  │
│  │  Recipes: bounded workflows, approval gates   │  │
│  └────────────────────┬──────────────────────────┘  │
│                       │                              │
│  ┌────────────────────▼──────────────────────────┐  │
│  │  modules/tool-cua/                            │  │
│  │  ┌──────────────────────────────────────────┐ │  │
│  │  │  Tool Interface (Amplifier tool surface) │ │  │
│  │  ├──────────────────────────────────────────┤ │  │
│  │  │  Target Abstraction (host / sandbox / VM)│ │  │
│  │  ├──────────────────────────────────────────┤ │  │
│  │  │  Backend Implementations                 │ │  │
│  │  │  ├─ host-desktop (Python-native, v1)     │ │  │
│  │  │  ├─ fixture/simulator (testing)          │ │  │
│  │  │  └─ [future: sandbox, VM, container]     │ │  │
│  │  └──────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────┘  │
│                                                      │
│  ┌───────────────────────────────────────────────┐  │
│  │  Optional helper lane (Rust prebuilt helpers)  │  │
│  │  (not required for v1; architecture permits)   │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
          │                              │
          ▼                              ▼
   Amplifier CLI               Future consumers
   (primary consumer)          (Kepler, MCP adapters,
                                Claude/Codex, etc.)
```

## Components and Repo Shape

### Root Bundle

A thin root bundle that assembles behaviors. Stays minimal — no implementation logic at this level.

### Behaviors

Compose the capability in stages:

- **Core behavior:** primitives (screenshot, click, type, scroll, window/screen info, semantic inspection).
- **Operator behavior:** the main `cua-operator` agent and its supporting context.
- **Recipes behavior (optional):** higher-level repeatable workflows.

### modules/tool-cua/

The main implementation unit. Exposes the stable tool contract with three internal layers:

1. **Tool interface:** what Amplifier sees. Stable tool signatures for screenshot capture, cursor state, click, type, scroll, window/screen info, and semantic inspection.
2. **Target abstraction:** distinguishes host desktop vs. future sandbox/VM targets. Defines the observation/action contract that all backends must satisfy.
3. **Backend implementations:** platform-specific work. Whether through pure Python, subprocess helpers, or prebuilt native helpers. v1 ships host-desktop backends.

### Agents

- **cua-operator:** the default agent that actually performs desktop tasks. Reasons in the dual-world model over visual and semantic observations, plans atomic actions, and executes bounded loops.
- **cua-planner / cua-reviewer:** specialized agent(s) for multi-step flow reasoning, failure analysis, and recovery planning.

### Context Files

Teach agents how to reason in the dual-world model. Include guidance on when to prefer visual vs. semantic observations, how to handle ambiguity, when to escalate, and how to reason about action confidence.

### Recipes

Repeatable workflows including:

- Observe screen and act (basic operator loop).
- Retry with semantic hints (fallback from visual to semantic).
- Bounded task execution with approval gates (safe multi-step flows).
- Recovery workflows (re-observe after failure, escalation patterns).

## Data Flow and Execution Model

### Bounded Operator Loop

The execution model centers on a bounded operator loop driven by Amplifier tools, not by embedding a foreign orchestration system:

```
User/Recipe request
       │
       ▼
  cua-operator agent
       │
       ├──► Observe (tool-cua: screenshot + semantic state)
       │         │
       │         ▼
       │    Normalize (stable observation format)
       │         │
       │         ▼
       ├──► Reason (agent layer — plan next atomic action)
       │         │
       │         ▼
       ├──► Approve (if required by policy)
       │         │
       │         ▼
       ├──► Act (tool-cua: exactly one bounded action)
       │         │
       │         ▼
       ├──► Verify (tool-cua: post-action observation)
       │         │
       │         ▼
       └──► Loop or terminate (based on goal, budget, confidence)
```

### Five-Stage Data Flow Within the Module

1. **Observe:** gather screenshots, window info, cursor state, and semantic element data from the active target backend.
2. **Normalize:** convert raw observations into a stable internal observation format. Agents and recipes never see backend-specific shapes — they see normalized observations regardless of whether the backend is host-desktop or future VM/sandbox.
3. **Reason:** remains outside the module, in the Amplifier agent/orchestrator layer. The module does not decide strategy.
4. **Act:** execute exactly one bounded action (click, type, scroll, focus, etc.). Never compound actions.
5. **Verify:** capture enough post-action state to determine whether the action succeeded, failed, or left the system in an ambiguous state.

### Key Design Rule

**The module provides mechanisms, not policy.** It never decides strategy like "find the login button and click it until success." That belongs in agents and recipes. The module only provides precise observations and precise actions. This keeps the core reusable across Amplifier CLI, future Kepler usage, and external adapters.

## Error Handling, Safety, and Recovery

### Structured Uncertainty

Computer use is inherently unreliable at the action level: windows move, focus changes, permissions fail, semantics are incomplete, screenshots can be stale, and UI state can change between observation and action. The error model is **structured uncertainty**, not "exception or success."

Each tool call returns a normalized result with one of four classifications:

| Status | Meaning |
|---|---|
| `success` | Action completed and post-state confirms expected outcome |
| `failure` | Action could not be performed (clear error) |
| `blocked` | Action denied due to approvals, permissions, missing capabilities, or policy |
| `ambiguous` | Action executed but post-state did not confirm expected change |

### Layered Safety

Safety is enforced at three layers with mechanism and policy cleanly separated:

- **Tool/module layer (mechanism):** hard invariants — bounds checking, capability detection, target availability, permission checks, timeouts, rate limits.
- **Agent/recipe layer (policy):** action budgets, retry ceilings, re-observe-before-repeat behavior, escalation to the user when confidence drops.
- **Bundle level (configuration):** approval patterns are configurable so dangerous actions can require explicit consent while observation remains lightweight.

### Recovery Model

Recovery favors **re-observation over blind retry.** If an action fails or returns ambiguous:

1. Capture fresh visual and semantic state.
2. Compare with prior expectations.
3. Only then decide whether to retry, adapt, escalate, or stop.

Recipes encode bounded recovery loops and explicit stop conditions so the operator never degenerates into thrashing. The bundle supports future kill-switch / cancel patterns cleanly, even if specific desktop consumers implement the UI differently.

## Testing Strategy

### Module-Level Contract Tests

`tool-cua` needs strong contract tests for every primitive: screenshot capture, click, type, scroll, cursor/window info, and semantic inspection. These tests verify:

- Normalized result shapes.
- Error classifications (`success`, `failure`, `blocked`, `ambiguous`).
- Capability detection and graceful degradation.

Because real desktops are unstable test environments, the module supports a **fixture/simulator backend** so most contract tests run deterministically without touching the real machine.

### Backend Conformance Suite

Each concrete backend has a conformance suite. The question is not "did macOS click a button in TextEdit," but "does this backend satisfy the required observation/action semantics?" This is where host vs. future sandbox targets can be tested against identical expectations.

For the dual-world model, the test harness supports **golden observations:** fixed screenshots, fixed semantic trees, and expected normalized observation outputs. This makes perception logic testable without requiring live UI state.

### Bounded Integration Tests

The default operator agent and recipes need bounded integration tests covering simple flows:

- Observe current screen.
- Focus app and re-observe.
- Perform one typed action and verify changed state.
- Stop safely when confidence is low.

These emphasize safety, recovery, and bounded loops — not heroic end-to-end automation.

### Consumer Integration Boundary

Consumer-specific integrations (Kepler, MCP adapters, external tools) are tested **outside** the bundle repo. `amplifier-bundle-cua` proves its own contract, behavior, and recipes. Consumers prove their own integration points.

## Open Questions and Future Tracks

### Open Questions

- **Exact accessibility-tree backend for v1:** which Python libraries or OS APIs to use for semantic inspection on macOS, Windows, and Linux. Requires prototyping during implementation.
- **Observation format specification:** the exact normalized observation schema (visual + semantic) needs to be defined during implementation, informed by real backend capabilities.
- **Approval gate granularity:** which specific actions should require approval by default vs. which should be configurable. Needs user-experience testing.
- **Action budget defaults:** reasonable default limits for retry counts, loop iterations, and total actions per task. Needs empirical tuning.

### Future Tracks

- **Sandbox/VM targets:** extend the target abstraction to support containerized or virtualized desktops (Docker, VNC, cloud VMs).
- **Rust helper binaries:** if performance-critical operations emerge (e.g., high-frequency screen capture, image diffing), introduce prebuilt Rust helpers behind the existing architecture.
- **MCP adapter layer:** expose `tool-cua` capabilities via MCP for consumption by non-Amplifier systems.
- **Kepler integration:** consume the bundle from Kepler's desktop app, proving the adapter pattern.
- **Multi-monitor and complex display support:** extend observation normalization for multi-screen setups.
- **OCR/vision integration:** integrate OCR or vision model pipelines into the observation normalize step for richer text extraction from screenshots.
