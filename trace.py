#! /usr/bin/python

import subprocess
import threading
import time
import sys
import re
import json
import os


class Statistics:
	def __init__(self):
		self.totalLocalBytes = 0
		self.totalRemoteBytes = 0
		self.totalBytes = 0
		self.totalLocalPackets = 0
		self.totalRemotePackets = 0
		self.totalPackets = 0
		self.totalLocalBps = 0
		self.totalRemoteBps = 0
		self.totalBps = 0
		self.totalLocalPps = 0
		self.totalRemotePps = 0
		self.totalPps = 0

class Stream:
	def __init__(self):
		self.uid = 0
		self.localAddress = ''
		self.remoteAddress = ''
		self.protocol = ''
		self.localPort = 0
		self.remotePort = 0
		self.localBytes = 0
		self.remoteBytes = 0
		self.totalBytes = 0
		self.localPackets = 0
		self.remotePackets = 0
		self.totalPackets = 0
		self.localBps = 0
		self.remoteBps = 0
		self.totalBps = 0
		self.localPps = 0
		self.remotePps = 0
		self.totalPps = 0
		self.filterData = ''

resp_regexp = re.compile(r'^([^:]+):([^ ]+) (.+)$')

jnettop = subprocess.Popen([ '/usr/sbin/jnettop', '--display', 'jnet' ],
	bufsize=-1,
	stdin=subprocess.PIPE, stdout=subprocess.PIPE)

(j_in, j_out) = (jnettop.stdin, jnettop.stdout)

j_in.write("HELLO 1\n");
j_in.flush(); print(j_out.readline())
j_in.write("INTERFACE \"eth0\"\n")
j_in.flush(); print(j_out.readline())
j_in.write("RUN\n")
j_in.flush(); print(j_out.readline())

def parse_statistics(stats, data):
	stats.totalLocalBytes = long(data[0])
	stats.totalRemoteBytes = long(data[1])
	stats.totalBytes = long(data[2])
	stats.totalLocalPackets = long(data[3])
	stats.totalRemotePackets = long(data[4])
	stats.totalPackets = long(data[5])
	stats.totalLocalBps = long(data[6])
	stats.totalRemoteBps = long(data[7])
	stats.totalBps = long(data[8])
	stats.totalLocalPps = long(data[9])
	stats.totalRemotePps = long(data[10])
	stats.totalPps = long(data[11])

def new_stream(data, streams):
	s = Stream()
	s.uid = long(data[0], 16)
	s.localAddress = data[1]
	s.remoteAddress = data[2]
	s.protocol = data[3]
	s.localPort = int(data[4])
	s.remotePort = int(data[5])
	streams[s.uid] = s

def parse_update_stream(data, streams):
	uid = long(data[0], 16)
	s = streams[uid]

	s.localBytes = long(data[1])
	s.remoteBytes = long(data[2])
	s.totalBytes = long(data[3])
	s.localPackets = long(data[4])
	s.remotePackets = long(data[5])
	s.totalPackets = long(data[6])
	s.localBps = long(data[7])
	s.remoteBps = long(data[8])
	s.totalBps = long(data[9])
	s.localPps = long(data[10])
	s.remotePps = long(data[11])
	s.totalPps = long(data[12])

	if len(data[13]) > 0:
		s.filterData = data[13]

def parse_delete_stream(data, streams):
	uid = long(data[0], 16)
	del streams[uid]

def parse_lookup(data, resolver):
	resolver[data[0]] = data[1]

def print_streams(streams, resolver):
	if len(streams) < 1:
		return

	keys = streams.keys()
	keys.sort()
	with open('streams.new', 'w') as w:
		for key in keys:
			stream = streams[key]
			w.write("%s:%d <-> %s:%d        %d %d %d\n" %
				(stream.localAddress,
				stream.localPort,
				stream.remoteAddress,
				stream.remotePort,
				stream.localBps,
				stream.remoteBps,
				stream.totalBps))
	
	os.rename('streams.new', 'streams.txt')
	os.chmod('streams.txt', 0644)

streams = dict()
resolver = dict()
stats = Statistics()


while (True):
	s = j_out.readline()
	if s == None and len(s) < 1:
		break
	
	match = resp_regexp.match(s)
	# print(match.group(1), match.group(2))

	cmd = match.group(1)
	status = match.group(2)
	st1 = status[0]
	data_str = match.group(3)
	data = data_str.split('\t')


	if st1 == 'S':
		# statistics
		parse_statistics(stats, data)
	elif st1 == 'N':
		# new connection
		new_stream(data, streams)
	elif st1 == 'U':
		# update on connection
		parse_update_stream(data, streams)
	elif st1 == 'D':
		parse_delete_stream(data, streams)
	elif st1 == 'L':
		# ip lookup info
		parse_lookup(data, resolver)
	elif st1 == 'E':
		pass
		# update
	
	# print(status + ' -> ' + str(data))
	# print(len(streams))
	print_streams(streams, resolver)


