import sublime, sublime_plugin

import os
import re
import shlex
import subprocess

options = sublime.load_settings('ContextBuild.sublime-settings')

pythonPath = os.environ.get(options.get('pythonEnvironmentVariable', ''), '')

class Build(object):
    last = None

    def __init__(self, paths = [], tests = [], onlyLastFailures = False):
        self.paths = paths
        self.tests = tests
        self.noseFailureData = None
        if onlyLastFailures:
            with open(".noseids", "r") as f:
                self.noseFailureData = f.read()


    def run(self):
        cmd = "nosetests"
        if self.paths:
            print(self.paths)
            cmd += " " + " ".join([ p.encode('utf8') for p in self.paths ])
        elif self.noseFailureData is not None:
            with open(".noseids", "w") as f:
                f.write(self.noseFailureData)
            cmd += " --failed"
        elif self.tests:
            print(self.tests)
            cmd += " " + " ".join([ p.encode('utf8') for p in self.tests ])
        else:
            print("No tests to run.")
            return
            
        env = os.environ.copy()
        env['PYTHONPATH'] = pythonPath
        p = subprocess.Popen(shlex.split(cmd), stdout = subprocess.PIPE, 
                stderr = subprocess.STDOUT, env = env,
                universal_newlines = True)
        stdout, _ = p.communicate()
        print stdout
        print("Result: " + str(p.poll()))


class ContextBuildCurrentCommand(sublime_plugin.TextCommand):
    def run(self, editor):
        Build.last = Build(paths = [ self.view.file_name() ])
        Build.last.run()


    def is_enabled(self):
        return True


class ContextBuildSelectedCommand(sublime_plugin.WindowCommand):
    def run(self, paths = []):
        Build.last = Build(paths)
        Build.last.run()


    def is_enabled(self):
        return True


def findTestFromLine(view, testLine, actualStart, testsOut):
    indent = testLine.group(1)
    testName = testLine.group(2)
    # Find the class
    for sel in reversed(view.find_all("^([ \t]*)class (Test[^( ]*)", 
            re.M)):
        if sel.a > actualStart:
            continue
        text = view.substr(sel)
        print(repr(text))
        clsIndent = len(re.match("[ \t]*", text).group())
        print("Comparing " + str(clsIndent))
        if clsIndent < indent:
            # MATCH!
            testsOut.append(view.file_name() + ':' 
                    + text[clsIndent + len('class '):] + '.' 
                    + testName)
            break


class ContextBuildSelectionCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.active_view()
        reg = view.sel()[0]
        tests = []
        testLineRe = re.compile("^([ \t]*)def (test[^( ]*)", re.M)
        if not reg.empty():
            selection = view.substr(reg)
            for test in testLineRe.finditer(selection):
                findTestFromLine(view, test, test.start() + reg.a, tests)

        if not tests:
            # Still no tests... try to find one immediately before our
            # current line
            for line in reversed(view.find_all(testLineRe.pattern, re.M)):
                # After cursor?  ignore it
                if line.a > reg.a:
                    continue
                testLine = testLineRe.match(view.substr(line))
                findTestFromLine(view, testLine, line.a, tests)
                if tests:
                    # Only one test this way
                    break

        if tests:
            print(tests)
            Build.last = Build(tests = tests)
            Build.last.run()
        else:
            print("No tests found")


class ContextBuildLastCommand(sublime_plugin.WindowCommand):
    def run(self):
        Build.last.run()


    def is_enabled(self):
        return Build.last is not None


class ContextBuildFailuresCommand(sublime_plugin.WindowCommand):
    def run(self):
        Build.last = Build(onlyLastFailures = True)
        Build.last.run()

    def is_enabled(self):
        return Build.last is not None
