import argparse, sys
from .ESCPOS_printer import Printer
from .version import __version__


def main(args):
    printer = Printer(bluetooth_address=args.bluetooth_address, channel=args.channel)

    if args.image:
        printer.print_image(args.image)

    printer.close()


def cli():
    parser = argparse.ArgumentParser(
        description="Print bytes to stdout for redirection to an ESC POS printer"
    )

    parser.add_argument(
        "-v", "--version", action="version", version="%(prog)s " + __version__
    )
    group = parser.add_mutually_exclusive_group(required=True)
    
    group.add_argument(
        "-i", "--image", type=str, help="Image file to print", required=False
    )
    parser.add_argument(
        "-a",
        "--bluetooth_address",
        type=str,
        help="The address of your bluetooth device (found using `hcitool scan`)",
        required=True,
    )
    parser.add_argument(
        "-c",
        "--channel",
        type=int,
        help="The channel to connect to your bluetooth device on",
        required=True,
    )

    args = parser.parse_args()
    main(args)
