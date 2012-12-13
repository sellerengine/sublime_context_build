# ContextBuild for Sublime Text 2

## Usage

Clone into (or ln -s to) your ~/.config/sublime-text-2/Packages folder.  Enjoy!

Note: Sublime Text clobbers PYTHONPATH.  So, you MUST set the
"context_build_python_path" setting in either your .sublime-project file or
your user settings.

Shortcuts (Ctrl / Super and Option / Alt are interchangeable):

* Ctrl+B - Build selected test(s) (or the one before the cursor)
* Ctrl+Shift+B - Build current file
* Alt+B - Re-run last build
* Alt+Shift+B - Re-run failures from last build

You may also right click files in the tree-view and choose "Build Selected" to
trigger a build.
