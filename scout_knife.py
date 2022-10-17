import subprocess
import time
import sys
import os
from typing import Tuple
import requests  # Need to be pip installed
import signal


taxa = sys.argv[1]
max_size = 10           # Max cocurrent running children
sub_process = 1         # starting batch 
max_sub_process = 100   # To max batch (including)
children = []           # List of sub_process children
sleep_time = 60*30   # How often to check in on the children in seconds
webhook_url = None
completed = False


def send_message(message: str):
    global webhook_url
    print(message)
    if webhook_url is None:
        return
    # Send message a post request to the webhook_url with message as content
    json_data = None
    data = None
    if "discord" in webhook_url:
        json_data = {"content": message}
    elif "slack" in webhook_url:
        json_data = {"text": message}
    else:
        data = message
    headers = {
        "method": 'POST',
        "Content-Type": "application/json"
        }

    r = requests.post(webhook_url, headers=headers, json=json_data, data=data)
    print(r.status_code, r.reason)


def exit_now(sig, frame):
    send_message("I am exiting gracefully, however all batches will continue")
    sys.exit(0)


def exit_soon(sig, frame):
    global children
    global completed
    completed = True
    send_message(f"I am exiting gracefully, as soon as all batches finishes {children}")


signal.signal(signal.SIGINT, exit_now)
signal.signal(signal.SIGTERM, exit_now)
signal.signal(signal.SIGUSR1, exit_soon)

with open(".config", "r") as config_file:
    for config in config_file.readlines():
        conf, val = config.split("=")
        if conf == "webhook_url":
            webhook_url = val.strip()
        elif conf == "max_size":
            max_size = int(val)
        elif conf == "sub_process":
            sub_process = int(val)
        elif conf == "max_sub_process":
            max_sub_process = int(val)
        elif conf == "sleep_time":
            sleep_time = int(val)

start_nr = sub_process


def squeue() -> Tuple[str, str, str, str, str, str, str, str]:
    squeue = subprocess.Popen(["squeue"], stdout=subprocess.PIPE)
    squeue.wait()
    for line in squeue.stdout.readlines():
        jobid, partition, name, user, st, time, nodes, nodelist = line.decode("utf-8").split()
        yield jobid, partition, name, user, st, time, nodes, nodelist
    return


def start_child(taxa: str, i: int) -> int:

    with open(f"/home/piamer/{taxa}/ScoutKnifes/ScoutKnife_{i}/{i}.Submitter.pbs", "w") as f:
        sed = subprocess.Popen(["sed", "-e", f's/1\\.allseqs/{i}\\.allseqs/g', "-e",
                               f's/_1/_{i}/g', "-e" f's/Scorpiones/{taxa}/g', "/home/piamer/4Pia/MPITemplate.pbs"],
                               stdout=f)
        sed.wait()
        f.flush()
    # sbatch /home/piamer/$taxa/ScoutKnifes/ScoutKnife_$i/$i.Submitter.pbs
    sbatch = subprocess.Popen(["sbatch", f"/home/piamer/{taxa}/ScoutKnifes/ScoutKnife_{i}/{i}.Submitter.pbs"])
    sbatch.wait()
    # Wait for the log to update
    time.sleep(5)
    for jobid, partition, name, user, st, _, nodes, nodelist in squeue():
        new_job = -1
        if user == os.getlogin():
            print(taxa, "contains", name)
            if name in taxa:
                print(jobid, ">", new_job)
                if int(jobid) > new_job:
                    new_job = int(jobid)
                pass
            else:
                send_message(f"user: {user} is also running {name} along side of {taxa}, is this intended?")

    # child = subprocess.Popen(["python3", f"example_script.py", str(i)])
    return new_job


def start_subprocess(sub_process: int, children: list, taxa: str) -> bool:
    child_job = start_child(taxa, sub_process)
    if child_job == -1 or str(child_job) in children:
        return False
    
    children.append((str(child_job), sub_process))
    return True


send_message(f"I am PID: {os.getpid()}\nI am cleaning {taxa}")
# Calls the cleaning command
c = subprocess.Popen(["perl", "/home/piamer/4Pia/Step1_PartitionSedder.pl", taxa])
# c = subprocess.Popen(["python", "example_clear.py", taxa])
c.wait()

send_message(f"{taxa} is clean")

while True:
    alive_jobs = []
    children_cpy = children
    for jobid, partition, name, user, st, _, nodes, nodelist in squeue():
        alive_jobs.append(jobid)
    for child in children_cpy:
        if child[0] not in alive_jobs:
            send_message(f"{taxa} ScoutKnife nr {child[1]} finished")
            children.remove(child)

    while len(children) < max_size and not completed:
        if start_subprocess(sub_process, children, taxa):
            send_message(f"Started {taxa}({sub_process}) jobid: {children[-1][0]}")
        else:
            send_message(f"Failed to start {taxa}({sub_process})")
        sub_process += 1
        if sub_process > max_sub_process:
            completed = True
        time.sleep(3)
    if len(children) == 0:
        break

    time.sleep(sleep_time)


send_message(f"All from {start_nr} to {sub_process} {taxa} have been Knife Scouted :) ")
