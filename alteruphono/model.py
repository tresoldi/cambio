"""
Defines the phonetic model class.

This class is the core of the system, taking care of forward and backward
operations. It requires a sound model from disk, defining properties such
as list of sounds, features, etc. By default, it will load the model
distributed with the package.
"""

# Import Python standard libraries
import csv
import itertools
from pathlib import Path

# Import package
import alteruphono
import alteruphono.utils
from alteruphono.sequence import Sequence


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


def read_sounds(filename):
    """
    Read sound definitions.
    """

    sounds = {}
    with open(filename) as csvfile:
        for row in csv.DictReader(csvfile, delimiter="\t"):
            grapheme = alteruphono.utils.clear_text(row["GRAPHEME"])
            features = row["NAME"].split()

            # NOTE: currently skipping over clusters and tones
            if "from" in features:
                continue
            if "tone" in features:
                continue

            sounds[grapheme] = tuple(sorted(features))

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


class Model:
    """
    Sound change model.
    """

    # Define our custom caches; we are not using Python's functools because
    # we need a finer management of the cache. Note that this only holds
    # forward and backward calls as a whole: other functions might
    # implement their own caches
    _cache = {
        "forward": {},
        "backward": {},
        "match": {},
        "modifier": {},
        "desc2graph": {},
    }
    _cache_stats = {
        "forward": [0, 0],  # hits, misses
        "backward": [0, 0],  # hits, misses
        "match": [0, 0],  # hits, misses
        "modifier": [0, 0],  # hits, misses
        "desc2graph": [0, 0],  # hits, misses
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
        self.sounds = read_sounds(sounds_file.as_posix())

        classes_file = model_path / "classes.tsv"
        self.sound_classes = read_sound_classes(
            self.sounds, classes_file.as_posix()
        )

    def _cache_query(self, collection, key):
        if key in self._cache[collection]:
            # Update individual and global hits
            self._cache_stats[collection][0] += 1
            self._cache[collection][key][0] += 1

            #            print("> CACHE", collection, key, self._cache[collection][key])

            return self._cache[collection][key][1]

        # update miss
        self._cache_stats[collection][1] += 1

        return None

    # TODO: clean cache when necessary
    def _cache_add(self, collection, key, value):
        #        print(sys.getsizeof(self._cache_fw), sys.getsizeof(self._cache_bw))
        #        print(alteruphono.utils.rec_getsizeof(self._cache_fw),
        #            alteruphono.utils.rec_getsizeof(self._cache_bw))

        self._cache[collection][key] = [0, value]

    def apply_modifier(self, grapheme, modifier, inverse=False):
        """
        Apply a modifier to a grapheme.
        """

        # In case of no modifier, the grapheme is obviously the same
        if not modifier:
            return grapheme

        # Check if the combination has already been computed and cached
        cache_key = (grapheme, str(modifier), inverse)
        cache_val = self._cache_query("modifier", cache_key)
        if cache_val:
            return cache_val

        # Invert features if requested
        # TODO: for the time being, just hard-coding them; should be
        #       implemented with some search (that can be *very* expansive...)
        if inverse:
            modifier_key = str(modifier)

            ret = alteruphono.utils.HARD_CODED_INVERSE_MODIFIER.get(
                (grapheme, modifier_key), None
            )

            if not ret:
                raise ValueError(
                    "Missing hardcoded backwards modifier:",
                    (grapheme, modifier_key),
                )

            # cache
            self._cache_add("modifier", cache_key, ret)

            return ret

        # Obtain the phonological descriptors for the base sound, returning
        # an alternative representation if not found
        # TODO: consider redoing the logic, as we don't need to extract values
        #       given that those are already properly organized in the data
        # TODO: build an ipa description no matter what...
        if grapheme not in self.sounds:
            ret = f"{grapheme}{modifier}"
        else:
            # Build list of descriptors, removing requested features (in
            # modifier.negative) and all descriptors from features we are
            # changing (for example, remove all vowel heights and only later
            # add the new one)
            descriptors = []
            rem_features = [self.features[desc] for desc in modifier.positive]
            for desc in self.sounds[grapheme]:
                if desc not in modifier.negative:
                    if self.features[desc] not in rem_features:
                        descriptors.append(desc)
            descriptors += modifier.positive

            # Obtain the grapheme based on the description
            ret = self.descriptors2grapheme(descriptors)

        # cache
        self._cache_add("modifier", cache_key, ret)

        return ret

    # TODO: hardcode exceptions
    # TODO: call to pyclts?
    def descriptors2grapheme(self, descriptors):
        """
        Translate a list of descriptors to a graphemic representation.
        """

        # Check if the combination has already been computed and cached
        cache_key = tuple(sorted(descriptors))
        cache_val = self._cache_query("desc2graph", cache_key)
        if cache_val:
            return cache_val

        # Run manual fixes related to pyclts
        if "palatal" in descriptors and "fricative" in descriptors:
            # Fricative palatals are described as alveolo-palatal in pyclts, so
            # replace all of them
            descriptors = [
                feature if feature != "palatal" else "alveolo-palatal"
                for feature in descriptors
            ]

        if "alveolo-palatal" in descriptors and "fricative" in descriptors:
            if "sibilant" not in descriptors:
                descriptors.append("sibilant")

        if "alveolar" in descriptors and "fricative" in descriptors:
            if "sibilant" not in descriptors:
                descriptors.append("sibilant")

        # TODO: do an inverse map, and then keep updating
        ret = None
        desc = tuple(sorted(descriptors))
        for sound, features in self.sounds.items():
            if desc == features:
                ret = sound

        # TODO: fixes in case we missed
        if "breathy" in desc:
            new_desc = [v for v in desc if v != "breathy"]
            new_gr = self.descriptors2grapheme(new_desc)
            if new_gr:
                ret = "%s[breathy]" % new_gr

        if "long" in desc:
            new_desc = [v for v in desc if v != "long"]
            new_gr = self.descriptors2grapheme(new_desc)
            if new_gr:
                ret = "%sː" % new_gr

        if not ret:
            ret = "[%s]" % ",".join(descriptors)

        # cache
        self._cache_add("desc2graph", cache_key, ret)

        return ret

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
            return [False] * len(sequence)

        # Build cache key
        cache_key = (
            " ".join(sequence),
            " ".join([str(token) for token in pattern]),
        )
        cache_val = self._cache_query("match", cache_key)
        if cache_val:
            return cache_val

        ret = True
        ret_list = []
        for token, ref in zip(sequence, pattern):
            ret = True
            # check choice (list) first
            if isinstance(ref, list):
                # Check the sub-match for each alternative; if the
                # alternative is a grapheme, carry any modifier
                alt_matches = [
                    all(self.check_match([token], [alt])) for alt in ref
                ]
                if not any(alt_matches):
                    ret = False
                    # break
            elif "set" in ref:
                # Check if it is a set correspondence, which effectively
                # works as a choice here (but we need to keep track of)
                # which set alternative was matched
                alt_matches = [
                    all(self.check_match([token], [alt])) for alt in ref.set
                ]

                # NOTE: as in this case we need to know which alternative in
                # set had a match, instead of returning a boolean we will
                # return the index of such alternative. To make the logic
                # more transparent, we shift the index of one unit, so
                # that no match will be returned as zero.
                # NOTE: this will return the index of the first matched
                # element, if there are more than one, following the PEG
                # principles
                # TODO: improve this logic
                if not any(alt_matches):
                    ret = False
                    # break
                else:
                    alt_matches = [False] + alt_matches
                    ret = alt_matches.index(True)
            elif "grapheme" in ref:
                ipa = self.apply_modifier(ref.grapheme, ref.modifier)
                if token != ipa:
                    ret = False
                    # break
            elif "boundary" in ref:
                if token != "#":
                    ret = False
                    # break
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
                    # break

            # Append to the return list, so we carry extra information like
            # element matched in a set (most of the time, this will be
            # just booleans)
            ret_list.append(ret)

        # cache
        self._cache_add("match", cache_key, tuple(ret_list))

        return ret_list

    def _forward_translate(self, sequence, rule, match_list):
        """
        Translate an intermediary `ante` to `post` sequence.
        """

        post_seq = []

        # Build a list of indexes from `match_list`, which will be used
        # in sequence in case of sets
        indexes = [v for v in match_list if v is not True]

        # iterate over all entries
        for entry in rule.post:
            # Note that this will, as intended, skip over `null`s
            if "grapheme" in entry:
                post_seq.append(entry.grapheme)
            elif "set" in entry:
                # NOTE: the -1 in the `match` index is to offset the one
                # applied in `.check_match()`, that returns zero for false
                # TODO: what if it is a backref, sound-class, etc.?
                idx = indexes.pop(0) - 1
                post_seq.append(entry["set"][idx]["grapheme"])
            elif "backref" in entry:
                # Refer to `correspondence`, if specified
                # TODO: recheck correspondence after adding sets
                if "correspondence" in entry:
                    # get the alternative index in `ante`
                    # NOTE: `post_alts` has [1:-1] for the curly brackets
                    ante_alts = [
                        alt.ipa for alt in rule.ante[entry.backref].alternative
                    ]
                    post_alts = (
                        rule.post[entry.backref].correspondence[1:-1].split(",")
                    )

                    idx = ante_alts.index(sequence[entry.backref])

                    post_seq.append(post_alts[idx])
                else:
                    token = sequence[entry.backref]
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
        cache_key = (ante_seq, rule)
        cache_val = self._cache_query("forward", cache_key)
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
            if all(match):
                post_seq += self._forward_translate(sub_seq, rule, match)
                idx += len(rule.ante)
            else:
                post_seq.append(ante_seq[idx])
                idx += 1

            if idx == len(ante_seq):
                break

        # add to cache
        post_seq = Sequence(post_seq)
        self._cache_add("forward", cache_key, post_seq)

        return post_seq

    def _backward_translate(self, sequence, rule, match_list):
        # Collect all information we have on what was matched,
        # in terms of back-references and classes/features,
        # from what we have in the reflex
        value = {}
        no_nulls = [token for token in rule.post if "empty" not in token]
        for post_entry, token in zip(no_nulls, sequence):
            if "backref" in post_entry:
                value[post_entry.backref] = self.apply_modifier(
                    token, post_entry.modifier, inverse=True
                )

        # NOTE: `ante_seq` is here the modified one for reconstruction,
        #       not the one in the rule
        ante_seq = []
        for idx, (ante_entry, match) in enumerate(zip(rule.ante, match_list)):
            if isinstance(ante_entry, list):
                # build alternative string, for cases when deleted
                # TODO: account for modifiers, choices, sets. etc
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
            elif "set" in ante_entry:
                # TODO: deal with non-graphemes
                ante_seq.append(ante_entry.set[match - 1]["grapheme"])

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
        cache_key = (post_seq, rule)
        cache_val = self._cache_query("backward", cache_key)
        if cache_val:
            return cache_val

        # This method makes a copy of the original AST ante-tokens and applies
        # the modifiers from the post sequence; in a way, it "fakes" the
        # rule being applied, so that something like "d > @1[+voiceless]"
        # is transformed in the equivalent "t > @1".
        def _add_modifier(entry1, entry2):
            if isinstance(entry1, list):
                return [_add_modifier(alt, entry2) for alt in entry1]

            return entry1.copy({"modifier": entry2.modifier})

        # Compute the `post_ast`, applying modifiers and skipping nulls
        post_ast = [token for token in rule.post if "empty" not in token]
        post_ast = [
            token
            if "backref" not in token
            else _add_modifier(rule.ante[token.backref], token)
            for token in post_ast
        ]

        # Iterate over the sequence, checking if subsequences match the
        # specified `post`. As for the forward operation, we proceed
        # inside a `while True` loop
        # because we don't allow overlapping matches.
        idx = 0
        ante_seqs = []
        while True:
            # TODO: this comprehension for `sub_seq` is testing subsequences
            # shorter than post_ast, should we fix it? check comprehension
            # at the end of loop (and check performed here)
            sub_seq = post_seq[idx : idx + len(post_ast)]
            match = self.check_match(sub_seq, post_ast)
            if len(match) == 0:
                break

            if all(match):
                ante_seqs.append(self._backward_translate(sub_seq, rule, match))
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
        self._cache_add("forward", cache_key, ante_seqs)

        return ante_seqs
