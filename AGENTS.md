# Agent Operating Guide: Synchronize Workspaces

This repository maintains a patched distribution of the **Synchronize Workspaces** Blender add-on (originally created by Michael Soluyanov / MultLabs).

---

## 1. Branch Architecture
- **`upstream`**: 100% clean mirror of releases downloaded from `extensions.blender.org`. Contains historical version tags (`v1.12.0`, `v1.13.0`, `v1.14.0`, `v1.15.0`).
- **`main`** (Default): Contains our custom bug fixes and distribution tooling.

---

## 2. Custom Patches Maintained in `main`

### Viewport Sync Bug with Fullscreen/Maximized `temp` Screens
- **Problem**: In upstream v1.15.0, `update_workspace` called `get_biggest_area(prev, "VIEW_3D", False)`. Whenever any editor area was maximized in Blender (`Ctrl+Space`), Blender created a temporary full-window screen (e.g. `temp.031`). Because `get_biggest_area` checked sizes across all screens, it always selected the inactive, oversized `temp` screen (which has static/default camera matrices) instead of the active viewport.
- **Fix in `__init__.py`**:
  - `get_biggest_area` now accepts `ignore_temp=True` by default, skipping screens whose names start with `temp`.
  - `update_workspace` first attempts to resolve `prevArea` from `sinchmanager.last_area` (matching against non-temp screens of `prev`), falling back to `get_biggest_area(..., ignore_temp=True)`.

---

## 3. Standard Upgrade Workflow for Agents

When requested to pull an upstream release or perform routine maintenance:

### Step 1: Switch to `upstream` & pull new version
```bash
git checkout upstream
python scripts/pull_upstream.py
```
If a new release was downloaded:
```bash
git commit -am "Upstream release v<VERSION>"
git tag v<VERSION>
```

### Step 2: Merge into `main`
```bash
git checkout main
git merge v<VERSION>
```

### Step 3: Verify Custom Patches
Inspect `__init__.py` to ensure `ignore_temp=True` logic in `get_biggest_area` and `update_workspace` is preserved after the merge.

### Step 4: Headless Validation
Run Blender test:
```bash
blender --background --factory-startup --python-expr "import sys; sys.path.insert(0, '.'); import synchronize_workspaces; synchronize_workspaces.register(); print('TEST PASSED')"
```

### Step 5: Build Package
```bash
python scripts/build_extension.py
```
