#!/usr/bin/env python
import os
import cPickle as pickle
import csv
import Tools
import Roster

m = Tools.metadata()

class Course:
	"""container for course objects"""
	def __init__(self, name):
		self.name = name
		self.roster = None
		self.roster_file = None
		self.assignments = None
		self.grades = {}
		self.grades['Students'] = {}
		self.grades['Entries'] = []
		self.grades['Points Possible'] = []
		self.grades['Weights'] = []

	def _load(self, name=None):
		"""load course from repository.

		Parameters
		----------
		name : str
			 (Default value = None)

		Returns
		-------

		"""
		if name is None:
			name = self.name
		
		pfile = os.path.join(m.repository, "courses", "{0}.pickle".format(name))
		with open(pfile, "rb") as f:
			load_dict = pickle.load(f)
		self.roster_file = load_dict['roster_file']
		self.assignments = load_dict['assignments']
		self.grades = load_dict['grades']

		if self.roster_file is not None:
			self.roster = Roster.Roster(self.roster_file)

	def _save(self):
		"""Saves course to repository."""
		pfile = os.path.join(m.repository,"courses","{0}.pickle".format(self.name))
		with open(pfile, "wb") as f:
			pickle.dump({'roster_file':self.roster_file, 'assignments':self.assignments, 'grades':self.grades}, f)

	def import_roster(self, filename, fieldnames=None, nameformat='onecolumn', idcolumn=None):
		"""import a .csv or .pickle roster to a course.

		Parameters
		----------
		filename : str
			Full path to input roster file
		fieldnames : list
			Fieldnames for input roster (Default value = None)
		nameformat : str
			Format for input names (Default value = 'onecolumn')
		idcolumn : int
			Index of column containing ID numbers (Default value = None)

		Returns
		-------

		"""
		self.roster = Roster.Roster(filename, fieldnames=fieldnames, nameformat=nameformat, idcolumn=idcolumn, name=self.name)
		
		try:
			self.roster._save(self.name)
			self.roster_file = os.path.join(m.repository, "rosters", "{0}.pickle".format(self.name))
		except RosterSaveError:
			print "Could not save roster to repository because a roster by the same name already exists."
			self.roster_file = filename

		for student in self.roster.studentlist:
			self.grades['Students'][student['Last Name'], student['First Name']] = {'Scores':[], 'Total':0., 'Weighted Total':0., 'Percent':None, 'Weighted Percent':None}

	def add_roster(self, roster):
		"""Add an existing roster from the repository.

		Parameters
		----------
		roster : str
			Name of roster to add to the current course

		Returns
		-------

		"""
		rfile = os.path.join(m.repository, "rosters", "{0}.pickle".format(roster))
		if os.path.isfile(rfile):
			self.roster = Roster.Roster(rfile)
			self.roster_file = rfile
			for student in self.roster.studentlist:
				self.grades['Students'][student['Last Name'], student['First Name']] = {'Scores':[], 'Total':0., 'Weighted Total':0., 'Percent':None, 'Weighted Percent':None}
		else:
			print "roster/{0} does not exist.".format(roster)

	def import_grades(self, name, gfile, points_possible=None, matching=False, weight=1.0):
		"""import grades from file.

		Parameters
		----------
		name : str
			Name of the assignment which is being added
		gfile : str
			Full path to .csv file containing grades
		points_possible : float, int, or None
			Number of points possible (Default value = None)
		matching : bool
			Matches grades to students in roster if an exact match doesn't exist (Default value = False)
		weight : float
			Weight to apply to assignment (Default value = 1.0)

		Returns
		-------

		"""

		self.grades['Entries'].append(name)
		self.grades['Points Possible'].append(points_possible)
		self.grades['Weights'].append(weight)

		tmp_grades = {}
		with open(gfile, "r") as f:
			reader = csv.Reader(f)
			for row in reader:
				try:
					lastname = self.roster[row[0]][row[1]]['Last Name']
					firstname = self.roster[row[0]][row[1]]['First Name']
				except KeyError:
					if matching:
						lastname, firstname = self.roster.match(row[0], row[1])
						if (lastname, firstname) in tmp_grades.keys():
							continue
					else:
						continue

				tmp_grades[lastname, firstname] = float(row[2])

		for student in self.roster.studentlist:
			lastname = student['Last Name']
			firstname = student['First Name']
			score = 0
			try:
				score = tmp_grades[lastname, firstname]
			except KeyError:
				pass
			self.grades["Students"][lastname, firstname]["Scores"].append(score)
			self.grades["Students"][lastname, firstname][name] = score
			self.grades["Students"][lastname, firstname]["Total"] += score
	
	def add_student(self, student):
		"""Add a new student to the course.

		Parameters
		----------
		student : dict
			

		Returns
		-------

		"""
		new_student = self.roster.add_student(student)
		self.grades["Students"][new_student['Last Name'], new_student['First Name']] = {'Scores':[], 'Total':0., 'Weighted Total':0., 'Percent':None, 'Weighted Percent':None}
		for entry in self.grades["Entries"]:
			self.grades["Students"][new_student['Last Name'], new_student['First Name']]['Scores'].append(0.)
			self.grades["Students"][new_student['Last Name'], new_student['First Name']][entry] = 0.

	def remove_student(self, lastname, firstname):
		"""Remove a student from the course entirely

		Parameters
		----------
		lastname : str
			Last name of student to remove from course
		firstname : str
			First name of student to remove from course

		Returns
		-------

		"""
		self.roster.remove_student(lastname, firstname)
		self.grades["Students"].pop((lastname, firstname))

	def change_grade(self, lastname, firstname, entry, score):
		"""Change a single student's grade on one assignment.

		Parameters
		----------
		lastname : str
			Last name of student
		firstname : str
			First name of student
		entry : str
			Name of assignment
		score : float
			New score

		Returns
		-------

		"""
		old_score = self.grades["Students"][lastname, firstname][entry]
		self.grades["Students"][lastname, firstname][entry] = score
		self.grades["Students"][lastname, firstname]["Total"] += (score - old_score)

	def change_weight(self, entry, weight):
		"""Change the weight of an assignment.

		Parameters
		----------
		entry : str
			Name of assignment
		weight : float
			New weight for assignment

		Returns
		-------

		"""
		idx = self.grades["Entries"].index(entry)
		self.grades["Weights"][idx] = weight

	def change_points_possible(self, entry, points_possible):
		"""Change the points possible on an assignment.

		Parameters
		----------
		entry : str
			Name of assignment
		points_possible : float
			New points possible

		Returns
		-------

		"""
		idx = self.grades["Entries"].index(entry)
		self.grades["Points Possible"][idx] = points_possible

	def remove_entry(self, entry):
		"""Remove an assignment from the grades.

		Parameters
		----------
		entry : str
			Name of assignment

		Returns
		-------

		"""
		idx = self.grades["Entries"].index(entry)
		self.grades["Entries"].pop(idx)
		self.grades["Weights"].pop(idx)
		self.grades["Points Possible"].pop(idx)

		for student in self.roster.studentlist:
			lastName = student['Last Name']
			firstName = student['First Name']
			score = self.grades["Students"][lastName, firstName]["Scores"][idx]
			self.grades["Students"][lastName, firstName]["Scores"].pop(idx)
			self.grades["Students"][lastName, firstName]["Total"] -= score

	def calculate_grades(self):
		"""Calculate the final grades by summing over assignments and applying weights."""
		points_possible = np.sum(self.grades["Points Possible"])
		weighted_points_possible = np.sum(np.array(self.grades["Weights"])*np.array(self.grades["Points Possible"]))

		for k in self.grades["Students"].keys():
			weighted_total = 0.
			for idx in range(len(self.grades["Entries"])):
				weighted_total += self.grades["Weight"][idx]*self.grades["Students"][k]["Scores"][idx]
			self.grades["Students"][k]["Weighted Total"] = weighted_total
			self.grades["Students"][k]["Percent"] = 100.*self.grades["Students"][k]["Total"]/points_possible
			self.grades["Students"][k]["Weighted Percent"] = 100.*weighted_total/weighted_points_possible

	def add_entry(self, name, points_possible=0., weight=1.):
		"""Add an entry to the grades

		Parameters
		----------
		name : str
			Name of entry
		points_possible : float
			Points possible for this entry (Default = 0.0)
		weight : float
			weight for this entry (Default = 1.0)

		Returns
		-------

		"""
		self.grades['Entries'].append(name)
		self.grades['Points Possible'].append(points_possible)
		self.grades['Weights'].append(weight)

		for k in self.grades["Students"].keys():
			self.grades["Students"][k]["Scores"].append(0.)
			self.grades["Students"][k][name] = 0.

	def add_attendance(self, increment_by=1., *files):
		"""Add attendence grades from csv file assuming the file contains a single column of IDs

		Parameters
		----------
		increment_by : float
			Points to increment attendance scores (Default = 1.0)
		files : str
			Path to file(s) which contain attendance grades

		Returns
		-------

		"""
		if not "Attendance" in self.grades["Entries"]:
			self.add_entry("Attendance", points_possible=0., weight=1.)

		attendance_idx = self.grades["Entries"].index("Attendance")
		for f in files:
				self.grades["Points Possible"][attendance_idx] += increment_by
				with open(f, "rb") as csvfile:
					reader = csv.reader(csvfile)
					for row in reader:
						try:
							ID = int(row[0])
						except:
							continue
						student = self.roster.findID(ID,
							chatter=0)
						if student is not None:
							self.grades["Students"][student["Last Name"], student["First Name"]]["Attendance"] += increment_by
							self.grades["Students"][student["Last Name"], student["First Name"]]["Scores"][attendance_idx] += increment_by
							self.grades["Students"][student["Last Name"], student["First Name"]]["Total"] += increment_by
						else:
							print ID

	def export_grades(self, filename, export_format="canvascsv", *entries):
		"""Export grades to file

		Parameters
		----------
		filename : str
			Name of the file to write grades to
		export_format : str
			Output format for grades (Options: canvascsv) (Default = canvascsv)
		entries : str
			Entries to export. If none are entered all entries will be exported including totals

		Returns
		-------
		filename : str
			Name of file that grades were written to

		"""
		totals = False
		if len(entries) == 0:
			entries = self.grades["Entries"]
			totals = True

		if export_format == "canvascsv":
			fieldnames = ["Student"] + list(entries)
		else:
			raise TypeError("Unknown export format {0}".format(export_format))

		entries_indices = [self.grades["Entries"].index(entry) for entry in entries]

		second_row = {"Student":"\tPoints Possible"}
		for idx in entries_indices:
			second_row[self.grades["Entries"][idx]] = self.grades["Points Possible"][idx]

		if totals:
			fieldnames += ["Total", "Weighted Total", "Percent", "Weighted Percent"]
			total = 0
			weighted_total = 0
			for idx in entries_indices:
				total += self.grades["Points Possible"][idx]
				weighted_total += self.grades["Points Possible"][idx] * self.grades["Weights"][idx]
			second_row["Total"] = total
			second_row["Weighted Total"] = weighted_total
			second_row["Percent"] = 100.
			second_row["Weighted Percent"] = 100.

		with open(filename, "wb") as f:
			writer = csv.DictWriter(f, fieldnames)
			writer.writeheader()
			writer.writerow(second_row)
			for student in self.grades["Students"].keys():
				row = {}
				for fieldname in fieldnames:
					if fieldname == "Student":
						row["Student"] = self.roster.roster[student[0]][student[1]]["Full Name"]
					else:
						row[fieldname] = self.grades["Students"][student][fieldname]
				writer.writerow(row)