from __future__ import annotations

import logging

import pytest

from configgen.utils.logger import setup_logging


def test_setup_logging() -> None:
    with setup_logging():
        logger = logging.getLogger('configgen')

        assert len(logger.handlers) == 2
        assert logger.handlers[0].level == logging.DEBUG
        assert logger.handlers[0].formatter
        assert (
            logger.handlers[0].formatter._fmt
            == '%(asctime)s %(levelname)s (%(filename)s:%(lineno)d):%(funcName)s %(message)s'
        )
        assert logger.handlers[1].level == logging.WARNING
        assert logger.handlers[1].formatter
        assert (
            logger.handlers[1].formatter._fmt
            == '%(asctime)s %(levelname)s (%(filename)s:%(lineno)d):%(funcName)s %(message)s'
        )
        assert logger.level == logging.DEBUG

    assert not logger.handlers


def test_setup_logging_cleanup() -> None:
    with pytest.raises(Exception, match=r'^Passthrough$'), setup_logging():
        raise Exception('Passthrough')

    assert not logging.getLogger('configgen').handlers
