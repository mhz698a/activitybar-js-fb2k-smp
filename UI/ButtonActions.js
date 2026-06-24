// Sliderbar/UI/ButtonActions.js

function actionFrameEtude() {
    runPythonScript(PATHS.frame_etude_py, '', false);
}

function actionCatchEtude() {
    runPythonScript(PATHS.catch_etude_py, '', false);
}

function actionRenderDomains(){
    runPythonScript(PATHS.render_domains_py, '', false);
}

function actionYearsMenu(x, y) {
    showYearFolderTreeMenu(x, y);
}

function actionEffectsMenu(x, y) {
    showEffectsMenu(x, y);
}

function actionGoogleArtistTitle(x, y) {
    showGoogleSearcherSongsMenu(x, y);
}

function actionFileMenu(x, y) {
    showFileActions(x, y);
}

function actionYTMenu(x, y) {
    showYTMenu(x, y);
}

function actionShazam() {
    fb.RunContextCommand("Run service/Search with Shazam");
}