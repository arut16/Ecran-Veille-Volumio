from __future__ import annotations

import unittest

from volumio_screensaver.config import parse_pins


class ConfigTest(unittest.TestCase):
    def test_parse_pins(self) -> None:
        self.assertEqual(parse_pins("5,6,16,24"), [5, 6, 16, 24])
        self.assertEqual(parse_pins(" 5, 6, 16, 20 "), [5, 6, 16, 20])

    def test_parse_pins_rejects_empty_list(self) -> None:
        with self.assertRaises(ValueError):
            parse_pins(" , ")


if __name__ == "__main__":
    unittest.main()
