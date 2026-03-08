# amplifier-bundle-cua Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an Amplifier-native bundle for computer-use automation with universal desktop control, semantic UI understanding, and safe bounded operation — starting with a macOS real backend and fixture/simulator backend.

**Architecture:** The bundle centers on `modules/tool-cua/` which exposes screenshot capture, input actions, window/screen info, and semantic inspection through a three-layer architecture: tool interface → target abstraction → backend implementations. A fixture backend enables deterministic testing. A real macOS backend provides host-desktop control. Windows/Linux stubs preserve host-agnostic architecture. Agents and recipes sit above the module, providing the dual-world operator loop and bounded recovery workflows.

**Tech Stack:** Python ≥3.11, pytest, pytest-asyncio, ruff, pyright, uv workspaces, hatchling. macOS backend uses pyobjc-framework-Quartz + pyobjc-framework-ApplicationServices (optional deps). No Rust toolchain required for v1.

---

## Design Decisions Locked for This Plan

These were open questions in the design doc. They are now resolved:

| Question | Decision |
|---|---|
| Shared code location | All code lives inside `modules/tool-cua/amplifier_module_tool_cua/`. No separate `src/` package for v1. |
| Observation schema | Defined concretely in Tasks 4-6. Dataclasses: `ScreenInfo`, `CursorPosition`, `WindowInfo`, `SemanticElement`, `Observation`, `ActionResult`. |
| macOS accessibility deps | `pyobjc-framework-Quartz` for screenshots/cursor/windows/input. `pyobjc-framework-ApplicationServices` for accessibility tree. Both optional. |
| Approval gate mechanism | Standard Amplifier recipe `approval:` blocks. The tool module does not implement approval gates — that's the recipe/agent layer's job. |
| Tool return format | Plain dicts from `execute()` (follows graph-canvas pattern). No `amplifier_core` dependency. |
| Bundle reference name | `cua` (used in behavior/agent/context references like `cua:modules/tool-cua`). |

---

## Target File Tree

When all tasks are complete, the repo should look like this:

```
amplifier-bundle-cua/
├── .gitignore
├── bundle.md
├── pyproject.toml                          # root workspace config
├── ruff.toml
├── pytest.ini
├── behaviors/
│   ├── cua-core.yaml                       # primitives behavior
│   ├── cua-operator.yaml                   # operator agent behavior
│   └── cua-recipes.yaml                    # recipes behavior
├── agents/
│   ├── cua-operator.md                     # main operator agent
│   └── cua-planner.md                      # planner/reviewer agent
├── context/
│   ├── dual-world-reasoning.md
│   ├── action-confidence.md
│   └── recovery-patterns.md
├── recipes/
│   ├── observe-and-act.yaml
│   ├── bounded-task.yaml
│   └── recovery-workflow.yaml
├── modules/
│   └── tool-cua/
│       ├── pyproject.toml                  # module build config
│       └── amplifier_module_tool_cua/
│           ├── __init__.py                 # mount function
│           ├── models.py                   # ActionStatus, ActionResult, observations
│           ├── target.py                   # Target protocol
│           ├── tool.py                     # CuaTool class
│           └── backends/
│               ├── __init__.py
│               ├── fixture.py             # fixture/simulator backend
│               ├── macos.py               # real macOS backend
│               ├── windows.py             # Windows stub
│               ├── linux.py               # Linux stub
│               └── registry.py            # auto-detection + factory
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_target_protocol.py
│   ├── test_fixture_backend.py
│   ├── test_tool.py
│   ├── test_macos_backend.py
│   ├── test_stubs.py
│   ├── test_registry.py
│   ├── test_conformance.py
│   └── test_integration.py
└── docs/
    └── plans/
        ├── 2026-03-06-amplifier-bundle-cua-design.md
        └── 2026-03-08-amplifier-bundle-cua-implementation.md
```

---

## Phase 1: Repo Scaffolding

These tasks create the project skeleton. No TDD here — just config files and directory structure.

---

### Task 1: Config files and root pyproject.toml

**Files:**
- Create: `.gitignore`
- Create: `ruff.toml`
- Create: `pytest.ini`
- Create: `pyproject.toml`

**Step 1: Create `.gitignore`**

```
__pycache__/
*.pyc
*.py[cod]
*.egg-info/
dist/
build/
.eggs/
.venv/
.pytest_cache/
.ruff_cache/
.mypy_cache/
.pyright/
*.so
*.dylib
```

**Step 2: Create `ruff.toml`**

```toml
line-length = 100
target-version = "py311"

[lint]
select = ["E", "F", "I", "W"]
```

**Step 3: Create `pytest.ini`**

```ini
[pytest]
testpaths = tests
asyncio_mode = auto
```

**Step 4: Create root `pyproject.toml`**

```toml
[project]
name = "amplifier-bundle-cua"
version = "0.1.0"
description = "Amplifier bundle for computer-use automation"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.4.0",
]

[tool.uv.workspace]
members = [
    "modules/tool-cua",
]

[tool.uv.sources]
tool-cua = { workspace = true }

[tool.pytest.ini_options]
asyncio_mode = "auto"

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.4.0",
]
```

**Step 5: Commit**

```bash
git add .gitignore ruff.toml pytest.ini pyproject.toml
git commit -m "chore: add project config files"
```

---

### Task 2: Module skeleton and virtual environment

**Files:**
- Create: `modules/tool-cua/pyproject.toml`
- Create: `modules/tool-cua/amplifier_module_tool_cua/__init__.py`
- Create: `modules/tool-cua/amplifier_module_tool_cua/models.py`
- Create: `modules/tool-cua/amplifier_module_tool_cua/backends/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Step 1: Create `modules/tool-cua/pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "tool-cua"
version = "0.1.0"
description = "Computer-use automation tool module for Amplifier"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
macos = [
    "pyobjc-framework-Quartz>=10.0",
    "pyobjc-framework-ApplicationServices>=10.0",
]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24.0",
]

[project.entry-points."amplifier.modules"]
tool-cua = "amplifier_module_tool_cua:mount"

[tool.hatch.build.targets.wheel]
packages = ["amplifier_module_tool_cua"]

[tool.hatch.metadata]
allow-direct-references = true

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

**Step 2: Create `modules/tool-cua/amplifier_module_tool_cua/__init__.py`**

```python
"""Computer-use automation tool module for Amplifier."""

from typing import Any

__amplifier_module_type__ = "tool"


async def mount(coordinator: Any, config: dict[str, Any] | None = None) -> None:
    """Mount the CUA tool into the Amplifier coordinator.

    Called by Amplifier when loading the module via its entry point.
    """
    # Implementation will be added in Task 13
    raise NotImplementedError("mount() not yet implemented")
```

**Step 3: Create `modules/tool-cua/amplifier_module_tool_cua/models.py`**

```python
"""Core data models for computer-use automation."""
```

**Step 4: Create `modules/tool-cua/amplifier_module_tool_cua/backends/__init__.py`**

```python
"""Backend implementations for CUA target abstraction."""
```

**Step 5: Create `tests/__init__.py`**

```python
```

**Step 6: Create `tests/conftest.py`**

```python
"""Shared test fixtures for amplifier-bundle-cua."""

from __future__ import annotations

from typing import Any

import pytest


class FakeCoordinator:
    """Minimal coordinator for testing module mount."""

    def __init__(self) -> None:
        self._mounted: dict[str, dict[str, Any]] = {}

    async def mount(self, mount_point: str, module: Any, name: str | None = None) -> None:
        bucket = self._mounted.setdefault(mount_point, {})
        bucket[name or type(module).__name__] = module


@pytest.fixture
def coordinator() -> FakeCoordinator:
    return FakeCoordinator()
```

**Step 7: Create virtual environment and verify**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv sync
```
Expected: Virtual environment created in `.venv/`, dependencies installed.

Run:
```bash
uv run pytest tests/ -v
```
Expected: `no tests ran` (0 tests collected, no errors).

**Step 8: Commit**

```bash
git add modules/ tests/
git commit -m "chore: add module skeleton, test infrastructure, and venv"
```

---

### Task 3: Bundle manifest and directory structure

**Files:**
- Create: `bundle.md`
- Create: `behaviors/` (empty dir, with placeholder)
- Create: `agents/` (empty dir, with placeholder)
- Create: `context/` (empty dir, with placeholder)
- Create: `recipes/` (empty dir, with placeholder)

**Step 1: Create `bundle.md`**

```markdown
---
bundle:
  name: cua
  version: 0.1.0
  description: Computer-use automation — universal desktop control, semantic UI understanding, and safe bounded operation

includes:
  - bundle: cua:behaviors/cua-core
  - bundle: cua:behaviors/cua-operator
  - bundle: cua:behaviors/cua-recipes
---

# Computer-Use Automation

@cua:context/dual-world-reasoning.md
```

**Step 2: Create placeholder files for empty directories**

Create these empty placeholder files so git tracks the directories. They will be replaced by real files in later tasks:

- `behaviors/.gitkeep` (empty file)
- `agents/.gitkeep` (empty file)
- `context/.gitkeep` (empty file)
- `recipes/.gitkeep` (empty file)

**Step 3: Commit**

```bash
git add bundle.md behaviors/ agents/ context/ recipes/
git commit -m "chore: add bundle manifest and directory structure"
```

---

## Phase 2: Core Data Models

These tasks define the normalized data models that all backends, tools, and agents share. Strict TDD from here forward.

---

### Task 4: ActionStatus enum and ActionResult dataclass

**Files:**
- Create: `tests/test_models.py`
- Modify: `modules/tool-cua/amplifier_module_tool_cua/models.py`

**Step 1: Write the failing tests**

Create `tests/test_models.py`:

```python
"""Tests for core CUA data models."""

from __future__ import annotations

from amplifier_module_tool_cua.models import ActionResult, ActionStatus


class TestActionStatus:
    def test_status_values_exist(self):
        assert ActionStatus.SUCCESS == "success"
        assert ActionStatus.FAILURE == "failure"
        assert ActionStatus.BLOCKED == "blocked"
        assert ActionStatus.AMBIGUOUS == "ambiguous"

    def test_status_is_string(self):
        assert isinstance(ActionStatus.SUCCESS, str)
        assert isinstance(ActionStatus.FAILURE, str)


class TestActionResult:
    def test_success_result(self):
        result = ActionResult(status=ActionStatus.SUCCESS)
        assert result.status == ActionStatus.SUCCESS
        assert result.message == ""
        assert result.data == {}

    def test_failure_result_with_message(self):
        result = ActionResult(status=ActionStatus.FAILURE, message="permission denied")
        assert result.status == ActionStatus.FAILURE
        assert result.message == "permission denied"

    def test_result_with_data(self):
        result = ActionResult(
            status=ActionStatus.SUCCESS,
            data={"screenshot_base64": "abc123"},
        )
        assert result.data["screenshot_base64"] == "abc123"

    def test_blocked_result(self):
        result = ActionResult(status=ActionStatus.BLOCKED, message="accessibility not enabled")
        assert result.status == ActionStatus.BLOCKED

    def test_ambiguous_result(self):
        result = ActionResult(
            status=ActionStatus.AMBIGUOUS,
            message="click executed but state unchanged",
        )
        assert result.status == ActionStatus.AMBIGUOUS
```

**Step 2: Run tests to verify they fail**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_models.py -v
```
Expected: FAIL — `ImportError: cannot import name 'ActionResult' from 'amplifier_module_tool_cua.models'`

**Step 3: Implement the models**

Replace `modules/tool-cua/amplifier_module_tool_cua/models.py` with:

```python
"""Core data models for computer-use automation.

All backends, tools, and agents share these types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ActionStatus(str, Enum):
    """Normalized status for every tool call result.

    - SUCCESS: action completed, post-state confirms expected outcome
    - FAILURE: action could not be performed (clear error)
    - BLOCKED: denied due to approvals, permissions, missing capabilities, or policy
    - AMBIGUOUS: action executed but post-state did not confirm expected change
    """

    SUCCESS = "success"
    FAILURE = "failure"
    BLOCKED = "blocked"
    AMBIGUOUS = "ambiguous"


@dataclass
class ActionResult:
    """Normalized result returned by every backend method."""

    status: ActionStatus
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)
```

**Step 4: Run tests to verify they pass**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_models.py -v
```
Expected: All 6 tests PASS.

**Step 5: Commit**

```bash
git add tests/test_models.py modules/tool-cua/amplifier_module_tool_cua/models.py
git commit -m "feat: add ActionStatus enum and ActionResult dataclass"
```

---

### Task 5: Visual observation models

**Files:**
- Modify: `tests/test_models.py`
- Modify: `modules/tool-cua/amplifier_module_tool_cua/models.py`

**Step 1: Add failing tests to `tests/test_models.py`**

Append to the file:

```python
from amplifier_module_tool_cua.models import CursorPosition, ScreenInfo, WindowInfo


class TestScreenInfo:
    def test_basic_screen(self):
        screen = ScreenInfo(width=1920, height=1080)
        assert screen.width == 1920
        assert screen.height == 1080
        assert screen.scale_factor == 1.0

    def test_retina_screen(self):
        screen = ScreenInfo(width=1440, height=900, scale_factor=2.0)
        assert screen.scale_factor == 2.0


class TestCursorPosition:
    def test_position(self):
        pos = CursorPosition(x=100, y=200)
        assert pos.x == 100
        assert pos.y == 200


class TestWindowInfo:
    def test_basic_window(self):
        win = WindowInfo(
            title="Untitled",
            app_name="TextEdit",
            bounds={"x": 0, "y": 0, "width": 800, "height": 600},
        )
        assert win.title == "Untitled"
        assert win.app_name == "TextEdit"
        assert win.bounds["width"] == 800
        assert win.is_focused is False

    def test_focused_window(self):
        win = WindowInfo(
            title="main.py",
            app_name="VS Code",
            bounds={"x": 100, "y": 50, "width": 1200, "height": 800},
            is_focused=True,
        )
        assert win.is_focused is True
```

**Step 2: Run tests to verify new tests fail**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_models.py -v
```
Expected: FAIL — `ImportError: cannot import name 'ScreenInfo'`

**Step 3: Add visual models to `models.py`**

Add these classes after `ActionResult` in `modules/tool-cua/amplifier_module_tool_cua/models.py`:

```python
@dataclass
class ScreenInfo:
    """Display geometry."""

    width: int
    height: int
    scale_factor: float = 1.0


@dataclass
class CursorPosition:
    """Cursor coordinates in screen space."""

    x: int
    y: int


@dataclass
class WindowInfo:
    """Metadata about a single window."""

    title: str
    app_name: str
    bounds: dict[str, int]
    is_focused: bool = False
```

**Step 4: Run tests to verify they pass**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_models.py -v
```
Expected: All 11 tests PASS.

**Step 5: Commit**

```bash
git add tests/test_models.py modules/tool-cua/amplifier_module_tool_cua/models.py
git commit -m "feat: add ScreenInfo, CursorPosition, and WindowInfo models"
```

---

### Task 6: Semantic models and Observation container

**Files:**
- Modify: `tests/test_models.py`
- Modify: `modules/tool-cua/amplifier_module_tool_cua/models.py`

**Step 1: Add failing tests to `tests/test_models.py`**

Append to the file:

```python
from amplifier_module_tool_cua.models import Observation, SemanticElement


class TestSemanticElement:
    def test_basic_element(self):
        el = SemanticElement(role="AXButton", label="Submit")
        assert el.role == "AXButton"
        assert el.label == "Submit"
        assert el.value is None
        assert el.children == []

    def test_element_with_children(self):
        child = SemanticElement(role="AXStaticText", label="OK")
        parent = SemanticElement(role="AXButton", label="Submit", children=[child])
        assert len(parent.children) == 1
        assert parent.children[0].role == "AXStaticText"

    def test_element_with_bounds(self):
        el = SemanticElement(
            role="AXTextField",
            label="Search",
            bounds={"x": 10, "y": 20, "width": 200, "height": 30},
        )
        assert el.bounds["width"] == 200


class TestObservation:
    def test_empty_observation(self):
        obs = Observation()
        assert obs.screenshot_base64 is None
        assert obs.screen_info is None
        assert obs.cursor_position is None
        assert obs.focused_window is None
        assert obs.windows == []
        assert obs.semantic_tree == []

    def test_full_observation(self):
        obs = Observation(
            screenshot_base64="iVBORw...",
            screen_info=ScreenInfo(width=1920, height=1080),
            cursor_position=CursorPosition(x=500, y=300),
            focused_window=WindowInfo(
                title="test", app_name="App",
                bounds={"x": 0, "y": 0, "width": 800, "height": 600},
                is_focused=True,
            ),
            windows=[],
            semantic_tree=[SemanticElement(role="AXWindow", label="test")],
        )
        assert obs.screenshot_base64 == "iVBORw..."
        assert obs.screen_info.width == 1920
        assert obs.cursor_position.x == 500
        assert obs.focused_window.is_focused is True
        assert len(obs.semantic_tree) == 1
```

**Step 2: Run tests to verify new tests fail**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_models.py -v
```
Expected: FAIL — `ImportError: cannot import name 'SemanticElement'`

**Step 3: Add semantic models and Observation to `models.py`**

Add after `WindowInfo` in `modules/tool-cua/amplifier_module_tool_cua/models.py`:

```python
@dataclass
class SemanticElement:
    """A node in the accessibility / semantic tree."""

    role: str
    label: str | None = None
    value: str | None = None
    bounds: dict[str, int] | None = None
    children: list[SemanticElement] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class Observation:
    """Normalized dual-world observation combining visual and semantic state.

    This is the primary data structure agents receive when observing
    the current state of a target. Neither visual nor semantic is
    treated as secondary — both are first-class.
    """

    screenshot_base64: str | None = None
    screen_info: ScreenInfo | None = None
    cursor_position: CursorPosition | None = None
    focused_window: WindowInfo | None = None
    windows: list[WindowInfo] = field(default_factory=list)
    semantic_tree: list[SemanticElement] = field(default_factory=list)
```

**Step 4: Run tests to verify they pass**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_models.py -v
```
Expected: All 17 tests PASS.

**Step 5: Commit**

```bash
git add tests/test_models.py modules/tool-cua/amplifier_module_tool_cua/models.py
git commit -m "feat: add SemanticElement and Observation models"
```

---

## Phase 3: Target Protocol

---

### Task 7: Target protocol definition

**Files:**
- Create: `tests/test_target_protocol.py`
- Create: `modules/tool-cua/amplifier_module_tool_cua/target.py`

**Step 1: Write the failing tests**

Create `tests/test_target_protocol.py`:

```python
"""Tests for the Target protocol contract."""

from __future__ import annotations

import pytest

from amplifier_module_tool_cua.models import ActionResult, ActionStatus
from amplifier_module_tool_cua.target import Target


class MinimalTarget:
    """A bare-minimum Target implementation for protocol verification."""

    @property
    def platform(self) -> str:
        return "test"

    @property
    def capabilities(self) -> dict[str, bool]:
        return {"screenshot": True, "click": True, "type_text": True, "semantic_tree": False}

    async def screenshot(self) -> ActionResult:
        return ActionResult(status=ActionStatus.SUCCESS, data={"screenshot_base64": ""})

    async def cursor_position(self) -> ActionResult:
        return ActionResult(status=ActionStatus.SUCCESS, data={"x": 0, "y": 0})

    async def screen_info(self) -> ActionResult:
        return ActionResult(status=ActionStatus.SUCCESS, data={"width": 100, "height": 100})

    async def window_info(self) -> ActionResult:
        return ActionResult(status=ActionStatus.SUCCESS, data={"windows": [], "focused_window": None})

    async def semantic_tree(self, window_title: str | None = None) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message="not supported")

    async def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        return ActionResult(status=ActionStatus.SUCCESS)

    async def double_click(self, x: int, y: int) -> ActionResult:
        return ActionResult(status=ActionStatus.SUCCESS)

    async def type_text(self, text: str) -> ActionResult:
        return ActionResult(status=ActionStatus.SUCCESS)

    async def key_press(self, key: str, modifiers: list[str] | None = None) -> ActionResult:
        return ActionResult(status=ActionStatus.SUCCESS)

    async def scroll(self, x: int, y: int, dx: int = 0, dy: int = 0) -> ActionResult:
        return ActionResult(status=ActionStatus.SUCCESS)

    async def move_cursor(self, x: int, y: int) -> ActionResult:
        return ActionResult(status=ActionStatus.SUCCESS)


class TestTargetProtocol:
    def test_minimal_target_satisfies_protocol(self):
        target = MinimalTarget()
        assert isinstance(target, Target)

    def test_platform_property(self):
        target = MinimalTarget()
        assert target.platform == "test"

    def test_capabilities_property(self):
        target = MinimalTarget()
        caps = target.capabilities
        assert caps["screenshot"] is True
        assert caps["semantic_tree"] is False

    @pytest.mark.asyncio
    async def test_screenshot_returns_action_result(self):
        target = MinimalTarget()
        result = await target.screenshot()
        assert isinstance(result, ActionResult)
        assert result.status == ActionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_blocked_capability_returns_blocked(self):
        target = MinimalTarget()
        result = await target.semantic_tree()
        assert result.status == ActionStatus.BLOCKED
```

**Step 2: Run tests to verify they fail**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_target_protocol.py -v
```
Expected: FAIL — `ImportError: cannot import name 'Target' from 'amplifier_module_tool_cua.target'`

**Step 3: Implement the Target protocol**

Create `modules/tool-cua/amplifier_module_tool_cua/target.py`:

```python
"""Target protocol — the contract all CUA backends must satisfy.

A Target represents what the agent is controlling (host desktop, sandbox, VM).
The transport (how control is implemented) is an internal detail of each backend.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import ActionResult


@runtime_checkable
class Target(Protocol):
    """Protocol defining the observation/action contract for all backends.

    Every method returns an ActionResult with a normalized status.
    Backends that lack a capability should return BLOCKED, not raise.
    """

    @property
    def platform(self) -> str:
        """Platform identifier (e.g. 'macos', 'windows', 'linux', 'fixture')."""
        ...

    @property
    def capabilities(self) -> dict[str, bool]:
        """Map of capability name to availability.

        Standard keys: screenshot, cursor_position, screen_info, window_info,
        semantic_tree, click, double_click, type_text, key_press, scroll, move_cursor.
        """
        ...

    # -- Observation methods --

    async def screenshot(self) -> ActionResult:
        """Capture a screenshot. Returns base64 PNG in data['screenshot_base64']."""
        ...

    async def cursor_position(self) -> ActionResult:
        """Get cursor position. Returns data['x'] and data['y']."""
        ...

    async def screen_info(self) -> ActionResult:
        """Get screen geometry. Returns data['width'], data['height'], data['scale_factor']."""
        ...

    async def window_info(self) -> ActionResult:
        """Get window list. Returns data['windows'] list and data['focused_window']."""
        ...

    async def semantic_tree(self, window_title: str | None = None) -> ActionResult:
        """Get accessibility/semantic tree. Returns data['elements'] list."""
        ...

    # -- Action methods --

    async def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        """Click at screen coordinates."""
        ...

    async def double_click(self, x: int, y: int) -> ActionResult:
        """Double-click at screen coordinates."""
        ...

    async def type_text(self, text: str) -> ActionResult:
        """Type a text string."""
        ...

    async def key_press(self, key: str, modifiers: list[str] | None = None) -> ActionResult:
        """Press a key with optional modifiers."""
        ...

    async def scroll(self, x: int, y: int, dx: int = 0, dy: int = 0) -> ActionResult:
        """Scroll at screen coordinates."""
        ...

    async def move_cursor(self, x: int, y: int) -> ActionResult:
        """Move cursor to screen coordinates without clicking."""
        ...
```

**Step 4: Run tests to verify they pass**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_target_protocol.py -v
```
Expected: All 5 tests PASS.

**Step 5: Commit**

```bash
git add tests/test_target_protocol.py modules/tool-cua/amplifier_module_tool_cua/target.py
git commit -m "feat: add Target protocol for backend contract"
```

---

## Phase 4: Fixture Backend

The fixture backend enables deterministic testing without touching a real desktop. It returns canned observations and records actions.

---

### Task 8: Fixture backend — observation methods

**Files:**
- Create: `tests/test_fixture_backend.py`
- Create: `modules/tool-cua/amplifier_module_tool_cua/backends/fixture.py`

**Step 1: Write the failing tests**

Create `tests/test_fixture_backend.py`:

```python
"""Tests for the fixture/simulator backend."""

from __future__ import annotations

import pytest

from amplifier_module_tool_cua.models import ActionStatus
from amplifier_module_tool_cua.target import Target


@pytest.fixture
def backend():
    from amplifier_module_tool_cua.backends.fixture import FixtureBackend

    return FixtureBackend()


class TestFixtureProtocol:
    def test_satisfies_target_protocol(self, backend):
        assert isinstance(backend, Target)

    def test_platform(self, backend):
        assert backend.platform == "fixture"

    def test_all_capabilities_enabled(self, backend):
        caps = backend.capabilities
        assert caps["screenshot"] is True
        assert caps["click"] is True
        assert caps["semantic_tree"] is True


class TestFixtureObservation:
    @pytest.mark.asyncio
    async def test_screenshot(self, backend):
        result = await backend.screenshot()
        assert result.status == ActionStatus.SUCCESS
        assert "screenshot_base64" in result.data
        assert len(result.data["screenshot_base64"]) > 0

    @pytest.mark.asyncio
    async def test_cursor_position(self, backend):
        result = await backend.cursor_position()
        assert result.status == ActionStatus.SUCCESS
        assert "x" in result.data
        assert "y" in result.data

    @pytest.mark.asyncio
    async def test_screen_info(self, backend):
        result = await backend.screen_info()
        assert result.status == ActionStatus.SUCCESS
        assert result.data["width"] > 0
        assert result.data["height"] > 0
        assert "scale_factor" in result.data

    @pytest.mark.asyncio
    async def test_window_info(self, backend):
        result = await backend.window_info()
        assert result.status == ActionStatus.SUCCESS
        assert "windows" in result.data
        assert "focused_window" in result.data

    @pytest.mark.asyncio
    async def test_semantic_tree(self, backend):
        result = await backend.semantic_tree()
        assert result.status == ActionStatus.SUCCESS
        assert "elements" in result.data
        assert len(result.data["elements"]) > 0
```

**Step 2: Run tests to verify they fail**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_fixture_backend.py -v
```
Expected: FAIL — `ModuleNotFoundError` or `ImportError`

**Step 3: Implement the fixture backend observation methods**

Create `modules/tool-cua/amplifier_module_tool_cua/backends/fixture.py`:

```python
"""Fixture/simulator backend for deterministic testing.

Returns canned observations and records actions without touching a real desktop.
All capabilities are always available.
"""

from __future__ import annotations

from ..models import ActionResult, ActionStatus

# Minimal 1x1 transparent PNG, base64-encoded
_TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
    "2mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)

# Default fixture semantic tree
_DEFAULT_SEMANTIC_TREE = [
    {
        "role": "AXApplication",
        "label": "FixtureApp",
        "value": None,
        "bounds": {"x": 0, "y": 0, "width": 1920, "height": 1080},
        "children": [
            {
                "role": "AXWindow",
                "label": "Fixture Window",
                "value": None,
                "bounds": {"x": 100, "y": 100, "width": 800, "height": 600},
                "children": [
                    {
                        "role": "AXButton",
                        "label": "OK",
                        "value": None,
                        "bounds": {"x": 350, "y": 500, "width": 100, "height": 30},
                        "children": [],
                    },
                    {
                        "role": "AXTextField",
                        "label": "Search",
                        "value": "",
                        "bounds": {"x": 200, "y": 200, "width": 400, "height": 30},
                        "children": [],
                    },
                ],
            },
        ],
    },
]


class FixtureBackend:
    """Deterministic backend for testing. No real desktop interaction."""

    def __init__(self) -> None:
        self._cursor_x: int = 960
        self._cursor_y: int = 540
        self._action_log: list[dict] = []

    @property
    def platform(self) -> str:
        return "fixture"

    @property
    def capabilities(self) -> dict[str, bool]:
        return {
            "screenshot": True,
            "cursor_position": True,
            "screen_info": True,
            "window_info": True,
            "semantic_tree": True,
            "click": True,
            "double_click": True,
            "type_text": True,
            "key_press": True,
            "scroll": True,
            "move_cursor": True,
        }

    @property
    def action_log(self) -> list[dict]:
        """Recorded actions — useful for test assertions."""
        return list(self._action_log)

    # -- Observation methods --

    async def screenshot(self) -> ActionResult:
        return ActionResult(
            status=ActionStatus.SUCCESS,
            data={"screenshot_base64": _TINY_PNG_B64},
        )

    async def cursor_position(self) -> ActionResult:
        return ActionResult(
            status=ActionStatus.SUCCESS,
            data={"x": self._cursor_x, "y": self._cursor_y},
        )

    async def screen_info(self) -> ActionResult:
        return ActionResult(
            status=ActionStatus.SUCCESS,
            data={"width": 1920, "height": 1080, "scale_factor": 1.0},
        )

    async def window_info(self) -> ActionResult:
        return ActionResult(
            status=ActionStatus.SUCCESS,
            data={
                "windows": [
                    {
                        "title": "Fixture Window",
                        "app_name": "FixtureApp",
                        "bounds": {"x": 100, "y": 100, "width": 800, "height": 600},
                        "is_focused": True,
                    },
                ],
                "focused_window": {
                    "title": "Fixture Window",
                    "app_name": "FixtureApp",
                    "bounds": {"x": 100, "y": 100, "width": 800, "height": 600},
                    "is_focused": True,
                },
            },
        )

    async def semantic_tree(self, window_title: str | None = None) -> ActionResult:
        return ActionResult(
            status=ActionStatus.SUCCESS,
            data={"elements": _DEFAULT_SEMANTIC_TREE},
        )

    # -- Action methods (implemented in Task 9) --

    async def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        raise NotImplementedError

    async def double_click(self, x: int, y: int) -> ActionResult:
        raise NotImplementedError

    async def type_text(self, text: str) -> ActionResult:
        raise NotImplementedError

    async def key_press(self, key: str, modifiers: list[str] | None = None) -> ActionResult:
        raise NotImplementedError

    async def scroll(self, x: int, y: int, dx: int = 0, dy: int = 0) -> ActionResult:
        raise NotImplementedError

    async def move_cursor(self, x: int, y: int) -> ActionResult:
        raise NotImplementedError
```

**Step 4: Run tests to verify they pass**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_fixture_backend.py -v
```
Expected: All 8 tests PASS.

**Step 5: Commit**

```bash
git add tests/test_fixture_backend.py modules/tool-cua/amplifier_module_tool_cua/backends/fixture.py
git commit -m "feat: add fixture backend observation methods"
```

---

### Task 9: Fixture backend — action methods

**Files:**
- Modify: `tests/test_fixture_backend.py`
- Modify: `modules/tool-cua/amplifier_module_tool_cua/backends/fixture.py`

**Step 1: Add failing tests**

Append to `tests/test_fixture_backend.py`:

```python
class TestFixtureActions:
    @pytest.mark.asyncio
    async def test_click(self, backend):
        result = await backend.click(500, 300)
        assert result.status == ActionStatus.SUCCESS
        assert backend.action_log[-1]["action"] == "click"
        assert backend.action_log[-1]["x"] == 500

    @pytest.mark.asyncio
    async def test_click_updates_cursor(self, backend):
        await backend.click(500, 300)
        pos = await backend.cursor_position()
        assert pos.data["x"] == 500
        assert pos.data["y"] == 300

    @pytest.mark.asyncio
    async def test_double_click(self, backend):
        result = await backend.double_click(200, 400)
        assert result.status == ActionStatus.SUCCESS
        assert backend.action_log[-1]["action"] == "double_click"

    @pytest.mark.asyncio
    async def test_type_text(self, backend):
        result = await backend.type_text("hello world")
        assert result.status == ActionStatus.SUCCESS
        assert backend.action_log[-1]["text"] == "hello world"

    @pytest.mark.asyncio
    async def test_key_press(self, backend):
        result = await backend.key_press("return", modifiers=["command"])
        assert result.status == ActionStatus.SUCCESS
        assert backend.action_log[-1]["key"] == "return"
        assert backend.action_log[-1]["modifiers"] == ["command"]

    @pytest.mark.asyncio
    async def test_scroll(self, backend):
        result = await backend.scroll(400, 300, dx=0, dy=-3)
        assert result.status == ActionStatus.SUCCESS
        assert backend.action_log[-1]["dy"] == -3

    @pytest.mark.asyncio
    async def test_move_cursor(self, backend):
        result = await backend.move_cursor(100, 200)
        assert result.status == ActionStatus.SUCCESS
        pos = await backend.cursor_position()
        assert pos.data["x"] == 100
        assert pos.data["y"] == 200

    @pytest.mark.asyncio
    async def test_action_log_accumulates(self, backend):
        await backend.click(10, 20)
        await backend.type_text("a")
        await backend.scroll(0, 0, dy=1)
        assert len(backend.action_log) == 3
```

**Step 2: Run tests to verify new tests fail**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_fixture_backend.py::TestFixtureActions -v
```
Expected: FAIL — `NotImplementedError`

**Step 3: Implement the action methods**

In `modules/tool-cua/amplifier_module_tool_cua/backends/fixture.py`, replace the placeholder action methods (the `raise NotImplementedError` stubs) with:

```python
    async def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        self._cursor_x = x
        self._cursor_y = y
        self._action_log.append({"action": "click", "x": x, "y": y, "button": button})
        return ActionResult(status=ActionStatus.SUCCESS)

    async def double_click(self, x: int, y: int) -> ActionResult:
        self._cursor_x = x
        self._cursor_y = y
        self._action_log.append({"action": "double_click", "x": x, "y": y})
        return ActionResult(status=ActionStatus.SUCCESS)

    async def type_text(self, text: str) -> ActionResult:
        self._action_log.append({"action": "type_text", "text": text})
        return ActionResult(status=ActionStatus.SUCCESS)

    async def key_press(self, key: str, modifiers: list[str] | None = None) -> ActionResult:
        self._action_log.append({
            "action": "key_press",
            "key": key,
            "modifiers": modifiers or [],
        })
        return ActionResult(status=ActionStatus.SUCCESS)

    async def scroll(self, x: int, y: int, dx: int = 0, dy: int = 0) -> ActionResult:
        self._action_log.append({"action": "scroll", "x": x, "y": y, "dx": dx, "dy": dy})
        return ActionResult(status=ActionStatus.SUCCESS)

    async def move_cursor(self, x: int, y: int) -> ActionResult:
        self._cursor_x = x
        self._cursor_y = y
        self._action_log.append({"action": "move_cursor", "x": x, "y": y})
        return ActionResult(status=ActionStatus.SUCCESS)
```

**Step 4: Run tests to verify they pass**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_fixture_backend.py -v
```
Expected: All 16 tests PASS.

**Step 5: Commit**

```bash
git add tests/test_fixture_backend.py modules/tool-cua/amplifier_module_tool_cua/backends/fixture.py
git commit -m "feat: add fixture backend action methods with action log"
```

---

### Task 10: Golden observation tests

**Files:**
- Modify: `tests/test_fixture_backend.py`

**Step 1: Add golden observation tests**

Append to `tests/test_fixture_backend.py`:

```python
class TestGoldenObservations:
    """Verify fixture backend returns consistent, known observation shapes."""

    @pytest.mark.asyncio
    async def test_screenshot_is_valid_base64_png(self, backend):
        import base64

        result = await backend.screenshot()
        raw = base64.b64decode(result.data["screenshot_base64"])
        # PNG magic bytes
        assert raw[:4] == b"\x89PNG"

    @pytest.mark.asyncio
    async def test_semantic_tree_structure(self, backend):
        result = await backend.semantic_tree()
        tree = result.data["elements"]
        # Root is an application
        assert tree[0]["role"] == "AXApplication"
        assert tree[0]["label"] == "FixtureApp"
        # Has a window child
        window = tree[0]["children"][0]
        assert window["role"] == "AXWindow"
        # Window has a button and a text field
        roles = {child["role"] for child in window["children"]}
        assert "AXButton" in roles
        assert "AXTextField" in roles

    @pytest.mark.asyncio
    async def test_semantic_tree_has_bounds(self, backend):
        result = await backend.semantic_tree()
        button = result.data["elements"][0]["children"][0]["children"][0]
        assert button["role"] == "AXButton"
        assert button["bounds"]["width"] == 100
        assert button["bounds"]["height"] == 30

    @pytest.mark.asyncio
    async def test_window_info_matches_semantic_tree(self, backend):
        """Fixture's visual and semantic worlds should be consistent."""
        win_result = await backend.window_info()
        sem_result = await backend.semantic_tree()
        focused = win_result.data["focused_window"]
        sem_window = sem_result.data["elements"][0]["children"][0]
        assert focused["title"] == sem_window["label"]

    @pytest.mark.asyncio
    async def test_default_screen_geometry(self, backend):
        result = await backend.screen_info()
        assert result.data == {"width": 1920, "height": 1080, "scale_factor": 1.0}

    @pytest.mark.asyncio
    async def test_default_cursor_is_center(self, backend):
        result = await backend.cursor_position()
        assert result.data == {"x": 960, "y": 540}
```

**Step 2: Run tests to verify they pass**

These tests should pass immediately since the fixture backend already returns the right data:

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_fixture_backend.py::TestGoldenObservations -v
```
Expected: All 6 tests PASS.

**Step 3: Commit**

```bash
git add tests/test_fixture_backend.py
git commit -m "test: add golden observation tests for fixture backend"
```

---

## Phase 5: Tool Surface

The `CuaTool` class is what Amplifier sees. It dispatches actions to the active backend.

---

### Task 11: CuaTool — observe actions

**Files:**
- Create: `tests/test_tool.py`
- Create: `modules/tool-cua/amplifier_module_tool_cua/tool.py`

**Step 1: Write the failing tests**

Create `tests/test_tool.py`:

```python
"""Tests for the CuaTool Amplifier tool surface."""

from __future__ import annotations

import pytest

from amplifier_module_tool_cua.backends.fixture import FixtureBackend
from amplifier_module_tool_cua.tool import CuaTool


@pytest.fixture
def tool():
    return CuaTool(backend=FixtureBackend())


class TestToolProperties:
    def test_name(self, tool):
        assert tool.name == "cua"

    def test_description_not_empty(self, tool):
        assert len(tool.description) > 20

    def test_input_schema_has_action(self, tool):
        schema = tool.input_schema
        assert "action" in schema["properties"]
        assert "enum" in schema["properties"]["action"]


class TestToolObserveActions:
    @pytest.mark.asyncio
    async def test_screenshot(self, tool):
        result = await tool.execute(arguments={"action": "screenshot"})
        assert result["status"] == "success"
        assert "screenshot_base64" in result["data"]

    @pytest.mark.asyncio
    async def test_cursor_position(self, tool):
        result = await tool.execute(arguments={"action": "cursor_position"})
        assert result["status"] == "success"
        assert "x" in result["data"]
        assert "y" in result["data"]

    @pytest.mark.asyncio
    async def test_screen_info(self, tool):
        result = await tool.execute(arguments={"action": "screen_info"})
        assert result["status"] == "success"
        assert result["data"]["width"] == 1920

    @pytest.mark.asyncio
    async def test_window_info(self, tool):
        result = await tool.execute(arguments={"action": "window_info"})
        assert result["status"] == "success"
        assert "windows" in result["data"]

    @pytest.mark.asyncio
    async def test_semantic_tree(self, tool):
        result = await tool.execute(arguments={"action": "semantic_tree"})
        assert result["status"] == "success"
        assert "elements" in result["data"]

    @pytest.mark.asyncio
    async def test_observe_composite(self, tool):
        """observe returns screenshot + cursor + windows + semantic tree together."""
        result = await tool.execute(arguments={"action": "observe"})
        assert result["status"] == "success"
        data = result["data"]
        assert "screenshot_base64" in data
        assert "cursor" in data
        assert "windows" in data
        assert "semantic_tree" in data

    @pytest.mark.asyncio
    async def test_unknown_action_returns_failure(self, tool):
        result = await tool.execute(arguments={"action": "fly_to_moon"})
        assert result["status"] == "failure"
        assert "unknown" in result["message"].lower()
```

**Step 2: Run tests to verify they fail**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_tool.py -v
```
Expected: FAIL — `ImportError: cannot import name 'CuaTool' from 'amplifier_module_tool_cua.tool'`

**Step 3: Implement CuaTool observe actions**

Create `modules/tool-cua/amplifier_module_tool_cua/tool.py`:

```python
"""CuaTool — the Amplifier-visible tool surface for computer-use automation.

Dispatches actions to the active backend. Provides mechanisms, not policy.
"""

from __future__ import annotations

import logging
from typing import Any

from .target import Target

logger = logging.getLogger(__name__)

_ACTIONS = [
    "screenshot",
    "cursor_position",
    "screen_info",
    "window_info",
    "semantic_tree",
    "observe",
    "click",
    "double_click",
    "type_text",
    "key_press",
    "scroll",
    "move_cursor",
]


class CuaTool:
    """LLM-callable tool for computer-use automation."""

    def __init__(self, backend: Target) -> None:
        self._backend = backend

    @property
    def name(self) -> str:
        return "cua"

    @property
    def description(self) -> str:
        return (
            "Computer-use automation: observe screens, interact with desktop elements, "
            "and inspect UI semantics. Use 'observe' for a full dual-world snapshot. "
            "Use specific actions (screenshot, click, type_text, etc.) for precise control."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": _ACTIONS,
                    "description": "The action to perform.",
                },
                "x": {"type": "integer", "description": "X coordinate (for click/scroll/move)."},
                "y": {"type": "integer", "description": "Y coordinate (for click/scroll/move)."},
                "button": {
                    "type": "string",
                    "enum": ["left", "right", "middle"],
                    "description": "Mouse button (for click). Default: left.",
                },
                "text": {"type": "string", "description": "Text to type (for type_text)."},
                "key": {"type": "string", "description": "Key name (for key_press)."},
                "modifiers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Modifier keys (for key_press). e.g. ['command', 'shift'].",
                },
                "dx": {"type": "integer", "description": "Horizontal scroll delta."},
                "dy": {"type": "integer", "description": "Vertical scroll delta."},
                "window_title": {
                    "type": "string",
                    "description": "Window title filter (for semantic_tree).",
                },
            },
            "required": ["action"],
        }

    async def execute(self, *, arguments: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Dispatch to the appropriate action handler."""
        action = arguments.get("action", "")

        try:
            if action == "screenshot":
                return self._to_dict(await self._backend.screenshot())
            elif action == "cursor_position":
                return self._to_dict(await self._backend.cursor_position())
            elif action == "screen_info":
                return self._to_dict(await self._backend.screen_info())
            elif action == "window_info":
                return self._to_dict(await self._backend.window_info())
            elif action == "semantic_tree":
                wt = arguments.get("window_title")
                return self._to_dict(await self._backend.semantic_tree(window_title=wt))
            elif action == "observe":
                return await self._handle_observe()
            # Input actions will be added in Task 12
            else:
                return {"status": "failure", "message": f"Unknown action: {action}", "data": {}}
        except Exception as exc:
            logger.exception("CuaTool action '%s' raised", action)
            return {"status": "failure", "message": str(exc), "data": {}}

    async def _handle_observe(self) -> dict[str, Any]:
        """Composite observe: screenshot + cursor + windows + semantic tree."""
        data: dict[str, Any] = {}

        screenshot = await self._backend.screenshot()
        if screenshot.status.value == "success":
            data["screenshot_base64"] = screenshot.data.get("screenshot_base64")

        cursor = await self._backend.cursor_position()
        if cursor.status.value == "success":
            data["cursor"] = cursor.data

        windows = await self._backend.window_info()
        if windows.status.value == "success":
            data["windows"] = windows.data.get("windows", [])
            data["focused_window"] = windows.data.get("focused_window")

        semantic = await self._backend.semantic_tree()
        if semantic.status.value == "success":
            data["semantic_tree"] = semantic.data.get("elements", [])

        return {"status": "success", "data": data, "message": ""}

    @staticmethod
    def _to_dict(result: Any) -> dict[str, Any]:
        return {
            "status": result.status.value,
            "data": result.data,
            "message": result.message,
        }
```

**Step 4: Run tests to verify they pass**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_tool.py -v
```
Expected: All 10 tests PASS.

**Step 5: Commit**

```bash
git add tests/test_tool.py modules/tool-cua/amplifier_module_tool_cua/tool.py
git commit -m "feat: add CuaTool with observe actions"
```

---

### Task 12: CuaTool — input actions

**Files:**
- Modify: `tests/test_tool.py`
- Modify: `modules/tool-cua/amplifier_module_tool_cua/tool.py`

**Step 1: Add failing tests**

Append to `tests/test_tool.py`:

```python
class TestToolInputActions:
    @pytest.mark.asyncio
    async def test_click(self, tool):
        result = await tool.execute(arguments={"action": "click", "x": 500, "y": 300})
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_click_with_button(self, tool):
        result = await tool.execute(
            arguments={"action": "click", "x": 100, "y": 200, "button": "right"}
        )
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_double_click(self, tool):
        result = await tool.execute(arguments={"action": "double_click", "x": 300, "y": 400})
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_type_text(self, tool):
        result = await tool.execute(arguments={"action": "type_text", "text": "hello"})
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_key_press(self, tool):
        result = await tool.execute(
            arguments={"action": "key_press", "key": "return", "modifiers": ["command"]}
        )
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_scroll(self, tool):
        result = await tool.execute(
            arguments={"action": "scroll", "x": 400, "y": 300, "dx": 0, "dy": -3}
        )
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_move_cursor(self, tool):
        result = await tool.execute(arguments={"action": "move_cursor", "x": 100, "y": 200})
        assert result["status"] == "success"
```

**Step 2: Run tests to verify new tests fail**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_tool.py::TestToolInputActions -v
```
Expected: FAIL — returns `{"status": "failure", "message": "Unknown action: click"}`

**Step 3: Add input action dispatching to CuaTool**

In `modules/tool-cua/amplifier_module_tool_cua/tool.py`, find the `# Input actions will be added in Task 12` comment inside `execute()` and replace it with:

```python
            elif action == "click":
                return self._to_dict(
                    await self._backend.click(
                        x=arguments.get("x", 0),
                        y=arguments.get("y", 0),
                        button=arguments.get("button", "left"),
                    )
                )
            elif action == "double_click":
                return self._to_dict(
                    await self._backend.double_click(
                        x=arguments.get("x", 0),
                        y=arguments.get("y", 0),
                    )
                )
            elif action == "type_text":
                return self._to_dict(
                    await self._backend.type_text(text=arguments.get("text", ""))
                )
            elif action == "key_press":
                return self._to_dict(
                    await self._backend.key_press(
                        key=arguments.get("key", ""),
                        modifiers=arguments.get("modifiers"),
                    )
                )
            elif action == "scroll":
                return self._to_dict(
                    await self._backend.scroll(
                        x=arguments.get("x", 0),
                        y=arguments.get("y", 0),
                        dx=arguments.get("dx", 0),
                        dy=arguments.get("dy", 0),
                    )
                )
            elif action == "move_cursor":
                return self._to_dict(
                    await self._backend.move_cursor(
                        x=arguments.get("x", 0),
                        y=arguments.get("y", 0),
                    )
                )
```

**Step 4: Run all tool tests to verify they pass**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_tool.py -v
```
Expected: All 17 tests PASS.

**Step 5: Commit**

```bash
git add tests/test_tool.py modules/tool-cua/amplifier_module_tool_cua/tool.py
git commit -m "feat: add input actions to CuaTool"
```

---

### Task 13: Module mount function

**Files:**
- Modify: `tests/test_tool.py`
- Modify: `modules/tool-cua/amplifier_module_tool_cua/__init__.py`

**Step 1: Add failing tests**

Append to `tests/test_tool.py`:

```python
from amplifier_module_tool_cua import mount


class TestMount:
    @pytest.mark.asyncio
    async def test_mount_registers_tool(self, coordinator):
        await mount(coordinator, config={"backend": "fixture"})
        assert "cua" in coordinator._mounted.get("tools", {})

    @pytest.mark.asyncio
    async def test_mounted_tool_is_cua_tool(self, coordinator):
        await mount(coordinator, config={"backend": "fixture"})
        tool = coordinator._mounted["tools"]["cua"]
        assert tool.name == "cua"

    @pytest.mark.asyncio
    async def test_mount_fixture_backend_works(self, coordinator):
        await mount(coordinator, config={"backend": "fixture"})
        tool = coordinator._mounted["tools"]["cua"]
        result = await tool.execute(arguments={"action": "screenshot"})
        assert result["status"] == "success"
```

**Step 2: Run tests to verify new tests fail**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_tool.py::TestMount -v
```
Expected: FAIL — `NotImplementedError: mount() not yet implemented`

**Step 3: Implement the mount function**

Replace `modules/tool-cua/amplifier_module_tool_cua/__init__.py` with:

```python
"""Computer-use automation tool module for Amplifier."""

from __future__ import annotations

import logging
from typing import Any

__amplifier_module_type__ = "tool"

logger = logging.getLogger(__name__)


async def mount(coordinator: Any, config: dict[str, Any] | None = None) -> None:
    """Mount the CUA tool into the Amplifier coordinator.

    Config options:
        backend: Force a specific backend. Values: "fixture", "auto" (default).
                 "auto" detects the current platform and picks the best backend.
    """
    from .backends.registry import get_backend
    from .tool import CuaTool

    config = config or {}
    backend_name = config.get("backend", "auto")
    backend = get_backend(backend_name)

    tool = CuaTool(backend=backend)
    await coordinator.mount("tools", tool, name=tool.name)
    logger.info("tool-cua mounted with backend=%s", backend.platform)
```

Also, create the registry module now as a minimal stub (it will be fully implemented in Task 18):

Create `modules/tool-cua/amplifier_module_tool_cua/backends/registry.py`:

```python
"""Backend auto-detection and factory."""

from __future__ import annotations

from ..target import Target


def get_backend(name: str) -> Target:
    """Get a backend by name. Full implementation in Task 18."""
    if name == "fixture":
        from .fixture import FixtureBackend

        return FixtureBackend()
    elif name == "auto":
        # Full auto-detection will be implemented in Task 18.
        # For now, always return fixture backend.
        from .fixture import FixtureBackend

        return FixtureBackend()
    else:
        raise ValueError(f"Unknown backend: {name}")


def detect_backend() -> Target:
    """Auto-detect backend. Full implementation in Task 18."""
    from .fixture import FixtureBackend

    return FixtureBackend()
```

**Step 4: Run tests to verify they pass**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_tool.py -v
```
Expected: All 20 tests PASS.

**Step 5: Run full test suite**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/ -v
```
Expected: All tests PASS (should be ~40+ tests at this point).

**Step 6: Commit**

```bash
git add modules/tool-cua/amplifier_module_tool_cua/__init__.py modules/tool-cua/amplifier_module_tool_cua/backends/registry.py tests/test_tool.py
git commit -m "feat: add mount function and backend registry stub"
```

---

## Phase 6: macOS Backend

The real macOS backend uses pyobjc for screenshots, input, window info, and accessibility. Tests mock the platform calls so they run anywhere.

**Important:** The macOS backend requires `pyobjc-framework-Quartz` and `pyobjc-framework-ApplicationServices`. These are optional dependencies that only exist on macOS. All tests in this phase use mocks/monkeypatching — they do NOT require a real macOS desktop.

---

### Task 14: macOS backend — screenshot and screen info

**Files:**
- Create: `tests/test_macos_backend.py`
- Create: `modules/tool-cua/amplifier_module_tool_cua/backends/macos.py`

**Step 1: Write the failing tests**

Create `tests/test_macos_backend.py`:

```python
"""Tests for the macOS backend. Uses mocks — runs on any platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from amplifier_module_tool_cua.models import ActionStatus
from amplifier_module_tool_cua.target import Target


@pytest.fixture
def macos_backend():
    from amplifier_module_tool_cua.backends.macos import MacOSBackend

    return MacOSBackend(_skip_availability_check=True)


class TestMacOSProtocol:
    def test_satisfies_target_protocol(self, macos_backend):
        assert isinstance(macos_backend, Target)

    def test_platform(self, macos_backend):
        assert macos_backend.platform == "macos"


class TestMacOSScreenshot:
    @pytest.mark.asyncio
    async def test_screenshot_success(self, macos_backend, monkeypatch):
        async def fake_capture():
            return "iVBORw0KGgoAAAANSUhEUg=="

        monkeypatch.setattr(macos_backend, "_capture_screenshot", fake_capture)
        result = await macos_backend.screenshot()
        assert result.status == ActionStatus.SUCCESS
        assert result.data["screenshot_base64"] == "iVBORw0KGgoAAAANSUhEUg=="

    @pytest.mark.asyncio
    async def test_screenshot_failure(self, macos_backend, monkeypatch):
        async def failing_capture():
            raise RuntimeError("screencapture failed")

        monkeypatch.setattr(macos_backend, "_capture_screenshot", failing_capture)
        result = await macos_backend.screenshot()
        assert result.status == ActionStatus.FAILURE
        assert "screencapture failed" in result.message


class TestMacOSScreenInfo:
    @pytest.mark.asyncio
    async def test_screen_info_success(self, macos_backend, monkeypatch):
        def fake_get_screen():
            return {"width": 2560, "height": 1440, "scale_factor": 2.0}

        monkeypatch.setattr(macos_backend, "_get_screen_info_sync", fake_get_screen)
        result = await macos_backend.screen_info()
        assert result.status == ActionStatus.SUCCESS
        assert result.data["width"] == 2560
        assert result.data["scale_factor"] == 2.0
```

**Step 2: Run tests to verify they fail**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_macos_backend.py -v
```
Expected: FAIL — `ImportError`

**Step 3: Implement macOS backend skeleton with screenshot and screen info**

Create `modules/tool-cua/amplifier_module_tool_cua/backends/macos.py`:

```python
"""macOS host-desktop backend using Quartz and ApplicationServices.

Screenshots use the screencapture CLI (always available on macOS).
Input events use Quartz CGEvent APIs.
Accessibility uses ApplicationServices AXUIElement APIs.

All pyobjc imports are deferred so the module can be loaded on any platform
for testing. Pass _skip_availability_check=True to bypass platform detection.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import tempfile
from typing import Any

from ..models import ActionResult, ActionStatus

logger = logging.getLogger(__name__)


class MacOSBackend:
    """Real macOS backend. Requires macOS + appropriate permissions."""

    def __init__(self, *, _skip_availability_check: bool = False) -> None:
        self._available = True
        if not _skip_availability_check:
            self._check_availability()

    def _check_availability(self) -> None:
        import sys

        if sys.platform != "darwin":
            self._available = False
            return
        try:
            import Quartz  # noqa: F401
        except ImportError:
            self._available = False

    @property
    def platform(self) -> str:
        return "macos"

    @property
    def capabilities(self) -> dict[str, bool]:
        return {
            "screenshot": self._available,
            "cursor_position": self._available,
            "screen_info": self._available,
            "window_info": self._available,
            "semantic_tree": self._available,
            "click": self._available,
            "double_click": self._available,
            "type_text": self._available,
            "key_press": self._available,
            "scroll": self._available,
            "move_cursor": self._available,
        }

    def _blocked(self, msg: str = "macOS backend not available") -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=msg)

    # -- Screenshot --

    async def screenshot(self) -> ActionResult:
        try:
            data = await self._capture_screenshot()
            return ActionResult(status=ActionStatus.SUCCESS, data={"screenshot_base64": data})
        except Exception as exc:
            return ActionResult(status=ActionStatus.FAILURE, message=str(exc))

    async def _capture_screenshot(self) -> str:
        """Capture screenshot via screencapture CLI. Returns base64 PNG."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp_path = f.name
        try:
            proc = await asyncio.create_subprocess_exec(
                "screencapture", "-x", "-t", "png", tmp_path,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
            if proc.returncode != 0:
                raise RuntimeError(f"screencapture exited with code {proc.returncode}")
            with open(tmp_path, "rb") as img:
                return base64.b64encode(img.read()).decode("ascii")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # -- Screen info --

    async def screen_info(self) -> ActionResult:
        try:
            data = self._get_screen_info_sync()
            return ActionResult(status=ActionStatus.SUCCESS, data=data)
        except Exception as exc:
            return ActionResult(status=ActionStatus.FAILURE, message=str(exc))

    def _get_screen_info_sync(self) -> dict[str, Any]:
        """Get main display geometry via Quartz."""
        import Quartz

        display = Quartz.CGMainDisplayID()
        width = Quartz.CGDisplayPixelsWide(display)
        height = Quartz.CGDisplayPixelsHigh(display)
        mode = Quartz.CGDisplayCopyDisplayMode(display)
        if mode:
            pixel_w = Quartz.CGDisplayModeGetPixelWidth(mode)
            scale = pixel_w / width if width else 1.0
        else:
            scale = 1.0
        return {"width": int(width), "height": int(height), "scale_factor": float(scale)}

    # -- Stubs for remaining methods (implemented in Task 15 and 16) --

    async def cursor_position(self) -> ActionResult:
        raise NotImplementedError

    async def window_info(self) -> ActionResult:
        raise NotImplementedError

    async def semantic_tree(self, window_title: str | None = None) -> ActionResult:
        raise NotImplementedError

    async def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        raise NotImplementedError

    async def double_click(self, x: int, y: int) -> ActionResult:
        raise NotImplementedError

    async def type_text(self, text: str) -> ActionResult:
        raise NotImplementedError

    async def key_press(self, key: str, modifiers: list[str] | None = None) -> ActionResult:
        raise NotImplementedError

    async def scroll(self, x: int, y: int, dx: int = 0, dy: int = 0) -> ActionResult:
        raise NotImplementedError

    async def move_cursor(self, x: int, y: int) -> ActionResult:
        raise NotImplementedError
```

**Step 4: Run tests to verify they pass**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_macos_backend.py -v
```
Expected: All 5 tests PASS.

**Step 5: Commit**

```bash
git add tests/test_macos_backend.py modules/tool-cua/amplifier_module_tool_cua/backends/macos.py
git commit -m "feat: add macOS backend with screenshot and screen info"
```

---

### Task 15: macOS backend — cursor, window, and input actions

**Files:**
- Modify: `tests/test_macos_backend.py`
- Modify: `modules/tool-cua/amplifier_module_tool_cua/backends/macos.py`

**Step 1: Add failing tests**

Append to `tests/test_macos_backend.py`:

```python
class TestMacOSCursorAndWindow:
    @pytest.mark.asyncio
    async def test_cursor_position(self, macos_backend, monkeypatch):
        def fake_cursor():
            return (500, 300)

        monkeypatch.setattr(macos_backend, "_get_cursor_sync", fake_cursor)
        result = await macos_backend.cursor_position()
        assert result.status == ActionStatus.SUCCESS
        assert result.data["x"] == 500
        assert result.data["y"] == 300

    @pytest.mark.asyncio
    async def test_window_info(self, macos_backend, monkeypatch):
        def fake_windows():
            return [
                {
                    "title": "main.py",
                    "app_name": "VS Code",
                    "bounds": {"x": 0, "y": 0, "width": 1200, "height": 800},
                    "is_focused": True,
                },
            ]

        monkeypatch.setattr(macos_backend, "_get_windows_sync", fake_windows)
        result = await macos_backend.window_info()
        assert result.status == ActionStatus.SUCCESS
        assert len(result.data["windows"]) == 1
        assert result.data["focused_window"]["title"] == "main.py"


class TestMacOSInputActions:
    @pytest.mark.asyncio
    async def test_click(self, macos_backend, monkeypatch):
        calls = []

        async def fake_click(x, y, button):
            calls.append(("click", x, y, button))

        monkeypatch.setattr(macos_backend, "_perform_click", fake_click)
        result = await macos_backend.click(500, 300, "left")
        assert result.status == ActionStatus.SUCCESS
        assert calls == [("click", 500, 300, "left")]

    @pytest.mark.asyncio
    async def test_type_text(self, macos_backend, monkeypatch):
        calls = []

        async def fake_type(text):
            calls.append(text)

        monkeypatch.setattr(macos_backend, "_perform_type", fake_type)
        result = await macos_backend.type_text("hello")
        assert result.status == ActionStatus.SUCCESS
        assert calls == ["hello"]

    @pytest.mark.asyncio
    async def test_key_press(self, macos_backend, monkeypatch):
        calls = []

        async def fake_key(key, modifiers):
            calls.append((key, modifiers))

        monkeypatch.setattr(macos_backend, "_perform_key_press", fake_key)
        result = await macos_backend.key_press("return", modifiers=["command"])
        assert result.status == ActionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_scroll(self, macos_backend, monkeypatch):
        calls = []

        async def fake_scroll(x, y, dx, dy):
            calls.append((x, y, dx, dy))

        monkeypatch.setattr(macos_backend, "_perform_scroll", fake_scroll)
        result = await macos_backend.scroll(400, 300, dx=0, dy=-3)
        assert result.status == ActionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_move_cursor(self, macos_backend, monkeypatch):
        calls = []

        async def fake_move(x, y):
            calls.append((x, y))

        monkeypatch.setattr(macos_backend, "_perform_move", fake_move)
        result = await macos_backend.move_cursor(100, 200)
        assert result.status == ActionStatus.SUCCESS
```

**Step 2: Run tests to verify new tests fail**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_macos_backend.py::TestMacOSCursorAndWindow -v
```
Expected: FAIL — `NotImplementedError`

**Step 3: Implement cursor, window, and input methods**

In `modules/tool-cua/amplifier_module_tool_cua/backends/macos.py`, replace the `NotImplementedError` stubs for `cursor_position`, `window_info`, `click`, `double_click`, `type_text`, `key_press`, `scroll`, and `move_cursor` with:

```python
    # -- Cursor position --

    async def cursor_position(self) -> ActionResult:
        try:
            x, y = self._get_cursor_sync()
            return ActionResult(status=ActionStatus.SUCCESS, data={"x": x, "y": y})
        except Exception as exc:
            return ActionResult(status=ActionStatus.FAILURE, message=str(exc))

    def _get_cursor_sync(self) -> tuple[int, int]:
        """Get cursor position via Quartz."""
        import Quartz

        event = Quartz.CGEventCreate(None)
        point = Quartz.CGEventGetLocation(event)
        return int(point.x), int(point.y)

    # -- Window info --

    async def window_info(self) -> ActionResult:
        try:
            windows = self._get_windows_sync()
            focused = next((w for w in windows if w.get("is_focused")), None)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                data={"windows": windows, "focused_window": focused},
            )
        except Exception as exc:
            return ActionResult(status=ActionStatus.FAILURE, message=str(exc))

    def _get_windows_sync(self) -> list[dict[str, Any]]:
        """Get on-screen window list via Quartz."""
        import Quartz

        window_list = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
            Quartz.kCGNullWindowID,
        )
        results = []
        for w in window_list or []:
            bounds_dict = w.get(Quartz.kCGWindowBounds, {})
            results.append({
                "title": str(w.get(Quartz.kCGWindowName, "") or ""),
                "app_name": str(w.get(Quartz.kCGWindowOwnerName, "") or ""),
                "bounds": {
                    "x": int(bounds_dict.get("X", 0)),
                    "y": int(bounds_dict.get("Y", 0)),
                    "width": int(bounds_dict.get("Width", 0)),
                    "height": int(bounds_dict.get("Height", 0)),
                },
                "is_focused": int(w.get(Quartz.kCGWindowLayer, 999)) == 0,
            })
        return results

    # -- Click --

    async def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        try:
            await self._perform_click(x, y, button)
            return ActionResult(status=ActionStatus.SUCCESS)
        except Exception as exc:
            return ActionResult(status=ActionStatus.FAILURE, message=str(exc))

    async def _perform_click(self, x: int, y: int, button: str) -> None:
        """Perform a mouse click via Quartz CGEvent."""
        import Quartz

        point = Quartz.CGPoint(x, y)
        btn_map = {
            "left": (
                Quartz.kCGEventLeftMouseDown,
                Quartz.kCGEventLeftMouseUp,
                Quartz.kCGMouseButtonLeft,
            ),
            "right": (
                Quartz.kCGEventRightMouseDown,
                Quartz.kCGEventRightMouseUp,
                Quartz.kCGMouseButtonRight,
            ),
        }
        down_type, up_type, btn = btn_map.get(button, btn_map["left"])
        ev_down = Quartz.CGEventCreateMouseEvent(None, down_type, point, btn)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev_down)
        ev_up = Quartz.CGEventCreateMouseEvent(None, up_type, point, btn)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev_up)

    # -- Double click --

    async def double_click(self, x: int, y: int) -> ActionResult:
        try:
            await self._perform_click(x, y, "left")
            await self._perform_click(x, y, "left")
            return ActionResult(status=ActionStatus.SUCCESS)
        except Exception as exc:
            return ActionResult(status=ActionStatus.FAILURE, message=str(exc))

    # -- Type text --

    async def type_text(self, text: str) -> ActionResult:
        try:
            await self._perform_type(text)
            return ActionResult(status=ActionStatus.SUCCESS)
        except Exception as exc:
            return ActionResult(status=ActionStatus.FAILURE, message=str(exc))

    async def _perform_type(self, text: str) -> None:
        """Type characters via Quartz keyboard events."""
        import Quartz

        for char in text:
            ev_down = Quartz.CGEventCreateKeyboardEvent(None, 0, True)
            Quartz.CGEventKeyboardSetUnicodeString(ev_down, len(char), char)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev_down)
            ev_up = Quartz.CGEventCreateKeyboardEvent(None, 0, False)
            Quartz.CGEventKeyboardSetUnicodeString(ev_up, len(char), char)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev_up)

    # -- Key press --

    async def key_press(self, key: str, modifiers: list[str] | None = None) -> ActionResult:
        try:
            await self._perform_key_press(key, modifiers)
            return ActionResult(status=ActionStatus.SUCCESS)
        except Exception as exc:
            return ActionResult(status=ActionStatus.FAILURE, message=str(exc))

    _KEY_CODES: dict[str, int] = {
        "return": 36, "tab": 48, "space": 49, "delete": 51,
        "escape": 53, "up": 126, "down": 125, "left": 123, "right": 124,
        "f1": 122, "f2": 120, "f3": 99, "f4": 118, "f5": 96, "f6": 97,
    }

    async def _perform_key_press(self, key: str, modifiers: list[str] | None) -> None:
        """Press a key with optional modifiers via Quartz."""
        import Quartz

        key_code = self._KEY_CODES.get(key.lower(), 0)
        flags = 0
        for mod in (modifiers or []):
            if mod == "command":
                flags |= Quartz.kCGEventFlagMaskCommand
            elif mod == "shift":
                flags |= Quartz.kCGEventFlagMaskShift
            elif mod == "option":
                flags |= Quartz.kCGEventFlagMaskAlternate
            elif mod == "control":
                flags |= Quartz.kCGEventFlagMaskControl

        ev_down = Quartz.CGEventCreateKeyboardEvent(None, key_code, True)
        if flags:
            Quartz.CGEventSetFlags(ev_down, flags)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev_down)

        ev_up = Quartz.CGEventCreateKeyboardEvent(None, key_code, False)
        if flags:
            Quartz.CGEventSetFlags(ev_up, flags)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev_up)

    # -- Scroll --

    async def scroll(self, x: int, y: int, dx: int = 0, dy: int = 0) -> ActionResult:
        try:
            await self._perform_scroll(x, y, dx, dy)
            return ActionResult(status=ActionStatus.SUCCESS)
        except Exception as exc:
            return ActionResult(status=ActionStatus.FAILURE, message=str(exc))

    async def _perform_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        """Scroll at position via Quartz."""
        import Quartz

        # Move cursor to position first
        move_ev = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventMouseMoved, Quartz.CGPoint(x, y), 0
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, move_ev)
        # Scroll
        scroll_ev = Quartz.CGEventCreateScrollWheelEvent(
            None, Quartz.kCGScrollEventUnitLine, 2, dy, dx
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, scroll_ev)

    # -- Move cursor --

    async def move_cursor(self, x: int, y: int) -> ActionResult:
        try:
            await self._perform_move(x, y)
            return ActionResult(status=ActionStatus.SUCCESS)
        except Exception as exc:
            return ActionResult(status=ActionStatus.FAILURE, message=str(exc))

    async def _perform_move(self, x: int, y: int) -> None:
        """Move cursor without clicking via Quartz."""
        import Quartz

        event = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventMouseMoved, Quartz.CGPoint(x, y), 0
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
```

Also keep the `semantic_tree` stub as `raise NotImplementedError` — it will be implemented in Task 16.

**Step 4: Run tests to verify they pass**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_macos_backend.py -v
```
Expected: All 12 tests PASS.

**Step 5: Commit**

```bash
git add tests/test_macos_backend.py modules/tool-cua/amplifier_module_tool_cua/backends/macos.py
git commit -m "feat: add macOS backend cursor, window, and input actions"
```

---

### Task 16: macOS backend — semantic tree

**Files:**
- Modify: `tests/test_macos_backend.py`
- Modify: `modules/tool-cua/amplifier_module_tool_cua/backends/macos.py`

**Step 1: Add failing tests**

Append to `tests/test_macos_backend.py`:

```python
class TestMacOSSemanticTree:
    @pytest.mark.asyncio
    async def test_semantic_tree_success(self, macos_backend, monkeypatch):
        def fake_tree(window_title=None):
            return [
                {
                    "role": "AXApplication",
                    "label": "TestApp",
                    "value": None,
                    "bounds": None,
                    "children": [
                        {"role": "AXWindow", "label": "Main", "value": None,
                         "bounds": None, "children": []},
                    ],
                },
            ]

        monkeypatch.setattr(macos_backend, "_get_semantic_tree_sync", fake_tree)
        result = await macos_backend.semantic_tree()
        assert result.status == ActionStatus.SUCCESS
        assert result.data["elements"][0]["role"] == "AXApplication"
        assert len(result.data["elements"][0]["children"]) == 1

    @pytest.mark.asyncio
    async def test_semantic_tree_failure(self, macos_backend, monkeypatch):
        def failing_tree(window_title=None):
            raise RuntimeError("accessibility not enabled")

        monkeypatch.setattr(macos_backend, "_get_semantic_tree_sync", failing_tree)
        result = await macos_backend.semantic_tree()
        assert result.status == ActionStatus.FAILURE
        assert "accessibility" in result.message.lower()

    @pytest.mark.asyncio
    async def test_semantic_tree_with_window_filter(self, macos_backend, monkeypatch):
        def filtered_tree(window_title=None):
            if window_title == "Settings":
                return [{"role": "AXWindow", "label": "Settings", "value": None,
                         "bounds": None, "children": []}]
            return []

        monkeypatch.setattr(macos_backend, "_get_semantic_tree_sync", filtered_tree)
        result = await macos_backend.semantic_tree(window_title="Settings")
        assert result.status == ActionStatus.SUCCESS
        assert result.data["elements"][0]["label"] == "Settings"
```

**Step 2: Run tests to verify new tests fail**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_macos_backend.py::TestMacOSSemanticTree -v
```
Expected: FAIL — `NotImplementedError`

**Step 3: Implement semantic tree method**

In `modules/tool-cua/amplifier_module_tool_cua/backends/macos.py`, replace the `semantic_tree` stub with:

```python
    # -- Semantic tree --

    async def semantic_tree(self, window_title: str | None = None) -> ActionResult:
        try:
            elements = self._get_semantic_tree_sync(window_title=window_title)
            return ActionResult(status=ActionStatus.SUCCESS, data={"elements": elements})
        except Exception as exc:
            return ActionResult(status=ActionStatus.FAILURE, message=str(exc))

    def _get_semantic_tree_sync(
        self, window_title: str | None = None, max_depth: int = 5
    ) -> list[dict[str, Any]]:
        """Get accessibility tree via ApplicationServices AXUIElement API.

        Requires Accessibility permissions in System Settings > Privacy.
        """
        import ApplicationServices as AX

        system = AX.AXUIElementCreateSystemWide()
        err, focused_app = AX.AXUIElementCopyAttributeValue(
            system, "AXFocusedApplication", None
        )
        if err != 0 or focused_app is None:
            return []

        def traverse(element: Any, depth: int = 0) -> dict[str, Any] | None:
            if depth > max_depth:
                return None

            err, role = AX.AXUIElementCopyAttributeValue(element, "AXRole", None)
            if err != 0:
                return None

            err, title = AX.AXUIElementCopyAttributeValue(element, "AXTitle", None)
            err, value = AX.AXUIElementCopyAttributeValue(element, "AXValue", None)
            err, desc = AX.AXUIElementCopyAttributeValue(element, "AXDescription", None)

            node: dict[str, Any] = {
                "role": str(role) if role else "",
                "label": str(title or desc or ""),
                "value": str(value) if value else None,
                "bounds": None,
                "children": [],
            }

            # Try to get position and size
            try:
                err, pos_val = AX.AXUIElementCopyAttributeValue(element, "AXPosition", None)
                err2, size_val = AX.AXUIElementCopyAttributeValue(element, "AXSize", None)
                if err == 0 and err2 == 0 and pos_val and size_val:
                    pos_point = AX.AXValueGetValue(pos_val, AX.kAXValueCGPointType, None)
                    size_size = AX.AXValueGetValue(size_val, AX.kAXValueCGSizeType, None)
                    if pos_point and size_size:
                        node["bounds"] = {
                            "x": int(pos_point.x),
                            "y": int(pos_point.y),
                            "width": int(size_size.width),
                            "height": int(size_size.height),
                        }
            except Exception:
                pass  # Bounds are best-effort

            # Recurse into children
            err, children = AX.AXUIElementCopyAttributeValue(element, "AXChildren", None)
            if err == 0 and children:
                for child in children:
                    child_node = traverse(child, depth + 1)
                    if child_node:
                        node["children"].append(child_node)

            return node

        tree = traverse(focused_app)
        if tree is None:
            return []

        # If window_title filter is specified, find matching windows
        if window_title:
            matching = [
                c for c in tree.get("children", [])
                if c.get("label", "").lower() == window_title.lower()
                   or window_title.lower() in c.get("label", "").lower()
            ]
            return matching if matching else [tree]

        return [tree]
```

**Step 4: Run tests to verify they pass**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_macos_backend.py -v
```
Expected: All 15 tests PASS.

**Step 5: Commit**

```bash
git add tests/test_macos_backend.py modules/tool-cua/amplifier_module_tool_cua/backends/macos.py
git commit -m "feat: add macOS backend semantic tree via accessibility API"
```

---

## Phase 7: Platform Stubs and Backend Registry

---

### Task 17: Windows and Linux stub backends

**Files:**
- Create: `tests/test_stubs.py`
- Create: `modules/tool-cua/amplifier_module_tool_cua/backends/windows.py`
- Create: `modules/tool-cua/amplifier_module_tool_cua/backends/linux.py`

**Step 1: Write the failing tests**

Create `tests/test_stubs.py`:

```python
"""Tests for Windows and Linux stub backends."""

from __future__ import annotations

import pytest

from amplifier_module_tool_cua.models import ActionStatus
from amplifier_module_tool_cua.target import Target


class TestWindowsStub:
    @pytest.fixture
    def backend(self):
        from amplifier_module_tool_cua.backends.windows import WindowsStubBackend

        return WindowsStubBackend()

    def test_satisfies_protocol(self, backend):
        assert isinstance(backend, Target)

    def test_platform(self, backend):
        assert backend.platform == "windows"

    def test_all_capabilities_blocked(self, backend):
        for cap, available in backend.capabilities.items():
            assert available is False, f"{cap} should be False in stub"

    @pytest.mark.asyncio
    async def test_screenshot_blocked(self, backend):
        result = await backend.screenshot()
        assert result.status == ActionStatus.BLOCKED
        assert "not implemented" in result.message.lower()

    @pytest.mark.asyncio
    async def test_click_blocked(self, backend):
        result = await backend.click(0, 0)
        assert result.status == ActionStatus.BLOCKED

    @pytest.mark.asyncio
    async def test_semantic_tree_blocked(self, backend):
        result = await backend.semantic_tree()
        assert result.status == ActionStatus.BLOCKED


class TestLinuxStub:
    @pytest.fixture
    def backend(self):
        from amplifier_module_tool_cua.backends.linux import LinuxStubBackend

        return LinuxStubBackend()

    def test_satisfies_protocol(self, backend):
        assert isinstance(backend, Target)

    def test_platform(self, backend):
        assert backend.platform == "linux"

    def test_all_capabilities_blocked(self, backend):
        for cap, available in backend.capabilities.items():
            assert available is False

    @pytest.mark.asyncio
    async def test_screenshot_blocked(self, backend):
        result = await backend.screenshot()
        assert result.status == ActionStatus.BLOCKED

    @pytest.mark.asyncio
    async def test_type_text_blocked(self, backend):
        result = await backend.type_text("test")
        assert result.status == ActionStatus.BLOCKED
```

**Step 2: Run tests to verify they fail**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_stubs.py -v
```
Expected: FAIL — `ImportError`

**Step 3: Implement stub backends**

Both stubs follow the same pattern — every method returns BLOCKED.

Create `modules/tool-cua/amplifier_module_tool_cua/backends/windows.py`:

```python
"""Windows stub backend — all capabilities return BLOCKED.

This preserves the host-agnostic architecture. A real Windows backend
will replace these stubs in a future version.
"""

from __future__ import annotations

from ..models import ActionResult, ActionStatus

_MSG = "Windows backend not implemented yet"


class WindowsStubBackend:
    """Stub that satisfies the Target protocol but blocks all operations."""

    @property
    def platform(self) -> str:
        return "windows"

    @property
    def capabilities(self) -> dict[str, bool]:
        return {k: False for k in [
            "screenshot", "cursor_position", "screen_info", "window_info",
            "semantic_tree", "click", "double_click", "type_text",
            "key_press", "scroll", "move_cursor",
        ]}

    async def screenshot(self) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def cursor_position(self) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def screen_info(self) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def window_info(self) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def semantic_tree(self, window_title: str | None = None) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def double_click(self, x: int, y: int) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def type_text(self, text: str) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def key_press(self, key: str, modifiers: list[str] | None = None) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def scroll(self, x: int, y: int, dx: int = 0, dy: int = 0) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def move_cursor(self, x: int, y: int) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)
```

Create `modules/tool-cua/amplifier_module_tool_cua/backends/linux.py`:

```python
"""Linux stub backend — all capabilities return BLOCKED.

This preserves the host-agnostic architecture. A real Linux backend
will replace these stubs in a future version.
"""

from __future__ import annotations

from ..models import ActionResult, ActionStatus

_MSG = "Linux backend not implemented yet"


class LinuxStubBackend:
    """Stub that satisfies the Target protocol but blocks all operations."""

    @property
    def platform(self) -> str:
        return "linux"

    @property
    def capabilities(self) -> dict[str, bool]:
        return {k: False for k in [
            "screenshot", "cursor_position", "screen_info", "window_info",
            "semantic_tree", "click", "double_click", "type_text",
            "key_press", "scroll", "move_cursor",
        ]}

    async def screenshot(self) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def cursor_position(self) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def screen_info(self) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def window_info(self) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def semantic_tree(self, window_title: str | None = None) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def double_click(self, x: int, y: int) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def type_text(self, text: str) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def key_press(self, key: str, modifiers: list[str] | None = None) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def scroll(self, x: int, y: int, dx: int = 0, dy: int = 0) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)

    async def move_cursor(self, x: int, y: int) -> ActionResult:
        return ActionResult(status=ActionStatus.BLOCKED, message=_MSG)
```

**Step 4: Run tests to verify they pass**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_stubs.py -v
```
Expected: All 11 tests PASS.

**Step 5: Commit**

```bash
git add tests/test_stubs.py modules/tool-cua/amplifier_module_tool_cua/backends/windows.py modules/tool-cua/amplifier_module_tool_cua/backends/linux.py
git commit -m "feat: add Windows and Linux stub backends"
```

---

### Task 18: Backend registry and auto-detection

**Files:**
- Create: `tests/test_registry.py`
- Modify: `modules/tool-cua/amplifier_module_tool_cua/backends/registry.py`

**Step 1: Write the failing tests**

Create `tests/test_registry.py`:

```python
"""Tests for backend auto-detection and registry."""

from __future__ import annotations

from unittest.mock import patch

from amplifier_module_tool_cua.backends.registry import detect_backend, get_backend
from amplifier_module_tool_cua.target import Target


class TestDetectBackend:
    def test_returns_target(self):
        backend = detect_backend()
        assert isinstance(backend, Target)

    @patch("amplifier_module_tool_cua.backends.registry.sys")
    def test_darwin_returns_macos_or_fixture(self, mock_sys):
        mock_sys.platform = "darwin"
        backend = detect_backend()
        assert isinstance(backend, Target)
        # On macOS without pyobjc, falls back to fixture
        assert backend.platform in ("macos", "fixture")

    @patch("amplifier_module_tool_cua.backends.registry.sys")
    def test_win32_returns_windows_stub(self, mock_sys):
        mock_sys.platform = "win32"
        backend = detect_backend()
        assert backend.platform == "windows"

    @patch("amplifier_module_tool_cua.backends.registry.sys")
    def test_linux_returns_linux_stub(self, mock_sys):
        mock_sys.platform = "linux"
        backend = detect_backend()
        assert backend.platform == "linux"

    @patch("amplifier_module_tool_cua.backends.registry.sys")
    def test_unknown_platform_returns_fixture(self, mock_sys):
        mock_sys.platform = "freebsd"
        backend = detect_backend()
        assert backend.platform == "fixture"


class TestGetBackend:
    def test_fixture_by_name(self):
        backend = get_backend("fixture")
        assert backend.platform == "fixture"

    def test_auto_returns_something(self):
        backend = get_backend("auto")
        assert isinstance(backend, Target)

    def test_unknown_name_raises(self):
        import pytest

        with pytest.raises(ValueError, match="Unknown backend"):
            get_backend("quantum_computer")
```

**Step 2: Run tests to verify they fail**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_registry.py -v
```
Expected: FAIL — tests fail because the stub registry doesn't have `detect_backend` with `sys` access

**Step 3: Implement the full registry**

Replace `modules/tool-cua/amplifier_module_tool_cua/backends/registry.py` with:

```python
"""Backend auto-detection and factory.

Selects the best backend for the current platform or by explicit name.
"""

from __future__ import annotations

import sys

from ..target import Target


def detect_backend() -> Target:
    """Auto-detect and return the appropriate backend for the current platform.

    Falls back to FixtureBackend if no platform-specific backend is available.
    """
    if sys.platform == "darwin":
        try:
            from .macos import MacOSBackend

            backend = MacOSBackend()
            if backend._available:
                return backend
        except Exception:
            pass
        # Fall through to fixture if macOS backend can't initialize
        from .fixture import FixtureBackend

        return FixtureBackend()
    elif sys.platform == "win32":
        from .windows import WindowsStubBackend

        return WindowsStubBackend()
    elif sys.platform == "linux":
        from .linux import LinuxStubBackend

        return LinuxStubBackend()
    else:
        from .fixture import FixtureBackend

        return FixtureBackend()


def get_backend(name: str) -> Target:
    """Get a backend by explicit name.

    Args:
        name: One of "fixture", "macos", "windows", "linux", "auto".

    Raises:
        ValueError: If name is not recognized.
    """
    if name == "auto":
        return detect_backend()
    elif name == "fixture":
        from .fixture import FixtureBackend

        return FixtureBackend()
    elif name == "macos":
        from .macos import MacOSBackend

        return MacOSBackend()
    elif name == "windows":
        from .windows import WindowsStubBackend

        return WindowsStubBackend()
    elif name == "linux":
        from .linux import LinuxStubBackend

        return LinuxStubBackend()
    else:
        raise ValueError(f"Unknown backend: {name}")
```

**Step 4: Run tests to verify they pass**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_registry.py -v
```
Expected: All 8 tests PASS.

**Step 5: Commit**

```bash
git add tests/test_registry.py modules/tool-cua/amplifier_module_tool_cua/backends/registry.py
git commit -m "feat: add backend registry with auto-detection"
```

---

## Phase 8: Agents and Context

These are Amplifier markdown files — no Python code, no TDD. Follow the exact format from sibling bundle repos.

---

### Task 19: CUA operator and planner agents

**Files:**
- Create: `agents/cua-operator.md`
- Create: `agents/cua-planner.md`
- Delete: `agents/.gitkeep`

**Step 1: Create `agents/cua-operator.md`**

```markdown
---
meta:
  name: cua-operator
  description: |
    Computer-use automation operator. Observes desktop state via screenshots and semantic trees,
    plans atomic actions, and executes bounded control loops.

    **Use PROACTIVELY when:**
    - The user needs to interact with a desktop application
    - A task requires observing the current screen state
    - GUI automation is needed (clicking, typing, scrolling)
    - The user asks to "do something on screen" or "use the computer"

    **Capabilities:**
    - Dual-world observation (visual screenshots + semantic accessibility tree)
    - Atomic desktop actions (click, type, scroll, key press)
    - Bounded observe-act-verify loops
    - Structured uncertainty handling (success/failure/blocked/ambiguous)

    <example>
    Context: User wants to interact with a desktop app
    user: 'Open TextEdit and type hello world'
    assistant: 'I will delegate to cua:cua-operator to observe the screen, find TextEdit, and perform the typing action.'
    <commentary>Desktop interaction requires the operator's observation and action capabilities.</commentary>
    </example>

    <example>
    Context: User wants to check what's on screen
    user: 'What app is currently focused?'
    assistant: 'I will delegate to cua:cua-operator to observe the current screen state and report the focused application.'
    <commentary>Screen observation uses the operator's dual-world perception.</commentary>
    </example>
  model_role: coding

tools:
  - module: tool-cua
    source: cua:modules/tool-cua
---

# CUA Operator

You are the **computer-use automation operator**. You observe desktop state and perform precise, bounded actions. You reason over both visual and semantic information.

@cua:context/dual-world-reasoning.md
@cua:context/action-confidence.md
@cua:context/recovery-patterns.md

## Operating Principles

1. **Observe before acting** — Always capture current state before performing any action. Never act blind.
2. **One action at a time** — Each action is atomic. Never combine multiple clicks or keystrokes into a single step.
3. **Verify after acting** — After each action, re-observe to confirm the expected state change occurred.
4. **Prefer semantic when available** — If the accessibility tree provides element labels and roles, use them to confirm targets rather than relying solely on pixel coordinates.
5. **Report uncertainty honestly** — If an action result is ambiguous, say so. Do not claim success without evidence.
6. **Respect budgets** — Honor action count limits and retry ceilings. Escalate to the user rather than thrashing.

## Action Loop

For each step in a task:

1. **Observe** — Call `cua` with action `observe` to get screenshot + semantic tree + cursor + window state.
2. **Analyze** — Examine both visual and semantic data. Identify the target element or region.
3. **Plan** — Decide the single next atomic action (click, type, scroll, etc.).
4. **Act** — Execute exactly one action via the `cua` tool.
5. **Verify** — Call `observe` again. Compare with expected post-state.
6. **Decide** — If verified, continue to next step. If ambiguous, re-observe. If failed, report and stop or adapt.

## Safety Rules

- **Never** perform destructive actions without explicit user approval.
- **Never** type passwords or sensitive data unless the user explicitly provides them in the current turn.
- **Stop** if confidence drops below threshold — ask the user for guidance rather than guessing.
- **Stop** if the action budget is exhausted. Report what was accomplished and what remains.
```

**Step 2: Create `agents/cua-planner.md`**

```markdown
---
meta:
  name: cua-planner
  description: |
    Computer-use automation planner and reviewer. Decomposes multi-step desktop tasks
    into bounded action plans, reviews operator execution, and handles recovery.

    **Use PROACTIVELY when:**
    - A desktop task involves multiple steps or applications
    - An operator action failed or returned ambiguous results
    - Recovery planning is needed after an unexpected state change
    - The user requests a complex workflow spanning multiple UI interactions

    **Capabilities:**
    - Multi-step task decomposition into atomic operator actions
    - Failure analysis and recovery planning
    - Confidence assessment and escalation decisions
    - Strategy adaptation when initial approach fails

    <example>
    Context: Complex multi-step task
    user: 'Take a screenshot, open Safari, navigate to example.com, and save the page'
    assistant: 'I will delegate to cua:cua-planner to decompose this into a bounded action plan, then execute each step via the operator.'
    <commentary>Multi-step tasks need the planner to decompose, sequence, and handle failures.</commentary>
    </example>
  model_role: reasoning
---

# CUA Planner

You are the **computer-use automation planner**. You decompose complex desktop tasks into bounded sequences of atomic actions, review execution results, and plan recovery when things go wrong.

@cua:context/dual-world-reasoning.md
@cua:context/recovery-patterns.md

## Planning Principles

1. **Decompose into atomic steps** — Every plan step should be a single observation or a single action. No compound steps.
2. **Define success criteria** — For each step, specify what the post-state should look like if the step succeeded.
3. **Plan checkpoints** — Insert observation steps at natural boundaries to verify progress.
4. **Budget actions** — Assign maximum retry counts and total action limits. Plans must terminate.
5. **Plan recovery paths** — For critical steps, specify what to do if the step fails or returns ambiguous.

## Recovery Planning

When reviewing a failed or ambiguous operator result:

1. **Re-observe** — The first recovery step is always a fresh observation. Never retry blind.
2. **Diagnose** — Compare the current state with the expected state. Identify what went wrong.
3. **Adapt or escalate** — If the situation is recoverable, plan a new approach. If not, escalate to the user with a clear explanation.
4. **Never thrash** — If the same action has failed twice, do not retry a third time without changing strategy.
```

**Step 3: Remove `.gitkeep` and commit**

```bash
rm agents/.gitkeep
git add agents/cua-operator.md agents/cua-planner.md
git rm agents/.gitkeep 2>/dev/null || true
git commit -m "feat: add cua-operator and cua-planner agents"
```

---

### Task 20: Context files

**Files:**
- Create: `context/dual-world-reasoning.md`
- Create: `context/action-confidence.md`
- Create: `context/recovery-patterns.md`
- Delete: `context/.gitkeep`

**Step 1: Create `context/dual-world-reasoning.md`**

```markdown
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
```

**Step 2: Create `context/action-confidence.md`**

```markdown
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
```

**Step 3: Create `context/recovery-patterns.md`**

```markdown
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
```

**Step 4: Remove `.gitkeep` and commit**

```bash
rm context/.gitkeep
git add context/dual-world-reasoning.md context/action-confidence.md context/recovery-patterns.md
git rm context/.gitkeep 2>/dev/null || true
git commit -m "feat: add dual-world reasoning, action confidence, and recovery context files"
```

---

## Phase 9: Behaviors

---

### Task 21: Behavior files

**Files:**
- Create: `behaviors/cua-core.yaml`
- Create: `behaviors/cua-operator.yaml`
- Create: `behaviors/cua-recipes.yaml`
- Delete: `behaviors/.gitkeep`

**Step 1: Create `behaviors/cua-core.yaml`**

```yaml
bundle:
  name: behavior-cua-core
  version: 0.1.0
  description: Core CUA primitives — screenshot, input, window info, semantic inspection

modules:
  - module: tool-cua
    source: cua:modules/tool-cua

context:
  include:
    - cua:context/dual-world-reasoning.md
```

**Step 2: Create `behaviors/cua-operator.yaml`**

```yaml
bundle:
  name: behavior-cua-operator
  version: 0.1.0
  description: CUA operator agent with dual-world reasoning and safety context

agents:
  include:
    - cua:cua-operator
    - cua:cua-planner

context:
  include:
    - cua:context/action-confidence.md
    - cua:context/recovery-patterns.md
```

**Step 3: Create `behaviors/cua-recipes.yaml`**

```yaml
bundle:
  name: behavior-cua-recipes
  version: 0.1.0
  description: Repeatable CUA workflows — observe-and-act, bounded tasks, recovery

recipes:
  include:
    - cua:recipes/observe-and-act.yaml
    - cua:recipes/bounded-task.yaml
    - cua:recipes/recovery-workflow.yaml
```

**Step 4: Remove `.gitkeep` and commit**

```bash
rm behaviors/.gitkeep
git add behaviors/cua-core.yaml behaviors/cua-operator.yaml behaviors/cua-recipes.yaml
git rm behaviors/.gitkeep 2>/dev/null || true
git commit -m "feat: add cua-core, cua-operator, and cua-recipes behaviors"
```

---

## Phase 10: Recipes

---

### Task 22: observe-and-act recipe

**Files:**
- Create: `recipes/observe-and-act.yaml`

**Step 1: Create `recipes/observe-and-act.yaml`**

```yaml
name: observe-and-act
description: Basic operator loop — observe current screen state and perform a single action
version: 1.0.0
author: cua
tags:
  - cua
  - observe
  - action
  - basic

# Usage:
#   recipes execute cua:recipes/observe-and-act.yaml --context '{
#     "task_description": "Click the Submit button"
#   }'

context:
  task_description: ""

steps:
  - id: observe-screen
    agent: cua:cua-operator
    prompt: |
      Observe the current desktop state. Use the `cua` tool with action `observe`
      to capture a full dual-world snapshot (screenshot + semantic tree + cursor + windows).

      Report what you see:
      - What application is focused?
      - What are the main visible UI elements?
      - What is the cursor position?
      - What does the semantic tree show?
    output: observation_report
    timeout: 120

  - id: plan-action
    agent: cua:cua-operator
    prompt: |
      Based on your observation:

      {{observation_report}}

      The task is: {{task_description}}

      Plan exactly ONE atomic action to make progress on this task.
      Explain:
      1. What action you will take (click, type, scroll, etc.)
      2. The exact parameters (coordinates, text, etc.)
      3. What you expect to change after the action
      4. Your confidence level (high/medium/low)

      If you cannot identify a clear action, explain why and what additional
      information you need.
    output: action_plan
    timeout: 120

  - id: execute-action
    agent: cua:cua-operator
    prompt: |
      Execute the planned action:

      {{action_plan}}

      Use the `cua` tool to perform exactly one action.
      After executing, immediately observe again to verify the result.

      Report:
      1. The action result status (success/failure/blocked/ambiguous)
      2. What changed on screen after the action
      3. Whether the result matches your expectations
    output: action_result
    timeout: 120
```

**Step 2: Commit**

```bash
git add recipes/observe-and-act.yaml
git commit -m "feat: add observe-and-act recipe"
```

---

### Task 23: bounded-task recipe

**Files:**
- Create: `recipes/bounded-task.yaml`

**Step 1: Create `recipes/bounded-task.yaml`**

```yaml
name: bounded-task
description: Execute a multi-step desktop task with action budgets, approval gates, and bounded loops
version: 1.0.0
author: cua
tags:
  - cua
  - task
  - bounded
  - approval

# Usage:
#   recipes execute cua:recipes/bounded-task.yaml --context '{
#     "task_description": "Open Safari and navigate to example.com",
#     "max_actions": "10"
#   }'

context:
  task_description: ""
  max_actions: "10"

stages:
  - name: planning
    description: Decompose the task into bounded steps
    steps:
      - id: observe-initial
        agent: cua:cua-operator
        prompt: |
          Observe the current desktop state using the `cua` tool with action `observe`.
          Report the full state: focused app, windows, cursor, key semantic elements.
        output: initial_state
        timeout: 120

      - id: create-plan
        agent: cua:cua-planner
        prompt: |
          Current desktop state:
          {{initial_state}}

          Task: {{task_description}}
          Action budget: {{max_actions}} actions maximum.

          Create a step-by-step plan:
          1. List each atomic action needed
          2. Define success criteria for each step
          3. Identify potential failure points
          4. Total actions must not exceed {{max_actions}}

          Format as a numbered list with clear action descriptions.
        output: task_plan
        timeout: 180

    approval:
      required: true
      prompt: |
        ## Proposed Action Plan

        **Task:** {{task_description}}
        **Budget:** {{max_actions}} actions

        ### Plan
        {{task_plan}}

        **Approve** to begin execution, or **reject** to revise the plan.

  - name: execution
    description: Execute the approved plan step by step
    steps:
      - id: execute-plan
        agent: cua:cua-operator
        prompt: |
          Execute the following plan step by step:

          {{task_plan}}

          Rules:
          - Execute ONE action at a time
          - Observe after EVERY action to verify the result
          - If an action fails, re-observe and try a different approach (max 2 retries per step)
          - If a step cannot be completed after retries, stop and report
          - Track your action count — do not exceed {{max_actions}} total actions

          Report after completing or stopping:
          1. Steps completed successfully
          2. Steps that failed and why
          3. Total actions used
          4. Final screen state
        output: execution_result
        timeout: 600

    approval:
      required: true
      prompt: |
        ## Execution Complete

        **Task:** {{task_description}}

        ### Result
        {{execution_result}}

        **Approve** to confirm the task is complete, or **reject** if further action is needed.
```

**Step 2: Commit**

```bash
git add recipes/bounded-task.yaml
git commit -m "feat: add bounded-task recipe with approval gates"
```

---

### Task 24: recovery-workflow recipe

**Files:**
- Create: `recipes/recovery-workflow.yaml`
- Delete: `recipes/.gitkeep`

**Step 1: Create `recipes/recovery-workflow.yaml`**

```yaml
name: recovery-workflow
description: Recover from a failed or ambiguous CUA action — re-observe, diagnose, and adapt
version: 1.0.0
author: cua
tags:
  - cua
  - recovery
  - retry
  - diagnosis

# Usage:
#   recipes execute cua:recipes/recovery-workflow.yaml --context '{
#     "failed_action": "click at (500, 300)",
#     "expected_result": "Settings dialog should have opened",
#     "actual_result": "Nothing visible changed on screen"
#   }'

context:
  failed_action: ""
  expected_result: ""
  actual_result: ""

steps:
  - id: re-observe
    agent: cua:cua-operator
    prompt: |
      A previous action failed or produced an ambiguous result.

      **Failed action:** {{failed_action}}
      **Expected:** {{expected_result}}
      **Actual:** {{actual_result}}

      First, capture fresh state using `cua` with action `observe`.
      Report the FULL current state — do not assume anything from the previous observation.
    output: fresh_observation
    timeout: 120

  - id: diagnose
    agent: cua:cua-planner
    prompt: |
      Diagnose why the action failed:

      **Failed action:** {{failed_action}}
      **Expected:** {{expected_result}}
      **Actual:** {{actual_result}}

      **Fresh observation after re-observe:**
      {{fresh_observation}}

      Analyze:
      1. Is the current state what was expected BEFORE the failed action? (action had no effect)
      2. Is the current state something unexpected? (action had wrong effect)
      3. Is the target element still visible? (in screenshot or semantic tree)
      4. Could the failure be due to: wrong coordinates, wrong window focus, timing, permissions?

      Recommend ONE of:
      - **RETRY** with adjusted parameters (specify what to change)
      - **ALTERNATIVE** approach (specify the new strategy)
      - **ESCALATE** to user (explain what information is needed)
    output: diagnosis
    timeout: 180

  - id: attempt-recovery
    agent: cua:cua-operator
    prompt: |
      Based on the diagnosis:

      {{diagnosis}}

      If the recommendation is RETRY or ALTERNATIVE:
      - Execute the recommended action
      - Observe the result
      - Report whether recovery succeeded

      If the recommendation is ESCALATE:
      - Do not take any action
      - Summarize the situation for the user clearly
    output: recovery_result
    timeout: 180
```

**Step 2: Remove `.gitkeep` and commit**

```bash
rm recipes/.gitkeep
git add recipes/recovery-workflow.yaml
git rm recipes/.gitkeep 2>/dev/null || true
git commit -m "feat: add recovery-workflow recipe"
```

---

## Phase 11: Final Testing

---

### Task 25: Backend conformance test suite

**Files:**
- Create: `tests/test_conformance.py`

The conformance suite runs the same tests against every backend that satisfies the Target protocol.

**Step 1: Create `tests/test_conformance.py`**

```python
"""Backend conformance test suite.

Runs identical contract tests against every available backend.
This ensures all backends satisfy the same observation/action semantics.
"""

from __future__ import annotations

import pytest

from amplifier_module_tool_cua.backends.fixture import FixtureBackend
from amplifier_module_tool_cua.backends.linux import LinuxStubBackend
from amplifier_module_tool_cua.backends.windows import WindowsStubBackend
from amplifier_module_tool_cua.models import ActionStatus
from amplifier_module_tool_cua.target import Target

# All backends to test. macOS is excluded because it requires real pyobjc.
_BACKENDS = [
    pytest.param(FixtureBackend, id="fixture"),
    pytest.param(WindowsStubBackend, id="windows-stub"),
    pytest.param(LinuxStubBackend, id="linux-stub"),
]


@pytest.fixture(params=_BACKENDS)
def backend(request):
    cls = request.param
    return cls()


class TestConformanceProtocol:
    """Every backend satisfies the Target protocol."""

    def test_satisfies_protocol(self, backend):
        assert isinstance(backend, Target)

    def test_platform_is_string(self, backend):
        assert isinstance(backend.platform, str)
        assert len(backend.platform) > 0

    def test_capabilities_is_dict(self, backend):
        caps = backend.capabilities
        assert isinstance(caps, dict)
        # Must declare all standard capabilities
        required = {
            "screenshot", "cursor_position", "screen_info", "window_info",
            "semantic_tree", "click", "double_click", "type_text",
            "key_press", "scroll", "move_cursor",
        }
        assert required.issubset(set(caps.keys())), f"Missing caps: {required - set(caps.keys())}"


class TestConformanceResults:
    """Every backend returns ActionResult with valid status for all methods."""

    @pytest.mark.asyncio
    async def test_screenshot_returns_valid_status(self, backend):
        result = await backend.screenshot()
        assert result.status in (
            ActionStatus.SUCCESS, ActionStatus.FAILURE,
            ActionStatus.BLOCKED, ActionStatus.AMBIGUOUS,
        )

    @pytest.mark.asyncio
    async def test_cursor_position_returns_valid_status(self, backend):
        result = await backend.cursor_position()
        assert result.status in (
            ActionStatus.SUCCESS, ActionStatus.FAILURE,
            ActionStatus.BLOCKED, ActionStatus.AMBIGUOUS,
        )

    @pytest.mark.asyncio
    async def test_click_returns_valid_status(self, backend):
        result = await backend.click(0, 0)
        assert result.status in (
            ActionStatus.SUCCESS, ActionStatus.FAILURE,
            ActionStatus.BLOCKED, ActionStatus.AMBIGUOUS,
        )

    @pytest.mark.asyncio
    async def test_type_text_returns_valid_status(self, backend):
        result = await backend.type_text("test")
        assert result.status in (
            ActionStatus.SUCCESS, ActionStatus.FAILURE,
            ActionStatus.BLOCKED, ActionStatus.AMBIGUOUS,
        )

    @pytest.mark.asyncio
    async def test_semantic_tree_returns_valid_status(self, backend):
        result = await backend.semantic_tree()
        assert result.status in (
            ActionStatus.SUCCESS, ActionStatus.FAILURE,
            ActionStatus.BLOCKED, ActionStatus.AMBIGUOUS,
        )


class TestConformanceCapabilityConsistency:
    """Backends that declare a capability as False should return BLOCKED."""

    @pytest.mark.asyncio
    async def test_unavailable_screenshot_returns_blocked(self, backend):
        if not backend.capabilities.get("screenshot"):
            result = await backend.screenshot()
            assert result.status == ActionStatus.BLOCKED

    @pytest.mark.asyncio
    async def test_unavailable_semantic_tree_returns_blocked(self, backend):
        if not backend.capabilities.get("semantic_tree"):
            result = await backend.semantic_tree()
            assert result.status == ActionStatus.BLOCKED

    @pytest.mark.asyncio
    async def test_unavailable_click_returns_blocked(self, backend):
        if not backend.capabilities.get("click"):
            result = await backend.click(0, 0)
            assert result.status == ActionStatus.BLOCKED
```

**Step 2: Run the conformance suite**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_conformance.py -v
```
Expected: All tests PASS. Each test runs 3 times (once per backend).

**Step 3: Commit**

```bash
git add tests/test_conformance.py
git commit -m "test: add backend conformance test suite"
```

---

### Task 26: Bounded integration tests

**Files:**
- Create: `tests/test_integration.py`

These tests verify the full stack: mount -> tool -> backend -> result. They use the fixture backend so they run deterministically everywhere.

**Step 1: Create `tests/test_integration.py`**

```python
"""Bounded integration tests — full stack with fixture backend.

Tests the complete flow: mount -> CuaTool -> FixtureBackend -> ActionResult.
Emphasizes safety, bounded loops, and recovery patterns.
"""

from __future__ import annotations

import pytest

from amplifier_module_tool_cua import mount


@pytest.fixture
async def mounted_tool(coordinator):
    await mount(coordinator, config={"backend": "fixture"})
    return coordinator._mounted["tools"]["cua"]


class TestObserveFlow:
    """Test the observation pipeline end-to-end."""

    @pytest.mark.asyncio
    async def test_full_observe(self, mounted_tool):
        result = await mounted_tool.execute(arguments={"action": "observe"})
        assert result["status"] == "success"
        data = result["data"]
        # Visual world
        assert data["screenshot_base64"] is not None
        assert data["cursor"]["x"] == 960  # fixture default
        assert len(data["windows"]) > 0
        # Semantic world
        assert len(data["semantic_tree"]) > 0

    @pytest.mark.asyncio
    async def test_observe_then_act_then_verify(self, mounted_tool):
        """The core observe-act-verify loop."""
        # 1. Observe
        obs1 = await mounted_tool.execute(arguments={"action": "observe"})
        assert obs1["status"] == "success"
        initial_cursor = obs1["data"]["cursor"]

        # 2. Act — click somewhere else
        act = await mounted_tool.execute(arguments={"action": "click", "x": 200, "y": 400})
        assert act["status"] == "success"

        # 3. Verify — cursor should have moved
        obs2 = await mounted_tool.execute(arguments={"action": "cursor_position"})
        assert obs2["status"] == "success"
        assert obs2["data"]["x"] == 200
        assert obs2["data"]["y"] == 400
        # Cursor changed from initial position
        assert (obs2["data"]["x"], obs2["data"]["y"]) != (
            initial_cursor["x"], initial_cursor["y"]
        )


class TestActionAndVerify:
    @pytest.mark.asyncio
    async def test_type_text_flow(self, mounted_tool):
        result = await mounted_tool.execute(
            arguments={"action": "type_text", "text": "hello world"}
        )
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_key_press_with_modifiers(self, mounted_tool):
        result = await mounted_tool.execute(
            arguments={"action": "key_press", "key": "c", "modifiers": ["command"]}
        )
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_scroll_flow(self, mounted_tool):
        result = await mounted_tool.execute(
            arguments={"action": "scroll", "x": 500, "y": 500, "dx": 0, "dy": -5}
        )
        assert result["status"] == "success"


class TestSafetyBehavior:
    @pytest.mark.asyncio
    async def test_unknown_action_does_not_crash(self, mounted_tool):
        """Unknown actions should return failure, never raise."""
        result = await mounted_tool.execute(arguments={"action": "format_hard_drive"})
        assert result["status"] == "failure"

    @pytest.mark.asyncio
    async def test_missing_action_does_not_crash(self, mounted_tool):
        """Missing action key should return failure, never raise."""
        result = await mounted_tool.execute(arguments={})
        assert result["status"] == "failure"

    @pytest.mark.asyncio
    async def test_all_observation_actions_succeed(self, mounted_tool):
        """All observation actions should succeed with fixture backend."""
        for action in ["screenshot", "cursor_position", "screen_info", "window_info",
                        "semantic_tree", "observe"]:
            result = await mounted_tool.execute(arguments={"action": action})
            assert result["status"] == "success", f"{action} failed: {result}"

    @pytest.mark.asyncio
    async def test_all_input_actions_succeed(self, mounted_tool):
        """All input actions should succeed with fixture backend."""
        actions = [
            {"action": "click", "x": 100, "y": 100},
            {"action": "double_click", "x": 200, "y": 200},
            {"action": "type_text", "text": "test"},
            {"action": "key_press", "key": "return"},
            {"action": "scroll", "x": 0, "y": 0, "dy": 1},
            {"action": "move_cursor", "x": 50, "y": 50},
        ]
        for args in actions:
            result = await mounted_tool.execute(arguments=args)
            assert result["status"] == "success", f"{args['action']} failed: {result}"
```

**Step 2: Run integration tests**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/test_integration.py -v
```
Expected: All tests PASS.

**Step 3: Run the FULL test suite one final time**

Run:
```bash
cd /path/to/amplifier-bundle-cua && uv run pytest tests/ -v
```
Expected: ALL tests PASS. Should be approximately 80-90 tests total.

**Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add bounded integration tests for full observe-act-verify flow"
```

---

## Final Verification

After all 26 tasks are complete, run these final verification commands:

```bash
# Full test suite
cd /path/to/amplifier-bundle-cua && uv run pytest tests/ -v --tb=short

# Linting
uv run ruff check .

# Format check
uv run ruff format --check .

# Verify directory structure
find . -not -path './.git/*' -not -path './.venv/*' -not -path './.pytest_cache/*' -not -path './.ruff_cache/*' -not -path '*/__pycache__/*' -not -path '*/.*' | sort
```

If all pass, create a final commit:

```bash
git add -A
git status  # should be clean or only have the plan file
git log --oneline  # verify all task commits are present
```

---

## Summary of Commits

| Task | Commit Message |
|---|---|
| 1 | `chore: add project config files` |
| 2 | `chore: add module skeleton, test infrastructure, and venv` |
| 3 | `chore: add bundle manifest and directory structure` |
| 4 | `feat: add ActionStatus enum and ActionResult dataclass` |
| 5 | `feat: add ScreenInfo, CursorPosition, and WindowInfo models` |
| 6 | `feat: add SemanticElement and Observation models` |
| 7 | `feat: add Target protocol for backend contract` |
| 8 | `feat: add fixture backend observation methods` |
| 9 | `feat: add fixture backend action methods with action log` |
| 10 | `test: add golden observation tests for fixture backend` |
| 11 | `feat: add CuaTool with observe actions` |
| 12 | `feat: add input actions to CuaTool` |
| 13 | `feat: add mount function and backend registry stub` |
| 14 | `feat: add macOS backend with screenshot and screen info` |
| 15 | `feat: add macOS backend cursor, window, and input actions` |
| 16 | `feat: add macOS backend semantic tree via accessibility API` |
| 17 | `feat: add Windows and Linux stub backends` |
| 18 | `feat: add backend registry with auto-detection` |
| 19 | `feat: add cua-operator and cua-planner agents` |
| 20 | `feat: add dual-world reasoning, action confidence, and recovery context files` |
| 21 | `feat: add cua-core, cua-operator, and cua-recipes behaviors` |
| 22 | `feat: add observe-and-act recipe` |
| 23 | `feat: add bounded-task recipe with approval gates` |
| 24 | `feat: add recovery-workflow recipe` |
| 25 | `test: add backend conformance test suite` |
| 26 | `test: add bounded integration tests for full observe-act-verify flow` |
