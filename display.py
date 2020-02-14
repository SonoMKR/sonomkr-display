#!/usr/bin/python3

from typing import Any, List
import argparse
import libconf
import zmq
import sys
import re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from multiprocessing import Process, Value, Array
from pprint import pprint


index_to_freq: List[str] = ["0.8Hz", "1Hz", "1.25Hz", "1.6Hz", "2Hz", "2.5Hz", "3.15Hz", "4Hz", "5Hz", "6.3Hz", "8Hz", "10Hz", "12.5Hz", "16Hz", "20Hz", "25Hz", "31.5Hz", "40Hz", "50Hz", "63Hz", "80Hz", "100Hz", "125Hz", "160Hz", "200Hz", "250Hz", "315Hz", "400Hz", "500Hz", "630Hz", "800Hz", "1kHz", "1.25kHz", "1.6kHz", "2kHz", "2.5kHz", "3.15kHz", "4kHz", "5kHz", "6.3kHz", "8kHz", "10Hz", "12.5kHz", "16kHz", "20kHz"]

parser = argparse.ArgumentParser(description="Display for the SonoMKR Project")
parser.add_argument("-c", "--conf", dest="conf", default="./display.conf", help="The location of the configuration file")
parser.add_argument("--display-conf", dest="display_conf", action="store_true", help="Set this flag to display current config and return")

args = parser.parse_args()

class Channel:

    zmq_address: str
    zmq_topic: str

    freqs: Array
    values: Array
    size: Value

    def __init__(self, config):

        self.freqs = Array('I', len(index_to_freq))
        self.values = Array('d', len(index_to_freq))
        self.size = Value('I', 0)

        if not config.zmqAddress:
            raise Exception("Channel config misses the 'zmqAddress' parameter")
        self.zmq_address = config.zmqAddress

        if not config.zmqTopic:
            raise Exception("Channel config misses the 'zmqTopic' parameter")
        self.zmq_topic = config.zmqTopic

            
try:
    with open(args.conf, 'r') as cf:
        conf = libconf.load(cf)
except OSError as err:
    sys.stderr.write(f"[ERROR] display config file {args.conf} open error : {err}\n")
    exit(1)

if (args.display_conf):
    print(libconf.dumps(conf))
    exit(0)

zmq_context = zmq.Context()

channels = []
for channel_cfg in conf.channels:
    if channel_cfg.active is False:
        break
    try:
        channel = Channel(channel_cfg)
    except Exception as err:
        sys.stderr.write(f"[ERROR] channel config error :\n{libconf.dumps(channel_cfg)}\nError message : {err}\n")
        break
    channels.append(channel)

# p = Process(target=man.start_listening)
# p.start()

# man.start_listening()

def listen(channel, zmq_context):
    zmq_socket = zmq_context.socket(zmq.SUB)
    zmq_socket.connect(channel.zmq_address)
    zmq_socket.subscribe(channel.zmq_topic)
    while True:
        msg = zmq_socket.recv_multipart()
        msg = msg[1]
        data_matches = re.finditer(r"(\d{1,2}):(-?\d{1,3}.\d{1,2});", msg.decode("utf-8"))
        i = 0
        for match in data_matches:
            channel.freqs[i] = int(match.group(1))
            channel.values[i] = float(match.group(2))
            i += 1
        channel.size.value = i

zmq_context = zmq.Context()
procs = []

for channel in channels:
    proc = Process(target=listen, args=(channel, zmq_context))
    proc.start()
    procs.append(proc)

fig, ax = plt.subplots()

print((index_to_freq))
print((list(range(len(index_to_freq)))))

# bars = ax.bar(index_to_freq, list(range(len(index_to_freq))))

def init():
    ax.set_xticks(list(range(len(index_to_freq))))
    ax.set_xticklabels(index_to_freq, [])
    ax.set_ylim(0, 100)
    # return bars

def update(frame):
    for channel in channels:
        size = int(channel.size.value)
        bar = ax.bar(list(range(size)), list(channel.values[:size]), color='blue')
        ax.set_xticks(list(range(size)))
        ax.set_xticklabels(index_to_freq[channel.freqs[0]:channel.freqs[0]+size], rotation=45)
        ax.set_ylim(0, 100)
    return bar

ani = animation.FuncAnimation(fig, update, init_func=None, blit=True, interval=100)

print('test1')
plt.show()
print('test2')

for proc in procs:
    proc.terminate()

exit(0)