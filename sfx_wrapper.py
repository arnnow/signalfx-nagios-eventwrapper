#!/usr/bin/env python
# This script is a dirty hack in order to migrate from nagios to signalfx
#
# It will work with telegraf/exec
# You can pass this script as the command
# exemple :
# ./sfx_wrapper.py --scriptname DNSMASQ --command "/usr/lib/nagios/plugins/check_dns -H www.google.fr -s localhost -w 1 -c 3"
#
# It create an event on signalfx which you can display on dashboards
# You can then have the script output on your dashboard

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

# We will need a temp file in order to verify if the event has already been sent.
# if we do not store this, event will be sent on each execution with a return code != 0
# temp folder
cachedir = '/tmp/sfx_wrapper/'
# Create it if it does not exist
if not os.path.exists(cachedir):
    os.mkdir(cachedir)
# cache file name construction
# we need one for each test, so we will use the args provided to create the name
cachefile = cachedir+args.eventtype+"_"+args.scriptname+".cache"

# if command exit with 0 -> to nothing, just exit
if command_output.returncode == 0:
    # we remove the local trace of event send if it exist
    # it will enable us to send an event again if the script fail
    if os.path.exists(cachefile):
        os.remove(cachefile)


# if command exit is not 0 push payload to signalfx print error and exit with command exitcode
if command_output.returncode != 0:

    # Payload for signalfx
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
    # if the cache file exist, event has already been sent
    # so we just write the check timestamp to the file and exit with the script error code
    if os.path.exists(cachefile):
        f = open(cachefile, "w")
        f.write(str(time.time()))
        f.close()
    # if the cache file does not exist, we need to send the event to signalfx
    else:
        # event sent to sfx : https://dev.splunk.com/observability/reference/api/ingest_data/latest#endpoint-send-custom-events
        sfx_event_request = requests.post(SFX_ENDPOINT, data = "["+json.dumps(sfx_payload)+"]", headers = sfx_headers)
        f = open(cachefile, "w")
        f.write(str(time.time()))
        f.close()

# just print the script output
print(stderr.decode("utf-8"))
print(stdout.decode("utf-8"))
# exit with command return code
sys.exit(command_output.returncode)
