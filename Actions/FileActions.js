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

function showAndRunMassDialog() {
  const paths = getSelectedPathsArray();
  if (!paths) { showPopupSafe("No hay archivos seleccionados.", "Mover archivos"); return; }
  const listFile = fb.ProfilePath + "\\foobar_selection.txt";
  if (!writeSelectionToFile(listFile, paths)) { 
    showPopupSafe("Error creando archivo de rutas: " + listFile, "Error"); 
    return; 
  }
  // lanzar script con argumento listFile
  runPythonScript(PATHS.mass_dialog, [listFile], false);
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
    
    // 1. Transformamos el objeto en un arreglo secuencial
    const actions = [
      { text: "Move Selected Files", action: showAndRunMover },
      { text: "View Recicler Bin", action: openTrashFolder },
      { text: "Delete Selected Files", action: showAndRunDeletings },
      { text: "Rename Selected File", action: renameDialog },
      { text: "Mass Selected File", action: showAndRunMassDialog },
      { text: "Enumerate Folder", action: enumFolderDialog },
      { text: "Des-Enumerate Folder", action: desenumFolderDialog },
      { text: "Copy Names", action: copySelectedFileNames },
      { text: "Copy Paths", action: copySelectedFilePaths },
      { text: "Mp3Tag This Folder", action: openmp3Tag },
      { text: "Explore folder of current song", action: actionExploreDirectory },
      { text: "Connect current year to SMB", action: year_connect_smb },
    ];

    // 2. Agregamos los ítems usando el índice del arreglo (+1 para evitar el ID 0)
    actions.forEach((item, index) => {
      menu.AppendMenuItem(0, index + 1, item.text);
    });

    const res = menu.TrackPopupMenu(x, y);

    // 3. Restamos 1 al resultado para obtener el elemento correcto del arreglo
    const selectedAction = actions[res - 1];
    
    if (selectedAction && selectedAction.action) {
      selectedAction.action();
    }
  } catch (e) {
    showPopupSafe(`Error al abrir el menú: ${e.message}`, "Error");
  }
}
