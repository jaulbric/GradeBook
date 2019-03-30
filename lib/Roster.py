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
    pass

class Roster():
    def __init__(self, rfile=None, name="default", fieldnames=None, nameformat='onecolumn', idcolumn=None):
        """Stores class roster with search and name matching methods.
        Parameter       :   Description
        rfile           :   Full path to input roster file. Can be .csv or .pickle.
        headings        :   (Optional) headings of the roster csv. If None (default) the headings will be taken from the csv file.
        nameformat      :   (Optional) Column definitions for students names. Options are
                                'onecolumn': The student's full name is in the first column (default).
                                'firstlast': The student's first name is in the first column and their last name is in the second column.
                                'lastfirst': The student's last name is in the first column and their first name is in the second column.
        idcolumn        :   (Optional) Column number (starting at 0) that contains student ID. This column will become searchable if the value is not None (default).
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

        if rfile is not None:
            filename, ext = os.path.splitext(rfile)

            if ext == '.pickle':
                self.loadPickle(rfile)

            elif ext == '.csv':
                self.loadCSV(rfile, fieldnames, nameformat, idcolumn)
            
            else: # Attempt to load the input file first as a .pickle. If that fails try loading it as a .csv.
                try:
                    self.loadPickle(rfile)
                except pickle.UnpicklingError:
                    self.loadCSV(rfile, fieldnames, nameformat, idcolumn)

    def search(self,matchfield,returnmax=10):
        return_list = []

        assert isinstance(matchfield,str)

        for student in self.studentlist:
            if (matchfield in student['Last Name']) or (matchfield in student['First Name']):
                return_list.append(student)
            elif (matchfield in student['First Name Alias']) or (matchfield in student['Last Name Alias']):
                return_list.append(student)
 
        for ID in self.ID.keys():
            if matchfield in str(ID):
                return_list.self.ID[ID]

        return return_list[:returnmax]

    def match(self,lastname,firstname,nmax=None,nmin=0):
        """Returns best match or matches for a student in the roster.
        Parameter   :   Description
        firstname   :   First name of student
        lastname    :   Last name of student
        nmax        :   The size of the maximum partition
        nmin        :   The size of the minimum partition
        """
        match_lastname = []
        match_lastname_score = []
        match_firstname = []
        match_firstname_score = []

        # Try to get the student from the Roster
        try:
            return self.roster[lastname][firstname]
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

            print found_firstname + ' ' + found_lastname
            return found_lastname, found_firstname

    def genSubstringOccurences(self):
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
        with open(output,'wb') as f:
            writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['Incorrect Name','Correct Last Name','Correct First Name'])
            for incorrect in self.newcorrections:
                writer.writerow([' '.join([incorrect[1], incorrect[0]])] + self.newcorrections[incorrect])

    def loadCorrections(self,input='corrections.txt'):
        print 'Loading corrections, make sure you have looked over this file before loading. Sometimes the correction algorithm makes mistakes.'
        with open(input,'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                incorrect_name = row['Incorrect Name'].split(' ')
                self.corrections[' '.join(incorrect_name[1:]),incorrect_name[0]] = [row['Correct Last Name'], row['Correct First Name']]

    def findID(self,idnum,chatter=2):
        try:
            lname, fname = self.ID[str(idnum)]
            print fname + " " + lname
            return self.roster[lname][fname]
        except KeyError:
            if chatter >= 2:
                print 'ID number does not exist'
            return None

    def findAlias(self,lastname,firstname,chatter=2):
        try:
            lname, fname = self.aliases[lastname,firstname]
            print fname + " " + lname
            return self.roster[lname][fname]
        except KeyError:
            if chatter >= 2:
                print 'Alias does not exist'
            return None

    def findCorrection(self,lastname,firstname,chatter=2):
        try:
            lname, fname = self.corrections[lastname,firstname]
            print fname + " " + lname
            return self.roster[lname][fname]
        except KeyError:
            if chatter >= 2:
                print 'Correction does not exist'
            return None

    def save(self, filename):
        """Saves the current roster"""
        with open(os.path.join(m.repository, "rosters", "{0}.pickle".format(filename)), 'wb') as f:
            pickle.dump({'name':self.name, 'roster':self.roster, 'studentlist':self.studentlist, 'corrections':self.corrections, 'newcorrections':self.newcorrections, 'aliases':self.aliases, 'ID':self.ID, 'fieldnames':self.fieldnames, 'nameformat':self.nameformat, 'idcolumn':self.idcolumn},f)

    def loadCSV(self, filename, fieldnames, nameformat, idcolumn):
        self.roster = {}
        self.studentlist = []
        self.corrections = {}
        self.newcorrections = {}
        self.aliases = {}
        self.ID = {}
        self.nameformat = nameformat
        self.idcolumn = int(idcolumn)
        lastNames = []

        with open(filename, 'rb') as r:
            reader = csv.DictReader(r,fieldnames=fieldnames)
            self.fieldnames = reader.fieldnames
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

    def loadPickle(self, filename):
        with open(os.path.join(m.repository, "rosters", "{0}.pickle".format(filename)), "r") as r:
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
        student = self.roster[lastname][firstname]

        self.studentlist.remove(student)
        self.roster[lastname].pop(student)
        if len(self.roster[lastname]):
            self.roster.pop[lastname]

def partition(names):
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
