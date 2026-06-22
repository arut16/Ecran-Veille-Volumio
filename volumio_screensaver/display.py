from __future__ import annotations

import logging
from pathlib import Path

from .config import Config

LOGGER = logging.getLogger(__name__)


class ClockDisplay:
    def __init__(self, config: Config) -> None:
        from PIL import Image, ImageDraw, ImageFont
        import st7789

        self._image_cls = Image
        self._draw_cls = ImageDraw
        self._font_cls = ImageFont
        self._width = config.display_width
        self._height = config.display_height
        self._blank_turns_backlight_off = config.blank_turns_backlight_off

        self._disp = st7789.ST7789(
            port=config.display_port,
            cs=config.display_cs,
            dc=config.display_dc,
            backlight=config.display_backlight,
            width=config.display_width,
            height=config.display_height,
            rotation=config.display_rotation,
            spi_speed_hz=config.display_spi_speed,
            offset_left=config.display_offset_left,
            offset_top=config.display_offset_top,
        )
        self._disp.begin()
        self._font = self._load_font(config.font_path, config.font_size)
        # Do not clear the display at service startup. Volumio/Pirate Audio may
        # already be using the ST7789 screen, and the screen saver should only
        # take over once the idle delay has elapsed.

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def measure(self, text: str) -> tuple[int, int]:
        image = self._image_cls.new("RGB", (self._width, self._height), color=(0, 0, 0))
        draw = self._draw_cls.Draw(image)
        bbox = draw.textbbox((0, 0), text, font=self._font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def show_clock(self, text: str, position: tuple[int, int]) -> None:
        image = self._image_cls.new("RGB", (self._width, self._height), color=(0, 0, 0))
        draw = self._draw_cls.Draw(image)
        bbox = draw.textbbox((0, 0), text, font=self._font)
        x = position[0] - bbox[0]
        y = position[1] - bbox[1]
        draw.text((x, y), text, font=self._font, fill=(255, 255, 255))
        self._disp.display(image)
        self._set_backlight(True)

    def clear(self, backlight_on: bool | None = None) -> None:
        image = self._image_cls.new("RGB", (self._width, self._height), color=(0, 0, 0))
        self._disp.display(image)

        if backlight_on is None:
            backlight_on = not self._blank_turns_backlight_off

        self._set_backlight(backlight_on)

    def _set_backlight(self, on: bool) -> None:
        try:
            self._disp.set_backlight(on)
        except AttributeError:
            LOGGER.debug("ST7789 library does not expose set_backlight")

    def _load_font(self, configured_path: str, size: int):
        candidates = [
            configured_path,
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        ]

        for path in candidates:
            if path and Path(path).exists():
                return self._font_cls.truetype(path, size)

        LOGGER.warning("No configured TTF font found, using PIL default font")
        return self._font_cls.load_default()
