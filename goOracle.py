# Copyright (c) 2014 Jesse Meek <https://github.com/waigani>
# This program is Free Software see LICENSE file for details.

"""
GoOracle is a Go oracle plugin for Sublime Text 3.
It depends on the oracle tool being installed:
go get golang.org/x/tools/cmd/oracle
"""

import sublime, sublime_plugin, subprocess, time, re

class GoOracleCommand(sublime_plugin.TextCommand):
    def run(self, edit, mode=None):

        region = self.view.sel()[0]
        text = self.view.substr(sublime.Region(0, region.end()))
        cb_map = self.get_map(text)
        byte_end = cb_map[sorted(cb_map.keys())[-1]]
        byte_begin = None
        if not region.empty(): 
            byte_begin = cb_map[region.begin()-1]

        if mode:
            self.write_running(mode)
            self.oracle(byte_end, begin_offset=byte_begin, mode=mode, callback=self.oracle_complete)
            return

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
                self.write_running(modes[i])

                self.oracle(byte_end, begin_offset=byte_begin, mode=modes[i], callback=self.oracle_complete)

        self.view.window().show_quick_panel(descriptions, on_done, sublime.MONOSPACE_FONT)

    def oracle_complete(self, out, err):
        self.write_out(out, err)

    def write_running(self, mode):
        """ Write the "Running..." header to a new file and focus it to get results
        """

        window = self.view.window()
        view = get_output_view(window)

        # Run a new command to use the edit object for this view.
        view.run_command('go_oracle_write_running', {'mode': mode})

        if get_setting("output", "buffer") == "output_panel":
            window.run_command('show_panel', {'panel': "output." + view.name() })
        else:
            window.focus_view(view)

    def write_out(self, result, err):
        """ Write the oracle output to a new file.
        """

        window = self.view.window()
        view = get_output_view(window)

        # Run a new command to use the edit object for this view.
        view.run_command('go_oracle_write_results', {
            'result': result,
            'err': err})

        if get_setting("output", "buffer") == "output_panel":
            window.run_command('show_panel', {'panel': "output." + view.name() })
        else:
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

        #Set GOOS based on os at the end of the file name.
        #TODO Check file header for builds.
        file_path = self.view.file_name()
        goos = ""
        #From https://golang.org/doc/install/source
        goos_options = ["darwin", "dragonfly", "freebsd", "linux", "netbsd", "openbsd", "plan9", "solaris", "windows"]
        sp = file_path.rsplit("_", 1)
        if len(sp) == 2:
            if sp[1].endswith('.go'):
                last = sp[1][:-3]
                if last in goos_options:
                    goos = last

        # Build oracle cmd.
        cmd = "export GOPATH=\"%(go_path)s\"; export PATH=%(path)s; GOOS=%(goos)s oracle -pos=%(file_path)s:%(pos)s -format=%(output_format)s %(mode)s %(scope)s" % {
        "go_path": env["GOPATH"],
        "path": env["PATH"],
        "goos": goos,
        "file_path": file_path,
        "pos": pos,
        "output_format": get_setting("oracle_format"),
        "mode": mode,
        # TODO if scpoe is not set, use main.go under pwd or sublime project path.
        "scope": ' '.join(get_setting("oracle_scope"))} 

        if "GOROOT" in env:
            gRoot = "export GOROOT=\"%s\"; " % env["GOROOT"] 
            cmd = gRoot + cmd

        sublime.set_timeout_async(lambda: self.runInThread(cmd, callback), 0)

    def runInThread(self, cmd, callback):
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
        out, err = proc.communicate()
        callback(out.decode('utf-8'), err.decode('utf-8'))


class GoOracleWriteResultsCommand(sublime_plugin.TextCommand):
    """ Writes the oracle output to the current view.
    """

    def run(self, edit, result, err):
        view = self.view

        view.insert(edit, view.size(), "\n")

        if result:
            view.insert(edit, view.size(), result)
        if err:
            view.insert(edit, view.size(), err)

        view.insert(edit, view.size(), "\n\n\n")
        

class GoOracleWriteRunningCommand(sublime_plugin.TextCommand):
    """ Writes the oracle output to the current view.
    """

    def run(self, edit, mode):
        view = self.view

        content = "Running oracle " + mode + " command...\n"
        view.set_viewport_position(view.text_to_layout(view.size() - 1))

        view.insert(edit, view.size(), content)


class GoOracleShowResultsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if get_setting("output", "buffer") == "output_panel":
            self.view.window().run_command('show_panel', {'panel': "output.Oracle Output" })
        else:
            output_view = get_output_view(self.view.window())
            self.view.window().focus_view(output_view)


class GoOracleOpenResultCommand(sublime_plugin.EventListener):
    def on_selection_modified(self, view):
      if view.name() == "Oracle Output":
        if len(view.sel()) != 1:
            return
        if view.sel()[0].size() == 0:
            return

        lines = view.lines(view.sel()[0])
        if len(lines) != 1:
            return

        line = view.full_line(lines[0])
        text = view.substr(line)

        format = get_setting("oracle_format")

        # "filename:line:col" pattern for json
        m = re.search("\"([^\"]+):([0-9]+):([0-9]+)\"", text)

        # >filename:line:col< pattern for xml
        if m == None:
            m = re.search(">([^<]+):([0-9]+):([0-9]+)<", text)

        # filename:line.col-line.col: pattern for plain
        if m == None:
            m = re.search("^([^:]+):([0-9]+).([0-9]+)[-: ]", text)
        
        if m:
            w = view.window()
            new_view = w.open_file(m.group(1) + ':' + m.group(2) + ':' + m.group(3), sublime.ENCODED_POSITION)
            group, index = w.get_view_index(new_view)
            if group != -1:
                w.focus_group(group)


def get_setting(key, default=None):
    """ Returns the setting in the following hierarchy: project setting, user setting, 
    default setting.  If none are set the 'default' value passed in is returned.
    """

    val = None
    try:
       val = sublime.active_window().active_view().settings().get('GoOracle', {}).get(key)
    except AttributeError:
        pass

    if not val:
        val = sublime.load_settings("User.sublime-settings").get(key)
    if not val:
        val = sublime.load_settings("Default.sublime-settings").get(key)
    if not val:
        val = default
    return val

def get_output_view(window):
    view = None
    buff_name = 'Oracle Output'

    if get_setting("output", "buffer") == "output_panel":
        view = window.create_output_panel(buff_name)
    else:
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
    view_settings = view.settings()
    view_settings.set('line_numbers', False)
    view.set_syntax_file('Packages/GoOracle/GoOracleResults.tmLanguage')

    return view
