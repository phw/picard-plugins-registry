"""Plugin operations."""

from registry_lib.manifest import fetch_manifest, validate_manifest
from registry_lib.picard.constants import REGISTRY_TRUST_LEVELS
from registry_lib.utils import derive_plugin_id, now_iso8601


def add_plugin(registry, git_url, trust_level, categories=None, ref="main"):
    """Add plugin to registry.

    Args:
        registry: Registry instance
        git_url: Git repository URL
        trust_level: Trust level (official, trusted, community)
        categories: List of categories (optional)
        ref: Git ref to use (default: main)

    Returns:
        dict: Added plugin entry

    Raises:
        ValueError: If validation fails or plugin exists
    """
    if trust_level not in REGISTRY_TRUST_LEVELS:
        raise ValueError(f"Invalid trust level: {trust_level}")

    # Fetch and validate manifest
    manifest = fetch_manifest(git_url, ref)
    validate_manifest(manifest)

    # Derive plugin ID
    plugin_id = derive_plugin_id(git_url)

    # Build plugin entry
    now = now_iso8601()
    plugin = {
        "id": plugin_id,
        "uuid": manifest["uuid"],
        "name": manifest["name"],
        "description": manifest["description"],
        "git_url": git_url,
        "categories": categories or manifest.get("categories", []),
        "trust_level": trust_level,
        "authors": manifest.get("authors", []),
        "added_at": now,
        "updated_at": now,
    }

    # Add optional fields
    if "maintainers" in manifest:
        plugin["maintainers"] = manifest["maintainers"]
    if "name_i18n" in manifest:
        plugin["name_i18n"] = manifest["name_i18n"]
    if "description_i18n" in manifest:
        plugin["description_i18n"] = manifest["description_i18n"]

    # Add refs if not default
    if ref != "main":
        plugin["refs"] = [{"name": ref}]

    registry.add_plugin(plugin)
    return plugin


def update_plugin(registry, plugin_id):
    """Update plugin metadata from MANIFEST.

    Args:
        registry: Registry instance
        plugin_id: Plugin ID to update

    Returns:
        dict: Updated plugin entry

    Raises:
        ValueError: If plugin not found or validation fails
    """
    plugin = registry.find_plugin(plugin_id)
    if not plugin:
        raise ValueError(f"Plugin {plugin_id} not found")

    # Get ref (default to main if not specified)
    refs = plugin.get("refs", [{"name": "main"}])
    ref = refs[0]["name"]

    # Fetch and validate manifest
    manifest = fetch_manifest(plugin["git_url"], ref)
    validate_manifest(manifest)

    # Update fields from manifest
    plugin["name"] = manifest["name"]
    plugin["description"] = manifest["description"]
    plugin["authors"] = manifest.get("authors", [])
    plugin["updated_at"] = now_iso8601()

    # Update optional fields
    if "maintainers" in manifest:
        plugin["maintainers"] = manifest["maintainers"]
    elif "maintainers" in plugin:
        del plugin["maintainers"]

    if "name_i18n" in manifest:
        plugin["name_i18n"] = manifest["name_i18n"]
    elif "name_i18n" in plugin:
        del plugin["name_i18n"]

    if "description_i18n" in manifest:
        plugin["description_i18n"] = manifest["description_i18n"]
    elif "description_i18n" in plugin:
        del plugin["description_i18n"]

    return plugin
