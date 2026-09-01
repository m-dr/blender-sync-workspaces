# Synchronize Workspaces (Patched Fork)

A Blender extension to synchronize 3D viewport orientation, position, zoom, and display settings across workspaces.

* **Original Author**: Michael Soluyanov (MultLabs / Crantisz)
* **Original Extension Page**: [extensions.blender.org/add-ons/synchronize-workspaces](https://extensions.blender.org/add-ons/synchronize-workspaces/)
* **Upstream Discussion**: [Blender Artists Community Thread](https://blenderartists.org/t/synchronize-workspaces-blender-add-on/1356695)

---

## Origin & Fork Details

This repository is a maintained fork reconstructed directly from the official **Blender Extensions Platform** releases (`v1.12.0` through `v1.15.0`).

The `upstream` branch preserves the exact original vendor code with historical tags. The `main` branch tracks the active working version while retaining upstream version numbering (`1.15.0`).

---

## Documented Changes & Fixes

### 1. Viewport Synchronization Bug with Temporary/Maximized Screens (`temp.*`)
* **Problem**: In upstream version `1.15.0`, `update_workspace` attempted to resolve the source viewport from the previous workspace using `get_biggest_area(prev, "VIEW_3D", False)`.  
  Whenever any editor area in Blender is maximized or made fullscreen (`Ctrl+Space` or `Ctrl+Alt+Space`), Blender generates temporary full-window screen data-blocks (`temp`, `temp.001`, `temp.031`, etc.) attached to the workspace.  
  Because `get_biggest_area` checked dimensions across all screens without checking active status, it **always selected the inactive, oversized `temp` screen** instead of the active viewport. Because `temp` screens contain default/frozen camera matrices (`[1,0,0,0], [0,1,0,0], [0,0,1,-10]`, loc `[0,0,0]`), switching workspaces constantly overwrote the target viewport with a static dummy camera matrix.
* **The Fix** (in [`__init__.py`](__init__.py)):
  1. Updated `get_biggest_area(workspace, type, checkscreen=False, ignore_temp=True)` to filter out `temp.*` screens by default.
  2. Prioritized `sinchmanager.last_area` matching active non-temp screens of the source workspace.
  3. Added graceful fallback to `sinchmanager.last_area` if no valid normal screen is found.

### 2. Automation & Maintenance Tooling
* [`scripts/pull_upstream.py`](scripts/pull_upstream.py): Automated tool to check `extensions.blender.org`, download future upstream releases, and update the `upstream` branch.
* [`scripts/build_extension.py`](scripts/build_extension.py): Automated builder that packages the extension into a compliant `.zip` archive in `dist/` with SHA-256 calculation.

---

## Installation

1. Download the latest `.zip` package from the [Releases](https://github.com/m-dr/blender-sync-workspaces/releases) page.
2. In Blender: **Edit > Preferences > Get Extensions (or Add-ons)**.
3. Click the **arrow menu (▼)** in the top right $\rightarrow$ **Install from Disk...**
4. Select the downloaded `.zip` file.

---

## Building from Source

To package the `.zip` archive locally:
```bash
python scripts/build_extension.py
```
Package output is created in `dist/synchronize_workspaces-1.15.0.zip`.

---

## License

GNU General Public License v3.0 or later (see [LICENSE](LICENSE)).
