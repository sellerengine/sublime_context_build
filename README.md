# ContextBuild for Sublime Text 2

ContextBuild is a plugin for Sublime Text 2 that replaces build functionality
for working with dynamic languages.  It has the ability to run any number of
files under a test runner configured on a per-project basis, and also the
ability to run any single test or multiple tests within an individual file.

ContextBuild also supports re-running the last build selection, as well as only failed tests from the last selection.

The result is a build system that cuts time off from fixing broken tests and
also from creating new tests.

ContextBuild currently supports Python (nosetests) and NodeJS (mocha).

## Usage

Clone into (or ln -s to) your ~/.config/sublime-text-2/Packages folder.  Enjoy!

Note: Sublime Text clobbers PYTHONPATH.  So, you MUST set the
"context_build_python_path" setting in either your .sublime-project file or
your user settings.

Shortcuts (Ctrl / Super and Option / Alt are interchangeable):

* Alt+B - Build current file
* Alt+Shift+B - Build selected test(s) (or the one before the cursor)
* Ctrl+B - Re-run last build
* Ctrl+Shift+B - Re-run failures from last build

You may also right click files in the tree-view and choose "Build Selected" to
trigger a build.

## Language support

### Python

The default ContextBuild action is to run nosetests with -v.

### NodeJS / Mocha

If you want to use the mocha test runner (NodeJS), you'll need to modify your
.sublime-project file to include "context_build_runner" in its "settings"
section:

    "settings": {
        "context_build_runner": "mocha"
    }

If you want to pass additional options to mocha, use the ContextBuild user
configuration (may be found under Preferences -> Package Settings ->
ContextBuild -> Settings - User).  For instance:

    {
        "mocha_compilers": [ "sjs:/home/walt/dev/seriousjs/src/seriousjs" ]
    }

## Changelog

### 0.8.2

* Save on build won't try to save files that do not exist on your hard drive
  (and would result in a prompt)

### 0.8.1

* When you close and re-open sublime text, any existing build views will be
  replaced with new builds, rather than creating a new view.

* Output from child process (e.g. nosetests) displays as it happens rather
  than based on lines.

* Repeated builds are sensitive to config changes
