import itertools
from pathlib import Path

import alteruphono.parser
import alteruphono.utils
from alteruphono.sequence import Sequence

from copy import copy

# TODO: create class for sequence and for rule
class Model:
    def __init__(self, model_path=None):
        # Read the model from disk, defaulting to the one distributed
        # with the library.
        if not model_path:
            model_path = Path(__file__).parent.parent / "resources"
            model_path = model_path.as_posix()

        # TODO: fix paths after prototyping
        self.features = alteruphono.utils.read_sound_features(
            f"{model_path}/features_bipa.tsv"
        )
        self.sounds = alteruphono.utils.read_sounds(
            self.features, f"{model_path}/sounds.tsv"
        )
        self.sound_classes = alteruphono.utils.read_sound_classes(
            self.sounds, f"{model_path}/sound_classes.tsv"
        )

        # caches
        self.modifier_cache = {}
        self.desc2graph = {}

    # TODO: deal with custom features
    # TODO: have it as part of a class, erasing difference between forward
    #       and backward
    # TODO: reimplement cache
    def apply_modifier(self, grapheme, modifier, inverse=False):
        """
        Apply a modifier to a grapheme.
        """

        # In case of no modifier, the grapheme is obviously the same
        if not modifier:
            return grapheme

        # Check if the (grapheme, modifier) combination has already been computed
        cache_key = tuple([grapheme, modifier, inverse])
        if cache_key in self.modifier_cache:
            return self.modifier_cache[cache_key]

        # Parse the provided modifier
        features = alteruphono.parser.parse_features(modifier)

        # Invert features if requested
        # TODO: for the time being, just hard-coding them; should be
        #       implemented in the Sound object
        if inverse:
            hard_coded = {
                ("ɸ", "[+fricative]"): "p",
                ("t", "[+voiceless]"): "d",
                ("f", "[+voiceless]"): "v",
                ("ɶ", "[+rounded]"): "a",
                ("ĩ", "[+nasalized]"): "i",
                ("t", "[+alveolar]"): "k",
                ("c", "[+palatal]"): "k",
                ("g", "[+voiced]"): "k",
                ("k", "[+velar]"): "p",
                ("ɲ", "[+palatal]"): "n",
                ("d", "[+voiced]"): "t",
                ("b", "[+voiced]"): "p",
                ("b̪", "[+stop]"): "v",
                ("g", "[+stop]"): "ɣ",
                ("x", "[+voiceless]"): "ɣ",
                ("d̪", "[+stop]"): "ð",
                ("b", "[+stop]"): "β",
                ("t̠", "[+post-alveolar]"): "k",
                ("k", "[+voiceless]"): "g",
            }
            ret = hard_coded.get((grapheme, modifier), None)

            if not ret:
                raise ValueError(
                    "Missing hardcoded backwards modifier:",
                    (grapheme, modifier),
                )

            # cache
            self.modifier_cache[(grapheme, modifier, inverse)] = ret

            return ret

        # Obtain the phonological descriptors for the base sound
        # TODO: consider redoing the logic, as we don't need to extract values
        #       given that those are already properly organized in the data
        # TODO: build an ipa description no matter what...
        if grapheme not in self.sounds:
            return "%s%s" % (grapheme, modifier)
        descriptors = list(self.sounds[grapheme].values())

        # Remove requested features
        # TODO: write tests
        descriptors = [
            value for value in descriptors if value not in features.negative
        ]

        # Remove any descriptor from a feature type we are changing, and add
        # all positive descriptors
        for feature in features.positive:
            descriptors = [
                value
                for value in descriptors
                if self.features[value] != self.features[feature]
            ]
        descriptors += features.positive

        # Obtain the grapheme based on the description
        # TODO: decide if we should just memoize
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
                # TODO: better order?
                grapheme = "[%s]" % ",".join(descriptors)

        # cache
        self.modifier_cache[cache_key] = grapheme

        return grapheme

    def check_match(self, sequence, pattern):
        """
        Check if a sequence matches a given pattern.
        """

        # If there is a length mismatch, it does not match by definition
        if len(sequence) != len(pattern):
            return False

        for token, ref in zip(sequence, pattern):
            if ref.toktype == "ipa":
                ipa = self.apply_modifier(ref.ipa, ref.modifier)
                if token != ipa:
                    return False
            elif ref.toktype == "boundary":
                if token != "#":
                    return False
            elif ref.toktype == "sound_class":
                # Apply the modifier to all the items in the sound class,
                # so we can check if the `token` is actually there.
                modified = [
                    self.apply_modifier(grapheme, ref.modifier)
                    for grapheme in self.sound_classes[ref.sound_class][
                        "graphemes"
                    ]
                ]
                modified = sorted({gr for gr in modified if gr})

                if token not in modified:
                    return False
            elif ref.toktype == "alternative":
                # Check the sub-match for each alternative -- if one works, it
                # is ok
                # TODO: apply modifiers everywhere (not only in IPA)
                alts = [
                    alt
                    if alt.toktype != "ipa"
                    else alteruphono.parser.TokenIPA(alt.ipa, ref.modifier)
                    for alt in ref.alternative
                ]

                alt_matches = [
                    self.check_match([token], [alt])
                    for alt in alts  # ref["alternative"]
                ]

                if not any(alt_matches):
                    return False

        return True

    def forward_translate(self, sequence, rule):
        """
        Translate an intermediary `ante` to `post` sequence.
        """

        post_seq = []

        # TODO: rename `entry` to `token`? also below
        for entry in rule.post:
            # Note that this will, as intended, skip over `null`
            if entry.toktype == "ipa":
                post_seq.append(entry.ipa)
            elif entry.toktype == "backref":
                # Refer to `correspondence`, if specified
                # -1 as back-references as 1-based, and Python lists 0-based
                if entry.correspondence:
                    # get the alternative index in `ante`
                    # NOTE: `post_alts` has [1:-1] for the curly brackets
                    # TODO: this is only working with BIPA, should we allow others?
                    ante_alts = [
                        alt.ipa
                        for alt in rule.ante[entry.index - 1].alternative
                    ]
                    post_alts = (
                        rule.post[entry.index - 1]
                        .correspondence[1:-1]
                        .split(",")
                    )

                    idx = ante_alts.index(sequence[entry.index - 1])

                    post_seq.append(post_alts[idx])
                else:
                    token = sequence[entry.index - 1]
                    post_seq.append(self.apply_modifier(token, entry.modifier))

        return post_seq

    def forward(self, ante_seq, rule):
        # Transform `ante_seq` in a Sequence, if necessary
        if not isinstance(ante_seq, alteruphono.sequence.Sequence):
            ante_seq = Sequence(ante_seq)

        # Iterate over the sequence, checking if subsequences match the
        # specified `ante`. While this could, once more, be perfomed with a
        # list comprehension, for easier conversion to Go it is better to
        # keep it as a dumb loop.
        idx = 0
        post_seq = []
        while True:
            sub_seq = ante_seq[idx : idx + len(rule.ante)]
            match = self.check_match(sub_seq, rule.ante)
            if match:
                post_seq += self.forward_translate(sub_seq, rule)
                idx += len(rule.ante)
            else:
                post_seq.append(ante_seq[idx])
                idx += 1

            if idx == len(ante_seq):
                break

        return Sequence(post_seq)

    # TODO: comment as we return two options, because it might or not apply...
    def backward_translate(self, sequence, rule):
        # Collect all information we have on what was matched,
        # in terms of back-references and classes/features,
        # from what we have in the reflex
        # TODO: could we get a set of potential sources when
        # a modifier is applied (for example, different places of
        # articulation) and get the merge with with source rule
        # (such only labials?)

        value = {}
        no_nulls = [token for token in rule.post if token.toktype != "null"]
        for post_entry, token in zip(no_nulls, sequence):
            if post_entry.toktype == "backref":
                idx = post_entry.index
                value[idx - 1] = self.apply_modifier(
                    token, post_entry.modifier, inverse=True
                )

        # TODO: note that ante_seq is here the modified one
        ante_seq = []
        for idx, ante_entry in enumerate(rule.ante):
            if ante_entry.toktype == "ipa":
                ante_seq.append(ante_entry.ipa)
            elif ante_entry.toktype == "alternative":
                # build alternative string, for cases when deleted
                # TODO: modifiers etc
                alts = []
                for alt in ante_entry.alternative:
                    if alt.toktype == "ipa":
                        alts.append(alt.ipa)
                    elif alt.toktype == "sound_class":
                        alts.append(alt.sound_class)
                    else:
                        alts.append("#")
                alt_string = "|".join(alts)
                ante_seq.append(value.get(idx, alt_string))
            elif ante_entry.toktype == "sound_class":
                ante_seq.append(value.get(idx, ante_entry.sound_class))

        # NOTE: returning `sequence` for the unalterted ("did not apply")
        # option -- should it be added outisde this function? TODO
        return [" ".join(sequence), " ".join(ante_seq)]

    def backward(self, post_seq, rule):
        # Transform `post_seq` in a Sequence, if necessary
        if not isinstance(post_seq, alteruphono.sequence.Sequence):
            post_seq = Sequence(post_seq)

        # This method makes a copy of the original AST ante-tokens and applies
        # the modifiers from the post sequence; in a way, it "fakes" the
        # rule being applied, so that something like "d > @1[+voiceless]"
        # is transformed in the equivalent "t > @1".
        def _add_modifier(entry1, entry2):
            # TODO: do we need a copy?
            v = copy(entry1)
            v.modifier = entry2.modifier
            return v

        post_ast = [token for token in rule.post if token.toktype != "null"]
        post_ast = [
            token
            if token.toktype != "backref"
            else _add_modifier(rule.ante[token.index - 1], token)
            for token in post_ast
        ]

        idx = 0
        ante_seqs = []
        while True:
            sub_seq = post_seq[idx : idx + len(post_ast)]
            match = self.check_match(sub_seq, post_ast)
            #        print(idx, match, sub_seq, [str(t) for t in post_ast])

            if match:
                ante_seqs.append(self.backward_translate(sub_seq, rule))
                idx += len(post_ast)
            else:
                ante_seqs.append([post_seq[idx]])
                idx += 1

            if idx == len(post_seq):
                break

        ante_seqs = [
            Sequence(" ".join(candidate))
            for candidate in itertools.product(*ante_seqs)
        ]

        return ante_seqs
