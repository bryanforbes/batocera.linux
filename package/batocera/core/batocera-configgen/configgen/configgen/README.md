## Directory navigation

 - `generators` The infamous Python configuration generators, bane of the end-user who's used to modifying INI and XML files directly. These are what create the necessary configuration files, controller profiles and any other necessary INI/CFG file an emulator uses upon launching an emulator. Used in conjunction with [ES features](https://github.com/batocera-linux/batocera.linux/blob/master/package/batocera/emulationstation/batocera-es-system/es_features.yml) to make these generated configs based on the options the user has set in ES. If creating a new one, don't forget to [define](https://github.com/batocera-linux/batocera.linux/blob/master/package/batocera/core/batocera-configgen/configgen/configgen/emulatorlauncher.py) it as well.
 - `batoceraPaths.py` The paths used by emulators for their configuration files, saves, etc.
 - `Emulator.py` How do we grab all the settings? And in what order?
 - `emulatorlauncher.py` The main launcher.

## Development

## Getting started

To get started, create a [virtual environment](https://docs.python.org/3/library/venv.html) using Python 3.12.8 in the root of the `batocera.linux` project and install `configgen` with the `tests` extra:

```sh
cd path/to/batocera.linux
python3.12 -m venv .venv
source .venv/bin/activate
cd package/batocera/core/batocera-configgen/configgen
pip install -U -e '.[test]'
```

### Tests

`configgen` uses [`pytest`](https://docs.pytest.org/en/stable/) as its test runner. All tests must be formatted with [`ruff format`](https://docs.astral.sh/ruff/formatter/), must pass [`ruff check`](https://docs.astral.sh/ruff/linter/), and must pass type checking with [`pyright`](https://microsoft.github.io/pyright/#/).

#### Running tests

To run the tests, run the virtual environment's `py.test` in the `configgen` root directory (all examples after this assume the virtual environment has been activated):

```sh
cd path/to/batocera.linux
source .venv/bin/activate
cd package/batocera/core/batocera-configgen/configgen
py.test
```

`configgen` has a lot of tests, so distributing test running across multiple CPUs will speed up test runs:

```sh
py.test -n auto
```

See the docs for [`pytest-xdist`](https://pytest-xdist.readthedocs.io/en/stable/) for more options.

If all tests pass, [`pytest-cov`](https://pytest-cov.readthedocs.io/en/latest/) will output a coverage report on the command line. To output an HTML coverage report that goes into much greater detail, use the following:

```sh
py.test --cov-report=html
```

The HTML coverage report will be output to the `htmlcov/index.html` and can be opened in any web browser.

#### Writing tests

The [`pytest` docs](https://docs.pytest.org/en/stable/) will be the best place to learn how to write tests, however `configgen` uses three plugins that aid in writing generator tests and allow the tests to be run cross-platform.

- [`pytest-mock`](https://pytest-mock.readthedocs.io/en/latest/) provides a `pytest` fixture (named `mocker`) to use [`unittest.mock`](https://docs.python.org/3/library/unittest.mock.html) within any tests that may need to patch outside modules to isolate the test. `pytest-mock` ensures that any patching done before the test is run is cleaned up after the end of the test.
- [`pyfakefs`](https://pytest-pyfakefs.readthedocs.io/en/latest/) sets up an empty in-memory filesystem that mimics a Linux filesystem for each test. This means that tests that need to write to a filesystem will never pollute the host machine's filesystem, even if the tests fail or are interrupted. Any test can use the mock filesystem by requesting the `fs` fixture.
- [`syrupy`](https://syrupy-project.github.io/syrupy/) is a snapshot plugin. Rather than re-parsing configuration files and checking that one or two settings were changed based on certain conditions, `syrupy` can check if a configuration file matches what we expect the configuration file to look like. It can be used to compare any Python object against a previous state, but we mostly use it to check configuration file contents. When writing new tests, you will need to run `py.test --snapshot-update` to generate the initial snapshot.

Test files should be organized in the `tests` directory following the directory structure of `configgen`, prefixed with `test_` and use the snake-case version of the module name. For instance, `tests/test_controller.py` for `configgen/controller.py` and `tests/utils/test_video_mode.py` for `configgen/utils/videoMode.py`. Each module should have a test file with the exception of generators. Generators should be tested as a unit even if they are comprised of multiple modules. The `libretro` generator is the exception to this rule and has one test file for every `libretro` core and each core is treated as a unit.

Generator tests must inherit from `GeneratorBaseTest` in `tests.generators.base`. This provides tests for all of the default generator methods except `generate()`. If the generator being written overrides one of those methods, that test method will need to be overridden to test all possible outcomes.

Generator tests can utilize the fixtures in `tests/mock_emulator.py` to test various options the generator will be using:

- `mock_system` provides an instance of `configgen.Emulator.Emulator` to pass to the generator
- `system_name` can be overridden to set `mock_system.name`; it defaults to `'unset'`
- `emulator` must be overridden to set `mock_system.config['emulator']`
- `core` can be overridden to set `mock_system.config['core']`; it defaults to the value of the `emulator` fixture
- `mock_system_config` can be overridden to set various values in `mock_system.config`
- `mock_system_render_config` can be overridden to set various values in `mock_system.renderconfig`

Additionally, there are several marks that can be used to override the above fixtures for individual test cases or classes:

- `pytest.mark.system(system)`
- `pytest.mark.emulator(emulator)`
- `pytest.mark.core(core)`
- `pytest.mark.mock_system_config(config)`
- `pytest.mark.mock_system_render_config(config)`

Various mock controllers have been provided for testing purposes. See `tests/mock_controllers.py` for the full list.

`libretro` core tests must inherit from `LibretroBaseCoreTest` in `tests.generators.libretro.base`. This provides the same tests as `GeneratorBaseTest` as well as a basic test for `generate()` and tests for options that all cores utilize. There are also two convenience methods to take a snapshot of the two `libretro` config files: `assert_config_matches()` and `assert_core_config_matches()`.

While writing tests, there are a few command line flags and arguments that are very helpful:

- Run all tests, distributing the load across all CPUs, and generate an HTML coverage report: `py.test -n auto --cov-report=html`
- Run an individual test file: `py.test tests/test_gun.py`
- Run an individual test case: `py.test tests/test_gun.py::test_guns_need_crosses`
- Run all the test cases in a test class: `py.test tests/test_gun.py::TestGun`
- Run one test case in a test class: `py.test tests/test_gun.py::TestGun::test_button_map`
- Append new coverage information onto an already generated coverage report (to check overall coverage): `py.test --cov-report=html --cov-append`
- Update snapshot data: `py.test --snapshot-update`
- Update snapshot data for one test file: `py.test --snapshot-update tests/test_gun.py`
