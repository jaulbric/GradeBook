#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import csv
import re
import numpy as np
from collections import Counter
import cPickle as pickle

import Tools

m = Tools.metadata()

class RosterLoadError(Exception):
	"""Custom exception for loading rosters"""
	pass

class RosterSaveError(Exception):
	"""Custom exception for saving rosters"""
	pass

class Roster():
	def __init__(self, rfile=None, name="default", fieldnames=None, nameformat='onecolumn', idcolumn=None):
		"""Stores class roster with search and name matching methods.

		Parameters
		----------

		Returns
		-------

		"""
		self.name = name
		self.roster = None
		self.studentlist = None
		self.corrections = None
		self.newcorrections = None
		self.aliases = None
		self.ID = None
		self.fieldnames = None
		self.nameformat = None
		self.idcolumn = None
		self.SubstringOccurences = None

		if rfile is not None:
			filename, ext = os.path.splitext(rfile)

			if ext == '.pickle':
				self._loadPickle(rfile)

			elif ext == '.csv':
				self.loadCSV(rfile, nameformat=nameformat, idcolumn=idcolumn, *fieldnames)
			
			else: # Attempt to load the input file first as a .pickle. If that fails try loading it as a .csv.
				try:
					self._loadPickle(rfile)
				except pickle.UnpicklingError:
					self.loadCSV(rfile, nameformat=nameformat, idcolumn=idcolumn, *fieldnames)

	def search(self,matchfield,returnmax=10):
		"""Returns a list of students that match the input matchfield.

		Parameters
		----------
		matchfield : str
			String to match
		returnmax : int
			Maximum number of returned students (Default value = 10)

		Returns
		-------
		return_list : list
			A list of dictionaries
		
		"""
		return_list = []
		assert isinstance(matchfield,str)
		returnmax = int(returnmax)

		for student in self.studentlist:
			if (matchfield in student['Last Name']) or (matchfield in student['First Name']):
				return_list.append(student)
			elif (matchfield in student['First Name Alias']) or (matchfield in student['Last Name Alias']):
				return_list.append(student)
 
		for ID in self.ID.keys():
			if matchfield in str(ID):
				return_list.append(self.ID[ID])

		return return_list[:returnmax]

	def match(self,lastname,firstname,nmax=None,nmin=0,threshold=0.,chatter=0):
		"""Returns best match or matches for a student in the roster.

		The algorithm works by first checking for an exact match. If none exists it will check known aliases. If there is still no match it partitions the names into substrings and creates a profile for the input name based on these substrings. It then compares to the profiles of other names in the roster and returns the best match. It will also save the match to a list of name corrections. This list can be output with writecorrections().

		Parameters
		----------
		lastname : str
			Last name of student
		firstname : str
			First name of student
		nmax : int or None
			Size of maximum partition (Default value = None)
		nmin : int
			Size of minimum partition (Default value = 0)
		threshold : float
			Threshold to exceed in order to return name (Default = 0.)
		chatter : int
			Output Verbosity. 0 is no output, 2 is maximum output (Default = 0)

		Returns
		-------
		found_lastname : str
			Last name of the best match
		found_firstname : str
			First name of the best match

		"""
		match_lastname = []
		match_lastname_score = []
		match_firstname = []
		match_firstname_score = []

		# Try to get the student from the Roster
		try:
			student = self.roster[lastname][firstname]
			if chatter > 0:
				print "{0}, {1}".format(student["Last Name"], student["First Name"])
			return student["Last Name"], student["First Name"]
		except KeyError:
			#Partition the input names
			if nmax is None:
				nmax = len(lastname)
			sequences = []
			for idx in range(nmax,nmin,-1):
				s = r'(?=(\w{' + str(idx) + r'}))'
				sequences += re.findall(s,lastname)
				
			for lname in self.roster:
				match_lastname.append(lname)
				matchscore = 0.0
				for seq in sequences:
					if seq in lname:
						try:
							matchscore += 1./float(self.SubstringOccurences[seq])
						except AttributeError:
							self.genSubstringOccurences()
							matchscore += 1./float(self.SubstringOccurences[seq])

				match_lastname_score.append(matchscore)

			found_lastname = match_lastname[np.argmax(match_lastname_score)]

			for fname in self.roster[found_lastname]:
				match_firstname.append(fname)
				matchscore = 0.0
				for seq in sequences:
					if seq in fname:
						try:
							matchscore += 1./float(self.SubstringOccurences[seq])
						except AttributeError:
							self.genSubstringOccurences()
							matchscore += 1./float(self.SubstringOccurences[seq])
				
				match_firstname_score.append(matchscore)

			found_firstname = match_firstname[np.argmax(match_firstname_score)]

			self.newcorrections[lastname,firstname] = [found_lastname,found_firstname]

			if chatter > 0:
				print "{0}, {1}".format(found_lastname, found_firstname)
			
			return found_lastname, found_firstname

	def genSubstringOccurences(self):
		"""Generates a dictionary of substring occurences from roster names."""
		sequences = []
		for student in self.studentlist:
			name = student['Full Name']
			longestname = max(name.split(' '), key=len)
			for idx in range(1,len(longestname)+1):
				s = r'(?=(\w{' + str(idx) + r'}))'
				sequences += re.findall(s,name)

		self.SubstringOccurences = Counter(sequences)
		filename = os.path.join(m.tmp,"{0}_substring.txt".format(self.name))
		with open(filename,'wb') as f:
			sequencewriter = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
			for substring, instances in self.SubstringOccurences.iteritems():
				sequencewriter.writerow([substring, instances])

	def addAlias(self,lastname,firstname,lastnameAlias=None,firstnameAlias=None):
		"""Add a name to which a student will also be associated

		Parameters
		----------
		lastname : str
			Last name of student in roster
		firstname : str
			First name of student in roster
		lastnameAlias : str
			New last name to associate to student (Default value = None)
		firstnameAlias : str
			New first name to associate to student (Default value = None)

		Returns
		-------

		"""
		if (firstnameAlias is not None) and (lastnameAlias is None):
			self.roster[lastname][firstname]['First Name Alias'].append(firstnameAlias)
			self.aliases[lastname,firstnameAlias] = (lastname, firstname)
		elif (lastnameAlias is not None) and (firstnameAlias is None):
			self.roster[lastname][firstname]['Last Name Alias'].append(lastnameAlias)
			self.aliases[lastnameAlias,firstname] = (lastname,firstname)
		elif (firstnameAlias is not None) and (lastnameAlias is not None):
			self.roster[lastname][firstname]['First Name Alias'].append(firstnameAlias)
			self.roster[lastname][firstname]['Last Name Alias'].append(lastnameAlias)
			self.aliases[lastnameAlias,firstnameAlias] = (lastname,firstname)
		else:
			print 'No alias specified'

	def addAliases(self,AliasFile):
		"""Add aliases from file

		Parameters
		----------
		AliasFile : str
			Full path to file containing alias definitions

		Returns
		-------

		"""
		with open(AliasFile,'r') as f:
			aliasreader = csv.DictReader(f)
			for row in aliasreader:
				if (row['First Name Alias'] != '') and (row['Last Name Alias'] == ''):
					self.roster[row['Last Name']][row['First Name']]['First Name Alias'].append(row['First Name Alias'])
					self.aliases[row['Last Name'],row['First Name Alias']] = (row['Last Name'], row['First Name'])
				elif (row['Last Name Alias'] != '') and (row['First Name Alias'] == ''):
					self.roster[row['Last Name']][row['First Name']]['Last Name Alias'].append(row['Last Name Alias'])
					self.aliases[row['Last Name Alias'],row['First Name']] = (row['Last Name'], row['First Name'])
				elif (row['Last Name Alias'] != '') and (row['First Name Alias'] != ''):
					self.roster[row['Last Name']][row['First Name']]['First Name Alias'].append(row['First Name Alias'])
					self.roster[row['Last Name']][row['First Name']]['Last Name Alias'].append(row['Last Name Alias'])
					self.aliases[row['Last Name Alias'],row['First Name Alias']] = (row['Last Name'], row['First Name'])

	def writeCorrections(self,output='corrections.txt'):
		"""Write name corrections to file.

		Parameters
		----------
		output : str
			Name of output file (Default value = 'corrections.txt')

		Returns
		-------

		"""
		with open(output,'wb') as f:
			writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
			writer.writerow(['Incorrect Name','Correct Last Name','Correct First Name'])
			for incorrect in self.newcorrections:
				writer.writerow([' '.join([incorrect[1], incorrect[0]])] + self.newcorrections[incorrect])

	def loadCorrections(self,filename='corrections.txt'):
		"""Load name corrections from input file

		Parameters
		----------
		filename : str
			Name of input filename (Default value = 'corrections.txt')

		Returns
		-------

		"""
		print 'Loading corrections, make sure you have looked over this file before loading. Sometimes the correction algorithm makes mistakes.'
		with open(filename,'r') as f:
			reader = csv.DictReader(f)
			for row in reader:
				incorrect_name = row['Incorrect Name'].split(' ')
				self.corrections[' '.join(incorrect_name[1:]),incorrect_name[0]] = [row['Correct Last Name'], row['Correct First Name']]

	def findID(self,idnum,chatter=2):
		"""Locate a student in roster using ID number

		Parameters
		----------
		idnum : int
			The student's ID number
		chatter : int
			Output verbosity. 0 is no output, 2 is maximum output (Default value = 2)

		Returns
		-------
		student : dict or None
			 Student dictionary if found, else returns None

		"""
		try:
			lname, fname = self.ID[str(idnum)]
			if chatter > 0:
				print "{0}, {1}".format(lname, fname)
			return self.roster[lname][fname]
		except KeyError:
			if chatter > 0:
				print 'ID number does not exist'
			return None

	def findAlias(self,lastname,firstname,chatter=2):
		"""Find a student by their alias

		Parameters
		----------
		lastname : str
			Last name alias of student
		firstname : str
			First name alias of student
		chatter : int
			Output verbosity. 0 is no output, 2 is maximum output (Default value = 2)

		Returns
		-------
		student : dict or None
			Dictionary of student values if found, else None

		"""
		try:
			lname, fname = self.aliases[lastname,firstname]
			print fname + " " + lname
			return self.roster[lname][fname]
		except KeyError:
			if chatter >= 2:
				print 'Alias does not exist'
			return None

	def findCorrection(self,lastname,firstname,chatter=2):
		"""Find a name correct for a student

		Parameters
		----------
		lastname : str
			Last name of student
		firstname : str
			First name of student
		chatter : int
			Output verbosity. 0 is no output, 2 is maximum output (Default value = 2)

		Returns
		-------
		student : dict or None
			Dictionary of student values if found, else None

		"""
		try:
			lname, fname = self.corrections[lastname,firstname]
			print fname + " " + lname
			return self.roster[lname][fname]
		except KeyError:
			if chatter >= 2:
				print 'Correction does not exist'
			return None

	def _save(self, name):
		"""Saves the current roster to repository.

		Parameters
		----------
		name : str
			Name with which to give the roster in the repository

		Returns
		-------

		"""
		filepath = os.path.join(m.repository, "rosters", "{0}.pickle".format(name))

		if os.path.isfile(filepath):
			raise RosterSaveError
		else:
			with open(filepath, 'wb') as f:
				pickle.dump({'name':self.name, 'roster':self.roster, 'studentlist':self.studentlist, 'corrections':self.corrections, 'newcorrections':self.newcorrections, 'aliases':self.aliases, 'ID':self.ID, 'fieldnames':self.fieldnames, 'nameformat':self.nameformat, 'idcolumn':self.idcolumn, 'SubstringOccurences':self.SubstringOccurences},f)

	def loadCSV(self, filename, nameformat='onecolumn', idcolumn=2, *fieldnames):
		"""Load roster from a comma separated value (.csv) file

		Parameters
		----------
		filename : str
			Full path to .csv file
		nameformat : str
			Name format from input file. Options are 'onecolumn', 'firstlast', 'lastfirst'
		idcolumn : int
			ID column index (indexing starts at 0). Enables search by ID
		fieldnames : str or None
			Field names in csv file. If None fieldnames will be taken from input file

		Returns
		-------

		To Do
		-----
		Allow multiple students with same first and last name by changing names to aliases.

		"""
		self.roster = {}
		self.studentlist = []
		self.corrections = {}
		self.newcorrections = {}
		self.aliases = {}
		self.ID = {}
		self.nameformat = nameformat
		self.idcolumn = int(idcolumn)
		lastNames = []

		if len(fieldnames) == 0:
			fieldnames = None

		with open(filename, 'rb') as r:
			reader = csv.DictReader(r,fieldnames=fieldnames)
			self.fieldnames = reader.fieldnames
			print self.fieldnames
			for row in reader:
				student = {}
				if '    Points Possible' in row.values(): # This row is often in the csv exported from Canvas grades
					continue
				for field in self.fieldnames:
					student[field] = row[field]

				if nameformat == 'onecolumn':
					student["Full Name"] = student[self.fieldnames[0]]
					names = student["Full Name"].split(' ')
					firstName = names[0]
					lastName = names[-1]
				elif nameformat == 'firstlast':
					student["Full Name"] = ' '.join([student[self.fieldnames[0]] + student[self.fieldnames[1]]])
					names = [student[self.fieldnames[0]], student[self.fieldnames[1]]]
					firstName = student[names[0]]
					lastName = student[names[1]]
				elif nameformat == 'lastfirst':
					student["Full Name"] = ' '.join([student[self.fieldnames[1]] + student[self.fieldnames[0]]])
					names = [student[self.fieldnames[1]], student[self.fieldnames[0]]]
					firstName = student[names[1]]
					lastName = student[names[0]]
				else:
					raise ValueError("name format '{0}' is not valid.".format(nameformat))

				student['Last Name'] = lastName
				student['First Name'] = firstName

				if self.idcolumn is not None:
					self.ID[student[self.fieldnames[self.idcolumn]]] = lastName, firstName

				firstAlias = []
				lastAlias = []

				if len(names) > 2:
					for idx in range(1,len(names) - 1):
						lastAlias.append(' '.join(names[idx:]))

				for la in lastAlias:
					self.aliases[la,firstName] = lastName, firstName

				student['Last Name Alias'] = lastAlias
				student['First Name Alias'] = firstAlias

				self.studentlist.append(student)
		
				if lastName not in lastNames:
					lastNames.append(lastName)

		if len(self.studentlist) == 0:
			raise RosterLoadError("Could not load roster file. It is either empty or not a valid .csv file.")

		for lastName in lastNames:
			self.roster[lastName] = {}
			for student in self.studentlist:
				if student['Last Name'] == lastName:
					self.roster[lastName][student['First Name']] = student

	def _loadPickle(self, filename):
		"""Load roster from repository

		Parameters
		----------
		filename : str
			Name of roster in repository

		Returns
		-------

		"""
		if os.path.splitext(filename)[1] != ".pickle":
			filename = filename + ".pickle"

		with open(os.path.join(m.repository, "rosters", filename), "r") as r:
			load_dict = pickle.load(r)
		self.name = load_dict['name']
		self.roster = load_dict['roster']
		self.studentlist = load_dict['studentlist']
		self.corrections = load_dict['corrections']
		self.newcorrections = load_dict['newcorrections']
		self.aliases = load_dict['aliases']
		self.ID = load_dict['ID']
		self.fieldnames = load_dict['fieldnames']
		self.nameformat = load_dict['nameformat']
		self.idcolumn = load_dict['idcolumn']

	def add_student(self, student):
		"""Add a single student to the roster

		Parameters
		----------
		student : dict
			Dictionary containing student parameters.

		Returns
		-------

		"""
		new_student = {}
		for fieldname in self.fieldnames:
			try:
				new_student[fieldname] = student[fieldname]
			except KeyError:
				print "New student is missing {0}".format(fieldname)

		firstName = ''
		lastName = ''
		if self.nameformat == 'onecolumn':
			names = student[self.fieldnames[0]].split(' ')
			firstName = names[0]
			lastName = names[-1]
		elif self.nameformat == 'firstlast':
			names = [student[self.fieldnames[0]], student[self.fieldnames[1]]]
			firstName = student[names[0]]
			lastName = student[names[1]]
		elif self.nameformat == 'lastfirst':
			names = [student[self.fieldnames[1]], student[self.fieldnames[0]]]
			firstName = student[names[1]]
			lastName = student[names[0]]
		else:
			raise ValueError("name format '{0}' is not valid.".format(nameformat))

		new_student['Last Name'] = lastName
		new_student['First Name'] = firstName

		if self.idcolumn is not None:
			self.ID[student[self.fieldnames[idcolumn]]] = lastName, firstName

		firstAlias = []
		lastAlias = []

		if len(names) > 2:
			for idx in range(1,len(names) - 1):
				lastAlias.append(' '.join(names[idx:]))

		for la in lastAlias:
			self.aliases[la,firstName] = lastName, firstName

		new_student['Last Name Alias'] = lastAlias
		new_student['First Name Alias'] = firstAlias

		self.studentlist.append(student)
		
		if lastName in self.roster.keys():
			self.roster[lastName][firstName] = new_student
		else:
			self.roster[lastName] = {'First Name': new_student}

		return new_student

	def remove_student(self, lastname, firstname):
		"""Remove student from roster

		Parameters
		----------
		lastname : str
			Last name of student to remove
		firstname : str
			First name of student to remove

		Returns
		-------

		"""
		student = self.roster[lastname][firstname]

		self.studentlist.remove(student)
		self.roster[lastname].pop(student)
		if len(self.roster[lastname]):
			self.roster.pop[lastname]

def partition(names):
	"""

	Parameters
	----------
	names :
		

	Returns
	-------

	"""
	partitions = []
	if isinstance(names,str):
		names = [[names]]
	
	for name in names:
		for idx, n in enumerate(name):
			for i in range(1,len(n)):
				l = [n[i:],n[:i]] + [name[j] for j in range(len(name)) if j != idx]
				partitions.append(l)

	return partitions

def deeppartition(name,n=3):
	"""

	Parameters
	----------
	name :
		
	n :
		 (Default value = 3)

	Returns
	-------

	"""
	idx = 1
	partitions = []
	parts = [[name]]
	while n > idx:
		parts = partition(parts)
		partitions += parts
		idx += 1
	return partitions

if __name__ == '__main__':
	rfile = '/home/jaryd/Dropbox/Phys6C/2018Phys6CRoster.csv'

	roster = Roster(rfile)
	roster.genSubstringOccurences()
	matched_lname, matched_fname = roster.match('druz','febby')
	print matched_lname, matched_fname

	roster.addAlias('Cruz','Febby',lastnameAlias='DeLa Cruz')
	stu = roster.findAlias('DeLa Cruz','Febby')
	print stu['Last Name'], stu['First Name']

	roster.writeCorrections()

	roster.loadCorrections()
	stu = roster.findCorrection('Hurmt','Wendy')
	print stu['Last Name'], stu['First Name']
