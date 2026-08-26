"""Tests for the pydantic result shapes."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from research_agent.schema import Report, Source, Step


def test_step_rejects_bad_action():
    with pytest.raises(ValidationError):
        Step(n=1, thought="t", action="teleport")  # not search/read/finish


def test_step_number_must_be_positive():
    with pytest.raises(ValidationError):
        Step(n=0, thought="t", action="search")


def test_report_round_trips_through_json(question):
    report = Report(
        question=question,
        answer="A claim. [1]",
        sources=[Source(n=1, title="A", locator="a.txt", snippet="A claim.")],
        steps=[Step(n=1, thought="t", action="search", action_input=question, observation="o")],
        reflection="Looks fine.",
    )
    again = Report.model_validate_json(report.model_dump_json())
    assert again == report


def test_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        Source(n=1, title="A", locator="a", extra="nope")  # type: ignore[call-arg]
