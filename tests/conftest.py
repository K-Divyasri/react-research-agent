"""Shared fixtures. Everything is offline, deterministic, and keyless."""

from __future__ import annotations

import pytest

QUESTION = "What causes coral bleaching and what are its main effects?"


@pytest.fixture
def question() -> str:
    return QUESTION
