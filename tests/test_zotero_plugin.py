import json
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]
PLUGIN_ROOT = PROJECT_ROOT / "zotero-plugin"


def test_manifest_is_pinned_to_supported_zotero_minor_version() -> None:
    manifest = json.loads((PLUGIN_ROOT / "manifest.json").read_text())
    application = manifest["applications"]["zotero"]

    assert manifest["version"] == "0.1.2"
    assert application["id"] == "zotero-local-tts@zhangzizhong.local"
    assert application["update_url"].endswith("/updates.json")
    assert application["strict_min_version"] == "9.0"
    assert application["strict_max_version"] == "9.0.*"


def test_bootstrap_contains_reversible_contract_guard() -> None:
    bootstrap = (PLUGIN_ROOT / "bootstrap.js").read_text()

    assert "SUPPORTED_VERSION" in bootstrap
    assert "standard: [" in bootstrap
    assert "ChromeUtils.importESModule" not in bootstrap
    assert "expected Read Aloud API contract is missing" in bootstrap
    assert "prototype.getReadAloudVoices = originalGetReadAloudVoices" in bootstrap
    assert "prototype.getReadAloudAudio = originalGetReadAloudAudio" in bootstrap


def test_built_xpi_has_files_at_archive_root(tmp_path: Path) -> None:
    archive = tmp_path / "plugin.xpi"
    with zipfile.ZipFile(archive, "w") as xpi:
        xpi.write(PLUGIN_ROOT / "manifest.json", "manifest.json")
        xpi.write(PLUGIN_ROOT / "bootstrap.js", "bootstrap.js")

    with zipfile.ZipFile(archive) as xpi:
        assert set(xpi.namelist()) == {"manifest.json", "bootstrap.js"}
