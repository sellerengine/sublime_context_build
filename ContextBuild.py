
from __future__ import print_function

import sublime, sublime_plugin

import os
import re
import shlex
import subprocess
import threading
import time

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
        self.thread = None


    def abort(self):
        while self.thread:
            self.shouldStop = True
            time.sleep(0.1)


    def run(self):
        self.shouldStop = False
        self.thread = threading.Thread(target = self._realRun)
        self.thread.daemon = True
        self.thread.start()


    def _realRun(self):
        oldBuild = getattr(self.window, '_ContextBuildRunning', None)
        if oldBuild:
            oldBuild.abort()

        self.window._ContextBuildRunning = self
        try:
            self._doBuild()
        finally:
            self.window._ContextBuildRunning = None
            self.thread = None


    def _doBuild(self):
        cmd = "nosetests -v"
        testDesc = None
        if self.paths:
            testDesc = repr(self.paths)
            cmd += " " + " ".join([ p.encode('utf8') for p in self.paths ])
        elif self.noseFailureData is not None:
            with open(".noseids", "w") as f:
                f.write(self.noseFailureData)
            cmd += " --failed"
            testDesc = "failed tests"
        elif self.tests:
            testDesc = repr(self.tests)
            cmd += " " + " ".join([ p.encode('utf8') for p in self.tests ])
        else:
            print("No tests to run.")
            return
            
        env = os.environ.copy()
        env['PYTHONPATH'] = self._option('context_build_python_path')

        print("Running tests: " + testDesc)

        p = subprocess.Popen(shlex.split(cmd), stdout = subprocess.PIPE, 
                stderr = subprocess.STDOUT, env = env,
                universal_newlines = True)
        stdThread = threading.Thread(target = self._dumpStdout, args = (p,))
        stdThread.start()
        while p.poll() is None:
            if self.shouldStop:
                break
            time.sleep(0.1)
        if p.poll() is None:
            print("Aborting tests...")
            while p.poll() is None:
                try:
                    p.terminate()
                except OSError, e:
                    # Died already
                    pass
                time.sleep(0.1)


    def _dumpStdout(self, p):
        """Dumps the stdout from subprocess p; called in a new thread."""
        while p.poll() is None:
            p.stdout.flush()
            buffer = []
            while True:
                l = p.stdout.read(1)
                if not l:
                    break
                print(l, end = '')
            time.sleep(0.1)
        print(p.stdout.read())


    def _option(self, name, default = ''):
        """We want to use the project's overloaded settings if they're 
        available for things like paths, but default to sane defaults
        specified in ContextBuild.sublime-settings.
        """
        return self.window.active_view().settings().get(name, 
                options.get(name, default))


class ContextBuildPlugin(sublime_plugin.WindowCommand):
    def hasLastBuild(self):
        return getattr(self.window, '_ContextBuild', None) is not None


    @property
    def lastBuild(self):
        return self.window._ContextBuild


    @lastBuild.setter
    def lastBuild(self, value):
        value.window = self.window
        self.window._ContextBuild = value


class ContextBuildCurrentCommand(ContextBuildPlugin):
    def run(self):
        self.lastBuild = Build(paths = 
                [ self.window.active_view().file_name() ])
        self.lastBuild.run()


    def is_enabled(self):
        return True


class ContextBuildSelectedCommand(ContextBuildPlugin):
    def run(self, paths = []):
        self.lastBuild = Build(paths)
        self.lastBuild.run()


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
        clsIndent = len(re.match("[ \t]*", text).group())
        if clsIndent < indent:
            # MATCH!
            testsOut.append(view.file_name() + ':' 
                    + text[clsIndent + len('class '):] + '.' 
                    + testName)
            break


class ContextBuildSelectionCommand(ContextBuildPlugin):
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
            self.lastBuild = Build(tests = tests)
            self.lastBuild.run()
        else:
            print("No tests found")


class ContextBuildLastCommand(ContextBuildPlugin):
    def run(self):
        self.lastBuild.run()


    def is_enabled(self):
        return self.hasLastBuild()


class ContextBuildFailuresCommand(ContextBuildPlugin):
    def run(self):
        self.lastBuild = Build(onlyLastFailures = True)
        self.lastBuild.run()

    def is_enabled(self):
        return self.hasLastBuild()


class ContextBuildStopCommand(ContextBuildPlugin):
    def run(self):
        self.lastBuild.abort()


    def is_enabled(self):
        return self.hasLastBuild() and self.lastBuild.thread
