
class NotImplementedEffect(Exception):
    def __init__(self, message="Current effect isn't implemented."):
        self.message = message
        super().__init__(self.message)

class InvalidValue(Exception):
    pass
