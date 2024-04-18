import os, sys
from .ESCPOS_constants import *
import socket
import time
from PIL import Image


class Printer:
    def __init__(self, bluetooth_address, channel):
        self.s = socket.socket(
            socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM
        )
        self.s.connect((bluetooth_address, channel))

    def close(self):
        """
            Close the connection to the bluetooth socket
        """
        self.s.close()

    def _print_bytes(self, bytes):
        """
            Write bytes to stdout

            Args:
                bytes (bytes): Bytes to write to stdout
        """
        self.s.send(bytes)

    # from https://github.com/vivier/phomemo-tools
    def print_image(self, image_path):
        """
            Print an image

            Args:
                image_path (str): Path to an image file to print
        """
        image = Image.open(image_path)

        # width was determined empirically, using 80mm paper on a printer at 300 dpi
        IMAGE_WIDTH_BYTES = 110
        IMAGE_WIDTH_BITS = IMAGE_WIDTH_BYTES * 8
        image = image.resize(
            size=(IMAGE_WIDTH_BITS, int(image.height * IMAGE_WIDTH_BITS / image.width))
        )

        # black & white printer: dithering
        image = image.convert(mode="1")

        # Both sleeping and reducing the number of lines per block (from 256)
        # seem to be necessary otherwise the printer stops printing prematurely.
        SLEEP_BETWEEN_BLOCKS_IN_SECONDS = 0.5
        LINES_PER_BLOCK = 64

        self._print_bytes(HEADER)
        for start_index in range(0, image.height, LINES_PER_BLOCK):
            end_index = (
                start_index + LINES_PER_BLOCK if image.height - LINES_PER_BLOCK > start_index else image.height
            )
            line_height = end_index - start_index

            time.sleep(SLEEP_BETWEEN_BLOCKS_IN_SECONDS)

            BLOCK_MARKER = (
                GSV0
                + bytes([IMAGE_WIDTH_BYTES])
                + b"\x00"
                + bytes([line_height - 1])
                + b"\x00"
            )
            self._print_bytes(BLOCK_MARKER)

            image_lines = []
            for image_line_index in range(line_height):
                image_line = b""
                for byte_start in range(int(image.width / 8)):
                    byte = 0
                    for bit in range(8):
                        if (
                            image.getpixel(
                                (byte_start * 8 + bit, image_line_index + start_index)
                            )
                            == 0
                        ):
                            byte |= 1 << (7 - bit)
                    # 0x0a breaks the rendering
                    # 0x0a alone is processed like LineFeed by the printer
                    if byte == 0x0A:
                        byte = 0x14
                    # self._print_bytes(byte.to_bytes(1, 'little'))
                    image_line += byte.to_bytes(1, "little")

                image_lines.append(image_line)

            for l in image_lines:
                self._print_bytes(l)


        time.sleep(SLEEP_BETWEEN_BLOCKS_IN_SECONDS)
        self._print_bytes(PRINT_FEED)
        self._print_bytes(PRINT_FEED)
        time.sleep(SLEEP_BETWEEN_BLOCKS_IN_SECONDS)
        self._print_bytes(FOOTER)
        time.sleep(SLEEP_BETWEEN_BLOCKS_IN_SECONDS)
