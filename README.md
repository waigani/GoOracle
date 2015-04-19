GoOracle
=========

GoOracle is a Golang plugin for [SublimeText](http://www.sublimetext.com/) that integrates the Go [oracle](https://godoc.org/code.google.com/p/go.tools/oracle) tool.


Usage
-----

Select, or place your cursor over, a symbol (function, variable, constant etc) and press `ctrl+shift+o`. You will be presented with the following modes of analysis to choose from:

```
callees     show possible targets of selected function call
callers     show possible callers of selected function
callgraph   show complete callgraph of program
callstack   show path from callgraph root to selected function
describe    describe selected syntax: definition, methods, etc
freevars    show free variables of selection
implements  show 'implements' relation for selected package
peers       show send/receive corresponding to selected channel op
referrers   show all refs to entity denoted by selected identifier
```

Select one and the output will be displayed in a new tab.


Install
-------

Install Sublime Package Control (if you haven't done so already) from http://wbond.net/sublime_packages/package_control. Be sure to restart ST to complete the installation.

Bring up the command palette (default ctrl+shift+p or cmd+shift+p) and start typing Package Control: Install Package then press return or click on that option to activate it. You will be presented with a new Quick Panel with the list of available packages. Type GoOracle and press return or on its entry to install GoOracle. If there is no entry for GoOracle, you most likely already have it installed.

Oracle requires several variables to be set in order to work. These are explained in the comments of the default settings `Preferences > Package Settings > GoOracle > Settings-Default`:

```javascript
{
    // env is a map of GOPATH, GOROOT and PATH variables.
    // e.g "env": { "PATH": "$HOME/go/bin:$PATH" }
    "env": {},

    // oracle_scope is an array of scopes of analysis for oracle.
    // e.g (for github.com/juju/juju) "oracle_scope": ["github.com/juju/juju/cmd/juju", "github.com/juju/juju/cmd/jujud"]
    "oracle_scope": [],

    // The format of oracle's output can be one of: 'json', 'xml' or 'plain'
    "oracle_format": "json",

    // The output can either be one of: 'buffer', 'output_panel'
    // Buffers can hold results from more than one invocation
    // Output panels sit underneath the editor area and are easily dismissed
    "output": "buffer"
}
```

You set your own variables in `Preferences > Package Settings > GoOracle > Settings-User`. Below is an example which sets up GoOracle to be used on the [github.com/juju/juju](github.com/juju/juju) codebase:

```javascript
{
    "env": { "GOPATH": "$HOME/go", "GOROOT": "$HOME/.gvm/gos/go1.2.1", "PATH": "$GOPATH/bin:$PATH" },
    "oracle_scope": ["github.com/juju/juju/cmd/juju", "github.com/juju/juju/cmd/jujud"],
    "oracle_format": "json",
    "output": "buffer"
}
```

You can also make project specific settings. First save your current workspace as a project `Project > Save as project ...`, then edit your project `Project > Edit Project`. Below is an example which sets up GoOracle to be used on the [github.com/juju/juju](github.com/juju/juju) codebase:

```javascript
{
    "folders":
    [
        {
            "follow_symlinks": true,
            "path": "/home/user/go/src/github.com/juju/juju"
        }
    ],
    "settings":
    {
        "GoOracle": {
            "oracle_scope": ["github.com/juju/juju/cmd/juju", "github.com/juju/juju/cmd/jujud"],
            "output": "output_panel"
        }
    },
}
```

Default key binding:

```javascript
[
    { "keys": ["ctrl+shift+o"], "command": "go_oracle"},
    { "keys": ["ctrl+alt+shift+o"], "command": "go_oracle_show_results"},
]
```

You can set your own key binding by copying the above into `Preferences > Keybindings - User` and replacing ctrl+shift+o with your preferred key(s).

You can also set a key binding for a specific mode by adding a "mode" arg, e.g.:

```javascript
    ...
    { "keys": ["ctrl+super+c"], "command": "go_oracle", "args": {"mode": "callers"} },
    { "keys": ["ctrl+super+i"], "command": "go_oracle", "args": {"mode": "implements"} },
    { "keys": ["ctrl+super+r"], "command": "go_oracle", "args": {"mode": "referrers"} },
    ...
```


Dependencies
------------
GoOracle relies on the oracle tool. You must install it in order for GoOracle to work. Run the following on your command line:

`go get golang.org/x/tools/cmd/oracle`


About Go Oracle
---------------

- [User Manual](https://docs.google.com/document/d/1SLk36YRjjMgKqe490mSRzOPYEDe0Y_WQNRv-EiFYUyw/view#)
- [Design Document](https://docs.google.com/a/canonical.com/document/d/1WmMHBUjQiuy15JfEnT8YBROQmEv-7K6bV-Y_K53oi5Y/edit#heading=h.m6dk5m56ri4e)
- [GoDoc](https://godoc.org/code.google.com/p/go.tools/oracle)


Copyright, License & Contributors
=================================

GoOracle is released under the MIT license. See [LICENSE.md](LICENSE.md)

GoOracle is the copyrighted work of *The GoOracle Authors* i.e me ([waigani](https://github.com/waigani/GoOracle)) and *all* contributors. If you submit a change, be it documentation or code, so long as it's committed to GoOracle's history I consider you a contributor. See [AUTHORS.md](AUTHORS.md) for a list of all the GoOracle authors/contributors.
