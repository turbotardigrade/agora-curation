import signal, os, threading, sys
import json
import Queue
import curation

quit = False
jobs = Queue.Queue()

def handler(signum, frame):
    global quit
    quit = True

signal.signal(signal.SIGINT, handler)

def handle_job():
    global quit
    while not quit:
        job = jobs.get()
        if job["command"] == "quit":
            quit = True
            result = [("result", "ok"),
                      ("error", None),
                      ("id", job["id"])]
            break
        function = getattr(curation, job["command"])
        if function is not None:
            job_result = function(job["arguments"])
            result = [("result", job_result.result),
                      ("error", job_result.error),
                      ("id", job["id"])]
            print json.dumps(result)
        else:
            result = [("result", None),
                      ("error", "Command not found"),
                      ("id", job["id"])]

threading.Thread(target=handle_job).start()

while not quit:
    jobs.put(json.loads(raw_input())
