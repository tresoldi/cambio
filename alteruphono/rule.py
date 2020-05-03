# TODO: perform text normalization

class Rule:
    def __init__(self, ante, post):
        self._ante = ante
        self._post = post

    # NOTE: using __getattr_ for future expansions
    def __getattr__(self, key):
        if key == "ante":
            return self._ante
        elif key == "post":
            return self._post

        raise ValueError(f"Unknown attribute `{key}`.")
