# TODO: have different/equivalent names, such as high (vowel) = open (value)?
# TODO: add support for positive/negative features, different, etc.
# TODO: add boundaries, syllables, backrefs
# TODO: study how to add maps
# TODO: study how to add multisegment sequences
# TODO: add modifier to soundclass (and others?)
# TODO: for each token, store the raw source that generated it (it is better
# for debugging and can help the compilers)
# TODO: allow to set a token as optional?


class Token:
    """
    Class defining a token in a sound sequence.

    A Token is defined as one or more bundles of features. Features are
    collections of features and values, with each feature (such as
    `roundedness`) allowing at each time one only value among a set
    (e.g., `rounded` and `unrounded`).
    """

    # TODO: note about methods for initializing graphemes, sound_classes,
    # etc.
    # TODO: rename to feature system?
    # TODO: note that `features` is a map value:feature
    def __init__(self, featsys, sound_classes, sounds):
        """
        Initializes a Token object.

        `featsys` should better be a dictionary shared by all Token objects,
        but it is stored locally for complex cases.
        """

        # TODO: have these as internal properties
        self.featsys = featsys
        self.sound_classes = sound_classes
        self.sounds = sounds

        self.descriptors = []

    def __str__(self):
        return str(self.descriptors)

    # TODO: this assumes a single alternative, i.e., cannot (currently, at
    # least) initialize somehting like ["consonant"]["vowel"]
    # TODO: decide what to do if different values of the same feature are
    # passed; currently this is just overriding
    def from_features(self, values):
        """
        Initializes from a list of features.
        """

        # Set the single `descriptor`
        self.descriptors = [{}]
        for value in values:
            feature = self.featsys[value]
            self.descriptors[0][feature] = value

    def from_soundclass(self, sound_class, modifier):
        # TODO: the descriptor should be split as a list when loading
        values = self.sound_classes[sound_class]["description"].split()
        self.from_features(values)

    def to_graphemes(self):
        """
        Return all the graphemes matching the internal descriptors.
        """

        # TODO: should check if it was initialized
        # TODO: change when there are positive descriptors, negative, etc.
        for descriptor in self.descriptors:
            matches = [
                grapheme
                for grapheme, features in self.sounds.items()
                if all(
                    [desc in features.values() for desc in descriptor.values()]
                )
            ]
            print(descriptor)
            print(matches)
