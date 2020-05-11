"""
Defines the phonetic model class.

This class is the core of the system, taking care of forward and backward
operations. It requires a sound model from disk, defining properties such
as list of sounds, features, etc. By default, it will load the model
distributed with the package.
"""

# Import Python standard libraries
from copy import copy
import csv
import itertools
from pathlib import Path
import sys

# Import package
from alteruphono.ast import AST
import alteruphono.utils
from alteruphono.sequence import Sequence
from alteruphono.rule import Rule


def read_sound_features(filename):
    """
    Read sound feature definitions.

    Parameters
    ----------
    filename : string
        Path to the TSV file holding the sound feature definition.

    Returns
    -------
    features : dict
        A dictionary with feature values (such as "devoiced") as keys and
        feature classes (such as "voicing") as values.
    """

    with open(filename) as tsvfile:
        features = {
            row["VALUE"]: row["FEATURE"]
            for row in csv.DictReader(tsvfile, delimiter="\t")
        }

    return features


def read_sounds(featsys, filename):
    """
    Read sound definitions.

    Parameters
    ----------
    featsys : dict
        The feature system to be used.

    filename : string
        Path to the TSV file holding the sound definition.

    Returns
    -------
    sounds : dict
        A dictionary with graphemes (such as "a") as keys and
        feature definitions as values.
    """

    sounds = {}
    with open(filename) as csvfile:
        for row in csv.DictReader(csvfile, delimiter="\t"):
            grapheme = alteruphono.utils.clear_text(row["GRAPHEME"])
            features = row["NAME"].split()

            # TODO: currently skipping over clusters and tones
            if "from" in features:
                continue
            if "tone" in features:
                continue

            descriptors = {featsys[feat]: feat for feat in features}
            sounds[grapheme] = descriptors

    return sounds


def read_sound_classes(sounds, filename):
    """
    Read sound class definitions.

    Parameters
    ----------
    filename : string
        Path to the TSV file holding the sound class definition.

    Returns
    -------
    sound_classes : dict
        A dictionary with sound class names as keys (such as "A" or
        "CV"), and corresponding descriptions and list of graphemes
        as values.
    """

    with open(filename) as tsvfile:
        sound_classes = {}
        for row in csv.DictReader(tsvfile, delimiter="\t"):
            # GRAPHEMES can hold either a list of graphemes separated by
            # a vertical bar or a set of features that will be compiled
            # into graphemes with `sounds`
            # TODO: rename GRAPHEMES column
            if row["GRAPHEMES"]:
                graphemes = tuple(
                    [
                        alteruphono.utils.clear_text(grapheme)
                        for grapheme in row["GRAPHEMES"].split("|")
                    ]
                )
            else:
                graphemes = alteruphono.utils.features2graphemes(
                    row["GRAPHEMES"], sounds
                )

            sound_classes[row["SOUND_CLASS"]] = {
                "description": row["DESCRIPTION"],
                "features": row["FEATURES"],
                "graphemes": graphemes,
            }

    return sound_classes


# TODO: rename to collect features or something in these lines
def parse_features(modifier):
    """
    Returns
    -------
    features : Features
        A `Features` object, with attributes `.positive` (a list of strings),
        `negative` (a list of strings), and `custom` (a dictionary with
        strings as keys and strings as values).
    """

    # TODO: write properly, currently without custom
    # TODO: rename AST to something more general, out attrib class
    # TODO: rename feature.feature to feature.name or something similar
    positive, negative = [], []
    for feature in modifier:
        if feature.value == "+":
            positive.append(feature.feature)
        elif feature.value == "-":
            negative.append(feature.feature)

    # TODO: while sort? to cache/hash?
    return AST(
        {
            "positive": sorted(positive),
            "negative": sorted(negative),
            "custom": [],
        }
    )

class Model:
    # Define our custom caches; we are not using Python's functools because
    # we need a finer management of the cache. Note that this only holds
    # forward and backward calls as a whole: other functions might
    # implement their own caches
    # TODO: incorporate self.modifier_cache and self.desc2graph
    _cache = {"forward": {}, "backward": {}, "match": {}}
    _cache_stats = {
        "forward": [0, 0],  # hits, misses
        "backward": [0, 0],  # hits, misses
        "match": [0, 0],  # hits, misses
    }

    def __init__(self, model_path=None):
        # Read the model from disk, defaulting to the package one
        if not model_path:
            model_path = Path(__file__).parent.parent / "resources"
        else:
            model_path = Path(model_path)

        # TODO: fix paths after prototyping
        feature_file = model_path / "features.tsv"
        self.features = read_sound_features(feature_file.as_posix())

        sounds_file = model_path / "sounds.tsv"
        self.sounds = read_sounds(self.features, sounds_file.as_posix())

        classes_file = model_path / "classes.tsv"
        self.sound_classes = read_sound_classes(
            self.sounds, classes_file.as_posix()
        )

        # caches
        self.modifier_cache = {}
        self.desc2graph = {}

    def cache_query(self, collection, key):
        if key in self._cache[collection]:
            # Update individual and global hits
            self._cache_stats[collection][0] += 1
            self._cache[collection][key][0] += 1

#            print("> CACHE", collection, key, self._cache[collection][key])

            return self._cache[collection][key][1]

        # update miss
        self._cache_stats[collection][1] += 1

        return None

    def cache_add(self, collection, key, value):
        #        print(sys.getsizeof(self._cache_fw), sys.getsizeof(self._cache_bw))
        #        print(alteruphono.utils.rec_getsizeof(self._cache_fw),
        #            alteruphono.utils.rec_getsizeof(self._cache_bw))

        self._cache[collection][key] = [0, value]

    # TODO: deal with custom features
    def apply_modifier(self, grapheme, modifier, inverse=False):
        """
        Apply a modifier to a grapheme.
        """

        # In case of no modifier, the grapheme is obviously the same
        if not modifier:
            return grapheme

        # Check if the combination has already been computed and cached
        # TODO: reimplement cache
        # cache_key = tuple([grapheme, modifier, inverse])
        # if cache_key in self.modifier_cache:
        #    return self.modifier_cache[cache_key]

        # Parse the provided modifier
        features = parse_features(modifier)

        # Invert features if requested
        # TODO: for the time being, just hard-coding them; should be
        #       implemented with some search (that can be *very* expansive...)
        if inverse:
            modifier_key = tuple(
                sorted(
                    [(feat["feature"], feat["value"]) for feat in modifier],
                    key=lambda f: f[0],
                )
            )

            ret = alteruphono.utils.HARD_CODED_INVERSE_MODIFIER.get(
                (grapheme, modifier_key), None
            )

            if not ret:
                raise ValueError(
                    "Missing hardcoded backwards modifier:",
                    (grapheme, modifier_key),
                )

            # cache
            self.modifier_cache[(grapheme, modifier_key, inverse)] = ret

            return ret

        # Obtain the phonological descriptors for the base sound, returning
        # an alternative representation if not found
        # TODO: consider redoing the logic, as we don't need to extract values
        #       given that those are already properly organized in the data
        # TODO: build an ipa description no matter what...
        if grapheme not in self.sounds:
            return f"{grapheme}{modifier}"
        descriptors = list(self.sounds[grapheme].values())

        # Remove any requested features
        descriptors = [
            value for value in descriptors if value not in features.negative
        ]

        # Remove any descriptor from a feature type we are changing, and add
        # all positive descriptors. If we are adding a vowel height, for
        # example, will first remove all vowel heights and only then add
        # the one we desire.
        for feature in features.positive:
            descriptors = [
                value
                for value in descriptors
                if self.features[value] != self.features[feature]
            ]
        descriptors += features.positive

        # Obtain the grapheme based on the description
        # TODO: decide if we should just memoize instead of caching this way
        descriptors = tuple(sorted(descriptors))
        grapheme = self.desc2graph.get(descriptors, None)
        if not grapheme:
            grapheme = alteruphono.utils.descriptors2grapheme(
                descriptors, self.sounds
            )

            # TODO: should always return, can we guarantee?
            if grapheme:
                self.desc2graph[descriptors] = grapheme
            else:
                # TODO: decide on descriptor order
                grapheme = "[%s]" % ",".join(descriptors)

        # cache
        # TODO: reimplement cache
        # self.modifier_cache[cache_key] = grapheme

        return grapheme

    # TODO: return False as soon as possible
    def check_match(self, sequence, pattern):
        """
        Check if a sequence matches a given pattern.
        """

        # If there is a length mismatch, it does not match by definition
        # NOTE: with the standard code in place for forward and backward
        #       operation, this test will always fail ("sequence" and
        #       "pattern" will always have the same length), but it is worth
        #       keeping the code as the `.check_match()` method is one
        #       facing the users, who may provide sequences mismatched in
        #       length.
        if len(sequence) != len(pattern):
            return False

        # Build cache key
        cache_key = (
            " ".join(sequence),
            " ".join([str(token) for token in pattern]),
        )
        cache_val = self.cache_query("match", cache_key)
        if cache_val:
            return cache_val

        ret = True
        for token, ref in zip(sequence, pattern):
            # check choice (list) first
            if isinstance(ref, list):
                # Check the sub-match for each alternative; if the
                # alternative is a grapheme, carry any modifier
                # TODO: return as soon as possible

                alt_matches = [self.check_match([token], [alt]) for alt in ref]

                if not any(alt_matches):
                    ret = False
            elif "grapheme" in ref:
                ipa = self.apply_modifier(ref.grapheme, ref.modifier)
                if token != ipa:
                    ret = False
            elif "boundary" in ref:
                if token != "#":
                    ret = False
            elif "sound_class" in ref:
                # Apply the modifier to all the items in the sound class,
                # so we can check if the `token` is actually there.
                modified = [
                    self.apply_modifier(grapheme, ref.modifier)
                    for grapheme in self.sound_classes[ref.sound_class][
                        "graphemes"
                    ]
                ]
                modified = list({grapheme for grapheme in modified if grapheme})

                if token not in modified:
                    ret = False

        # cache
        self.cache_add("match", cache_key, ret)

        return ret

    # TODO: rename `rule` to `pattern`
    def _forward_translate(self, sequence, rule):
        """
        Translate an intermediary `ante` to `post` sequence.
        """

        post_seq = []

        for entry in rule.post:
            # Note that this will, as intended, skip over `null`s
            if "grapheme" in entry:
                post_seq.append(entry.grapheme)
            elif "backref" in entry:
                # Compute the actual index (Python lists are 0-based)
                index = entry.backref - 1

                # Refer to `correspondence`, if specified
                # TODO: recheck correspondence
                if "correspondence" in entry:
                    # get the alternative index in `ante`
                    # NOTE: `post_alts` has [1:-1] for the curly brackets
                    ante_alts = [
                        alt.ipa for alt in rule.ante[index].alternative
                    ]
                    post_alts = rule.post[index].correspondence[1:-1].split(",")

                    idx = ante_alts.index(sequence[index])

                    post_seq.append(post_alts[idx])
                else:
                    token = sequence[index]
                    post_seq.append(self.apply_modifier(token, entry.modifier))

        return post_seq

    def forward(self, ante_seq, rule):
        """
        Apply forward transformation to a sequence given a rule.
        """

        # Transform `ante_seq` in a Sequence, if necessary
        if not isinstance(ante_seq, alteruphono.sequence.Sequence):
            ante_seq = Sequence(ante_seq)

        # Return the cached value, if it exists
        cache_key = (ante_seq._sequence, rule.source)
        cache_val = self.cache_query("forward", cache_key)
        if cache_val:
            return cache_val

        # Iterate over the sequence, checking if subsequences match the
        # specified `ante`. We operate inside a `while True` loop
        # because we don't allow overlapping matches, and as such the
        # `idx` might be update either with 1 (looking for the next
        # position) or with the match length.
        # While this logic could, once more, be perfomed with a
        # list comprehension, for easier conversion to Go it is better to
        # keep it as a dumb loop.
        idx = 0
        post_seq = []
        while True:
            sub_seq = ante_seq[idx : idx + len(rule.ante)]
            match = self.check_match(sub_seq, rule.ante)
            if match:
                post_seq += self._forward_translate(sub_seq, rule)
                idx += len(rule.ante)
            else:
                post_seq.append(ante_seq[idx])
                idx += 1

            if idx == len(ante_seq):
                break

        # add to cache
        # TODO: deal with Sequence
        self.cache_add("forward", cache_key, Sequence(post_seq))

        return Sequence(post_seq)

    def _backward_translate(self, sequence, rule):
        # Collect all information we have on what was matched,
        # in terms of back-references and classes/features,
        # from what we have in the reflex
        value = {}
        no_nulls = [token for token in rule.post if "empty" not in token]
        for post_entry, token in zip(no_nulls, sequence):
            if "backref" in post_entry:
                value[post_entry.backref - 1] = self.apply_modifier(
                    token, post_entry.modifier, inverse=True
                )

        # NOTE: `ante_seq` is here the modified one for reconstruction,
        #       not the one in the rule
        ante_seq = []
        for idx, ante_entry in enumerate(rule.ante):
            if isinstance(ante_entry, list):
                # build alternative string, for cases when deleted
                # TODO: modifiers etc
                alts = []
                for alt in ante_entry:
                    if "grapheme" in alt:
                        alts.append(alt.grapheme)
                    elif "sound_class" in alt:
                        alts.append(alt.sound_class)
                    else:
                        alts.append("#")
                alt_string = "|".join(alts)
                ante_seq.append(value.get(idx, alt_string))
            elif "grapheme" in ante_entry:
                ante_seq.append(ante_entry.grapheme)
            elif "sound_class" in ante_entry:
                ante_seq.append(value.get(idx, ante_entry.sound_class))

        # Depending on the type of rule that was applied, the `ante_seq` list
        # might at this point have elements expressing more than one
        # sound and expressing alternatives that need to be computed
        # with a product (e.g., `['#'], ['d'], ['i w', 'j u'], ['d'] ['#']`).
        # This correction is performed by the calling function, also allowing
        # to return a `Sequence` instead of a plain string (so that we also
        # deal with missing boundaries, etc.). We also return the unaltered,
        # original `sequence`, expressing cases where no changes were
        # applied.
        return [" ".join(sequence), " ".join(ante_seq)]

    def backward(self, post_seq, rule):
        """
        Apply backward transformation to a sequence given a rule.
        """

        # Transform `post_seq` in a Sequence, if necessary
        if not isinstance(post_seq, alteruphono.sequence.Sequence):
            post_seq = Sequence(post_seq)

        # Return the cached value, if it exists
        cache_key = (post_seq._sequence, rule.source)
        cache_val = self.cache_query("backward", cache_key)
        if cache_val:
            return cache_val

        # This method makes a copy of the original AST ante-tokens and applies
        # the modifiers from the post sequence; in a way, it "fakes" the
        # rule being applied, so that something like "d > @1[+voiceless]"
        # is transformed in the equivalent "t > @1".
        # TODO: remove copy, build new object
        def _add_modifier(entry1, entry2):
            if isinstance(entry1, list):
                return [_add_modifier(alt, entry2) for alt in entry1]

            # TODO: do we need a copy?
            return entry1.copy({"modifier":entry2.modifier})

        # Compute the `post_ast`, applying modifiers and skipping nulls
        post_ast = [token for token in rule.post if "empty" not in token]
        post_ast = [
            token
            if "backref" not in token
            else _add_modifier(rule.ante[token.backref - 1], token)
            for token in post_ast
        ]

        # Iterate over the sequence, checking if subsequences match the
        # specified `post`. As for the forward operation, we proceed
        # inside a `while True` loop
        # because we don't allow overlapping matches.
        idx = 0
        ante_seqs = []
        while True:
            sub_seq = post_seq[idx : idx + len(post_ast)]
            match = self.check_match(sub_seq, post_ast)

            if match:
                ante_seqs.append(self._backward_translate(sub_seq, rule))
                idx += len(post_ast)
            else:
                ante_seqs.append([post_seq[idx]])
                idx += 1

            if idx == len(post_seq):
                break

        # Computes the product of possibilities and convert everything to
        # a sequence (see comments in ._backward_translate)
        ante_seqs = [
            Sequence(" ".join(candidate))
            for candidate in itertools.product(*ante_seqs)
        ]

        # add to cache
        # TODO: tuples from the beginning, for cache?
        self.cache_add("forward", cache_key, ante_seqs)

        return ante_seqs
