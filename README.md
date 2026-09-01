# Synchronize Workspaces (Patched)

A Blender extension to synchronize 3D viewport orientation, position, and settings across workspaces.

* Original Author: **Michael Soluyanov (MultLabs)**
* Original Extension Page: [extensions.blender.org/add-ons/synchronize-workspaces](https://extensions.blender.org/add-ons/synchronize-workspaces/)

---

## Patches in this Fork

* **Fullscreen / Temp Screen Bug Fix**:
  In Blender, maximizing any area generates temporary `temp.*` full-window screens. Upstream v1.15.0 frequently latched onto these inactive screens when resolving the source viewport. This fork filters out temporary screens and prioritizes the active viewport.

---

## Building the Extension Package

To build the `.zip` archive for distribution:
```bash
python scripts/build_extension.py
```
Output package is written to `dist/synchronize_workspaces-<version>.zip`.

---

## Updating from Upstream

See [AGENTS.md](AGENTS.md) for the automated upstream pulling and merging procedure.
