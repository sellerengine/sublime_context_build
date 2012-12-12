import sublime, sublime_plugin

import re
import shlex
import subprocess

options = sublime.load_settings('ContextBuild.sublime-settings')

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
            
        p = subprocess.Popen(shlex.split(cmd), stdout = subprocess.PIPE, 
                stderr = subprocess.STDOUT, universal_newlines = True)
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


class ContextBuildSelectionCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.active_view()
        path = view.file_name()
        reg = view.sel()[0]
        if not reg.empty():
            tests = []

            selection = view.substr(reg)
            for test in re.finditer("^([ \t]*)def (test[^( ]*)", selection, 
                    re.M):
                testStart = test.start() + reg.a
                indent = test.group(1)
                testName = test.group(2)
                # Find the class
                for sel in reversed(view.find_all("^([ \t]*)class (Test[^( ]*)", 
                        re.M)):
                    print("Looking at " + view.substr(sel) + " at " 
                            + str(sel.a) + " from " + str(testStart))
                    if sel.a > testStart:
                        continue
                    text = view.substr(sel)
                    print(repr(text))
                    clsIndent = len(re.match("[ \t]*", text).group())
                    print("Comparing " + str(clsIndent))
                    if clsIndent < indent:
                        # MATCH!
                        tests.append(path + ':' 
                                + text[clsIndent + len('class '):] + '.' 
                                + testName)
                        break

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
