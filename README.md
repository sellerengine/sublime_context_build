# ContextBuild for Sublime Text 2

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
