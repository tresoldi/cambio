#!/usr/bin/env python3

"""
Development script for downloading CLTS data and building local resources.

The script is used to pre-process and cache some expansive computations
needed by `alteruphono`, such as those returned by `features2graphemes()`.
It also allows to remove the dependency on `pyclts` and associated
libraries, which is necessary for preparing the Golang version of
the library.
"""

# TODO: use alteruphono.utils.clear_text

# Import Python standard libraries
import csv
import logging
from pathlib import Path
import urllib.request

# Import the library to compute the graphemes
import alteruphono

# Set the resource directory
RESOURCE_DIR = Path(__file__).parent / "resources"

# Hard-coded urls for files
FEATURE_FILE = (
    "https://raw.githubusercontent.com/cldf-clts/clts/master/data/features.tsv"
)
SOUNDS_FILE = (
    "https://raw.githubusercontent.com/cldf-clts/clts/master/data/sounds.tsv"
)


def tokenize(line):
    """
    Process a CSV line returned by `urllib`.
    """

    return line.decode("utf-8").strip().split("\t")


def prepare_features():
    """
    Prepare feature file.
    """

    feature_data = [
        {"VALUE": "consonant", "FEATURE": "type"},
        {"VALUE": "vowel", "FEATURE": "type"},
    ]
    with urllib.request.urlopen(FEATURE_FILE) as response:
        header = True
        for line in response:
            # Skip over header
            if header:
                header = False
                continue

            # Collect everything except tones
            f_type, f_feature, f_value = tokenize(line)
            if f_type != "tone":
                feature_data.append({"VALUE": f_value, "FEATURE": f_feature})

    # Write output
    filename = RESOURCE_DIR / "features_bipa.tsv"
    with open(filename.as_posix(), "w") as handler:
        header = ["VALUE", "FEATURE"]
        handler.write("%s\n" % "\t".join(header))

        feature_data = sorted(feature_data, key=lambda i: i["VALUE"])
        for row in feature_data:
            buf = [row[field] for field in header]
            handler.write("%s\n" % "\t".join(buf))


def prepare_sounds():
    """
    Prepare sound file.
    """

    sounds_data = []
    with urllib.request.urlopen(SOUNDS_FILE) as response:
        header = True
        for line in response:
            # Skip over header
            if header:
                header = False
                continue

            # Collect everything except tones and clusters
            f_name, f_type, f_grapheme, f_unicode_gen = tokenize(line)[:4]
            if "tone" in f_name.split():
                continue
            if "from" in f_name.split():
                continue

            sounds_data.append({"GRAPHEME": f_grapheme, "NAME": f_name})

    # Write output
    filename = RESOURCE_DIR / "sounds.tsv"
    with open(filename.as_posix(), "w") as handler:
        header = ["GRAPHEME", "NAME"]
        handler.write("%s\n" % "\t".join(header))

        sounds_data = sorted(sounds_data, key=lambda i: i["GRAPHEME"])
        for row in sounds_data:
            buf = [row[field] for field in header]
            handler.write("%s\n" % "\t".join(buf))


def prepare_classes():
    """
    Prepare sound classes.
    """

    # Read data, as if in the normal execution
    features = alteruphono.utils.read_sound_features()
    sounds = alteruphono.utils.read_sounds(features)

    # Read the sound classes defined in resources, and from there
    # the graphemes
    filename = RESOURCE_DIR / "sound_classes.tsv"
    classes = []
    with open(filename.as_posix()) as handler:
        reader = csv.DictReader(handler, delimiter="\t")
        for row in reader:
            sound_class = {}
            sound_class["SOUND_CLASS"] = row["SOUND_CLASS"]
            sound_class["DESCRIPTION"] = row["DESCRIPTION"]
            sound_class["FEATURES"] = row["FEATURES"]
            sound_class["GRAPHEMES"] = alteruphono.utils.features2graphemes(
                row["FEATURES"], sounds
            )

            classes.append(sound_class)

    # output to the same file
    with open(filename.as_posix(), "w") as handler:
        header = ["SOUND_CLASS", "DESCRIPTION", "FEATURES", "GRAPHEMES"]
        handler.write("%s\n" % "\t".join(header))

        for row in classes:
            buf = [row[field] for field in header]
            buf = [v if isinstance(v, str) else "|".join(v) for v in buf]
            handler.write("%s\n" % "\t".join(buf))


def main():
    """
    Entry point.
    """

    # Set logger
    logging.basicConfig(level=logging.INFO)

    # Download the list of features; unfortunately we cannot pass urllib's
    # handler to csv.DictReader due to encoding
    logging.info("Downloading and processing features")
    prepare_features()

    # Prepare sounds
    logging.info("Downloading and processing sounds")
    prepare_sounds()

    # Prepare classes and their graphemes
    logging.info("Building sound classes")
    prepare_classes()


if __name__ == "__main__":
    main()
