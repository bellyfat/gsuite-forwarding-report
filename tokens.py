#!/usr/bin/python
import config
import time
import simplejson
import threading
import Queue
import random
import sys
import csv
import os
import pprint
from socket import error

import subprocess
import smtplib

import apiclient.errors
import unigoogle

google_domain = config.GOOGLE_DOMAIN

cwd = os.path.dirname(os.path.realpath(__file__)) + '/'
tempfile = os.path.join(cwd,'temp_tokens')
tokens_filename = os.path.join(config.OUTPUT_DIR,'tokens_report.csv')

num_workers = config.NUM_WORKERS
job_q = Queue.Queue()
status_q = Queue.Queue()


def main():
    log("Starting report.")
    print "Retrieving list of all users...please wait."
    users = get_users()

    print "\nTotal Users: " + str(len(users))

    # Set up workers
    for i in range(num_workers - 1):
        clear_worker_log(i)
        worker = threading.Thread(target=get_tokens, args=(i, job_q, status_q))
        worker.setDaemon(True)
        worker.start()

    work_count = 0
    for u in users:
        work_count += 1
        job_q.put((str(work_count), u))
        # if work_count == 500: break # For debugging

    total_users = work_count
    start_time = time.time()
    last_status = start_time
    success = 0
    errors = 0
    retry_count = 0
    retries = dict()
    users_dict = dict()
    error_text = ''
    while work_count > 0:
        try:
            (user, data, tokens) = status_q.get()
        except Queue.Empty:
            break
        if data['result'] == "ok":
            # Update status every second
            if time.time() - last_status > 1:
                status = ''
                elapsed_time = time.time() - start_time
                gs = int((total_users - work_count) / elapsed_time)
                status += "(" + str(work_count) + "/" + str(total_users) + ") (" + str(retry_count) + \
                    " retries) (" + str(gs) + " g/s) (Active Threads: " + \
                    str(threading.activeCount()) + ")"
                print "\r " + status,

            users_dict[user]=dict()
            users_dict[user]['tokens']=tokens

            success += 1
        else:
            errors += 1
            print "***************************************"
            print str(data['thread']) + " - " + user + " had ERROR."
            error_text += str(data['thread']) + " - " + user + " had ERROR.\n"
            print "***************************************"
            users_dict[user] = None
        if retries.get(data['retries']) is None:
            retries[data['retries']] = 0
        retries[data['retries']] += 1
        retry_count += data['retries']
        work_count -= 1

    stop = time.time() + 5
    while job_q.unfinished_tasks and time.time()<stop:
        time.sleep(1)

    if job_q.unfinished_tasks:
	    write_errors(str(job_q.unfinished_tasks)+" unfinished tasks.")

    job_q.join()

    write_tokens_file(users_dict)

    #write_groups(users_dict)
    if errors > 0:
        write_errors(error_text)

    elapsed_time = time.time() - start_time
    print "\rFinished in " + str(int(elapsed_time)) + " seconds.                                   "
    sys.stdout.flush()
    print "Successfully retreived " + str(success) + " users."
    print "-----------------------------------------------"
    print "Errors: " + str(errors)
    for r in retries:
        if r == 0:
            continue
        print str(r) + " retries: " + str(retries[r])
        
    log("Finished report.")
    
def write_tokens_file(users_dict):

    if os.path.exists(config.OUTPUT_DIR) == False:
        os.mkdir(config.OUTPUT_DIR)

    with open(tokens_filename,'w') as f:
        for user in users_dict:
            if users_dict[user] is None:
                f.write(user+',Error\n')
                continue
            if len(users_dict[user]['tokens']) > 0:
                for token in users_dict[user]['tokens']:
                    f.write(user+','+token+"\n")
            elif len(users_dict[user]['tokens']) == 0:
                f.write(user+',None\n')


def write_errors(text):
    with open(cwd + 'get_tokens_errors.txt', 'a') as f:
        f.write(time.strftime("%c") + '\n-------------------------------\n')
        f.write(text)


def get_users():
    auth = unigoogle.Auth()
    auth.load_auth()

    users = list()
    service = auth.api_service('admin', 'directory_v1')

    nextPageToken = ''
    count = 0
    retries = 0
    while nextPageToken is not None:
        result = unigoogle.api_execute(service.users().list(customer='my_customer', domain=google_domain,
                                        pageToken=nextPageToken).execute)
        if result['data'] is None:
            log("Error retreiving list of users")
            sys.exit("Error retreiving list of users")
        count += len(result['data']['users'])
        print '\r' + str(count),
        sys.stdout.flush()
        for one in result['data']['users']:
            users.append(one['primaryEmail'])

        if result['data'].get('nextPageToken') is None:
            nextPageToken = None
        else:
            nextPageToken = result['data']['nextPageToken']

    return users

def get_tokens(worker_num, in_q, out_q):
    time.sleep(random.random())
    auth = unigoogle.Auth()
    auth.load_auth()

    service = auth.api_service('admin', 'directory_v1')

    while True:
        try:  # in one step, make sure queue is not empty and take cmd from queue
            (count, user_address) = in_q.get()
            worker_log(worker_num,"Checked out: "+user_address+"\n")
        except Queue.Empty:
            continue

        tokens = list()
        data = dict()
        data['result'] = 'ok'
        data['thread'] = worker_num
        
        timerstart = time.time()

        worker_log(worker_num,"Trying Google API for: "+user_address+"\n")
        
        result = unigoogle.api_execute(service.tokens().list(userKey=user_address).execute)

        data['retries'] = result['retries']

        worker_log(worker_num,"Finished Google API for: "+user_address+"\n")
        
        if result['data'] is None:
            data['result'] = 'error'
        elif result['data'].get('items') is not None:
            for one in result['data']['items']:
                tokens.append(one['clientId'])

        worker_log(worker_num,"Checking in: "+user_address+"\n")
        out_q.put((user_address, data, tokens))
        worker_log(worker_num,"Checked in: "+user_address+"\n")

        in_q.task_done()
        worker_log(worker_num,"Task Done: "+user_address+"\n\n")


def ignore_error(e):
    # Find errors that are safe to ignore and don't need to be retried
    error = simplejson.loads(e.content)
    reason = error['error']['errors'][0]['reason']
    message = error['error']['errors'][0]['message']
    if reason == 'failedPrecondition' and message == 'Mail service not enabled':
        return True
    if reason == 'failedPrecondition':
        return True
    return False

def log(text):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(os.path.join(cwd,"tokens_log.txt"),'a') as f:
        f.write(timestamp+" -- Tokens: "+text+"\n")

def worker_log(worker_num, text):
    if (config.DEBUG_WORKERS): # this is for debugging, everything seems to work OK now
        if os.path.exists(os.path.join(cwd,"debug")) == False:
            os.mkdir(os.path.join(cwd,"debug"))
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(os.path.join(cwd,"debug","token_worker_"+str(worker_num)+".log"),'a') as f:
            f.write(str(timestamp)+": "+text)

def clear_worker_log(num):
    if os.path.exists(os.path.join(cwd,"debug")) == False:
        return

	logfile = os.path.join(cwd,"debug","token_worker_"+str(num)+".log")
	if os.path.isfile(logfile):
		os.unlink(logfile)

main()
