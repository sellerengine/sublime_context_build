
import os
import pickle
import re

from runnerBase import RunnerBase

class RunnerNosetests(RunnerBase):
    def doRunner(self, writeOutput, shouldStop):
        writeOutput("Running tests: " + self.cmd)
        self._runProcess(self.cmd, echoStdout = True,
                env = { 'PYTHONPATH':
                        self.settings['context_build_python_path']})

        # Read nose output to see what failed
        try:
            with open('.noseids', 'r') as f:
                fails = pickle.load(f)
            for failId in fails['failed']:
                fpath, _module, testspec = fails['ids'][int(failId)]
                self.failures.append(fpath + ':' + testspec)
            os.remove('.noseids')
        except OSError:
            pass


    def getTestsFromRegion(self, filePath, viewText, start, end):
        """Find test_ methods in the given region, and resolve the
        class names to get to them.
        """
        tests = []
        testLineRe = re.compile("^([ \t]*)def (test[^( ]*)", re.M)

        # Add the test before the given start.. end region, and any tests
        # between start and end.
        for line in reversed(list(testLineRe.finditer(viewText))):
            # After end?  Ignore
            if line.end() > end:
                continue
            # Between points?
            if line.end() >= start:
                self._findTestFromLine(viewText, line, line.start(), tests)
            else:
                # Before start, if we got a hit, this is the last test we may
                # add before aborting
                self._findTestFromLine(viewText, line, line.start(), tests)
                break

        for i, t in enumerate(tests):
            tests[i] = filePath + ':' + tests[i]
        return tests



    def runnerSetup(self, paths = [], tests = []):
        """Build our command line based on the given paths and tests.
        """
        # We need --with-ids to generate the .noseids file
        cmd = "nosetests --with-id"
        args = self.options.get('nosetests_args', '')
        if args:
            cmd += " " + args

        if paths:
            for p in paths:
                if ' ' in p:
                    cmd += ' "{0}"'.format(p)
                else:
                    cmd += ' ' + p
            cmd += " " + " ".join(paths)
        elif tests:
            for t in tests:
                if ' ' in t:
                    cmd += ' "{0}"'.format(t)
                else:
                    cmd += ' ' + t
        else:
            self.cmd = 'echo "No tests to run."'
            return

        self.cmd = cmd


    def _findTestFromLine(self, viewText, testLine, actualStart, testsOut):
        indent = testLine.group(1)
        testName = testLine.group(2)
        findClass = re.compile("^([ \t]*)class (Test[^( ]*)", re.M)
        # Find the class
        for sel in reversed(list(findClass.finditer(viewText))):
            if sel.start() > actualStart:
                continue
            text = viewText[sel.start():sel.end()]
            clsIndent = len(re.match("[ \t]*", text).group())
            if clsIndent < indent:
                # MATCH!
                testsOut.append(text[clsIndent + len('class '):] + '.'
                        + testName)
                break
