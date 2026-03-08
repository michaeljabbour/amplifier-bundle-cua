# Recovery Patterns

When actions fail or produce ambiguous results, follow these recovery patterns.

## Pattern 1: Re-Observe Before Retry

**Never retry an action blindly.** Always re-observe first.

1. Call `observe` to get fresh state
2. Compare with what you expected
3. Only then decide: retry the same action, try a different approach, or escalate

## Pattern 2: Semantic Fallback

If a click at pixel coordinates failed or was ambiguous:

1. Check the semantic tree for the target element
2. If found with bounds, use the semantic bounds for more precise coordinates
3. If not found in semantic tree, the element may not be visible — check for overlapping windows or scroll position

## Pattern 3: Visual Fallback

If semantic identification failed (element not in tree, no label):

1. Take a screenshot
2. Reason about the visual layout to find the target
3. Use visual coordinates, but mark confidence as Medium

## Pattern 4: Escalation

Escalate to the user when:

- The same action has failed **twice** with different approaches
- The screen state is **completely unexpected** (wrong app, dialog box, error)
- An action requires **permissions** you don't have (e.g., accessibility not enabled)
- The **action budget** is exhausted

When escalating, always provide:
1. What you were trying to do
2. What happened instead
3. The current screen state (screenshot)
4. Your best guess at what went wrong
