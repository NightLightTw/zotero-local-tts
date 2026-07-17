import json
import subprocess
import tomllib
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]
PLUGIN_ROOT = PROJECT_ROOT / "zotero-plugin"


def test_manifest_is_pinned_to_supported_zotero_minor_version() -> None:
    manifest = json.loads((PLUGIN_ROOT / "manifest.json").read_text())
    application = manifest["applications"]["zotero"]

    assert manifest["version"] == "0.1.3"
    assert application["id"] == "zotero-local-tts@zhangzizhong.local"
    assert application["update_url"].endswith("/updates.json")
    assert application["strict_min_version"] == "9.0"
    assert application["strict_max_version"] == "9.0.*"


def test_bridge_and_plugin_versions_match() -> None:
    manifest = json.loads((PLUGIN_ROOT / "manifest.json").read_text())
    project = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())

    assert project["project"]["version"] == manifest["version"]


def test_bootstrap_contains_reversible_contract_guard() -> None:
    bootstrap = (PLUGIN_ROOT / "bootstrap.js").read_text()

    assert "SUPPORTED_VERSION" in bootstrap
    assert "standard: [" in bootstrap
    assert "originalGetReadAloudVoices.call(apiClient)" in bootstrap
    assert "standard: [...local.voices.standard, ...originalStandard]" in bootstrap
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


def test_build_script_derives_archive_version_from_manifest() -> None:
    script = (PROJECT_ROOT / "scripts" / "build-xpi.sh").read_text()

    assert "plutil -extract version" in script
    assert "zotero-local-tts-0.1.3.xpi" not in script
    assert '"$project_dir/LICENSE"' in script
    assert '"$project_dir/NOTICE"' in script


def test_bootstrap_runtime_contract() -> None:
    subprocess.run(
        ["node", PROJECT_ROOT / "tests" / "test_zotero_bootstrap.mjs"],
        check=True,
    )
