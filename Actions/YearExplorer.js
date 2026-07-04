function showYearMenu(x, y, type) {
    try {
        const menu = window.CreatePopupMenu();
        const ranges = getYearRanges(1999, 10);
        let id = 1;
        const map = {};

        menu.AppendMenuItem(MF_DISABLED, 0, `${type}`);
        menu.AppendMenuSeparator();

        ranges.forEach(range => {
            for (let year = range.from; year <= range.to; year++) {
                menu.AppendMenuItem(0, id, " " + year);
                map[id] = year;
                id++;
            }
        });

        const res = menu.TrackPopupMenu(x, y);
        if (!map[res]) return;

        const year = map[res];
        const targetPath = buildTargetPath(type, year);
        openFileOrFolder(targetPath);
    } catch (e) {
        fb.ShowPopupMessage("Error menú años:\n" + e, "Error");
    }
}

function showYearFolderTreeMenu(x, y) {
    try {
        const menu = window.CreatePopupMenu();
        const currentYear = new Date().getFullYear();
        const yearMap = {};
        let id = 1;

        menu.AppendMenuItem(MF_DISABLED, 0, "Year Explorer");
        menu.AppendMenuSeparator();

        for (let year = 1999; year <= currentYear; year++) {
            menu.AppendMenuItem(0, id, " " + year);
            yearMap[id] = year;
            id++;
        }

        const res = menu.TrackPopupMenu(x, y);
        if (!yearMap[res]) return;

        showSingleYearFolderTreeMenu(x, y, yearMap[res]);
    } catch (e) {
        fb.ShowPopupMessage("Error menú años:\n" + e, "Error");
    }
}

function showSingleYearFolderTreeMenu(x, y, year) {
    try {
        const yearRoot = INTERNAL_BASE + "\\" + year;
        const folders = getCachedSubfolders(yearRoot);

        const menu = window.CreatePopupMenu();
        const actions = {};
        let id = 1;

        menu.AppendMenuItem(MF_DISABLED, 0, String(year));
        menu.AppendMenuSeparator();

        menu.AppendMenuItem(0, id, "\u2190");
        actions[id] = function () {
            showYearFolderTreeMenu(x, y);
        };
        id++;

        menu.AppendMenuItem(0, id, "...");
        actions[id] = function () {
            openFileOrFolder(yearRoot);
        };
        id++;

        menu.AppendMenuSeparator();

        if (!folders.length) {
            menu.AppendMenuItem(MF_DISABLED, 0, "(sin carpetas)");
        } else {
            folders.forEach(function (folder) {
                const subMenu = window.CreatePopupMenu();

                subMenu.AppendMenuItem(0, id, "...");
                actions[id] = (function (targetPath) {
                    return function () {
                        openFileOrFolder(targetPath);
                    };
                })(folder.path);
                id++;

                subMenu.AppendMenuSeparator();

                const children = getCachedSubfolders(folder.path);

                if (!children.length) {
                    subMenu.AppendMenuItem(MF_DISABLED, 0, "(sin subcarpetas)");
                } else {
                    children.forEach(function (child) {
                        subMenu.AppendMenuItem(0, id, child.name);
                        actions[id] = (function (targetPath) {
                            return function () {
                                openFileOrFolder(targetPath);
                            };
                        })(child.path);
                        id++;
                    });
                }

                subMenu.AppendTo(menu, 0, folder.name);
            });
        }

        const res = menu.TrackPopupMenu(x, y);
        if (actions[res]) actions[res]();
    } catch (e) {
        fb.ShowPopupMessage("Error menú años:\n" + e, "Error");
    }
}