// foobar2000 Spider Monkey Panel JS2015 - ActivityBar.js
const isDUI = window.InstanceType;
let hovered_idx = -1; let pressed_idx = -1;
let g_fa_font = null; let COLORS = null;

include(fb.ComponentPath + 'docs\\Flags.js');
include(fb.ComponentPath + 'docs\\Helpers.js');
include(fb.ProfilePath + 'ActivityBar\\Config.js');
include(fb.ProfilePath + 'ActivityBar\\Paths.js');
include(fb.ProfilePath + 'ActivityBar\\Core\\ProcessRunner.js');
include(fb.ProfilePath + 'ActivityBar\\Core\\FileSystem.js');
include(fb.ProfilePath + 'ActivityBar\\Core\\Clipboard.js');
include(fb.ProfilePath + 'ActivityBar\\Core\\SelectionUtils.js');
include(fb.ProfilePath + 'ActivityBar\\Core\\MessageUtils.js');
include(fb.ProfilePath + 'ActivityBar\\Actions\\FileActions.js');
include(fb.ProfilePath + 'ActivityBar\\Actions\\YearPaths.js');
include(fb.ProfilePath + 'ActivityBar\\Actions\\YearExplorer.js');
include(fb.ProfilePath + 'ActivityBar\\Actions\\NewgroundsOpener.js');
include(fb.ProfilePath + 'ActivityBar\\UI\\ButtonActions.js');
include(fb.ProfilePath + 'ActivityBar\\UI\\Buttons.js');
include(fb.ProfilePath + 'ActivityBar\\UI\\Renderer.js');
include(fb.ProfilePath + 'ActivityBar\\UI\\MouseHandlers.js');
include(fb.ProfilePath + 'ActivityBar\\Menus\\EffectsMenu.js');
include(fb.ProfilePath + 'ActivityBar\\Menus\\YoutubeMenu.js');
include(fb.ProfilePath + 'ActivityBar\\Menus\\LegacyToolsMenu.js');
include(fb.ProfilePath + 'ActivityBar\\Menus\\GoogleSearcherSongsMenu.js');
include(fb.ProfilePath + 'ActivityBar\\Commands\\MainMenuCommands.js');
