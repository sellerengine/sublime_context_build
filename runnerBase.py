
import os
import shlex
import subprocess
import tempfile
import threading
import time

# Sublime doesn't let you iterate over loaded settings, so we just have to
# know what settings we're interested in collapsing from the project settings.
# (We have to know because options can only be fetched on the main thread)
buildSettings = [ "context_build_path", "context_build_python_path",
        "context_build_runner" ]

class RunnerBase(object):
    """A class to run a certain type of tests and populate self.failed with
    the specs for re-running failed tests.
    """

    def __init__(self, options, build):
        self.options = options
        self.build = build
        self.failures = []


    @property
    def settings(self):
        return self._settings


    def getTestsFromRegion(self, filePath, viewText, start, end):
        """Implement in subclass to get a list of tests (input into setupTests)
        to run based on the region from start to end in viewText.
        """
        raise NotImplementedError()


    def runTests(self, writeOutput, shouldStop):
        """Run the tests; this is called in a thread other than the main one.
        Any long-running operations should use shouldStop() to determine
        whether or not the user has requested the build be cancelled.

        writeOutput can be used to write output directly to the build pane.
        """
        self.failures = []
        if ('Runner' + self.settings['context_build_runner'].title()
                != self.__class__.__name__):
            return
        self.writeOutput = writeOutput
        self._shouldStop = shouldStop
        self.doRunner(writeOutput, shouldStop)


    def setupTests(self, paths = [], tests = []):
        """Set up the runner for new tests; load config.  Run in the main
        thread.

        paths - list of files and folders to consider for execution.

        tests - list of file:testspec to execute (line is optional, but
                there should be two colons)
        """
        # Used for settings only
        self.view = self.build.window.active_view()
        self._settings = {}
        for key in buildSettings:
            self._settings[key] = self._coalesceOption(key)
        self.runnerSetup(paths = paths, tests = tests)


    def useFailures(self):
        """Run the next set of tests based on the failures from the last.
        """
        self.setupTests(tests = self.failures)


    def _coalesceOption(self, name, default = ''):
        """We want to use the project's overloaded settings if they're
        available for things like paths, but default to sane defaults
        specified in ContextBuild.sublime-settings.

        Must be called in main thread
        """
        return self.view.settings().get(name, self.options.get(name, default))


    def _dumpStdout(self, p, lineCallback):
        """Dumps the stdout from subprocess p; called in a new thread."""
        while p.poll() is None:
            while True:
                l = p.stdout.readline()
                if not l:
                    break
                lineCallback(l)
            time.sleep(0.1)
        lineCallback(p.stdout.read())


    def _runProcess(self, cmd, echoStdout = True, **kwargs):
        """Run a command through subprocess.Popen and optionally spit all
        of the output to our output pane.  Checks shouldStop throughout
        the execution.

        echoStdout -- If false, returns the standard output as a file-like
                object.
        """
        cmd = str(self.cmd)
        defaultKwargs = {
            'universal_newlines': True
        }
        if echoStdout:
            defaultKwargs['stdout'] = subprocess.PIPE
        else:
            defaultKwargs['stdout'] = tempfile.TemporaryFile()
        defaultKwargs['stderr'] = subprocess.STDOUT
        defaultKwargs.update(kwargs)

        env = os.environ.copy()
        env['PATH'] = self.settings['context_build_path'] + ':' + env['PATH']
        env.update(defaultKwargs.get('env', {}))
        defaultKwargs['env'] = env

        p = subprocess.Popen(shlex.split(cmd), **defaultKwargs)
        if echoStdout:
            if callable(echoStdout):
                lineCallback = echoStdout
            else:
                lineCallback = lambda l: self.writeOutput(l, end = '')

            stdThread = threading.Thread(target = self._dumpStdout,
                    args = (p, lineCallback))
            stdThread.start()
        while p.poll() is None:
            if self._shouldStop():
                break
            time.sleep(0.1)
        if p.poll() is None:
            # Exited due to shouldStop
            self.writeOutput("\n\nAborting tests...")
            while p.poll() is None:
                try:
                    p.terminate()
                except OSError:
                    # Died already
                    pass
                time.sleep(0.1)

        if echoStdout:
            # Finish getting output
            stdThread.join()

        if not echoStdout:
            tf = defaultKwargs['stdout']
            tf.seek(0)
            return tf
