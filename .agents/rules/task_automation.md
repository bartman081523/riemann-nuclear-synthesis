---
name: task-automation-mandates
description: Mandates proactive task decomposition, live UI step tracking via update_steps, task.md lifecycle, and asynchronous task management.
trigger: always_on
---

# Task Automation & Toolchain Parity Mandates

## 1. Live Step Tracking (update_steps)
- **Mandatory Step Tracking:** For every user request requiring multiple steps (3 to 12 distinct steps), you MUST immediately invoke `update_steps` in parallel with your first action.
- **State Progression:** Mark the active step as `in_progress` and remaining steps as `pending`. As each step completes, mark it `done` and the next step `in_progress`.
- **Final Completion:** When all steps are finished, call `update_steps` once more with every step marked `done` before writing your final reply.
- **Titles:** Short and imperative (2-6 words), in plain words the user would use.

## 2. Immediate Task Tracker Initialization (task.md)
- **Automatic Decomposition:** Upon receiving any task, you MUST create and initialize a task tracker (`task.md`) before calling modifying tools or executing multi-step workflows.
- **Task Formatting:**
  - `[ ]` uncompleted tasks
  - `[/]` in progress tasks
  - `[x]` completed tasks
- **Persistence:** Keep `task.md` updated as you progress through sub-items.

## 3. Planning Mode Workflow
- **When to Plan:** Major architectural changes, complex refactoring, ambiguous requirements, or significant deviation from existing design require generating `implementation_plan.md` first.
- **Plan Format:** Must include User Review Required, Open Questions, Proposed Changes, and Verification Plan.
- **Verification & Walkthrough:** Always verify changes by running tests or compilation checks, and record results in `walkthrough.md`.

## 4. Operational Asynchronous Toolchain
- **Background Tasks:** Use `run_command` with `WaitMsBeforeAsync` (5000-10000ms for synchronous operations, 500ms for background services). Commands exceeding the wait time automatically run in the background.
- **No Polling Loops:** NEVER run shell `sleep` loops or polling scripts. Use `manage_task` (status/logs/kill) to track running background commands.
- **Schedule & Timers:** Use `schedule` for one-shot timers or recurring cron triggers.
- **Subagents & Swarms:** Delegate isolated research or heavy exploration to `invoke_subagent`, and orchestrate multi-worker pipelines with `run_workflow` or `swarm`.
