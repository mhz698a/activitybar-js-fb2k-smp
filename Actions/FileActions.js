// =======================
// Selection Actions
// =======================

function getSelectedPathsArray() {
  const sel = plman.GetPlaylistSelectedItems(plman.ActivePlaylist);
  if (!sel || sel.Count === 0) return null;
  const arr = [];
  for (let i = 0; i < sel.Count; i++) arr.push(sel[i].Path);
  return arr;
}

function openmp3Tag(){
    fb.RunContextCommand("Run service/Edit Folder with mp3Tag")
}

function showAndRunMover() {
  const paths = getSelectedPathsArray();
  if (!paths) { showPopupSafe("No hay archivos seleccionados.", "Mover archivos"); return; }
  const listFile = fb.ProfilePath + "\\foobar_selection.txt";
  if (!writeSelectionToFile(listFile, paths)) { 
    showPopupSafe("Error creando archivo de rutas: " + listFile, "Error"); 
    return; 
  }
  // lanzar script con argumento listFile
  runPythonScript(PATHS.moverScript, [listFile], false);
}

function showAndRunDeletings() {
  const paths = getSelectedPathsArray();
  if (!paths) { showPopupSafe("No hay archivos seleccionados.", "Mover archivos"); return; }
  const listFile = fb.ProfilePath + "\\foobar_selection.txt";
  if (!writeSelectionToFile(listFile, paths)) { showPopupSafe("Error creando archivo de rutas: " + listFile, "Error"); return; }
  // en versión original se lanzaba movetrashfb2kd.py (sin pasar listFile en cmd original)
  runPythonScript(PATHS.movetrashScript, [listFile], false);
}

function openTrashFolder() {
  // Abrir ruta fija (ajusta si es necesario)
  openProgramNoStart('explorer.exe "' + 'E:\\_Exclude\\l_reallydeleted' + '"');
}

function renameDialog() {
  const sel = plman.GetPlaylistSelectedItems(plman.ActivePlaylist);
  if (!sel || sel.Count !== 1) {
    showPopupSafe("Esta operación solo acepta UN archivo seleccionado.", "Rename file");
    return;
  }
  const filePath = sel[0].Path;
  if (!filePath || !utils.FileExists(filePath)) {
    showPopupSafe("El archivo seleccionado no existe o no es válido: " + filePath, "Rename file");
    return;
  }
  const cmdArgs = [filePath];
  try {
    // La versión original lanzaba Python oculto (shell.Run(cmd, 0, false));
    runPythonScript(PATHS.renameScript, cmdArgs, false);
  } catch (e) {
    showPopupSafe("Error al lanzar comando:\n" + e + "\n", "Error");
  }
}

function year_connect_smb() {
  const sel = plman.GetPlaylistSelectedItems(plman.ActivePlaylist);
  if (!sel || sel.Count !== 1) {
    showPopupSafe("Esta operación solo acepta UN archivo seleccionado.", "SMB Dialog connection");
    return;
  }
  const filePath = sel[0].Path;
  if (!filePath || !utils.FileExists(filePath)) {
    showPopupSafe("El archivo seleccionado no existe o no es válido: " + filePath, "SMB Dialog connection");
    return;
  }
  const cmdArgs = [filePath];
  try {
    // La versión original lanzaba Python oculto (shell.Run(cmd, 0, false));
    runPythonScript(PATHS.smb_year_dialog, cmdArgs, false);
  } catch (e) {
    showPopupSafe("Error al lanzar comando:\n" + e + "\n", "Error");
  }
}

function enumFolderDialog() {
  const sel = plman.GetPlaylistSelectedItems(plman.ActivePlaylist);
  if (!sel || sel.Count !== 1) {
    showPopupSafe("Esta operación solo acepta UN archivo seleccionado.", "Enumerar carpeta");
    return;
  }
  const filePath = sel[0].Path;
  if (!filePath || !utils.FileExists(filePath)) {
    showPopupSafe("El archivo seleccionado no existe o no es válido: " + filePath, "Enumerar carpeta");
    return;
  }
  const cmdArgs = [filePath];
  try {
    // Igual que renameDialog: lanza el script Python ocultando la consola (startVisible = false)
    runPythonScript(PATHS.enumScript, cmdArgs, false);
  } catch (e) {
    showPopupSafe("Error al lanzar comando:\n" + e + "\n", "Error");
  }
}

function desenumFolderDialog() {
  const sel = plman.GetPlaylistSelectedItems(plman.ActivePlaylist);
  if (!sel || sel.Count !== 1) {
    showPopupSafe("Esta operación solo acepta UN archivo seleccionado.", "Enumerar carpeta");
    return;
  }
  const filePath = sel[0].Path;
  if (!filePath || !utils.FileExists(filePath)) {
    showPopupSafe("El archivo seleccionado no existe o no es válido: " + filePath, "Enumerar carpeta");
    return;
  }
  const cmdArgs = [filePath];
  try {
    // Igual que renameDialog: lanza el script Python ocultando la consola (startVisible = false)
    runPythonScript(PATHS.desenumScript, cmdArgs, false);
  } catch (e) {
    showPopupSafe("Error al lanzar comando:\n" + e + "\n", "Error");
  }
}

function actionExploreDirectory() {
    fb.RunContextCommand("Run service/Explore Directory");
}

function showFileActions(x, y) {
  try {
    const menu = window.CreatePopupMenu();

    const actions = {
      1: { text: "Move Selected Files", action: showAndRunMover },
      2: { text: "View Recicler Bin", action: openTrashFolder },
      3: { text: "Delete Selected Files", action: showAndRunDeletings },
      4: { text: "Rename Selected File", action: renameDialog },
      5: { text: "Enumerate Folder", action: enumFolderDialog },
      6: { text: "Des-Enumerate Folder", action: desenumFolderDialog },
      7: { text: "Copy Names", action: copySelectedFileNames },
      8: { text: "Copy Paths", action: copySelectedFilePaths },
      9: { text: "Mp3Tag This Folder", action: openmp3Tag },
      10: { text: "Explore folder of current song", action: actionExploreDirectory },
      11: { text: "Connect current year folder to SMB", action: year_connect_smb },
    };

    Object.entries(actions).forEach(([id, { text }]) =>
      menu.AppendMenuItem(0, Number(id), text)
    );

    const res = menu.TrackPopupMenu(x, y);

    if (actions[res] && actions[res].action) {
      actions[res].action();
    }

  } catch (e) {
    showPopupSafe(`Error al abrir el menú: ${e.message}`, "Error");
  }
}
