function _getFirstSelectedHandle() {
    const selected = plman.GetPlaylistSelectedItems(plman.ActivePlaylist);
    if (!selected || selected.Count === 0) return null;

    const arr = selected.Convert();
    return arr.length ? arr[0] : null;
}

function _openUrlInDefaultBrowser(url) {
    // Abre la URL con el manejador predeterminado del sistema.
    // En Windows esto normalmente termina en el navegador por defecto.
    new ActiveXObject("Shell.Application").ShellExecute(url);
}

function openSelectedNewgroundsPage() {
    const handle = _getFirstSelectedHandle();
    const letraEta = '\u03B7'
    if (!handle) {
        showPopupSafe("No hay elementos seleccionados.");
        return;
    }

    const fileName = utils.SplitFilePath(handle.Path)[1]; // sin extensión
    if (!/\s\(\u03B7\)$/.test(fileName)) {
        msg = 'El nombre de archivo "' + fileName + '" debe terminar con " (' + letraEta + ')"'
        showPopupSafe(msg, "Newgrounds");
        return;
    }

    const title = String(fb.TitleFormat("%title%").EvalWithMetadb(handle) || "").trim();
    const match = title.match(/\(ID:\s*(\d+)\)$/);

    if (!match) {
        showPopupSafe('El título debe terminar con "(ID: XXXXX)".');
        return;
    }

    const url = "https://www.newgrounds.com/audio/listen/" + match[1];
    _openUrlInDefaultBrowser(url);
}