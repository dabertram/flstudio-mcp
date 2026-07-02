"""Unit tests for cross-platform FL path discovery (pure filesystem)."""
from __future__ import annotations

import pytest

from fl_studio_mcp import paths

pytestmark = pytest.mark.unit


class TestPianoRollScriptsDir:
    def test_env_override_wins(self, monkeypatch):
        monkeypatch.setenv(paths.ENV_PIANO_ROLL_SCRIPTS, "/tmp/custom/scripts")
        assert paths.find_piano_roll_scripts_dir() == "/tmp/custom/scripts"

    def test_discovers_from_fake_home(self, monkeypatch, tmp_path):
        monkeypatch.delenv(paths.ENV_PIANO_ROLL_SCRIPTS, raising=False)
        monkeypatch.delenv(paths.ENV_FL_SETTINGS, raising=False)
        target = tmp_path / "Documents" / "Image-Line" / "FL Studio" / "Settings" / "Piano roll scripts"
        target.mkdir(parents=True)
        monkeypatch.setattr(paths.Path, "home", classmethod(lambda cls: tmp_path))
        assert paths.find_piano_roll_scripts_dir() == str(target)

    def test_versioned_folder(self, monkeypatch, tmp_path):
        monkeypatch.delenv(paths.ENV_PIANO_ROLL_SCRIPTS, raising=False)
        monkeypatch.delenv(paths.ENV_FL_SETTINGS, raising=False)
        target = tmp_path / "Documents" / "Image-Line" / "FL Studio 2025" / "Settings" / "Piano roll scripts"
        target.mkdir(parents=True)
        monkeypatch.setattr(paths.Path, "home", classmethod(lambda cls: tmp_path))
        assert paths.find_piano_roll_scripts_dir() == str(target)


class TestFlSettingsDir:
    def test_env_override(self, monkeypatch, tmp_path):
        monkeypatch.setenv(paths.ENV_FL_SETTINGS, str(tmp_path))
        assert paths.find_fl_settings_dir() == str(tmp_path)

    def test_none_when_absent(self, monkeypatch, tmp_path):
        monkeypatch.delenv(paths.ENV_FL_SETTINGS, raising=False)
        monkeypatch.setattr(paths.Path, "home", classmethod(lambda cls: tmp_path))
        assert paths.find_fl_settings_dir() is None


class TestSerumPresets:
    def test_env_override(self, monkeypatch, tmp_path):
        from fl_studio_mcp.music import preset_library as pl

        monkeypatch.setenv(pl._ENV_SERUM, str(tmp_path))
        assert pl.find_serum_presets() == str(tmp_path)

    def test_macos_library_audio_path(self, monkeypatch, tmp_path):
        from fl_studio_mcp.music import preset_library as pl

        monkeypatch.delenv(pl._ENV_SERUM, raising=False)
        target = tmp_path / "Library" / "Audio" / "Presets" / "Xfer Records" / "Serum Presets"
        target.mkdir(parents=True)
        monkeypatch.setattr(pl.Path, "home", classmethod(lambda cls: tmp_path))
        assert pl.find_serum_presets() == str(target)
