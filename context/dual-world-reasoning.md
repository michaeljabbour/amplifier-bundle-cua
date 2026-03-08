# Dual-World Reasoning

You have access to **two complementary views** of the desktop:

## Visual World (Screenshots)
- Raw pixel data of the current screen
- Shows exactly what a human would see
- Useful for: layout understanding, visual confirmation, finding elements by appearance
- Limitations: fragile to theme changes, resolution differences, overlapping windows

## Semantic World (Accessibility Tree)
- Structured tree of UI elements with roles, labels, and values
- Shows the logical structure of the interface
- Useful for: precise element identification, reading text content, understanding hierarchy
- Limitations: may be incomplete, some apps have poor accessibility support, tree can be stale

## How to Combine Them

1. **Use semantic data for identification** — When the accessibility tree has clear labels (e.g., "Submit" button, "Search" text field), prefer those over pixel coordinates.
2. **Use visual data for confirmation** — After identifying an element semantically, confirm it visually matches expectations (right location, visible on screen).
3. **Fall back gracefully** — If semantic data is missing or incomplete, fall back to visual-only reasoning. If the screenshot is unclear, fall back to semantic-only.
4. **Cross-validate** — When both worlds provide information about the same element, check that they agree. Disagreement is a signal to re-observe.

## When Each World is Preferred

| Situation | Prefer |
|---|---|
| Finding a button by label | Semantic |
| Confirming a dialog appeared | Visual |
| Reading text in a text field | Semantic (value attribute) |
| Checking if a menu is open | Visual |
| Identifying the focused element | Semantic (focused attribute) |
| Determining element position for clicking | Semantic (bounds) > Visual (pixel estimation) |
