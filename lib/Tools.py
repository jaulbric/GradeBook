#!/usr/bin/env python

class metadata():
	def __init__(self):
		with open("metadata", "rb") as f:
			d = {}
			for line in f.readlines():
				k, v = line.split(":",1)
				d[k] = v.strip()
			self.version = d["version"]
			self.created = d["created"]
			self.basepath = d["basepath"]
			self.lib = d["lib"]
			self.repository = d["repository"]
			self.tmp = d["tmp"]

