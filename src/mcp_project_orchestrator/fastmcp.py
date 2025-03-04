class FastMCP:
    def __init__(self, name):
        self.name = name
        self.config = {}

    def tool(self, func=None):
        # Decorator that does nothing for now
        if func is None:
            return lambda f: f
        return func

    def run(self):
        print(f"FastMCP server '{self.name}' running with configuration: {self.config}")
        # For testing, keep the server running indefinitely or just exit.
        # Here we simply exit after printing.
        exit(0) 