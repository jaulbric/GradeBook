#!/usr/bin/env python
import csv
import cPickle as pickle
import os
import sys
import datetime
import argparse
import Tkinter as tk
import tkFileDialog
import inspect

from pyfiglet import Figlet

import interface
import interactive
import Tools
import Course
import Roster

m =Tools.metadata()

def gui(args):
    """graphical user interface"""
    root = tk.Tk()
    root.withdraw()

    _ = interface.startup(root)
    root.mainloop()

def create(args,chatter=2):
    """Create a resource"""
    name = args.NAME
    if (name is None) and (args.mode == "ql"):
        inter = interactive.interface("create")
        name = inter.request("{0} name".format(args.TYPE))
        inter.close()
    elif name is None:
        raise IOError("Cannot create {0} without a name.".format(args.TYPE))

    args.NAME = name
    resources = get(args,chatter=0)
    resource_list = [resources] if not hasattr(resources,'__iter__') else resources
    if name in resource_list:
        print "{0}/{1} already exists. Try a different name or delete the other one.".format(args.TYPE, name)
        return None

    if args.TYPE == 'course':
        if args.mode == 'gui':
            print "not yet"
        else:
            new_course = Course.Course(name)
            new_course.save()
            print "created {0}/{1}".format(args.TYPE, name)
            return new_course
    
    elif args.TYPE == 'roster':
        if args.mode == 'gui':
            print "not yet"
        else:
            new_roster = Roster.Roster(name=name)
            new_roster.save(name)
            print "created {0}/{1}".format(args.TYPE, name)
            return new_roster
    
    else:
        print "not yet"

def delete(args,chatter=2):
    """Delete resource type"""
    if args.NAME is not None:
        file = os.path.join(m.repository,"{0}s".format(args.TYPE),"{0}.pickle".format(args.NAME))
        try:
            os.remove(file)
            print "deleted {0}/{1}".format(args.TYPE,args.NAME)
        except OSError:
            print "Resource {0}/{1} not found.".format(args.TYPE,args.NAME)
    elif args.mode == "ql":
        inter = interactive.interface("delete")
        name = inter.request("{0} name".format(args.TYPE))
        inter.close()
        file = os.path.join(m.repository,"{0}s".format(args.TYPE),"{0}.pickle".format(name))
        try:
            os.remove(file)
            print "deleted {0}/{1}".format(args.TYPE,name)
        except OSError:
            print "Resource {0}/{1} not found.".format(args.TYPE,name)
    elif args.mode == "gui":
        print "not yet"
    else:
        raise IOError("No resource supplied.")

def execute(args,chatter=2):
    """Executes a command on the input type"""
    name = args.NAME
    if (name is None) and (args.mode == "ql"):
        inter = interactive.interface("execute")
        name = inter.request("{0} name".format(args.TYPE))
    elif name is None:
        raise IOError("Cannot execute command on {0} without a name.".format(args.TYPE))
    
    if args.TYPE == "course":
        course = Course.Course(name)
        course.load()
        try:
            func = getattr(course, args.command[0])
            return_values = func(*args.command[1:])
            course.save()
        except AttributeError:
            if chatter > 0:
                print "{0} has no method {1}. Available options are: ".format(args.TYPE, args.command[0])
                print ' '.join([method[0] for method in inspect.getmembers(course, predicate=inspect.ismethod)][1:])
            return_values = None

    elif args.TYPE == "roster":
        roster = Roster.Roster(name)
        roster.loadPickle(name)
        try:
            func = getattr(roster, args.command[0])
            return_values = func(*args.command[1:])
            roster.save(name)
        except AttributeError:
            if chatter > 0:
                print "{0} has no method {1}. Available options are: ".format(args.TYPE, args.command[0])
                print ' '.join([method[0] for method in inspect.getmembers(roster, predicate=inspect.ismethod)][1:])
            return_values = None

    return return_values

def get(args,chatter=2):
    """Get resources of specified type"""
    d = ""
    if args.TYPE in ["courses", "assignments", "rosters"]:
        d = os.path.join(m.repository,args.TYPE)
        resources = os.listdir(d)
        if len(resources) == 0:
            if chatter > 0:
                print "No resources found."
                return None
        else:
            if chatter > 0:
                print "Name\t\t\tCreated"
            resources = [os.path.splitext(resource)[0] for resource in resources]
            for resource in resources:
                if chatter > 0:
                    print resource
            return resources
    elif args.NAME is not None:
        if os.path.isfile(os.path.join(m.repository,"{0}s".format(args.TYPE),"{0}.pickle".format(args.NAME))):
            if chatter > 0:
                print "Name\t\t\tCreated"
                print args.NAME
            return args.NAME
        else:
            if chatter > 0:
                print "No resources found."
            return None
    elif args.mode == "ql":
        inter = interactive.interface("get")
        name = inter.request("{0} name".format(args.TYPE))
        inter.close()
        if os.path.isfile(os.path.join(m.repository,"{0}s".format(args.TYPE),"{0}.pickle".format(name))):
            if chatter > 0:
                print "Name\t\t\tCreated"
                print name
            return name
        else:
            if chatter > 0:
                print "No resources found."
            return None
    else:
        raise IOError("No resource supplied.")

def describe(args,chatter=2):
    """Describe Gradebook Objects"""
    if args.mode == "ql":
        f = Figlet(font='slant')
        print f.renderText('GradeBook')

    print args