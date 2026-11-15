# Penta Boys / PentAGI — Hallucination Patterns & Briefing Lessons

## The Naming Hallucination Cascade (v3)

PentAGI agents pattern-matched exploit names against unrelated concepts:

| Real Exploit | Their Hallucinated Interpretation |
|---|---|
| PentaBleed (CitrixBleed 2, NetScaler memory disclosure) | "TLS/SSL heartbeat memory disclosure" (Heartbleed) |
| PentaShell (Erlang SSH pre-auth RCE) | "Web shell delivery and management" |
| PenaUnify (UniFi OS pre-auth RCE) | "Unified log aggregation and correlation" |

The "bleed" suffix triggered TLS/Heartbleed association. "Shell" triggered web shell. "Unify" triggered log aggregation. All wrong.

## The chwoot → Chroot Hallucination (v2→v3)

The exploit name "chwoot" contains "chroot" as a substring. PentAGI interpreted this as a container escape exploit and rewrote the module to require chroot detection, completely missing that it's actually a sudo privilege escalation. The word similarity triggered the wrong entire attack class.

## Root Cause

AI agents with vague prompts + exploit names as only input will pattern-match names to known categories, not read the actual code or CVE descriptions. They treat exploit names as semantic clues rather than opaque identifiers.

## Corrective Actions

1. **Never let AI agents "interpret" exploit names**. Provide exact file paths, exact CVE numbers, and a one-sentence description for each tool.
2. **Briefing format**: Include a manifest with `name → CVE → one-line-description → exact file path` for every tool.
3. **Do not reference tools by name alone** — always pair with the CVE number: "PentaBleed (CVE-2025-5777, NetScaler memory disclosure)"
4. **Assume zero prior knowledge** — agents in a new Flow session have no context from previous Flows.
5. **Provide deliverables as Flow files, not Resources** — Resources are not reliably accessible to agents.

## When to Use PentAGI/Penta Boys

- **Good for**: Well-scoped single-CVE tasks with exact instructions and source code provided
- **Bad for**: Multi-module integration, creative interpretation, anything requiring cross-session context
- **Critical**: Always provide a manifest file with exact module names, CVE numbers, and file paths
