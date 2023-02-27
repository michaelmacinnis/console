# console

When using Windows Terminal edit `settings.json` and remove:

        {
            "command":
            {
                "action": "copy",
                "singleLine": false
            },
            "keys": "ctrl+c"
        },
        {
            "command": "paste",
            "keys": "ctrl+v"
        },

from `"actions"` and add:

            "bellStyle": "none"

to `"defaults"`.

