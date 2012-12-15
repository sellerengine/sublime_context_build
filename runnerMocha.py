
from runnerBase import RunnerBase

class RunnerMocha(RunnerBase):
    def doRunner(self, writeOutput, shouldStop):
        writeOutput("Running tests: " + self.cmd)
        self._lastTest = -1
        self._tests = {}
        self._countOk = 0
        self._countFailed = 0
        # Use first failure as paths storage
        self.failures.append(self._paths)
        self._runProcess(self.cmd, echoStdout = self._processLine)

        self.writeOutput('')
        self.writeOutput("=" * 80)
        for t in self._tests.values():
            if not t['ok']:
                self.writeOutput("== " + t['test'] + " ==")
                self.writeOutput('\n'.join(t['errorLines']))
        self.writeOutput("=" * 80)
        self.writeOutput("{0} ok, {1} not ok".format(self._countOk,
                self._countFailed))


    def runnerSetup(self, paths = [], tests = []):
        cmd = "mocha --reporter tap"
        # mocha_compilers is a system-wide setting, not a project setting,
        # se we get it from options rather than settings.
        compilers = self.options.get('mocha_compilers')
        if compilers:
            cmd += ' --compilers '
            cmd += ','.join(compilers)

        if paths:
            cmd += ' ' + ' '.join(paths)
            # Remember our paths, since we re-use them for failed tests.
            self._paths = paths
        elif tests and len(tests) > 1:
            # First element is always an array of paths including the specified
            # tests.  Other elements optionally may be an arrow of paths
            # to add
            paths = []
            testNames = []
            for t in tests:
                if isinstance(t, list):
                    paths.extend(t)
                else:
                    testNames.append(t)
            cmd += ' ' + ' '.join(paths)
            cmd += ' --grep "'
            cmd += '|'.join(testNames)
            cmd += '"'
        else:
            cmd = "echo 'No tests to run.'"
            self._paths = []

        self.cmd = cmd


    def _processLine(self, line):
        if line.startswith('ok '):
            _, testId, text = line.split(' ', 2)
            if testId == self._lastTest:
                return
            self._lastTest = testId
            self._tests[testId] = { 'test': text.strip(), 'ok': True }
            self._countOk += 1
            self.writeOutput('.', end = '')
        elif line.startswith('not ok '):
            _, _, testId, text = line.split(' ', 3)
            if testId == self._lastTest:
                return
            self._lastTest = testId
            self._tests[testId] = { 'test': text.strip(), 'ok': False,
                    'errorLines': [] }
            self._countFailed += 1
            self.failures.append(text.strip())
            self.writeOutput('E', end = '')
        elif self._lastTest != -1 and (
                'errorLines' in self._tests[self._lastTest]):
            self._tests[self._lastTest]['errorLines'].append(line.rstrip())
            self.writeOutput(line.rstrip())
