## SignalFX Nagios wrapper

This script will push an event to signalFX based on the nagios-like script output

It will work with telegraf/exec
You can pass this script as the command
exemple :
```
./sfx_wrapper.py --scriptname DNSMASQ --command "/usr/lib/nagios/plugins/check_dns -H www.google.fr -s localhost -w 1 -c 3"
```
It create an event on signalfx which you can display on dashboards
You can then have the script output on your dashboard
