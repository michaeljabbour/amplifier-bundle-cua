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

> **Important — exit code 0 does not prove `tool-cua` loaded.**
> Amplifier treats tool/module load failures as non-fatal and can complete a session successfully
> even if `tool-cua` never mounted. An exit code of 0 from `amplifier run` is **not** an
> authoritative signal that the module loaded or that the macOS fail-fast behaviour fired
> correctly.
>
> **Authoritative verification methods for this bundle's fail-fast behaviour:**
>
> 1. Run the registry tests directly:
>    ```bash
>    uv run pytest tests/test_registry.py -v
>    ```
> 2. Inspect stderr for Amplifier's module-load error line:
>    ```
>    Failed to load module 'tool-cua'
>    ```
>    If that line is absent, the module loaded (or the run never attempted to load it).

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

---

## macOS real backend requirements

The `auto` backend (and the default when no backend is configured) on macOS **fails fast** if the required pyobjc dependencies are missing — it will **not** silently fall back to fixture data. This makes misconfiguration immediately visible rather than producing confusing no-op behaviour.

### Install pyobjc dependencies

```bash
~/.local/share/uv/tools/amplifier/bin/python -m pip install \
  "pyobjc-framework-Quartz>=10.0" \
  "pyobjc-framework-ApplicationServices>=10.0"
```

### Grant Accessibility permission

Semantic tree access and all input actions (click, type, key press, scroll) require macOS Accessibility permission. Grant it in:

**System Settings → Privacy & Security → Accessibility**

Add the application or terminal that runs Amplifier.

### CI / testing without a real desktop

Use `backend: fixture` to get deterministic fake data without any OS dependencies:

```yaml
# .amplifier/settings.local.yaml
modules:
  tools:
    - module: tool-cua
      config:
        backend: fixture
```

`FixtureBackend` is always reachable through an explicit `backend: fixture` setting. The `auto` backend will **never** silently return fixture data — if the real backend cannot initialise on a recognised platform, it raises an actionable error pointing here.
