# __all__ = ['DiceError', 'DiceSyntaxError']
class DiceError(Exception):
    """Generic dice exception."""

    def __init__(self, msg):
        super().__init__(msg)


class DiceSyntaxError(DiceError):
    def __init__(self, msg):
        super().__init__(msg)