
import sublime
import sublime_plugin

import datetime
import re
import threading
import time

from .runnerMocha import RunnerMocha
from .runnerNosetests import RunnerNosetests

runners = [ RunnerNosetests, RunnerMocha ]

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
        self.options = sublime.load_settings('ContextBuild.sublime-settings')
        self.runners = []
        for runner in runners:
            self.runners.append(runner(self.options, self))


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


    def getRunnerForPath(self, path):
        """Return the Runner instance that will handle path.
        """
        runnerType = self._coalesceOption('context_build_runner')
        for r in self.runners:
            if r.__class__.__name__ == 'Runner' + runnerType.title():
                return r


    def run(self):
        """Called in main thread, do the build."""
        if self.thread:
            scheduler = threading.Thread(target = self._abortThenRun)
            scheduler.start()
            return

        currentUserView = self.window.active_view()

        if self.options.get('save_before_build'):
            for view in self.window.views():
                if view.is_dirty() and view.file_name() is not None:
                    view.run_command("save")

        newView = True
        if self.options.get('hide_last_build_on_new'):
            if self.lastView is None:
                # Plugin may have been reloaded, see if our window has any 
                # other context builds that we should replace.
                viewNamePattern = "^Build.*\.context-build$"
                for view in self.window.views():
                    if (re.match(viewNamePattern, view.name()) is not None 
                            and self.window.get_view_index(view)[0] != -1):
                        # This is an old build view from a previous invocation, 
                        # use it instead of creating a new one.
                        self.lastView = view
                        break

            if self.lastView is not None:
                self.outputPane = self.lastView
                self.outputPane.run_command("context_build_clear_view")
                newView = False

        if newView:
            # Be sure to make the view for our output in the main thread, so
            # that we don't have issues with memory access in sublime.
            self.outputPane = self.window.new_file()
        self.lastView = self.outputPane
        self.viewId = self.outputPane.id()

        now = datetime.datetime.now()
        timeStr = now.strftime("%I:%M:%S%p-%d-%m-%Y")
        buildName = "Build-{0}.context-build".format(timeStr)
        self.outputPane.set_scratch(True)
        self.outputPane.set_name(buildName)
        self.window.focus_view(self.outputPane)
        if currentUserView is not None:
            self.window.focus_view(currentUserView)

        with self.lock:
            self.viewIdToBuild[self.viewId] = self

        # Settings must be loaded in the main thread.  Therefore, tell each
        # runner to cache its options for the impending build.
        for r in self.runners:
            r.cacheOptionsForBuild()

        self.shouldStop = False
        self.thread = threading.Thread(target = self._realRun)
        self.thread.daemon = True
        self.thread.start()
        

    def setupTests(self, paths = [], tests = []):
        madeView = None
        if self.window.active_view() is None:
            madeView = self.window.new_file()
            madeView.set_scratch(True)

        for r in self.runners:
            r.setupTests(paths = paths, tests = tests)

        if madeView is not None:
            self.window.run_command("close")


    def useFailures(self):
        for r in self.runners:
            r.useFailures()


    def _abortThenRun(self):
        self.abort()
        sublime.set_timeout(self.run, 0)


    def _realRun(self):
        """Called in a new thread.  self.outputPane must already have been set 
        to a new file in the main thread.
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
        self.outputPane = None
        self.thread = None
        self.hasBuilt = True


    def _coalesceOption(self, name, default = ''):
        """We want to use the project's overloaded settings if they're
        available for things like paths, but default to sane defaults
        specified in ContextBuild.sublime-settings.

        Must be called in main thread
        """
        return self.window.active_view().settings().get(name,
                self.options.get(name, default))


    def _doBuild(self):
        """The main method for the build thread"""
        for r in self.runners:
            r.runTests(self._writeOutput, self._shouldStop)
        self.outputPane.show(self.outputPane.size())



    def _shouldStop(self):
        return self.shouldStop


    def _writeOutput(self, text, end = '\n'):
        if text is None:
            return
        elif isinstance(text, bytes):
            text = text.decode('utf8')
        cat = text + end

        visibleRegion = self.outputPane.visible_region()
        shouldKeepInView = (visibleRegion.begin() <= self.outputPane.size() 
                <= visibleRegion.end())

        self.outputPane.run_command("context_build_append_text", 
                dict(text = cat, scroll = shouldKeepInView))


class ContextBuildAppendTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, text, scroll = False):
        self.view.insert(edit, self.view.size(), text)
        
        if scroll:
            self.view.show(self.view.size())


class ContextBuildClearViewCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.erase(edit, sublime.Region(0, self.view.size()))


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


class ContextBuildSelectionCommand(ContextBuildPlugin):
    def run(self):
        view = self.window.active_view()
        viewText = view.substr(sublime.Region(0, view.size()))
        regions = view.sel()
        tests = {}
        filePath = view.file_name()
        runner = self.build.getRunnerForPath(filePath)
        for reg in regions:
            newTests = runner.getTestsFromRegion(viewText, reg.a, reg.b)
            if not newTests:
                continue
            tests.setdefault(filePath, []).extend(newTests)

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
        return True if self.hasLastBuild() and self.build.thread else False


class ContextBuildViewClosedEvent(sublime_plugin.EventListener):
    def on_close(self, view):
        Build.abortBuildForView(view.id())
