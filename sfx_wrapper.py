#!/usr/bin/env python

import subprocess
from subprocess import Popen, PIPE
import sys
import requests
import argparse
import json
import time
import socket
import os

# Let's parse some input
parser = argparse.ArgumentParser(description='Magic Stuff')
parser.add_argument('--token',  help='sfx token to use in POST query', type=str)
parser.add_argument('--realm',  help='Realm to use for POST query', type=str)
parser.add_argument('--category',  help='Category for event payload', default='ALERT', type=str)
parser.add_argument('--eventtype',  help='eventType for event payload', default='NagiosScript', type=str)
parser.add_argument('--scriptname',  help='Name to push to the dimensions { script : scriptname }', default='NagiosLike', type=str)
parser.add_argument('--command',  help='Command to execute with BASH - typically the nagios script', default='', type=str)

args = parser.parse_args()

# We execute the command and get stdin & stderr
command_output = subprocess.Popen(args.command, shell = True, stdout=PIPE, stderr=PIPE)
stdout, stderr = command_output.communicate()

cachedir = '/tmp/sfx_wrapper/'
if not os.path.exists(cachedir):
    os.mkdir(cachedir)
cachefile = cachedir+args.eventtype+"_"+args.scriptname+".cache"

# if command exit with 0 -> to nothing, just exit
if command_output.returncode == 0:
    if os.path.exists(cachefile):
        os.remove(cachefile)

    print(stdout.decode("utf-8"))
    sys.exit(command_output.returncode)

# if command exit is not 0 push payload to signalfx print error and exit with command exitcode
if command_output.returncode != 0:

    SFX_ENDPOINT = "https://ingest."+args.realm+".signalfx.com/v2/event"
    sfx_payload = { 'category': '"'+args.category+'"',
            'eventType': args.eventtype,
            'dimensions': { 'script': args.scriptname,
                            'hostname': socket.gethostname(),
                            'returncode': str(command_output.returncode),
                            'stderr': stderr.decode("utf-8"),
                            'stdout': stdout.decode("utf-8"),
                          },
            'property' : { 'sources': 'nagioslike' },
            }
    sfx_headers = { 'Content-Type': 'application/json',
            'X-SF-Token': args.token,
            }
    if os.path.exists(cachefile):
        f = open(cachefile, "w")
        f.write(str(time.time()))
        f.close()
        print(stdout.decode("utf-8"))
        print(stderr.decode("utf-8"))
        sys.exit(command_output.returncode)
    else:
        sfx_event_request = requests.post(SFX_ENDPOINT, data = "["+json.dumps(sfx_payload)+"]", headers = sfx_headers)
        f = open(cachefile, "w")
        f.write(str(time.time()))
        f.close()
        print(stdout.decode("utf-8"))
        print(stderr.decode("utf-8"))
        sys.exit(command_output.returncode)

