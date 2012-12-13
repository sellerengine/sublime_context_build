
import sublime
import sublime_plugin

import datetime
import re
import threading
import time

from runnerNosetests import RunnerNosetests

runners = { "nosetests": RunnerNosetests }

options = sublime.load_settings('ContextBuild.sublime-settings')

class Build(object):
    last = None
    lock = threading.Lock()
    byWindow = {}
    viewIdToBuild = {}

    def __init__(self, window):
        self.window = window
        self.lastView = None
        self.thread = None
        self.hasBuilt = False
        self.runners = {}
        for lang in [ 'python' ]:
            runner = options.get(lang + '_runner')
            if runner:
                self.runners[lang] = runners[runner](options, self)


    def abort(self):
        while self.thread:
            self.shouldStop = True
            time.sleep(0.1)


    @classmethod
    def abortBuildForView(cls, viewId):
        with cls.lock:
            build = cls.viewIdToBuild.get(viewId)
        # Release lock before aborting, since aborts require the lock.
        # Also run it in a new thread to prevent "Slow plugin" warnings.
        if build:
            t = threading.Thread(target = build.abort)
            t.start()


    def run(self):
        """Called in main thread, do the build."""
        if self.thread:
            scheduler = threading.Thread(target = self._abortThenRun)
            scheduler.start()
            return

        # Be sure to make the view for our output in the main thread, so that
        # we don't have issues with memory access in sublime.
        self.view = self.window.new_file()
        self.viewId = self.view.id()

        now = datetime.datetime.now()
        timeStr = now.strftime("%I:%M:%S%p-%d-%m-%Y")
        buildName = "Build-{0}.context-build".format(timeStr)
        self.view.set_scratch(True)
        self.view.set_name(buildName)

        if options.get('hide_last_build_on_new'):
            if self.lastView:
                # Bah to dirty hacks.  Oh well...
                firstId = self.window.active_view().id()
                while True:
                    self.window.run_command("next_view")
                    myId = self.window.active_view().id()
                    if myId == self.lastView.id():
                        # Can only close current tab....
                        self.window.run_command("close")
                        break
                    elif myId == firstId:
                        # Cycle completed
                        break
        self.lastView = self.view

        if options.get('save_before_build'):
            av = self.window.active_view()
            curView = av.id()
            while True:
                if av.is_dirty():
                    av.run_command("save")
                self.window.run_command("next_view")
                av = self.window.active_view()
                if av.id() == curView:
                    break

        with self.lock:
            self.viewIdToBuild[self.viewId] = self

        self.shouldStop = False
        self.thread = threading.Thread(target = self._realRun)
        self.thread.daemon = True
        self.thread.start()


    def setupTests(self, paths = [], tests = []):
        for r in self.runners.values():
            r.setupTests(paths = paths, tests = tests)


    def useFailures(self):
        for r in self.runners.values():
            r.useFailures()


    def _abortThenRun(self):
        self.abort()
        sublime.set_timeout(self.run, 0)


    def _realRun(self):
        """Called in a new thread.  self.view must already have been set to
        a new file in the main thread.
        """
        try:
            self._doBuild()
        finally:
            sublime.set_timeout(self._cleanup, 0)


    def _cleanup(self):
        """Take care of all of our variables; in a timeout so that other
        callbacks from during the build execute first.
        """
        with self.lock:
            self.viewIdToBuild.pop(self.viewId)
        self.view = None
        self.thread = None
        self.hasBuilt = True


    def _doBuild(self):
        """The main method for the build thread"""
        for r in self.runners.values():
            r.runTests(self._writeOutput, self._shouldStop)


    def _shouldStop(self):
        return self.shouldStop


    def _writeOutput(self, text, end = '\n'):
        cat = text + end
        # Print in sublime's main thread to not cause buffer issues
        def realPrint():
            edit = self.view.begin_edit()
            self.view.insert(edit, self.view.size(), cat)
            self.view.end_edit(edit)
        sublime.set_timeout(realPrint, 0)


class ContextBuildPlugin(sublime_plugin.WindowCommand):
    def hasLastBuild(self):
        return self.build.hasBuilt


    @property
    def build(self):
        wid = self.window.id()
        build = Build.byWindow.get(wid)
        if build is None:
            build = Build.byWindow[wid] = Build(self.window)
        return build


class ContextBuildCurrentCommand(ContextBuildPlugin):
    def run(self):
        self.build.setupTests(paths = [
                self.window.active_view().file_name() ])
        self.build.run()


    def is_enabled(self):
        return True


class ContextBuildSelectedCommand(ContextBuildPlugin):
    def run(self, paths = []):
        self.build.setupTests(paths = paths)
        self.build.run()


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

        self.build.setupTests(tests = tests)
        self.build.run()


class ContextBuildLastCommand(ContextBuildPlugin):
    def run(self):
        self.build.run()


    def is_enabled(self):
        return self.hasLastBuild()


class ContextBuildFailuresCommand(ContextBuildPlugin):
    def run(self):
        self.build.useFailures()
        self.build.run()

    def is_enabled(self):
        return self.hasLastBuild()


class ContextBuildStopCommand(ContextBuildPlugin):
    def run(self):
        self.build.abort()


    def is_enabled(self):
        return self.hasLastBuild() and self.build.thread


class ContextBuildViewClosedEvent(sublime_plugin.EventListener):
    def on_close(self, view):
        Build.abortBuildForView(view.id())
