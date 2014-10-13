# Copyright (c) 2014 Jesse Meek <https://github.com/waigani>
# This program is Free Software see LICENSE file for details.

"""
GoOracle is a Go oracle plugin for Sublime Text 3.
It depends on the oracle tool being installed:
go get code.google.com/p/go.tools/cmd/oracle
"""

import sublime, sublime_plugin, subprocess, time

class GoOracleCommand(sublime_plugin.TextCommand):
    def run(self, edit):

        # Get the oracle mode from the user.
        modes = ["callees","callers","callgraph","callstack","describe","freevars","implements","peers","referrers"]
        descriptions  = [
            "callees     show possible targets of selected function call",
            "callers     show possible callers of selected function",
            "callgraph   show complete callgraph of program",
            "callstack   show path from callgraph root to selected function",
            "describe    describe selected syntax: definition, methods, etc",
            "freevars    show free variables of selection",
            "implements  show 'implements' relation for selected package",
            "peers       show send/receive corresponding to selected channel op",
            "referrers   show all refs to entity denoted by selected identifier"]

        # Call oracle cmd with the given mode.
        def on_done(i):
            if i >= 0 :
                region = self.view.sel()[0]
                text = self.view.substr(sublime.Region(0, region.end()))
                cb_map = self.get_map(text)
                byte_end = cb_map[sorted(cb_map.keys())[-1]]
                byte_begin = None
                if not region.empty(): 
                    byte_begin = cb_map[region.begin()-1]

                self.oracle(byte_end, begin_offset=byte_begin, mode=modes[i], callback=self.oracle_complete)

        self.view.window().show_quick_panel(descriptions, on_done)

    def oracle_complete(self, out, err, mode):
        self.write_out(out, err, mode)

    def write_out(self, result, err, mode):
        """ Write the oracle output to a new file.
        """

        window = self.view.window()
        view = None
        buff_name = 'Oracle Output'

        # If the output file is already open, use that.
        for v in window.views():
            if v.name() == buff_name:
                view = v
                break
        # Otherwise, create a new one.
        if view is None:
            view = window.new_file()
            view.set_name(buff_name)
            view.set_scratch(True)

        # Run a new command to use the edit object for this view.
        view.run_command('go_oracle_write_to_file', {
            'result': result,
            'err': err,
            'mode': mode})
        window.focus_view(view)

    def get_map(self, chars):
        """ Generate a map of character offset to byte offset for the given string 'chars'.
        """

        byte_offset = 0
        cb_map = {}

        for char_offset, char in enumerate(chars):
            cb_map[char_offset] = byte_offset
            byte_offset += len(char.encode('utf-8'))
        return cb_map

    def oracle(self, end_offset, begin_offset=None, mode="describe", callback=None):
        """ Builds the oracle shell command and calls it, returning it's output as a string.
        """

        pos = "#" + str(end_offset)
        if begin_offset is not None:
            pos = "#%i,#%i" %(begin_offset, end_offset)
        env = get_setting("env")

        # Build oracle cmd.
        cmd = "export GOPATH=\"%(go_path)s\"; export GOROOT=\"%(go_root)s\"; export PATH=%(path)s; oracle -pos=%(file_path)s:%(pos)s -format=%(output_format)s %(mode)s %(scope)s"  % {
        "go_path": env["GOPATH"],
        "go_root": env["GOROOT"],
        "path": env["PATH"],
        "file_path": self.view.file_name(),
        "pos": pos,
        "output_format": get_setting("oracle_format"),
        "mode": mode,
        "scope": ' '.join(get_setting("oracle_scope"))} 

        sublime.set_timeout_async(lambda: self.runInThread(cmd, callback, mode), 0)

    def runInThread(self, cmd, callback, mode):
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
        out, err = proc.communicate()
        callback(out.decode('utf-8'), err.decode('utf-8'), mode)

class GoOracleWriteToFileCommand(sublime_plugin.TextCommand):
    """ Writes the oracle output to the current view.
    """

    def run(self, edit, result, err, mode):
        view = self.view

        content = mode
        if result:
            content += "\n\n" + result
        if err:
            content += "\nErrors Found:\n\n"+ err

        view.replace(edit, sublime.Region(0, view.size()), content)
        view.sel().clear()


def get_setting(key, default=None):
    """ Returns the user setting if found, otherwise it returns the
    default setting. If neither are set the 'default' value passed in is returned.
    """

    val = sublime.load_settings("User.sublime-settings").get(key)
    if not val:
        val = sublime.load_settings("Default.sublime-settings").get(key)
    if not val:
        val = default
    return val
