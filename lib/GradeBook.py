#!/usr/bin/env python
import numpy as np
import csv
import cPickle as pickle
import os
import datetime
import errno
import argparse
import Tkinter as tk
import tkFileDialog

import Roster

version = 0.1
current_window = None

def replace_window(root):
    '''Destroy current window, create new window'''
    global current_window
    if current_window is not None:
        current_window.destroy()
    current_window = tk.Toplevel(root)

    # if the user kills the window via the window manager exit the application
    current_window.wm_protocol("WM_DELETE_WINDOW", root.destroy)

    return current_window

class StartUp_GUI:
    '''Initial frame when gradebook is opened'''
    def __init__(self, root, font="Helvetica", fontsize=12):
        self.root = root
        self.master = replace_window(root)
        # self.master.mainloop()
        # self.master = tk.Toplevel(root)
        # global current_window
        # current_window = self.master
        self.master.title("GradeBook")

        self.font = font
        self.fontsize = fontsize

        global version
        self.welcome_label = tk.Label(self.master, text="Welcome to GradeBook", font=(font,int(fontsize*1.25)))
        self.welcome_label.grid(row=0,column=1,padx=10)
        self.version_label = tk.Label(self.master, text="version {0}".format(version), font=(font,fontsize))
        self.version_label.grid(row=1,column=1)

        self.new_button = tk.Button(self.master, text="New", font=(font, fontsize), command=self.new, state=tk.ACTIVE, width=17)
        self.open_button = tk.Button(self.master, text="Open", font=(font, fontsize), command=self.open, state=tk.DISABLED, width=17)
        self.create_assignment_button = tk.Button(self.master, text="Create Assignment", font=(font, fontsize), command=self.create_assignment, state=tk.DISABLED, width=17)
        self.quit_button = tk.Button(self.master, text='Quit', font=(font, fontsize), command=self.quit, width=17)

        self.new_button.grid(row=1, column=0)
        self.open_button.grid(row=2, column=0)
        self.create_assignment_button.grid(row=3, column=0)
        self.quit_button.grid(row=4, column=0)
        
    def new(self):
        # coursename_gui = CourseName(self.root, font=self.font, fontsize=self.fontsize)
        coursename = Dialog(self.root, entry_type=str, label='Course Name', title='GradeBook', font="Helvetica", fontsize=12, entry_width=25)
        new_window = NewCourse(self.root, coursename.value)

    def open(self):
        print "To do"

    def create_assignment(self):
        print "To do"

    def quit(self):
        exit()    

class CourseName:
    def __init__(self, root, font="Helvetica", fontsize=12):
        self.root = root
        self.master = tk.Toplevel(root)
        self.master.title("GradeBook")
        self.master.bind("<Return>", self.enter)

        self.coursename_var = tk.StringVar()
        self.name_label = tk.Label(self.master, text="Course Name", font=("Helvetica", 12))
        self.name_entry = tk.Entry(self.master, textvariable=self.coursename_var, width=25)
        self.name_label.grid(row=0, column=0)
        self.name_entry.grid(row=0, column=1)
        self.name_entry.focus_set()

    def enter(self,event=None):
        self.coursename = self.coursename_var.get()
        self.master.destroy()
        newcourse_gui = NewCourse(self.root, self.coursename)

class Dialog(tk.Toplevel):
    def __init__(self, root, entry_type=str, label='Input', title='GradeBook', font="Helvetica", fontsize=12, entry_width=25):
        tk.Toplevel.__init__(self)
        self.title(title)
        self.bind("<Return>", self.enter)

        if entry_type is str:
            self.var = tk.StringVar()
        elif entry_type is int:
            self.var = tk.IntVar()
        elif entry_type is bool:
            self.var = tk.BooleanVar()
        elif entry_type is float:
            self.var = tk.DoubleVar()
        else:
            self.var = tk.StringVar()

        self.value = None

        self.label = tk.Label(self, text=label, font=(font,fontsize))
        self.entry = tk.Entry(self, textvariable=self.var, width=entry_width)

        self.label.grid(row=0, column=0)
        self.entry.grid(row=0, column=1)
        self.entry.focus_set()
        self.wait_window()

    def enter(self, event=None):
        self.value = self.var.get()
        self.destroy()

class NewCourse:
    def __init__(self, root, coursename, font="Helvetica", fontsize=12):
        self.root = root
        self.master = replace_window(root)
        self.master.title(coursename)

        self.save_button = tk.Button(self.master, text="Save", font=(font,fontsize), command=self.save)
        self.quit_button = tk.Button(self.master, text="Quit", font=(font,fontsize), command=self.quit)

        self.quit_button.grid(row=0, column=0)
        self.save_button.grid(row=0, column=1)

    def save(self):
        print "To Do"
        self.master.destroy()

    def quit(self):
        exit()

class Attendance_GUI:
    '''GUI window to load files.'''
    def __init__(self, master, old_name, old_roster, old_scores, old_output):
        self.old_name = old_name
        self.old_roster = old_roster
        self.old_scores = old_scores
        self.old_output = old_output

        self.master = master
        self.master.bind("<Return>",self.enter)
        self.master.title("GradeBook")
        self.roster_label = tk.Label(self.master, text="Roster File")
        self.roster_label.grid(row=1)
        self.scores_label = tk.Label(self.master, text="Input Scores")
        self.scores_label.grid(row=2)
        self.output_label = tk.Label(self.master, text="Output Filename")
        self.output_label.grid(row=3)
        self.class_label = tk.Label(self.master, text="Class Name (optional)")
        self.class_label.grid(row=0)

        self.roster_file = tk.StringVar()
        self.scores_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.save_roster = tk.IntVar()
        self.class_name = tk.StringVar()

        self.e1 = tk.Entry(self.master, width=40, textvariable=self.roster_file)
        self.e2 = tk.Entry(self.master, width=40, textvariable=self.scores_file)
        self.e3 = tk.Entry(self.master, width=40, textvariable=self.output_file)
        self.e4 = tk.Checkbutton(self.master, text="save roster as .pickle", variable=self.save_roster)
        self.e5 = tk.Entry(self.master, width=40, textvariable=self.class_name)

        self.e1.insert(0,old_roster)
        self.e2.insert(0,old_scores)
        self.e3.insert(0,old_output)
        self.e5.insert(0,old_name)

        self.e1.grid(row=1, column=1, sticky=tk.W, ipady=4)
        self.e2.grid(row=2, column=1, sticky=tk.W, ipady=4)
        self.e3.grid(row=3, column=1, sticky=tk.W, ipady=4)
        self.e4.grid(row=4, column=0, sticky=tk.W)
        self.e5.grid(row=0, column=1, sticky=tk.W, ipady=4)
    
        self.quit_button = tk.Button(self.master, text='Quit', command=self.quit)
        self.quit_button.grid(row=4, column=1, sticky=tk.E, ipadx=4, pady=4)
        self.enter_button = tk.Button(self.master, text='Enter', command=self.enter)
        self.enter_button.grid(row=4, column=2, ipadx=4, pady=4)

        self.roster_browse_button = tk.Button(self.master, text='Browse', command=self.browse_for_roster)
        self.roster_browse_button.grid(row=1, column=2, sticky=tk.W)
        self.scores_browse_button = tk.Button(self.master, text='Browse', command=self.browse_for_scores)
        self.scores_browse_button.grid(row=2, column=2, sticky=tk.W)

    def enter(self,event=None):
        self.roster = self.roster_file.get()
        self.scores = self.scores_file.get()
        self.output = self.output_file.get()
        self.save = self.save_roster.get()
        self.classname = self.class_name.get()
        self.master.quit()

    def quit(self):
        exit()

    def browse_for_roster(self):
        if os.path.isabs(self.old_roster):
            initialdir = os.path.dirname(self.old_roster)
        else:
            initialdir = os.path.expanduser("~")
        roster_file = tkFileDialog.askopenfilename(initialdir=initialdir,title="Select File")
        self.e1.delete(0,'end')
        self.e1.insert(0,roster_file)

    def browse_for_scores(self):
        if os.path.isabs(self.old_scores):
            initialdir = os.path.dirname(self.old_scores)
        else:
            initialdir = os.path.expanduser("~")
        scores_file = tkFileDialog.askopenfilename(initialdir=initialdir,title="Select File")
        self.e2.delete(0,'end')
        self.e2.insert(0,scores_file)

def cli():
    helpString = "Gradebook"
    parser=argparse.ArgumentParser(description=helpString)

    cwd = os.getcwd()

    parser.add_argument("-m", "--mode", type=str, default="gui", choices=["gui", "inline", "interactive"], help="Run mode. (gui) opens a graphical user interface. (inline) runs the program in command line execution mode. (interactive) the program will prompt the user for input. Default: gui")

    args = parser.parse_args()

    if args.mode == 'gui':
        # open gui
        root = tk.Tk()
        root.withdraw()

        gui = StartUp_GUI(root)
        root.mainloop()
    elif args.mode == 'inline':
        # run the program inline
        print "To do"
    elif args.mode == 'interactive':
        # run the program in interactive mode
        print "To do"
    else:
        print "{0} is an invalid mode.".format(args.m)
        exit()

if __name__ == '__main__': cli()
    