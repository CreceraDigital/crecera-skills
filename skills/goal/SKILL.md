---
name: goal
description: Use when the user wants to run a task autonomously to completion, says "/goal", "run this until it's done", "work on this without me", "keep going until X is true", or wants Claude to self-drive toward an outcome with a definition of done. Runs an execute → independently-evaluate → iterate loop where a SEPARATE evaluator agent (fresh context) grades the real artifacts against the definition of done, so the agent doing the work never grades its own homework. Stops on PASS, stall, or budget cap.
argument-hint: "[the goal] — and how you'll know it's done"
---

## What this does

`/goal` turns a desired outcome into an autonomous run. The trap with "work until it's done" is that the same agent that did the work decides it's done — and it's biased to declare victory. `/goal` fixes that by splitting the two jobs: an **Executor** does the work, and a **separate Evaluator** (a fresh agent that never saw the executor's reasoning, only the goal and the real artifacts) grades it. The loop repeats until the Evaluator returns PASS or a stop condition trips.

Use it for outcomes you can define crisply and verify objectively: "all tests pass", "the page renders with no console errors", "every row reconciles", "the report covers all 28 properties." Do NOT use it for open-ended judgment calls with no checkable definition of done — those need you in the loop.

## Step 1: Lock the Definition of Done (DoD)

This is the most important step. A vague DoD makes the Evaluator useless. If `$ARGUMENTS` already contains a checkable goal, restate it as a DoD and confirm. Otherwise ask, in one batch (max 3-4 questions):

1. **The outcome** in one sentence.
2. **Definition of Done** — the specific, checkable conditions that must ALL be true. Push for things a fresh agent can verify by running a command, reading a file, or observing output. ("Looks good" is not a DoD; "`npm test` exits 0 and the build produces `dist/index.html`" is.)
3. **Boundaries** — files/dirs/services it may touch, and anything off-limits (no pushing, no deploys, no destructive ops unless named).
4. **Budget + autonomy** — how many iterations or roughly how long it should run unattended before reporting back, and whether it may act on hard-to-reverse steps (commits, deploys, external sends) or must stop and ask.

Write the DoD as a numbered checklist. Every item must be independently verifiable. Paste this exact checklist into both the Executor and the Evaluator so they share one source of truth.

If the DoD can't be made checkable, say so and stop — `/goal` is the wrong tool. Offer to just do the task interactively instead.

## Step 2: Plan the work

Before looping, decompose the goal:
- List the concrete tasks needed to satisfy the DoD.
- Mark which tasks are **independent** (no shared files, no ordering dependency) — those fan out in parallel. Mark which are **sequential**.
- Track the plan with TodoWrite so progress is visible across iterations.

## Step 3: The loop (Execute → Evaluate → Iterate)

Run this loop. Each pass is one iteration.

**A. Execute.** Do the work toward any unmet DoD items. For independent tasks, spawn parallel sub-agents in a single message (one `Task` call each, `subagent_type: general-purpose`) — see "Parallel execution" below. For sequential or judgment-heavy work, do it directly. Keep the changes real and on disk; the Evaluator checks reality, not claims.

**B. Evaluate — with a SEPARATE agent.** Spawn ONE fresh `general-purpose` agent as the Evaluator. It must be independent: give it the DoD checklist and where the artifacts live, but NOT your narration of what you did. Its mandate:

> You are the Evaluator. You did NOT do this work and you trust nothing you are told about it — only what you can verify yourself. Here is the Definition of Done as a numbered checklist: [paste DoD]. The work lives here: [paths / how to run it]. For EACH checklist item, verify it against reality — run the command, read the file, observe the output, take the screenshot. Do not assume; check. Return a verdict per item: PASS (with the evidence you saw) or FAIL (with the exact gap and where it is). Then an overall verdict: PASS only if every item passes, otherwise FAIL. Be adversarial. If you cannot verify an item, that item is FAIL, not PASS.

The Evaluator runs commands and reads files itself — it never takes the Executor's word. An item it can't verify is a FAIL.

**C. Decide.** Read the Evaluator's per-item verdicts:
- **All PASS** → exit the loop, go to Step 4.
- **Any FAIL** → feed the specific gaps back as the next iteration's work list, update TodoWrite, and loop to A.

## Stop conditions (hard limits)

Exit the loop and report — even if not all PASS — when ANY of these trip:
1. **Done** — Evaluator returns overall PASS.
2. **Budget** — hit the iteration cap from Step 1 (default 5 if the user gave none).
3. **Stall** — two consecutive iterations close zero new DoD items. Looping more won't help; stop and surface why.
4. **Blocked** — work requires a decision, credential, or hard-to-reverse action the user didn't pre-authorize. Stop and ask; never guess past a boundary set in Step 1.

Never loop forever. If you're not converging, a human needs to see it.

## Parallel execution

The point of fanning out is throughput on **independent** work. Rules:
- Only parallelize tasks that share no files and have no ordering dependency. Concurrent edits to the same file corrupt each other — keep those sequential, or give each agent an isolated worktree.
- Spawn all parallel agents in a single message (multiple `Task` calls) so they actually run concurrently.
- Each sub-agent gets a tight, self-contained brief and returns a structured result, not a chat reply.
- The Executor (you) integrates their outputs before handing off to the Evaluator.

For a large fan-out with a deterministic loop (many items × execute-then-verify each), consider the **Workflow** tool instead of hand-spawning — it gives you a real pipeline with the same execute/evaluate shape.

## Unattended / scheduled runs

`/goal` runs the loop once, in this session, reporting when a stop condition trips. If the user wants it to keep going on a schedule or fully in the background, hand off to the right harness tool rather than reinventing it:
- **`/loop`** — re-run `/goal <same goal>` on an interval or self-paced until done.
- **`schedule`** — run it as a recurring cloud agent on a cron.
- **`run_in_background`** — for long-running build/test commands inside an iteration; surface the shell ID so the next iteration can check it.

## Step 4: Report

When the loop exits, report concisely:

```
## GOAL RUN COMPLETE — <PASS / STOPPED: reason>

**Goal:** <one line>

**Definition of Done:**
- [x] <item> — <evidence the Evaluator saw>
- [ ] <unmet item> — <the gap, and why it's still open>

**Iterations:** <n> (stopped because: done / budget / stall / blocked)
**What changed:** <key files/artifacts, absolute paths>
**Verify it yourself:** <the command(s) the user can run to confirm>
**If STOPPED short:** <the single decision or input needed to finish>
```

## Rules

- The Executor and the Evaluator are NEVER the same agent in the same pass. Splitting them is the whole point — an agent grading its own work is the failure mode `/goal` exists to prevent.
- The Evaluator verifies against reality (runs it, reads it, observes it), never against the Executor's self-report. Unverifiable = FAIL.
- The DoD is frozen at Step 1. Don't quietly relax it mid-loop to force a PASS. If it was wrong, stop and tell the user.
- Respect the boundaries from Step 1 absolutely. Hard-to-reverse actions (commit, push, deploy, external send, delete) require explicit pre-authorization or a stop-and-ask.
- Always terminate. PASS, budget, stall, or blocked — one of them ends every run.
