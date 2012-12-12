# ContextBuild for Sublime Text 2

## Usage

Clone into your ~/.config/sublime-text-2/Packages folder.  Enjoy

Note: You MUST set the PYTHONENV environment variable to be the PYTHONPATH
for tests that you are going to run.  sublime clobbers PYTHONPATH, so we
have to reset it for running the tests.

Shortcuts:

* Ctrl+B - Build current file
* Ctrl+Shift+B - Build selected tests (be sure to select leading newline)
* F12 - Re-run last build
* Ctrl+F12 - Re-run failures from last build

