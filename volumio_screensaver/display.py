from __future__ import annotations

import logging
import random
from pathlib import Path

from .config import Config

LOGGER = logging.getLogger(__name__)

FONT_EXTENSIONS = {".otf", ".ttf"}
MIN_COLOR_COMPONENT = 96
MIN_COLOR_LUMINANCE = 150
FONT_FIT_MARGIN = 16
CLOCK_SAMPLE_TEXT = "88:88"


def bundled_font_paths() -> list[Path]:
    return sorted(
        path
        for path in Path(__file__).resolve().parent.iterdir()
        if path.is_file() and path.suffix.lower() in FONT_EXTENSIONS
    )


def random_visible_color(rng: random.Random | None = None) -> tuple[int, int, int]:
    generator = rng or random

    for _ in range(100):
        color = tuple(generator.randint(MIN_COLOR_COMPONENT, 255) for _ in range(3))
        luminance = 0.2126 * color[0] + 0.7152 * color[1] + 0.0722 * color[2]
        if luminance >= MIN_COLOR_LUMINANCE:
            return color

    return (255, 255, 255)


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
        self._font_size = config.font_size
        self._font_paths = self._discover_font_paths(config.font_path)
        self._font_color = (255, 255, 255)

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
        self._font = self._load_fitted_font(
            self._font_paths[0] if self._font_paths else None,
        )
        # Do not clear the display at service startup. Volumio/Pirate Audio may
        # already be using the ST7789 screen, and the screen saver should only
        # take over once the idle delay has elapsed.

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def choose_random_style(self, rng: random.Random | None = None) -> None:
        generator = rng or random
        if self._font_paths:
            font_path = generator.choice(self._font_paths)
            self._font = self._load_fitted_font(font_path)
            LOGGER.debug("Clock font selected: %s", font_path)
        self._font_color = random_visible_color(generator)

    def measure(self, text: str) -> tuple[int, int]:
        image = self._image_cls.new("RGB", (self._width, self._height), color=(0, 0, 0))
        draw = self._draw_cls.Draw(image)
        return self._text_size(draw, text)

    def show_clock(self, text: str, position: tuple[int, int]) -> None:
        image = self._image_cls.new("RGB", (self._width, self._height), color=(0, 0, 0))
        draw = self._draw_cls.Draw(image)
        x, y = self._draw_origin(draw, position)
        for segment_text, segment_position in self._clock_segments(draw, text, x, y):
            draw.text(
                segment_position,
                segment_text,
                font=self._font,
                fill=self._font_color,
            )
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

    def _discover_font_paths(self, configured_path: str) -> list[Path]:
        bundled_fonts = bundled_font_paths()
        if bundled_fonts:
            LOGGER.info("Loaded %d bundled clock fonts", len(bundled_fonts))
            return bundled_fonts

        candidates = [
            Path(configured_path) if configured_path else None,
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
        ]
        return [path for path in candidates if path and path.exists()]

    def _load_fitted_font(self, path: Path | None):
        if not path or not path.exists():
            LOGGER.warning("No configured TTF/OTF font found, using PIL default font")
            return self._font_cls.load_default()

        max_width = max(1, self._width - FONT_FIT_MARGIN)
        max_height = max(1, self._height - FONT_FIT_MARGIN)
        best_size = self._font_size
        low = 1
        high = max(self._font_size * 3, self._font_size + 1)
        probe_image = self._image_cls.new(
            "RGB",
            (self._width, self._height),
            color=(0, 0, 0),
        )
        probe_draw = self._draw_cls.Draw(probe_image)

        while low <= high:
            size = (low + high) // 2
            font = self._font_cls.truetype(str(path), size)
            width, height = self._text_size(probe_draw, CLOCK_SAMPLE_TEXT, font)
            if width <= max_width and height <= max_height:
                best_size = size
                low = size + 1
            else:
                high = size - 1

        return self._font_cls.truetype(str(path), best_size)

    def _clock_segments(self, draw, text: str, x: int, y: int):
        hours = text[:2]
        minutes = text[-2:]
        hours_width, _ = self._text_size(draw, "88")
        colon_width, _ = self._text_size(draw, ":")

        segments = [
            (hours, (x, y)),
            (minutes, (x + hours_width + colon_width, y)),
        ]
        if ":" in text:
            segments.insert(1, (":", (x + hours_width, y)))
        return segments

    def _draw_origin(self, draw, position: tuple[int, int]) -> tuple[int, int]:
        bbox = draw.textbbox((0, 0), CLOCK_SAMPLE_TEXT, font=self._font)
        return position[0] - bbox[0], position[1] - bbox[1]

    def _text_size(self, draw, text: str, font=None) -> tuple[int, int]:
        bbox = draw.textbbox((0, 0), text, font=font or self._font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
