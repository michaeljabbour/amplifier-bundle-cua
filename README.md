# amplifier-bundle-cua

Amplifier bundle for computer-use automation — universal desktop control, semantic UI understanding, and safe bounded operation.

**Bundle namespace:** `cua`  
**Git source:** `git+https://github.com/michaeljabbour/amplifier-bundle-cua@main`

---

## Overview

This bundle provides CUA (Computer-Use Automation) capabilities to the Amplifier CLI. It exposes:

- **Behaviors** — reusable context/skill layers (`cua-core`, `cua-operator`, `cua-recipes`)
- **Agents** — task-oriented agents (`cua-operator`, `cua-planner`)
- **Recipes** — multi-step automation workflows (`bounded-task`, `observe-and-act`, `recovery-workflow`)
- **Tool module** — `tool-cua` Python package (lives in `modules/tool-cua/`)

---

## Repo structure

```
amplifier-bundle-cua/
├── bundle.md                  # Bundle manifest (name: cua)
├── pyproject.toml             # Root uv workspace / dev tooling
├── agents/
│   ├── cua-operator.md
│   └── cua-planner.md
├── behaviors/
│   ├── cua-core.yaml
│   ├── cua-operator.yaml
│   └── cua-recipes.yaml
├── context/
│   └── dual-world-reasoning.md
├── modules/
│   └── tool-cua/              # Python package (uv workspace member)
├── recipes/
│   ├── bounded-task.yaml
│   ├── observe-and-act.yaml
│   └── recovery-workflow.yaml
└── tests/                     # Pytest suite for tool-cua
```

---

## Local development setup

Requires [uv](https://docs.astral.sh/uv/) and Python ≥ 3.11.

```bash
# Clone the repo
git clone https://github.com/michaeljabbour/amplifier-bundle-cua
cd amplifier-bundle-cua

# Install all dev dependencies (workspace-aware)
uv sync --group dev
```

---

## Automated tests

```bash
# Run full test suite (quiet)
uv run pytest tests/ -q

# Run with verbose output and short tracebacks
uv run pytest tests/ -v --tb=short

# Lint
uv run ruff check .

# Format check
uv run ruff format --check .

# Type check
uv run pyright
```

---

## Smoke test — local clone with fixture backend

The fixture backend runs without any real desktop/OS access, making it safe for CI and quick validation.

**1. Create a settings override file** in your project (or a scratch directory):

```yaml
# .amplifier/settings.local.yaml
modules:
  tools:
    - module: tool-cua
      config:
        backend: fixture
```

**2. Run Amplifier against the local bundle:**

```bash
# Use the file:// URI form — verified to work with the current CLI
export REPO=/absolute/path/to/amplifier-bundle-cua
amplifier run --bundle "file://$REPO" ...
```

> **Note — `file://` is required for local bundles.** CLI verification in this repo confirmed that  
> `file:///absolute/path/to/amplifier-bundle-cua` (i.e. `file://$REPO`) works correctly, while  
> bare path forms such as `/absolute/path/to/amplifier-bundle-cua` did **not** work.  
>
> **Note — `--set` not supported.** The current Amplifier CLI does **not** support a `--set` flag  
> for inline config overrides. Backend selection must be supplied via `.amplifier/settings.local.yaml`  
> (shown above) placed in your working directory or home config directory.

---

## Smoke test — GitHub source with fixture backend

Once the bundle is pushed to GitHub, you can load it directly:

```bash
amplifier run --bundle git+https://github.com/michaeljabbour/amplifier-bundle-cua@main ...
```

Use the same `.amplifier/settings.local.yaml` from the section above to activate the fixture backend:

```yaml
modules:
  tools:
    - module: tool-cua
      config:
        backend: fixture
```

This tells Amplifier to install the bundle from the GitHub source at `@main`, editable-install the root (no Python packages are auto-discovered thanks to the `[tool.setuptools] packages = []` override in `pyproject.toml`), and use the fixture backend for `tool-cua`.

---

## Notes / troubleshooting

### `No packages found` or `flat-layout` install error

If you see setuptools complaining about flat-layout auto-discovery when installing the repo root as an editable package, ensure `pyproject.toml` contains:

```toml
[tool.setuptools]
packages = []
```

This suppresses auto-discovery for the root package (the actual Python code lives in `modules/tool-cua/`, not the root).

### `--set` flag not recognised

The `--set` flag for inline config overrides is not supported by the current Amplifier CLI. Use `.amplifier/settings.local.yaml` instead (see smoke test sections above).

### Workspace member not found

If `uv sync` cannot resolve `tool-cua`, verify that `modules/tool-cua/pyproject.toml` exists and that `[tool.uv.workspace]` in the root `pyproject.toml` lists `"modules/tool-cua"` as a member.

### Running against a specific branch

Append `@<branch-or-sha>` to the git URL:

```bash
amplifier run --bundle git+https://github.com/michaeljabbour/amplifier-bundle-cua@my-branch ...
```
