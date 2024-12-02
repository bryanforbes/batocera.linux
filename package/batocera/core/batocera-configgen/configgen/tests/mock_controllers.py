from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Callable
from functools import wraps
from typing import Any, Literal, cast

import pytest

from configgen.controller import Controller, ControllerList, Controllers
from configgen.input import Input


def controller_fixture[F: Callable[..., Controller]](xml: str) -> Callable[[F], F]:
    root = ET.fromstring(f"""<?xml version="1.0"?>{xml}""")

    controller = Controller(
        name=root.attrib['deviceName'],
        type=cast("Literal['keyboard', 'joystick']", root.attrib['type']),
        guid=root.attrib['deviceGUID'],
        player_number=-1,
        index=-1,
        real_name=root.attrib['deviceName'],
        device_path='',
        button_count=len(root.findall('./input[@type="button"]')),
        axis_count=len(root.findall('./input[@type="axis"]')),
        hat_count=len(root.findall('./input[@type="hat"]')),
        inputs_=Input.from_parent_element(root),
    )

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Controller:
            return controller.replace()

        return cast('F', pytest.fixture(wrapper))

    return decorator


@controller_fixture("""
	<inputConfig type="joystick" deviceName="Generic Xbox pad" deviceGUID="030000005e0400000a0b000005040000">
		<input name="a" type="button" id="0" value="1" code="304" />
		<input name="b" type="button" id="1" value="1" code="305" />
		<input name="down" type="hat" id="0" value="4" code="16" />
		<input name="hotkey" type="button" id="8" value="1" code="314" />
		<input name="joystick1left" type="axis" id="0" value="-1" code="0" />
		<input name="joystick1up" type="axis" id="1" value="-1" code="1" />
		<input name="joystick2left" type="axis" id="2" value="-1" code="3" />
		<input name="joystick2up" type="axis" id="3" value="-1" code="4" />
		<input name="l2" type="button" id="6" value="1" code="312" />
		<input name="l3" type="button" id="11" value="1" code="317" />
		<input name="left" type="hat" id="0" value="8" code="16" />
		<input name="pagedown" type="button" id="5" value="1" code="311" />
		<input name="pageup" type="button" id="4" value="1" code="310" />
		<input name="r2" type="button" id="7" value="1" code="313" />
		<input name="r3" type="button" id="12" value="1" code="318" />
		<input name="right" type="hat" id="0" value="2" code="16" />
		<input name="select" type="button" id="8" value="1" code="314" />
		<input name="start" type="button" id="9" value="1" code="315" />
		<input name="up" type="hat" id="0" value="1" code="16" />
		<input name="x" type="button" id="2" value="1" code="307" />
		<input name="y" type="button" id="3" value="1" code="308" />
	</inputConfig>
""")
def generic_xbox_pad() -> Controller: ...


@controller_fixture("""
	<inputConfig type="joystick" deviceName="GPIO Controller 1" deviceGUID="15000000010000000100000000010000">
		<input name="a" type="button" id="1" value="1" code="305" />
		<input name="b" type="button" id="0" value="1" code="304" />
		<input name="down" type="axis" id="1" value="1" code="1" />
		<input name="hotkey" type="button" id="8" value="1" code="316" />
		<input name="left" type="axis" id="0" value="-1" code="0" />
		<input name="pagedown" type="button" id="5" value="1" code="311" />
		<input name="pageup" type="button" id="4" value="1" code="310" />
		<input name="right" type="axis" id="0" value="1" code="0" />
		<input name="select" type="button" id="6" value="1" code="314" />
		<input name="start" type="button" id="7" value="1" code="315" />
		<input name="up" type="axis" id="1" value="-1" code="1" />
		<input name="x" type="button" id="2" value="1" code="307" />
		<input name="y" type="button" id="3" value="1" code="308" />
	</inputConfig>
""")
def gpio_controller_1() -> Controller: ...


@controller_fixture("""
	<inputConfig type="joystick" deviceName="GPIO Controller 2" deviceGUID="15000000010000000200000000010000">
		<input name="a" type="button" id="0" value="1" code="304" />
		<input name="b" type="button" id="1" value="1" code="305" />
		<input name="down" type="axis" id="1" value="1" code="1" />
		<input name="hotkey" type="key" id="0" value="1" code="31546504" />
		<input name="left" type="axis" id="0" value="-1" code="0" />
		<input name="pagedown" type="button" id="5" value="1" code="311" />
		<input name="pageup" type="button" id="4" value="1" code="310" />
		<input name="right" type="axis" id="0" value="1" code="0" />
		<input name="select" type="button" id="6" value="1" code="314" />
		<input name="start" type="button" id="7" value="1" code="315" />
		<input name="up" type="axis" id="1" value="-1" code="1" />
		<input name="x" type="button" id="2" value="1" code="307" />
		<input name="y" type="button" id="3" value="1" code="308" />
	</inputConfig>
""")
def gpio_controller_2() -> Controller: ...


@controller_fixture("""
	<inputConfig type="joystick" deviceName="Sony PLAYSTATION(R)3 Controller" deviceGUID="030000004c0500006802000011810000">
		<input name="a" type="button" id="1" value="1" code="305" />
		<input name="b" type="button" id="0" value="1" code="304" />
		<input name="down" type="button" id="14" value="1" code="545" />
		<input name="hotkey" type="button" id="10" value="1" code="316" />
		<input name="joystick1left" type="axis" id="0" value="-1" code="0" />
		<input name="joystick1up" type="axis" id="1" value="-1" code="1" />
		<input name="joystick2left" type="axis" id="3" value="-1" code="3" />
		<input name="joystick2up" type="axis" id="4" value="-1" code="4" />
		<input name="l2" type="axis" id="2" value="1" code="2" />
		<input name="l3" type="button" id="11" value="1" code="317" />
		<input name="left" type="button" id="15" value="1" code="546" />
		<input name="pagedown" type="button" id="5" value="1" code="311" />
		<input name="pageup" type="button" id="4" value="1" code="310" />
		<input name="r2" type="axis" id="5" value="1" code="5" />
		<input name="r3" type="button" id="12" value="1" code="318" />
		<input name="right" type="button" id="16" value="1" code="547" />
		<input name="select" type="button" id="8" value="1" code="314" />
		<input name="start" type="button" id="9" value="1" code="315" />
		<input name="up" type="button" id="13" value="1" code="544" />
		<input name="x" type="button" id="2" value="1" code="307" />
		<input name="y" type="button" id="3" value="1" code="308" />
	</inputConfig>
""")
def ps3_controller() -> Controller: ...


@controller_fixture("""
	<inputConfig type="joystick" deviceName="Sony Computer Entertainment Wireless Controller" deviceGUID="030000004c050000c405000011810000">
		<input name="a" type="button" id="1" value="1" code="305" />
		<input name="b" type="button" id="0" value="1" code="304" />
		<input name="down" type="hat" id="0" value="4" />
		<input name="hotkey" type="button" id="10" value="1" code="316" />
		<input name="joystick1left" type="axis" id="0" value="-1" code="0" />
		<input name="joystick1up" type="axis" id="1" value="-1" code="1" />
		<input name="joystick2left" type="axis" id="3" value="-1" code="3" />
		<input name="joystick2up" type="axis" id="4" value="-1" code="4" />
		<input name="l2" type="axis" id="2" value="1" code="2" />
		<input name="l3" type="button" id="11" value="1" code="317" />
		<input name="left" type="hat" id="0" value="8" />
		<input name="pagedown" type="button" id="5" value="1" code="311" />
		<input name="pageup" type="button" id="4" value="1" code="310" />
		<input name="r2" type="axis" id="5" value="1" code="5" />
		<input name="r3" type="button" id="12" value="1" code="318" />
		<input name="right" type="hat" id="0" value="2" />
		<input name="select" type="button" id="8" value="1" code="314" />
		<input name="start" type="button" id="9" value="1" code="315" />
		<input name="up" type="hat" id="0" value="1" />
		<input name="x" type="button" id="2" value="1" code="307" />
		<input name="y" type="button" id="3" value="1" code="308" />
	</inputConfig>
""")
def ds4_controller() -> Controller: ...


@controller_fixture("""
	<inputConfig type="joystick" deviceName="Sony Computer Entertainment Wireless Controller" deviceGUID="030000004c050000e60c000011810000">
		<input name="a" type="button" id="1" value="1" code="305" />
		<input name="b" type="button" id="0" value="1" code="304" />
		<input name="down" type="hat" id="0" value="4" />
		<input name="hotkey" type="button" id="10" value="1" code="316" />
		<input name="joystick1left" type="axis" id="0" value="-1" code="0" />
		<input name="joystick1up" type="axis" id="1" value="-1" code="1" />
		<input name="joystick2left" type="axis" id="3" value="-1" code="3" />
		<input name="joystick2up" type="axis" id="4" value="-1" code="4" />
		<input name="l2" type="axis" id="2" value="1" code="2" />
		<input name="l3" type="button" id="11" value="1" code="317" />
		<input name="left" type="hat" id="0" value="8" />
		<input name="pagedown" type="button" id="5" value="1" code="311" />
		<input name="pageup" type="button" id="4" value="1" code="310" />
		<input name="r2" type="axis" id="5" value="1" code="5" />
		<input name="r3" type="button" id="12" value="1" code="318" />
		<input name="right" type="hat" id="0" value="2" />
		<input name="select" type="button" id="8" value="1" code="314" />
		<input name="start" type="button" id="9" value="1" code="315" />
		<input name="up" type="hat" id="0" value="1" />
		<input name="x" type="button" id="2" value="1" code="307" />
		<input name="y" type="button" id="3" value="1" code="308" />
	</inputConfig>
""")
def ds5_controller() -> Controller: ...


@controller_fixture("""
	<inputConfig type="joystick" deviceName="Nintendo Co., Ltd. Pro Controller" deviceGUID="030000007e0500000920000011810000">
		<input name="a" type="button" id="3" value="1" code="305" />
		<input name="b" type="button" id="2" value="1" code="304" />
		<input name="down" type="hat" id="0" value="4" />
		<input name="hotkey" type="button" id="0" value="1" code="256" />
		<input name="joystick1left" type="axis" id="0" value="-1" code="0" />
		<input name="joystick1up" type="axis" id="1" value="-1" code="1" />
		<input name="joystick2left" type="axis" id="2" value="-1" code="3" />
		<input name="joystick2up" type="axis" id="3" value="-1" code="4" />
		<input name="l2" type="button" id="8" value="1" code="312" />
		<input name="l3" type="button" id="12" value="1" code="317" />
		<input name="left" type="hat" id="0" value="8" />
		<input name="pagedown" type="button" id="7" value="1" code="311" />
		<input name="pageup" type="button" id="6" value="1" code="310" />
		<input name="r2" type="button" id="9" value="1" code="313" />
		<input name="r3" type="button" id="13" value="1" code="318" />
		<input name="right" type="hat" id="0" value="2" />
		<input name="select" type="button" id="10" value="1" code="314" />
		<input name="start" type="button" id="11" value="1" code="315" />
		<input name="up" type="hat" id="0" value="1" />
		<input name="x" type="button" id="4" value="1" code="307" />
		<input name="y" type="button" id="5" value="1" code="308" />
	</inputConfig>
""")
def nintendo_pro_controller() -> Controller: ...


@controller_fixture("""
	<inputConfig type="keyboard" deviceName="Keyboard" deviceGUID="-1">
		<input name="up" type="key" id="1073741906" value="1" />
		<input name="down" type="key" id="1073741905" value="1" />
		<input name="left" type="key" id="1073741904" value="1" />
		<input name="right" type="key" id="1073741903" value="1" />
		<input name="a" type="key" id="27" value="1" />
		<input name="b" type="key" id="13" value="1" />
		<input name="pagedown" type="key" id="34" value="1" />
		<input name="pageup" type="key" id="33" value="1" />
		<input name="select" type="key" id="8" value="1" />
		<input name="start" type="key" id="32" value="1" />
		<input name="x" type="key" id="61" value="1" />
		<input name="y" type="key" id="45" value="1" />
	</inputConfig>
""")
def keyboard_controller() -> Controller: ...


@controller_fixture("""
	<inputConfig type="joystick" deviceName="Nintendo Wii Remote" deviceGUID="050000007e050000060300001c3a0000">
		<input name="a" type="button" id="5" value="1" code="258" />
		<input name="b" type="button" id="4" value="1" code="257" />
		<input name="down" type="button" id="1" value="1" code="105" />
		<input name="hotkey" type="button" id="8" value="1" code="316" />
		<input name="left" type="button" id="0" value="1" code="103" />
		<input name="right" type="button" id="3" value="1" code="108" />
		<input name="select" type="button" id="10" value="1" code="412" />
		<input name="start" type="button" id="9" value="1" code="407" />
		<input name="up" type="button" id="2" value="1" code="106" />
		<input name="x" type="button" id="7" value="1" code="305" />
		<input name="y" type="button" id="6" value="1" code="304" />
	</inputConfig>
""")
def wiimote() -> Controller: ...


@controller_fixture("""
    <inputConfig type="joystick" deviceName="N64 Controller" deviceGUID="050000007e0500001920000001800000">
            <input name="a" type="button" id="3" value="1" code="305" />
            <input name="b" type="button" id="2" value="1" code="304" />
            <input name="down" type="hat" id="0" value="4" />
            <input name="hotkey" type="button" id="0" value="1" code="256" />
            <input name="joystick1left" type="axis" id="0" value="-1" code="0" />
            <input name="joystick1up" type="axis" id="1" value="-1" code="1" />
            <input name="l2" type="button" id="10" value="1" code="545" />
            <input name="l3" type="button" id="1" value="1" code="257" />
            <input name="left" type="hat" id="0" value="8" />
            <input name="pagedown" type="button" id="6" value="1" code="311" />
            <input name="pageup" type="button" id="5" value="1" code="310" />
            <input name="r2" type="button" id="12" value="1" code="547" />
            <input name="r3" type="button" id="7" value="1" code="313" />
            <input name="right" type="hat" id="0" value="2" />
            <input name="select" type="button" id="4" value="1" code="309" />
            <input name="start" type="button" id="8" value="1" code="315" />
            <input name="up" type="hat" id="0" value="1" />
            <input name="x" type="button" id="9" value="1" code="544" />
            <input name="y" type="button" id="11" value="1" code="546" />
    </inputConfig>
""")
def n64_controller() -> Controller: ...


@controller_fixture("""
    <inputConfig type="joystick" deviceName="Nintendo Co., Ltd. N64 Controller" deviceGUID="030000007e0500001920000011810000">
            <input name="a" type="button" id="3" value="1" code="304" />
            <input name="b" type="button" id="2" value="1" code="305" />
            <input name="down" type="hat" id="0" value="4" />
            <input name="hotkey" type="button" id="0" value="1" code="256" />
            <input name="joystick1left" type="axis" id="0" value="-1" code="0" />
            <input name="joystick1up" type="axis" id="1" value="-1" code="1" />
            <input name="l2" type="button" id="10" value="1" code="545" />
            <input name="l3" type="button" id="1" value="1" code="257" />
            <input name="left" type="hat" id="0" value="8" />
            <input name="pagedown" type="button" id="6" value="1" code="311" />
            <input name="pageup" type="button" id="5" value="1" code="310" />
            <input name="r2" type="button" id="12" value="1" code="547" />
            <input name="r3" type="button" id="7" value="1" code="313" />
            <input name="right" type="hat" id="0" value="2" />
            <input name="select" type="button" id="4" value="1" code="309" />
            <input name="start" type="button" id="8" value="1" code="315" />
            <input name="up" type="hat" id="0" value="1" />
            <input name="x" type="button" id="9" value="1" code="544" />
            <input name="y" type="button" id="11" value="1" code="546" />
    </inputConfig>
""")
def nintendo_n64_controller() -> Controller: ...


@controller_fixture("""
    <inputConfig type="joystick" deviceName="8BitDo N64 Modkit" deviceGUID="05000000c82d00006928000000010000">
            <input name="a" type="button" id="1" value="1" code="305" />
            <input name="b" type="button" id="0" value="1" code="304" />
            <input name="down" type="hat" id="0" value="4" />
            <input name="hotkey" type="button" id="12" value="1" code="316" />
            <input name="joystick1left" type="axis" id="0" value="-1" code="0" />
            <input name="joystick1up" type="axis" id="1" value="-1" code="1" />
            <input name="l2" type="axis" id="3" value="1" code="5" />
            <input name="left" type="hat" id="0" value="8" />
            <input name="pagedown" type="button" id="7" value="1" code="311" />
            <input name="pageup" type="button" id="6" value="1" code="310" />
            <input name="r2" type="axis" id="2" value="1" code="2" />
            <input name="r3" type="button" id="9" value="1" code="313" />
            <input name="right" type="hat" id="0" value="2" />
            <input name="select" type="button" id="8" value="1" code="312" />
            <input name="start" type="button" id="11" value="1" code="315" />
            <input name="up" type="hat" id="0" value="1" />
            <input name="x" type="axis" id="3" value="-1" code="5" />
            <input name="y" type="axis" id="2" value="-1" code="2" />
    </inputConfig>
""")
def n64_modkit() -> Controller: ...


@controller_fixture("""
	<inputConfig type="joystick" deviceName="Logitech G920 Driving Force Racing Wheel" deviceGUID="030000006d04000062c2000011010000">
		<input name="joystick1left" type="axis" id="0" value="-1" code="0" />
		<input name="a" type="button" id="1" value="1" code="289" />
		<input name="b" type="button" id="0" value="1" code="288" />
		<input name="down" type="hat" id="0" value="4" />
		<input name="hotkey" type="button" id="10" value="1" code="298" />
		<input name="l2" type="axis" id="2" value="-1" code="5" />
		<input name="l3" type="button" id="9" value="1" code="297" />
		<input name="left" type="hat" id="0" value="8" />
		<input name="pagedown" type="button" id="4" value="1" code="292" />
		<input name="pageup" type="button" id="5" value="1" code="293" />
		<input name="r2" type="axis" id="1" value="-1" code="1" />
		<input name="r3" type="button" id="8" value="1" code="296" />
		<input name="right" type="hat" id="0" value="2" />
		<input name="select" type="button" id="7" value="1" code="295" />
		<input name="start" type="button" id="6" value="1" code="294" />
		<input name="up" type="hat" id="0" value="1" />
		<input name="x" type="button" id="3" value="1" code="291" />
		<input name="y" type="button" id="2" value="1" code="290" />
	</inputConfig>
""")
def g920_wheel() -> Controller: ...


@controller_fixture("""
	<inputConfig type="joystick" deviceName="Xtension 2P Player 1" deviceGUID="0000000010ba00008ace000000000000">
		<input name="a" type="button" id="1" value="1" code="305" />
		<input name="b" type="button" id="0" value="1" code="304" />
		<input name="down" type="hat" id="0" value="4" />
		<input name="hotkey" type="button" id="6" value="1" code="314" />
		<input name="left" type="hat" id="0" value="8" />
		<input name="pagedown" type="button" id="5" value="1" code="311" />
		<input name="pageup" type="button" id="4" value="1" code="310" />
		<input name="right" type="hat" id="0" value="2" />
		<input name="select" type="button" id="6" value="1" code="314" />
		<input name="start" type="button" id="7" value="1" code="315" />
		<input name="up" type="hat" id="0" value="1" />
		<input name="x" type="button" id="2" value="1" code="307" />
		<input name="y" type="button" id="3" value="1" code="308" />
	</inputConfig>
""")
def xtension_2p_p1() -> Controller: ...


@controller_fixture("""
	<inputConfig type="joystick" deviceName="Anbernic pad" deviceGUID="00000000416e6265726e696320706100">
		<input name="a" type="button" id="1" value="1" code="305" />
		<input name="b" type="button" id="0" value="1" code="304" />
		<input name="down" type="button" id="14" value="1" code="545" />
		<input name="hotkey" type="button" id="10" value="1" code="316" />
		<input name="joystick1left" type="axis" id="0" value="-1" code="0" />
		<input name="joystick1up" type="axis" id="1" value="1" code="1" />
		<input name="joystick2left" type="axis" id="2" value="-1" code="3" />
		<input name="joystick2up" type="axis" id="3" value="1" code="4" />
		<input name="l2" type="button" id="6" value="1" code="312" />
		<input name="l3" type="button" id="11" value="1" code="317" />
		<input name="left" type="button" id="15" value="1" code="546" />
		<input name="pagedown" type="button" id="5" value="1" code="311" />
		<input name="pageup" type="button" id="4" value="1" code="310" />
		<input name="r2" type="button" id="7" value="1" code="313" />
		<input name="r3" type="button" id="12" value="1" code="318" />
		<input name="right" type="button" id="16" value="1" code="547" />
		<input name="select" type="button" id="8" value="1" code="314" />
		<input name="start" type="button" id="9" value="1" code="315" />
		<input name="up" type="button" id="13" value="1" code="544" />
		<input name="x" type="button" id="2" value="1" code="307" />
		<input name="y" type="button" id="3" value="1" code="308" />
	</inputConfig>
""")
def anbernic_pad() -> Controller: ...


def make_player_controller(controller: Controller, player_number: int, /) -> Controller:
    return controller.replace(
        player_number=player_number,
        index=player_number - 1,
        device_path=f'/dev/input/event{player_number}',
    )


def make_player_controller_list(*controllers: Controller) -> ControllerList:
    return [
        make_player_controller(controller, player_number)
        for player_number, controller in enumerate(controllers, start=1)
    ]


@pytest.fixture
def one_player_controllers(generic_xbox_pad: Controller) -> Controllers:
    return make_player_controller_list(generic_xbox_pad)


@pytest.fixture
def two_player_controllers(generic_xbox_pad: Controller) -> Controllers:
    return make_player_controller_list(generic_xbox_pad, generic_xbox_pad)
