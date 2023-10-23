from concurrent.futures import ThreadPoolExecutor


class BaseCodeInterpreter:
    """
    .run is a generator that yields a dict with attributes: active_line, output
    """

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=5)

    def run(self, code):
        future = self.executor.submit(code)
        return future.result()

    def terminate(self):
        self.executor.shutdown(wait=True)
