const SMP_COMMANDS = {
    1001: { name: "Move Selected Files",   action: showAndRunMover },
    1002: { name: "Delete Selected Files", action: showAndRunDeletings },
    1003: { name: "Open Newgrounds Page", action: openSelectedNewgroundsPage },
    1004: { name: "Google Searcher Songs", action: showGoogleSearcherSongsMenu }
};

function registerMainMenuCommands() {
    for (const id in SMP_COMMANDS) {
        fb.RegisterMainMenuCommand(
            Number(id),
            SMP_COMMANDS[id].name
        );
    }
}

function UnregisterMainMenuCommands() {
    for (const id in SMP_COMMANDS) {
        try {
            fb.UnregisterMainMenuCommand(
                Number(id)
            );
        } catch (e) {}
    }
}

function on_main_menu_dynamic(id) {
    if (SMP_COMMANDS[id]) {
        SMP_COMMANDS[id].action();
    }
}

function on_script_unload() {
    UnregisterMainMenuCommands()
}

registerMainMenuCommands();