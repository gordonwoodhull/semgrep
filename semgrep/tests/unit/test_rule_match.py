from pathlib import Path
from textwrap import dedent
from unittest import mock

import pytest

import semgrep.output_from_core as core
from semgrep.constants import RuleSeverity
from semgrep.rule_match import RuleMatch
from semgrep.rule_match import RuleMatchSet


@pytest.mark.quick
def test_rule_match_attributes():
    file_content = dedent(
        """
        # first line
        def foo():
            5 == 5 # nosem
        """
    ).lstrip()
    with mock.patch.object(Path, "open", mock.mock_open(read_data=file_content)):
        match = RuleMatch(
            rule_id="long.rule.id",
            message="message",
            severity=RuleSeverity.ERROR,
            path=Path("relative/path/to/foo.py"),
            start=core.Position(3, 1, 24),
            end=core.Position(3, 15, 38),
        )
    assert match.lines == ["    5 == 5 # nosem\n"], "wrong line was read from file"
    assert (
        match.previous_line == "def foo():\n"
    ), "wrong previous line was read from file"
    assert (
        match.syntactic_context == "5 == 5"
    ), "indent and comment must be removed from code"
    assert (
        match.syntactic_id == "e9f75ffe95edb9e7b898d5f8c475501a"
    ), "syntactic IDs must remain consistent to not trigger new notifications"


@pytest.mark.quick
def test_rule_match_sorting():
    file_content = dedent(
        """
        # first line
        def foo():
            5 == 5 # nosem
            6 == 6 # nosem
        """
    ).lstrip()
    with mock.patch.object(Path, "open", mock.mock_open(read_data=file_content)):
        line3 = RuleMatch(
            rule_id="rule_id",
            message="message",
            severity=RuleSeverity.ERROR,
            path=Path("foo.py"),
            start=core.Position(3, 1, 24),
            end=core.Position(3, 15, 38),
        )
        line4 = RuleMatch(
            rule_id="rule_id",
            message="message",
            severity=RuleSeverity.ERROR,
            path=Path("foo.py"),
            start=core.Position(4, 1, 36),
            end=core.Position(4, 15, 50),
        )
    # fmt: off
    assert (
        sorted([line4, line3]) == [line3, line4]
    ), "after sorting, matches on earlier lines must go first"
    # fmt: on


@pytest.mark.quick
def test_rule_match_hashing():
    file_content = dedent(
        """
        # first line
        def foo():
            5 == 5 # nosem
        """
    ).lstrip()
    with mock.patch.object(Path, "open", mock.mock_open(read_data=file_content)):
        match = RuleMatch(
            rule_id="rule_id",
            message="message",
            severity=RuleSeverity.ERROR,
            path=Path("foo.py"),
            start=core.Position(3, 1, 24),
            end=core.Position(3, 15, 38),
        )
    assert {match, match} == {match}, "matches must deduplicate when added to a set"


@pytest.mark.quick
def test_rule_match_set_indexes():
    file_content = dedent(
        """
        # first line
        def foo():
            5 == 5 # nosem
            5 == 5 # nosem
            6 == 6 # nosem
            5 == 5 # nosem
        """
    ).lstrip()
    with mock.patch.object(Path, "open", mock.mock_open(read_data=file_content)):
        line3 = RuleMatch(
            rule_id="rule_id",
            message="message",
            severity=RuleSeverity.ERROR,
            path=Path("foo.py"),
            start=core.Position(3, 1, 24),
            end=core.Position(3, 15, 38),
        )
        line4 = RuleMatch(
            rule_id="rule_id",
            message="message",
            severity=RuleSeverity.ERROR,
            path=Path("foo.py"),
            start=core.Position(4, 1, 36),
            end=core.Position(4, 15, 50),
        )
        line5 = RuleMatch(
            rule_id="rule_id",
            message="message",
            severity=RuleSeverity.ERROR,
            path=Path("foo.py"),
            start=core.Position(5, 1, 48),
            end=core.Position(5, 15, 62),
        )
        line6 = RuleMatch(
            rule_id="rule_id",
            message="message",
            severity=RuleSeverity.ERROR,
            path=Path("foo.py"),
            start=core.Position(6, 1, 60),
            end=core.Position(6, 15, 74),
        )
        matches = RuleMatchSet()
        matches.update(
            [line3, line4, line5, line6]
        )  # we do need to add them in the correct order
        sorted_matches = list(sorted(matches))
    assert sorted_matches[0].index == 0, "1st duplicate match must be assigned index 0"
    assert sorted_matches[1].index == 1, "2nd duplicate match must be assigned index 1"
    assert sorted_matches[3].index == 2, "3rd duplicate match must be assigned index 2"
    assert sorted_matches[2].index == 0, "unique match must be assigned index 0"
