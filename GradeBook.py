#!/usr/bin/env python
import csv
import cPickle as pickle
import os
import sys
import datetime
import argparse
import Tkinter as tk
import tkFileDialog

sys.path.append("/home/jaryd/GitHub/GradeBook/lib")
import core

import inspect

import Course
import Roster
import Tools

m = Tools.metadata()

def cli(description_string):
	# function_map = {"create":create, "open":load, "get":get, "describe":describe}

	helpString = "Welcome to GradeBook."
	# parser = argparse.ArgumentParser(prog="GradeBook", description=description_string, usage="%(prog)s [command] [TYPE] [NAME] [flags]")
	parser = argparse.ArgumentParser(prog="GradeBook", description=description_string)
	parser.add_argument("-m", "--mode", type=str, choices=["gui", "ql", "h"], default="ql", help="Run mode for GradeBook. 'gui': Graphical user interface. 'ql': (default) Command line interactive mode. User is asked for inputs. 'h': Batch mode. No inputs are requested.")
	parser.add_argument("-f", "--file", help="Use configuration file.")
	parser.add_argument("--version", action="version", version="%(prog)s {0}".format(m.version))

	subparsers = parser.add_subparsers(help="Available commands")

	# Help strings for subparser commands
	create_helpString = "Create help string"
	delete_helpString = "Delete help string"
	exec_helpString = "Exec help string"
	get_helpString = "Get help string"
	describe_helpString = "Describe help string"

	# Create subparsers for commands
	create_parser = subparsers.add_parser("create", help=create_helpString)
	delete_parser = subparsers.add_parser("delete", help=delete_helpString)
	exec_parser = subparsers.add_parser("exec", help=exec_helpString)
	get_parser = subparsers.add_parser("get", help=get_helpString)
	describe_parser = subparsers.add_parser("describe", help=describe_helpString)

	# Add arguments for each command and tell each parser which function to execute
	#-- create --#
	create_parser.add_argument("TYPE", choices=["course", "assignment", "roster"], help="Type of resource to create.")
	create_parser.add_argument("NAME", nargs="?", help="Name of created resource.")
	create_parser.set_defaults(func=core.create)

	#-- delete --#
	delete_parser.add_argument("TYPE", choices=["course","assignment", "roster"], help="Type of resource to delete.")
	delete_parser.add_argument("NAME", nargs="?", help="Name of resource to delete.")
	delete_parser.set_defaults(func=core.delete)

	#-- exec --#
	type_choices = ["course", "assignment", "roster"]
	exec_parser.add_argument("TYPE", choices=type_choices, help="Type of resouce on which to execute command")
	exec_parser.add_argument("NAME", nargs="?", help="Name of rource on which to excute command")
	exec_parser.set_defaults(func=core.execute)
	# Add methods from types
	exec_subparsers = exec_parser.add_subparsers(help="Commands", dest="command")
	#-- course --#
	course_methods = inspect.getmembers(Course.Course, predicate=inspect.ismethod)
	for method in course_methods:
		if method[0][0] == "_":
			continue
		method_help, args_dict = Tools.docstring_reader(method[1])
		exec_command_parser = exec_subparsers.add_parser(method[0], help=method_help)
		method_args, varargs, keywords, defaults = inspect.getargspec(method[1])
		method_args.remove('self')
		try:
			default_idx = len(method_args) - len(defaults)
		except TypeError:
			default_idx = len(method_args)
		for idx in range(len(method_args)):
			parser_dict = {}
			arg_name = method_args[idx]
			arg_help = args_dict[arg_name]["help"]
			arg_type = args_dict[arg_name]["type"]
			arg_default = defaults[idx - default_idx] if (idx >= default_idx) else 'No default'
			
			parser_dict["help"] = arg_help
			if arg_type is not None:
				parser_dict["type"] = arg_type
			if arg_default != 'No default':
				parser_dict["default"] = arg_default
				arg_name = "--{0}".format(arg_name)

			exec_command_parser.add_argument(arg_name, **parser_dict)
			
		if varargs is not None:
			parser_dict = {}
			parser_dict["help"] = args_dict[varargs]["help"]
			arg_type = args_dict[varargs]["type"]
			parser_dict["nargs"] = "*"

			if arg_type is not None:
				parser_dict["type"] = arg_type
			
			exec_command_parser.add_argument(varargs, **parser_dict)

	#-- roster --#
	roster_methods = inspect.getmembers(Roster.Roster, predicate=inspect.ismethod)
	for method in roster_methods:
		if method[0][0] == "_":
			continue
		method_help, args_dict = Tools.docstring_reader(method[1])
		exec_command_parser = exec_subparsers.add_parser(method[0], help=method_help)
		method_args, varargs, keywords, defaults = inspect.getargspec(method[1])
		method_args.remove('self')
		try:
			default_idx = len(method_args) - len(defaults)
		except TypeError:
			default_idx = len(method_args)
		for idx in range(len(method_args)):
			parser_dict = {}
			arg_name = method_args[idx]
			arg_help = args_dict[arg_name]["help"]
			arg_type = args_dict[arg_name]["type"]
			arg_default = defaults[idx - default_idx] if (idx >= default_idx) else 'No default'
			
			parser_dict["help"] = arg_help
			if arg_type is not None:
				parser_dict["type"] = arg_type
			if arg_default != 'No default':
				parser_dict["default"] = arg_default
				arg_name = "--{0}".format(arg_name)

			exec_command_parser.add_argument(arg_name, **parser_dict)

		if varargs is not None:
			parser_dict = {}
			parser_dict["help"] = args_dict[varargs]["help"]
			arg_type = args_dict[varargs]["type"]
			parser_dict["nargs"] = "*"

			if arg_type is not None:
				parser_dict["type"] = arg_type
			
			exec_command_parser.add_argument(varargs, **parser_dict)

	#-- get --#
	get_parser.add_argument("TYPE", choices=["course", "courses", "assignment", "assignments", "roster", "rosters"], help="Type of resource to list.")
	get_parser.add_argument("NAME", nargs="?", help="Name of resource to get.")
	get_parser.set_defaults(func=core.get)

	#-- describe --#
	describe_parser.add_argument("TYPE", choices=["course", "courses", "assignment", "assignments", "roster", "rosters"], help="Type of resource to describe.")
	describe_parser.add_argument("NAME", nargs="?", help="Name of resource to describe.")
	describe_parser.set_defaults(func=core.describe)

	args = parser.parse_args()
	args.func(args)

if __name__ == "__main__":
	description_string = "GradeBook is a tool used for organization and recording of teaching courses"
	if len(sys.argv) == 1:
		parser = argparse.ArgumentParser(prog="GradeBook", description=description_string)
		parser.add_argument("-m", "--mode", choices=["gui", "ql", "h"], default="gui", help="Run mode for GradeBook. 'gui': (default) Graphical user interface. 'ql': Command line interactive mode. User is asked for inputs. 'h': Batch mode. No inputs are requested.")
		parser.set_defaults(func=core.gui)
		args = parser.parse_args()
		args.func(args)
	else:
		cli(description_string)
