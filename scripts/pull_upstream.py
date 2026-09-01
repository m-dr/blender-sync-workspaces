#!/usr/bin/env python3
"""
Pull latest release of Synchronize Workspaces from extensions.blender.org.
"""
import io
import json
import os
import sys
import tomllib
import urllib.request
import zipfile

INDEX_URL = "https://extensions.blender.org/api/v1/extensions/"
EXTENSION_ID = "synchronize_workspaces"
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MANIFEST_PATH = os.path.join(REPO_ROOT, "blender_manifest.toml")


def get_current_version():
    if not os.path.exists(MANIFEST_PATH):
        return None
    with open(MANIFEST_PATH, "rb") as f:
        data = tomllib.load(f)
    return data.get("version")


def fetch_upstream_info():
    req = urllib.request.Request(INDEX_URL, headers={"User-Agent": "Blender/5.2"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    for item in data.get("data", []):
        if item.get("id") == EXTENSION_ID:
            return item
    raise RuntimeError(f"Extension '{EXTENSION_ID}' not found in index.")


def download_and_extract(archive_url):
    print(f"Downloading: {archive_url}")
    req = urllib.request.Request(archive_url, headers={"User-Agent": "Blender/5.2"})
    with urllib.request.urlopen(req) as resp:
        content = resp.read()

    print(f"Extracting into: {REPO_ROOT}")
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        z.extractall(REPO_ROOT)


def main():
    force = "--force" in sys.argv
    current = get_current_version()
    print(f"Current local manifest version: {current}")

    info = fetch_upstream_info()
    upstream_version = info.get("version")
    archive_url = info.get("archive_url")
    print(f"Latest upstream version: {upstream_version}")

    if not force and current == upstream_version:
        print("Repository is already up-to-date with upstream release.")
        return

    download_and_extract(archive_url)
    print(f"Successfully updated files to upstream version {upstream_version}.")


if __name__ == "__main__":
    main()
