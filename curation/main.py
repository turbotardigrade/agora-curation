import Queue
import signal
quit = False
jobs = Queue.Queue()
def handler(signum, frame):
    global quit
    quit = True
    jobs.put({"command":"quit", "error": "SIGINT received", "id": -1})
    raise EOFError

signal.signal(signal.SIGINT, handler)

import json
import curation
import threading, os, sys
os.chdir(os.path.dirname(sys.executable))

# log for debugging
# log = open("log.txt", "a+", buffering=1)

def handle_job():
    global log
    global quit
    while not quit:
        job = jobs.get()
        if job["command"] == "quit":
            if "error" in job:
                result = {
                            "result": "ok",
                            "error": job["error"],
                            "id": job["id"]
                        }
            else:
                result = {
                            "result": "ok",
                            "error": None,
                            "id": job["id"]
                        }
            print json.dumps(result, separators=(',', ': ')) + "\n"
            sys.stdout.flush()
        try:
            function = getattr(curation, job["command"])
            job_result = function(job["arguments"])
            result = {
                        "result": job_result["result"],
                        "error": job_result["error"],
                        "id": job["id"]
                     }
        except Exception as e:
            result = {
                        "result": None,
                        "error": e.message,
                        "id": job["id"]
                     }
        print json.dumps(result, separators=(',', ': ')) + "\n"
        sys.stdout.flush()

threading.Thread(target=handle_job).start()
def loop():
    while not quit:
        jobs.put(json.loads(raw_input()))

try:
    loop()
except Exception as e:
    jobs.put({"command":"quit", "error": "end of file received", "id": -1})
