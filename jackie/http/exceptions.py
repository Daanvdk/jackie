class Disconnect(Exception):

    def __init__(self, code=None):
        self.code = code
