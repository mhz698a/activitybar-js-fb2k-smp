function _googleSongGetSelectedHandle() {
    if (plman.ActivePlaylist < 0) return null;

    var items = plman.GetPlaylistSelectedItems(plman.ActivePlaylist);
    if (!items || items.Count === 0) return null;

    var arr = items.Convert();
    return arr.length ? arr[0] : null;
}

function _googleSongGetMeta(handle) {
    var parts = utils.SplitFilePath(handle.Path);
    var fileName = parts[1] || "";
    fileName = fileName.replace(/\.[^\.]+$/, "");

    var title = fb.TitleFormat("%title%").EvalWithMetadb(handle) || "";
    title = String(title).replace(/\s*\(ID:\s*\d+\)\s*$/, "").trim();

    var artist = fb.TitleFormat("%artist%").EvalWithMetadb(handle) || fb.TitleFormat("%album artist%").EvalWithMetadb(handle) || "";
    artist = String(artist).trim();

    return {
        fileName: String(fileName).trim(),
        title: title,
        artist: artist,
        titleArtist: (title + " " + artist).trim()
    };
}

function _googleSongOpenSearch(query) {
    var url = "https://www.google.com/search?q=" + encodeURIComponent(query);
    new ActiveXObject("Shell.Application").ShellExecute(url);
}

function showGoogleSearcherSongsMenu(x, y) {
    try {
        var handle = _googleSongGetSelectedHandle();
        if (!handle) {
            showPopupSafe("No hay elementos seleccionados.");
            return;
        }

        var meta = _googleSongGetMeta(handle);

        var items = [
            { id: 1, text: "Buscar por nombre de archivo", query: function (m) { return m.fileName; } },
            { id: 2, text: "Buscar por nombre de archivo + lyrics", query: function (m) { return m.fileName + " lyrics"; } },
            { id: 3, text: "Buscar por nombre de archivo + release date", query: function (m) { return m.fileName + " release date"; } },
            { id: 4, text: "Buscar por titulo + artista", query: function (m) { return m.titleArtist; } },
            { id: 5, text: "Buscar por titulo + artista + lyrics", query: function (m) { return m.titleArtist + " lyrics"; } },
            { id: 6, text: "Buscar por titulo + artista + release date", query: function (m) { return m.titleArtist + " release date"; } }
        ];

        var menu = window.CreatePopupMenu();
        for (var i = 0; i < items.length; i++) {
            menu.AppendMenuItem(0, items[i].id, items[i].text);
        }

        var px = (typeof x === "number") ? x : Math.floor(window.Width / 2);
        var py = (typeof y === "number") ? y : Math.floor(window.Height / 2);
        var res = menu.TrackPopupMenu(px, py);

        for (var j = 0; j < items.length; j++) {
            if (items[j].id === res) {
                _googleSongOpenSearch(items[j].query(meta));
                break;
            }
        }
    } catch (e) {
        showPopupSafe("Error al abrir el menú: " + e.message, "Error");
    }
}