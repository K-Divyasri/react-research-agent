"""Tests for the command-line interface (offline)."""

from __future__ import annotations

import json

from research_agent.cli import main


def test_cli_prints_answer_and_sources(question, capsys):
    code = main([question])
    out = capsys.readouterr().out
    assert code == 0
    assert "Sources:" in out
    assert "[1]" in out


def test_cli_json_is_valid_report(question, capsys):
    code = main([question, "--json"])
    out = capsys.readouterr().out
    assert code == 0
    data = json.loads(out)
    assert data["question"] == question
    assert data["sources"]


def test_cli_steps_flag_shows_trace(question, capsys):
    main([question, "--steps"])
    out = capsys.readouterr().out
    assert "Reasoning trace" in out
    assert "action:" in out
