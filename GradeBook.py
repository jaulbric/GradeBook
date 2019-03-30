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

def cli(description_string):
    # function_map = {"create":create, "open":load, "get":get, "describe":describe}

    helpString = "Welcome to GradeBook."
    parser = argparse.ArgumentParser(prog="GradeBook", description=description_string, usage="%(prog)s [command] [TYPE] [NAME] [flags]")
    parser.add_argument("-m", "--mode", choices=["gui", "ql", "h"], default="ql", help="Run mode for GradeBook. 'gui': Graphical user interface. 'ql': (default) Command line interactive mode. User is asked for inputs. 'h': Batch mode. No inputs are requested.")
    parser.add_argument("-f", "--file", help="Use configure file.")

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
    exec_parser.add_argument("TYPE", choices=["course", "assignment", "roster"], help="Type of resouce on which to execute command")
    exec_parser.add_argument("NAME", nargs="?", help="Name of rource on which to excute command")
    exec_parser.add_argument("command", nargs="*", help="command to pass to resource")
    exec_parser.set_defaults(func=core.execute)

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
