#!/usr/bin/env python

class metadata():
	"""Reads metadata from file and stores attributes.

	"""
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

def docstring_reader(obj):
	"""Parses docstrings to determine parameter types and names

	Parameters
	----------
	obj : object
		Instance of the object to read docstring

	Returns
	-------

	"""
	ds = obj.__doc__
	lines = [line.strip() for line in ds.split('\n')]
	summary = lines[0]
	try:
		args_begins = lines.index("Parameters")
		args_end = lines.index("Returns")
	except ValueError:
		return summary, None
	# args = []
	# args_type = []
	# args_description = []
	args = {}
	idx = args_begins + 2
	while idx < args_end - 1:
		arg, t = lines[idx].split(" : ")
		args[arg] = {}
		if len(t.split(" ")) == 1:
			args[arg]["type"] = eval(t)
		else:
			args[arg]["type"] = None
		args[arg]["help"] = lines[idx+1]
		idx += 2

	return summary, args

