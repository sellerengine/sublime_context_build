# ContextBuild for Sublime Text 2

## Usage

Clone into (or ln -s to) your ~/.config/sublime-text-2/Packages folder.  Enjoy!

Note: Sublime Text clobbers PYTHONPATH.  So, you MUST set the
"context_build_python_path" setting in either your .sublime-project file or
your user settings.

Shortcuts (Ctrl / Super and Option / Alt are interchangeable):

* Alt+B - Build selected test(s) (or the one before the cursor)
* Alt+Shift+B - Build current file
* Ctrl+B - Re-run last build
* Ctrl+Shift+B - Re-run failures from last build

You may also right click files in the tree-view and choose "Build Selected" to
trigger a build.
