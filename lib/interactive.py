#!/usr/bin/env python
from pyfiglet import Figlet

import Tools

m = Tools.metadata()

class interface:
	"""Command line interface for GradeBook"""
	def __init__(self, caller, message="Welcome to GradeBook", questions=None):
		self.caller = caller
		self.questions = questions
		self.inputs = {}
		self.state = {}

		f = Figlet(font='slant')
		print f.renderText('GradeBook')
		print message

		try:
			with open("{0}/{1}_state.dat".format(m.tmp, self.caller), "r") as f:
				for line in f.readlines():
					q, a = line.split(":")
					self.state[q] = a.strip()
		except IOError:
			pass

	def request(self, question):
		saved = ''
		try:
			saved = self.state[question]
		except KeyError:
			pass

		inpt = raw_input(question + " [{0}]: ".format(saved))

		if inpt != '':
			self.inputs[question] = inpt
			return inpt
		elif (inpt == '') and (saved != ''):
			self.inputs[question] = saved
			return saved
		else:
			raise IOError("No response for {0}".format(question))

	def close(self):
		with open("{0}/{1}_state.dat".format(m.tmp,self.caller), "wb") as f:
			for q, a in self.inputs.items():
				f.write("{0}:{1}\n".format(q,a))
