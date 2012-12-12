# ContextBuild for Sublime Text 2

## Usage

Clone into your ~/.config/sublime-text-2/Packages folder.  Enjoy

Note: You MUST set the PYTHONENV environment variable to be the PYTHONPATH
for tests that you are going to run.  sublime clobbers PYTHONPATH, so we
have to reset it for running the tests.

Shortcuts (Ctrl / Super and Option / Alt are interchangeable):

* Ctrl+B - Build selected test(s)
* Ctrl+Shift+B - Build current file
* Alt+B - Re-run last build
* Alt+Shift+B - Re-run failures from last build

