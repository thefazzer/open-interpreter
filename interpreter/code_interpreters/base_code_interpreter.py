from concurrent.futures import ThreadPoolExecutor


class BaseCodeInterpreter:
    """
    This is a base class for code interpreters. It provides basic functionality for running and terminating code execution.
    """

    def __init__(self, max_workers=5):
        """
        Initialize the BaseCodeInterpreter with a ThreadPoolExecutor.
        
        Args:
            max_workers (int): The maximum number of workers in the thread pool.
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def run(self, code):
        """
        Run the given code in a separate thread and return the result.
        
        Args:
            code (callable): The code to be executed.
            
        Returns:
            The result of the code execution.
            
        Raises:
            Exception: If an error occurs during code execution.
        """
        future = self.executor.submit(code)
        try:
            return future.result()
        except Exception as e:
            print(f"An error occurred during code execution: {e}")
            return None

    def terminate(self):
        """
        Terminate the code execution by shutting down the executor.
        
        This method will block until all running tasks are done and the executor is shut down.
        """
        self.executor.shutdown(wait=True)
