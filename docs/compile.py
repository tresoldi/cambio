#!/usr/bin/env python3
# encoding: utf-8

from pathlib import Path
import subprocess

from pyclts import CLTS

# Cache the path of the compile script
# TODO: replace in the future when this is part of the general deployment
PEG_PATH = Path(__file__).parent.absolute()


def compile_grammar():
    print("Building IPA_REPLACE list")
    # Instantiate the BIPA transcription system
    bipa = CLTS().bipa

    # Extract the list of all graphemes, minus excludes
    # TODO: move excludes to a separate file
    excludes = ["ǃǃ", "+", "_", "←", "→", "∼", "¯"]
    graphemes = [key for key in bipa.sounds.keys() if key not in excludes]

    # Build a disjoint string of all graphemes in reverse length order
    graphemes.sort(key=lambda s: (-len(s), s))
    grapheme_string = "/%s/" % "|".join(graphemes)

    # Load the template, replace the grapheme_string, and write back
    template_file = PEG_PATH / "soundchange.peg.template"
    grammar_file = PEG_PATH / "soundchange.peg"
    graph_grammar_file = PEG_PATH / "graph_soundchange.peg"

    with open(template_file.as_posix()) as template_handler:
        template = template_handler.read()
        grammar_source = template.replace("$$IPA_REPLACE$$", grapheme_string)
        graph_source = template.replace("$$IPA_REPLACE$$", '"CLTS BIPA GRAPHEMES"')

    print("Building grammar file from template")
    with open(grammar_file.as_posix(), "w") as grammar_handler:
        grammar_handler.write(grammar_source)

    print("Building graph grammar file from template")
    with open(graph_grammar_file.as_posix(), "w") as graph_grammar_handler:
        graph_grammar_handler.write(graph_source)


def grammar2python():
    """
    Compiles the PEG grammar to a Python file.

    While this could be run using Tastu as a library, for workflow
    organization it is currently calling a subprocess.
    """

    print("Generating soundchange parser")
    input_file = PEG_PATH / "soundchange.peg"
    output_file = PEG_PATH / "soundchange.py"
    subprocess.run(["tatsu", "-o", output_file.as_posix(), input_file.as_posix()])


def grammar2graph():
    """
    Compiles the PEG grammar to a DOT file an build a graph.
    """

    print("Generating soundchange graph")
    input_file = PEG_PATH / "graph_soundchange.peg"
    dot_file = PEG_PATH / "soundchange.dot"
    png_file = PEG_PATH / "soundchange.png"

    subprocess.run(["tatsu", "-d", "-o", dot_file.as_posix(), input_file.as_posix()])
    subprocess.run(["dot", "-Tpng", "-o", png_file.as_posix(), dot_file.as_posix()])


if __name__ == "__main__":
    compile_grammar()
    grammar2python()
    grammar2graph()
