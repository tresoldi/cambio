class Compiler:
    def __init__(self, debug=False):
        self.debug = debug

    def compile(self, ast):
        if self.debug:
            print("---------", ast)

        if ast.get("ipa"):
            ret = self.compile_ipa(ast)
        elif ast.get("sound_class"):
            ret = self.compile_sound_class(ast)
        elif ast.get("boundary"):
            ret = self.compile_boundary(ast)
        elif ast.get("empty"):
            ret = self.compile_empty(ast)
        elif ast.get("back_ref"):
            ret = self.compile_back_ref(ast)
        elif ast.get("feature_desc"):
            ret = self.compile_feature_desc(ast)
        elif ast.get("alternative"):
            ret = self.compile_alternative(ast)
        elif ast.get("sequence"):
            ret = self.compile_sequence(ast)
        elif ast.get("source") and ast.get("target"):
            ret = self.compile_start(ast)

        # Single return point for the entire function
        return ret

    def compile_ipa(self, ast):
        return NotImplemented

    def compile_sound_class(self, ast):
        return NotImplemented

    def compile_boundary(self, ast):
        return NotImplemented

    def compile_empty(self, ast):
        return NotImplemented

    def compile_back_ref(self, ast):
        return NotImplemented

    def compile_feature_desc(self, ast):
        return NotImplemented

    def compile_alternative(self, ast):
        return NotImplemented

    def compile_sequence(self, ast):
        return NotImplemented

    def compile_context(self, ast):
        """
        The method returns a tuple of two variables, the first for the
        context preceding the position and the second for the one
        following it.
        """

        return NotImplemented

    def compile_start(self, ast):
        return NotImplemented
