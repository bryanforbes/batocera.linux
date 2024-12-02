from __future__ import annotations

from configgen.exceptions import (
    BadCommandLineArguments,
    BaseBatoceraException,
    BatoceraException,
    InvalidConfiguration,
    MissingCore,
    MissingEmulator,
    UnexpectedEmulatorExit,
    UnknownEmulator,
)


def test_base_exception() -> None:
    assert BaseBatoceraException().exit_code == BaseBatoceraException.EXIT_CODE


def test_batocera_exception() -> None:
    assert BatoceraException().exit_code == BaseBatoceraException.EXIT_CODE
    assert BatoceraException('foo').exit_code == 250


def test_exceptions() -> None:
    assert UnexpectedEmulatorExit().exit_code == UnexpectedEmulatorExit.EXIT_CODE
    assert UnexpectedEmulatorExit('foo').exit_code == UnexpectedEmulatorExit.EXIT_CODE
    assert BadCommandLineArguments().exit_code == BadCommandLineArguments.EXIT_CODE
    assert BadCommandLineArguments('foo').exit_code == BadCommandLineArguments.EXIT_CODE
    assert InvalidConfiguration().exit_code == InvalidConfiguration.EXIT_CODE
    assert InvalidConfiguration('foo').exit_code == InvalidConfiguration.EXIT_CODE
    assert UnknownEmulator().exit_code == UnknownEmulator.EXIT_CODE
    assert UnknownEmulator('foo').exit_code == UnknownEmulator.EXIT_CODE
    assert MissingEmulator().exit_code == MissingEmulator.EXIT_CODE
    assert MissingEmulator('foo').exit_code == MissingEmulator.EXIT_CODE
    assert MissingCore().exit_code == MissingCore.EXIT_CODE
    assert MissingCore('foo').exit_code == MissingCore.EXIT_CODE
