from __future__ import annotations

from typing import TYPE_CHECKING, NotRequired, TypedDict, cast

from tests.generators.libretro._cores import CORES_MAP as CORES_MAP, CoreDict as CoreDict

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping


def get_extensions_iter(core_name: str, system_name: str | None = None, /) -> Iterator[str]:
    core = CORES_MAP[core_name]
    yield from core['extensions'][core['systems'][0] if system_name is None else system_name]


def get_extensions(core_name: str, system_name: str | None = None, /) -> list[str]:
    return list(get_extensions_iter(core_name, system_name))


def get_first_extension(core_name: str, system_name: str | None = None, /) -> str:
    return next(get_extensions_iter(core_name, system_name))


type _ConfigSpec = dict[str, str | list[str]]


class _PartialCoreConfigDict(TypedDict):
    system: str
    configs: list[_ConfigSpec]


class _CoreConfigDict(_PartialCoreConfigDict):
    name: str


class _PartialMultiCoreConfigDict(TypedDict):
    systems: list[str]
    configs: NotRequired[list[_ConfigSpec]]
    system_configs: NotRequired[dict[str, list[_ConfigSpec]]]


class _MultiCoreConfigDict(_PartialMultiCoreConfigDict):
    name: str


def get_configs(key: str, values: Iterable[str], /, base: Mapping[str, str] | None = None) -> Iterator[dict[str, str]]:
    if isinstance(values, str):
        yield {**base, key: values} if base else {key: values}
    else:
        if base:
            yield from ({**base, key: value} for value in values)
        else:
            yield from ({key: value} for value in values)


def get_configs_from_base(
    base: Mapping[str, str], specs: Iterable[tuple[str, Iterable[str]]]
) -> Iterator[dict[str, str]]:
    for spec in specs:
        yield from get_configs(*spec, base)


def get_configs_with_base(
    base: Mapping[str, str], specs: Iterable[tuple[str, Iterable[str]]]
) -> Iterator[dict[str, str]]:
    yield dict(base)

    yield from get_configs_from_base(base, specs)


def get_configs_from_bases(
    bases: Iterable[Mapping[str, str]], specs: Iterable[tuple[str, Iterable[str]]]
) -> Iterator[dict[str, str]]:
    for base in bases:
        yield from get_configs_from_base(base, specs)


def get_configs_with_bases(
    bases: Iterable[Mapping[str, str]], specs: Iterable[tuple[str, Iterable[str]]]
) -> Iterator[dict[str, str]]:
    for base in bases:
        yield from get_configs_with_base(base, specs)


def config_for_cores(
    cores: Iterable[str], config: _PartialCoreConfigDict | _PartialMultiCoreConfigDict
) -> Iterator[_CoreConfigDict | _MultiCoreConfigDict]:
    for core in cores:
        yield cast('_CoreConfigDict | _MultiCoreConfigDict', {**config, 'name': core})


def get_systems_for_core_iter(core: str, /) -> Iterator[str]:
    yield from CORES_MAP[core]['systems']


def get_systems_for_core(core: str, /) -> list[str]:
    return list(CORES_MAP[core]['systems'])
