import sys
import io


class Logger:
    def __init__(self):
        self.terminal = sys.stdout
        self.log = io.StringIO()

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

    def attach(self):
        sys.stdout = self

    def get(self):
        return self.log.getvalue()
