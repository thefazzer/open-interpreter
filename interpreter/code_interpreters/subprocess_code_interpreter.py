import subprocess
import threading
import queue
import time
import traceback
import logging

logger = logging.getLogger(__name__)
from .base_code_interpreter import BaseCodeInterpreter

class SubprocessCodeInterpreter(BaseCodeInterpreter):
    def __init__(self):
        super().__init__()
        self.start_cmd = ""
        self.process = None
        self.debug_mode = False
        self.output_queue = queue.Queue()
        self.done = threading.Event()

    def start_process(self):
        try:
            if self.process:
                self.terminate()

            logger.debug('Starting subprocess.')
            self.process = subprocess.Popen(self.start_cmd.split(),
                                            stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            text=True,
                                            bufsize=0,
                                            universal_newlines=True)
            threading.Thread(target=self.handle_stream_output,
                             args=(self.process.stdout, False),
                             daemon=True).start()
            threading.Thread(target=self.handle_stream_output,
                             args=(self.process.stderr, True),
                             daemon=True).start()
        except Exception as e:
            logger.error(f"Failed to start subprocess: {e}")

    def run(self, code):
        retry_count = 1
        max_retries = 3

        try:
            code = self.preprocess_code(code)
            if not self.process:
                logger.debug('No existing process. Starting a new one.')
                self.start_process()
        except Exception as e:
            logger.error(f"PreTestprocess or process start failed: {e}")
            yield {"output": traceback.format_exc()}
            return

        while retry_count <= max_retries:
            if self.debug_mode:
                print(f"Running code:\n{code}\n---")

            self.done.clear()

            try:
                self.process.stdin.write(code + "\n")
                self.process.stdin.flush()
                break
            except:
                if retry_count != 0:
                    # For UX, I like to hide this if it happens once. Obviously feels better to not see errors
                    # Most of the time it doesn't matter, but we should figure out why it happens frequently with:
                    # applescript
                    yield {"output": traceback.format_exc()}
                    yield {"output": f"Retrying... ({retry_count}/{max_retries})"}
                    yield {"output": "Restarting process."}

                self.start_process()

                retry_count += 1
                if retry_count > max_retries:
                    yield {"output": "Maximum retries reached. Could not execute code."}
                    return

        while True:
            if not self.output_queue.empty():
                yield self.output_queue.get()
            else:
                time.sleep(0.1)
            try:
                output = self.output_queue.get(timeout=0.3)  # Waits for 0.3 seconds
                yield output
            except queue.Empty:
                if self.done.is_set():
                    # Try to yank 3 more times from it... maybe there's something in there...
                    # (I don't know if this actually helps. Maybe we just need to yank 1 more time)
                    # for _ in range(3):
                    #    if not self.output_queue.empty():
                    #        yield self.output_queue.get()
                    #    time.sleep(0.2)
                    break

    def handle_stream_output(self, stream, is_error_stream):
        try:
            for line in iter(stream.readline, ''):
                logger.debug(f"Read line from {'stderr' if is_error_stream else 'stdout'}: {line.strip()}")
                if self.debug_mode:
                    print(f"Received output line:\n{line}\n---")

                line = self.line_postprocessor(line)

                if line is None:
                    continue # `line = None` is the postprocessor's signal to discard completely

                if self.detect_active_line(line):
                    active_line = self.detect_active_line(line)
                    self.output_queue.put({"active_line": active_line})
                elif self.detect_end_of_execution(line):
                    self.output_queue.put({"active_line": None})
                    time.sleep(0.1)
                    self.done.set()
                elif is_error_stream and "KeyboardInterrupt" in line:
                    self.output_queue.put({"output": "KeyboardInterrupt"})
                    time.sleep(0.1)
                    self.done.set()
                else:
                    self.output_queue.put({"output": line})
        except Exception as e:
                logger.error(f"Failed to handle stream output: {e}")

