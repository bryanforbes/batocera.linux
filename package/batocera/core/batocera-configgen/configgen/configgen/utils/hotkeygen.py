from __future__ import annotations

import json
import logging
import subprocess
from contextlib import contextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from ..generators.Generator import Generator

_logger = logging.getLogger(__name__)

@contextmanager
def set_hotkeygen_context(generator: Generator, /) -> Iterator[None]:
    # hotkeygen context
    hkc = generator.getHotkeysContext()
    _logger.debug("hotkeygen: updating context to %s", hkc["name"])
    subprocess.call(["hotkeygen", "--new-context", hkc["name"], json.dumps(hkc["keys"])])

    try:
        yield
    finally:
        # reset hotkeygen context
        _logger.debug("hotkeygen: resetting to default context")
        subprocess.call(["hotkeygen", "--default-context"])
