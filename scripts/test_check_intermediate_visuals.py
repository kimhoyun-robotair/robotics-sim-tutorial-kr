from __future__ import annotations

import subprocess
from collections.abc import Callable
from types import ModuleType
from typing import Protocol

from scripts import check_intermediate_visuals as visuals


class MonkeyPatch(Protocol):
    def setattr(
        self,
        target: ModuleType,
        name: str,
        value: Callable[[list[str], float], subprocess.CompletedProcess[str]],
    ) -> None: ...


def xwininfo_result(rows: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["xwininfo", "-root", "-tree"], 0, rows, "")


def test_windows_for_keeps_exact_canonical_titles(monkeypatch: MonkeyPatch) -> None:
    # Given: canonical Gazebo and RViz window rows.
    rows = (
        '     0x4e0000e "Gazebo": ("gz-sim-gui" "Gazebo GUI")  1200x1000+14+49  +1556+492\n'
        '     0x62001f7 "RViz": ("rviz2" "Rviz")  1280x720+14+49  +1605+541\n'
    )
    monkeypatch.setattr(visuals, "command", lambda _argv, _timeout=12.0: xwininfo_result(rows))

    # When: frozen exact title patterns are resolved.
    gazebo = visuals.windows_for(r"^Gazebo$")
    rviz = visuals.windows_for(r"^RViz$")

    # Then: the original canonical fixtures remain selectable.
    assert [window.xid for window in gazebo] == ["0x4e0000e"]
    assert [window.xid for window in rviz] == ["0x62001f7"]


def test_windows_for_canonicalizes_real_gazebo_title_only_for_gazebo_gui_class(
    monkeypatch: MonkeyPatch,
) -> None:
    # Given: a real Gazebo Sim row plus similar but unrelated window titles.
    rows = (
        '     0x4e0000e "Gazebo Sim": ("gz-sim-gui" "Gazebo GUI")  1200x1000+14+49  +1556+492\n'
        '     0x4e0000f "My Gazebo": ("gz-sim-gui" "Gazebo GUI")  1200x1000+14+49  +1556+492\n'
        '     0x4e00010 "Gazebo Sim": ("chromium" "Chromium")  1200x1000+14+49  +1556+492\n'
        '     0x4e00011 "Gazebo Sim": ("gz-sim-gui" "Gazebo GUI") malformed\n'
    )
    monkeypatch.setattr(visuals, "command", lambda _argv, _timeout=12.0: xwininfo_result(rows))

    # When: the frozen exact Gazebo pattern is resolved.
    windows = visuals.windows_for(r"^Gazebo$")

    # Then: only the verified Gazebo GUI identity is selected.
    assert [(window.xid, window.title) for window in windows] == [("0x4e0000e", "Gazebo")]


def test_windows_for_canonicalizes_real_rviz_config_title_only_for_rviz_class(
    monkeypatch: MonkeyPatch,
) -> None:
    # Given: a real RViz config-title row plus similar but unrelated window titles.
    rows = (
        '     0x62001f7 "/tmp/tutorial_bot.rviz - RViz": ("rviz2" "Rviz")  1280x720+14+49  +1605+541\n'
        '     0x62001f8 "Browser RViz - RViz": ("chromium" "Chromium")  1280x720+14+49  +1605+541\n'
        '     0x62001f9 "/tmp/tutorial_bot.rviz - RViz": ("other" "Other")  1280x720+14+49  +1605+541\n'
    )
    monkeypatch.setattr(visuals, "command", lambda _argv, _timeout=12.0: xwininfo_result(rows))

    # When: the frozen exact RViz pattern is resolved.
    windows = visuals.windows_for(r"^RViz$")

    # Then: only the verified RViz identity is selected.
    assert [(window.xid, window.title) for window in windows] == [("0x62001f7", "RViz")]


def test_required_window_rejects_ambiguous_canonical_matches(monkeypatch: MonkeyPatch) -> None:
    # Given: two verified Gazebo GUI windows that both canonicalize to Gazebo.
    rows = (
        '     0x4e0000e "Gazebo Sim": ("gz-sim-gui" "Gazebo GUI")  1200x1000+14+49  +1556+492\n'
        '     0x4e0000f "Gazebo Sim": ("gz-sim-gui" "Gazebo GUI")  1200x1000+14+49  +1556+492\n'
    )
    monkeypatch.setattr(visuals, "command", lambda _argv, _timeout=12.0: xwininfo_result(rows))

    # When: the checker requires a single frozen-pattern Gazebo window.
    try:
        _ = visuals.required_window("Gazebo", r"^Gazebo$")
    except visuals.AuditInputError as error:
        assert "Gazebo window ambiguous" in str(error)
    else:
        raise AssertionError("expected ambiguous Gazebo windows to be rejected")
