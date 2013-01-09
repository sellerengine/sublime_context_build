
import os
import pickle
import re
import tempfile

from runnerBase import RunnerBase

class RunnerNosetests(RunnerBase):

    _TEST_REGEX = re.compile("^([ \t]*)def (test[^( ]*)", re.M)


    def doRunner(self, writeOutput, shouldStop):
        realCmd = self.cmd
        nosetestsArgs = self.options.get('nosetests_args', '')
        if nosetestsArgs:
            # Must have preceding space
            nosetestsArgs = ' ' + nosetestsArgs
        realCmd = realCmd.replace("{nosetests_args}", nosetestsArgs)
        writeOutput("Running tests: " + realCmd)
        self._runProcess(realCmd, echoStdout = True,
                env = { 'PYTHONPATH':
                        self.settings['context_build_python_path']})

        # Read nose output to see what failed
        try:
            with open(self._noseIdsFile, 'r') as f:
                fails = pickle.load(f)
            for failId in fails['failed']:
                fpath, _module, testspec = fails['ids'][int(failId)]
                self.failures.setdefault(fpath, []).append(testspec)
            os.remove(self._noseIdsFile)
        except IOError:
            pass


    def runnerSetup(self, paths = [], tests = {}):
        """Build our command line based on the given paths and tests.
        """
        # We need --with-ids to generate the .noseids file
        cmd = "nosetests --with-id --id-file="
        self._noseIdsFile = os.path.join(tempfile.gettempdir(),
                "context-build-nose-ids")
        cmd += self._noseIdsFile
        cmd += "{nosetests_args}"

        if paths:
            cmd += self._escapePaths(paths)
        elif tests:
            for filePath, testSpecs in tests.iteritems():
                if None in testSpecs:
                    # Whole file
                    cmd += self._escapePaths([ filePath ])
                else:
                    cmd += self._escapePaths([ filePath + ':' + t
                            for t in testSpecs ])
        else:
            self.cmd = 'echo "No tests to run."'
            return

        self.cmd = cmd


    def _findTestFromLine(self, viewText, testMatch, testStartPos):
        indent = testMatch.group(1)
        testName = testMatch.group(2)
        findClass = re.compile("^([ \t]*)class (Test[^( ]*)", re.M)
        # Find the class
        for sel in reversed(list(findClass.finditer(viewText))):
            if sel.start() > testStartPos:
                continue
            text = viewText[sel.start():sel.end()]
            clsIndent = len(re.match("[ \t]*", text).group())
            if clsIndent < indent:
                # MATCH!
                return (text[clsIndent + len('class '):] + '.'
                        + testName)
        return None
