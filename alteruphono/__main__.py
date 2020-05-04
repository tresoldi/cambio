#!/usr/bin/env python3

"""
Entry point for the command line `alteruphono` utility.
"""

# Import Python standard libraries
import argparse

# Import our library
import alteruphono


def parse_arguments():
    """
    Parse command-line arguments and return as a namespace.

    Returns
    -------
    args : namespace
        A namespace with all the parameters.
    """

    # Define the parser
    parser = argparse.ArgumentParser(
        description="AlteruPhono command-line utility."
    )
    parser.add_argument(
        "command",
        choices=["forward", "backward"],
        help="Direction of sound change.",
    )
    parser.add_argument(
        "sequence",
        type=str,
        help='Sequence of sounds to operate upon (e.g., `"# p a t #"`).',
    )
    parser.add_argument(
        "rule", type=str, help='Rule to apply (e.g., `"p > b / _ V"`)'
    )

    # parse arguments and return
    args = parser.parse_args()

    return args


def main():
    """
    Entry point for the command-line utility.
    """

    # Collect arguments (can load from a config file as well in the future)
    args = parse_arguments()

    # Execute and show results
    if args.command == "forward":
        ret = alteruphono.forward(args.sequence, args.rule)
    elif args.command == "backward":
        ret = [
            str(seq) for seq in alteruphono.backward(args.sequence, args.rule)
        ]

    print(ret)


if __name__ == "__main__":
    main()
