# Define global holders of phonetic/phonological data. Global variables
# might be considered a bad practice, but here they are justified
# by facilitating the logic, allowing to transparently cache the most
# expansive computations (which are needed and must be persistent for
# intensive simulations), and adopting a solution that can be easily
# recoded in a different programming language if/when needed.
FEATURES = None
SOUNDS = None
SOUND_CLASSES = None
DESC2GRAPH = None
APPLYMOD = None
