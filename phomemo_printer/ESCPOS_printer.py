import os, sys
from .ESCPOS_constants import *
import socket
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
        if image.width > image.height:
            image = image.transpose(Image.ROTATE_90)

        # width 384 dots
        IMAGE_WIDTH_BYTES = 70
        IMAGE_WIDTH_BITS = IMAGE_WIDTH_BYTES * 8
        image = image.resize(
            size=(IMAGE_WIDTH_BITS, int(image.height * IMAGE_WIDTH_BITS / image.width))
        )

        # black&white printer: dithering
        image = image.convert(mode="1")

        self._print_bytes(HEADER)
        for start_index in range(0, image.height, 256):
            end_index = (
                start_index + 256 if image.height - 256 > start_index else image.height
            )
            line_height = end_index - start_index

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
                    # 0x0a alone is processed like LineFeed by the printe
                    if byte == 0x0A:
                        byte = 0x14
                    # self._print_bytes(byte.to_bytes(1, 'little'))
                    image_line += byte.to_bytes(1, "little")

                image_lines.append(image_line)

            for l in image_lines:
                self._print_bytes(l)

        self._print_bytes(PRINT_FEED)
        self._print_bytes(PRINT_FEED)
        self._print_bytes(FOOTER)
