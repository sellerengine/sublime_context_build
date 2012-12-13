
import os
import pickle

from runnerBase import RunnerBase

class RunnerNosetests(RunnerBase):
    def doRunner(self, writeOutput, shouldStop):
        env = os.environ.copy()
        env['PYTHONPATH'] = self.settings['context_build_python_path']
        env['PATH'] = self.settings['context_build_path'] + ':' + env['PATH']

        writeOutput("Running tests: " + self.cmd)
        self.runProcess(self.cmd, echoStdout = True, env = env)

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


    def _runnerSetup(self, paths = [], tests = []):
        """Build our command line based on the given paths and tests.
        """
        cmd = self._getBaseCmd()

        if paths:
            cmd += " " + " ".join([ p.encode('utf8') for p in paths ])
        elif tests:
            cmd += " " + " ".join([ p.encode('utf8') for p in tests ])
        else:
            self.cmd = 'echo "No tests to run."'
            return

        self.cmd = cmd


    def _getBaseCmd(self):
        """Gets the nosetests args without specific tests or files"""
        # We need --with-ids to generate the .noseids file
        cmd = "nosetests --with-id"
        args = self.options.get('nosetests_args', '')
        if args:
            cmd += " " + args
        return cmd
