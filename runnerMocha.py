
import re

from runnerBase import RunnerBase

class RunnerMocha(RunnerBase):

    # NOTE - we allow either open paren or space to support both javascript and
    # coffee-script-like syntaxes.
    _JS_CALL_STRING = r"""[\( ]("[^"]*"|'[^']*'),"""
    _TEST_REGEX = re.compile("^([ \t]*)it" + _JS_CALL_STRING, re.M)
    _DESCRIBE_REGEX = re.compile("^([ \t]*)describe" + _JS_CALL_STRING, re.M)
    _HEADER_LINE = re.compile(r"^\d+\.\.\d+$", re.M)
    _ERROR_LINE = re.compile(r"^( +.*Error:.*| +at .*:\d+:\d+\)?)$")


    def doRunner(self, writeOutput, shouldStop):
        realCmd = self.cmd
        mochaOptions = ""

        # mocha_compilers is a system-wide setting, not a project setting,
        # se we get it from options rather than settings.
        compilers = self.options.get('mocha_compilers')
        if compilers:
            mochaOptions += ' --compilers '
            mochaOptions += ','.join(compilers)

        realCmd = realCmd.replace("{mocha_options}", mochaOptions)

        writeOutput("Running tests: " + realCmd)
        self._nextTestLines = None  # Set to None before the header line
        self._lastTest = -1
        self._tests = {}
        self._countOk = 0
        self._countFailed = 0
        self._allOutput = ""
        # Use first failure as paths storage
        self._runProcess(realCmd, echoStdout = self._processOutput)

        self.writeOutput('')
        self.writeOutput("=" * 80)
        if len(self.failures) > 0:
            self.writeOutput("All failures")
            self.writeOutput("=" * 80)
            for t in self._tests.values():
                if not t['ok']:
                    self.writeOutput("== " + t['test'] + " ==")
                    self.writeOutput('\n'.join(t['errorLines']))
            self.writeOutput("=" * 80)
        self.writeOutput("{0} ok, {1} not ok".format(self._countOk,
                self._countFailed))


    def runnerSetup(self, paths = [], tests = {}):
        cmd = "mocha --reporter tap{mocha_options} "

        if paths:
            cmd += self._escapePaths(paths)
            # Remember our paths, since we re-use them for failed tests.
            self._paths = paths
        elif tests:
            # Mocha doesn't tell us which paths contain which tests, so just
            # keep a set of paths and add them to our cmd as we go
            paths = set()
            testNames = set()
            for filePath, testSpecs in tests.iteritems():
                paths.add(filePath)
                for ts in testSpecs:
                    testNames.add(ts)

            cmd += self._escapePaths(paths)
            cmd += ' --grep "'
            cmd += '|'.join(testNames)
            cmd += '"'
            # and keep _paths the same as it was in tests
            self._paths = list(paths)
        else:
            cmd = "echo 'No tests to run.'"
            self._paths = []

        self.cmd = cmd


    def _findTestFromLine(self, viewText, lineMatch, lineStartPos):
        indent = len(lineMatch.group(1))
        testName = lineMatch.group(2)[1:-1]
        for sel in reversed(list(self._DESCRIBE_REGEX.finditer(viewText))):
            if sel.start() > lineStartPos:
                continue
            clsIndent = len(sel.group(1))
            if clsIndent < indent:
                # Parent describe!
                indent = clsIndent
                testName = sel.group(2)[1:-1] + " " + testName
        return testName


    def _processLine(self, line):
        if self._nextTestLines is None:
            # Looking for header line or initialization errors
            if self._HEADER_LINE.match(line.strip()):
                # No longer looking for header
                self._nextTestLines = []
            else:
                # If it's not the header line, print it, since it's possibly
                # error or debug information
                self.writeOutput(line.rstrip())
        elif line.startswith('ok '):
            _, testId, text = line.split(' ', 2)
            if testId == self._lastTest:
                return
            self._lastTest = testId
            self._tests[testId] = { 'test': text.strip(), 'ok': True,
                    'lines': self._nextTestLines }
            self._nextTestLines = []
            self._countOk += 1
            self.writeOutput('.', end = '')
        elif line.startswith('not ok '):
            _, _, testId, text = line.split(' ', 3)
            if testId == self._lastTest:
                return
            self._lastTest = testId
            self._tests[testId] = { 'test': text.strip(), 'ok': False,
                    'errorLines': self._nextTestLines }
            self._nextTestLines = []
            self._countFailed += 1
            # Mocha doesn't tell us which file a test came from... so....
            for f in self._paths:
                self.failures.setdefault(f, []).append(text.strip())
            self.writeOutput('E', end = '')
        elif self._ERROR_LINE.match(line.rstrip()):
            self._tests[self._lastTest]['errorLines'].append(line.rstrip())
        else:
            self._nextTestLines.append(line.rstrip())


    def _processOutput(self, output):
        self._allOutput += output
        while True:
            parts = self._allOutput.split('\n', 1)
            if len(parts) == 1:
                break
            self._processLine(parts[0] + '\n')
            self._allOutput = parts[1]
