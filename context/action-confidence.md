# Action Confidence

Every action you take has an associated confidence level. Be honest about uncertainty.

## Confidence Levels

| Level | When | What to Do |
|---|---|---|
| **High** | Semantic tree clearly identifies the target element with role, label, and bounds | Proceed with the action |
| **Medium** | Visual screenshot shows the target but semantic data is incomplete or missing | Proceed, but verify the post-state carefully |
| **Low** | Neither visual nor semantic data clearly identifies the target | Re-observe first. If still low, ask the user for guidance |
| **None** | Screen state is completely unexpected or unrecognizable | Stop. Report the situation to the user |

## Interpreting Action Results

| Status | Meaning | Next Step |
|---|---|---|
| `success` | Action completed and post-state confirms the change | Continue to next step |
| `failure` | Action could not be performed (e.g., coordinates out of bounds) | Report error, do not retry the same action |
| `blocked` | Action denied (permissions, missing capability) | Report the block, escalate to user |
| `ambiguous` | Action executed but post-state didn't confirm the expected change | Re-observe. If still ambiguous after 2 re-observations, escalate |

## Budget Rules

- Default action budget per task: **20 actions**
- Default retry limit per step: **2 retries**
- If budget is exhausted: **stop and report** what was accomplished
