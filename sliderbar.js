// foobar2000 Spider Monkey Panel JS2015 - Sliderbar.js
const isDUI = window.InstanceType;
let hovered_idx = -1; let pressed_idx = -1;
let g_fa_font = null; let COLORS = null;

include(fb.ComponentPath + 'docs\\Flags.js');
include(fb.ComponentPath + 'docs\\Helpers.js');
include(fb.ProfilePath + 'Sliderbar\\Config.js');
include(fb.ProfilePath + 'Sliderbar\\Paths.js');
include(fb.ProfilePath + 'Sliderbar\\Core\\ProcessRunner.js');
include(fb.ProfilePath + 'Sliderbar\\Core\\FileSystem.js');
include(fb.ProfilePath + 'Sliderbar\\Core\\Clipboard.js');
include(fb.ProfilePath + 'Sliderbar\\Core\\SelectionUtils.js');
include(fb.ProfilePath + 'Sliderbar\\Core\\MessageUtils.js');
include(fb.ProfilePath + 'Sliderbar\\Actions\\FileActions.js');
include(fb.ProfilePath + 'Sliderbar\\Actions\\YearPaths.js');
include(fb.ProfilePath + 'Sliderbar\\Actions\\YearExplorer.js');
include(fb.ProfilePath + 'Sliderbar\\Actions\\NewgroundsOpener.js');
include(fb.ProfilePath + 'Sliderbar\\UI\\ButtonActions.js');
include(fb.ProfilePath + 'Sliderbar\\UI\\Buttons.js');
include(fb.ProfilePath + 'Sliderbar\\UI\\Renderer.js');
include(fb.ProfilePath + 'Sliderbar\\UI\\MouseHandlers.js');
include(fb.ProfilePath + 'Sliderbar\\Menus\\EffectsMenu.js');
include(fb.ProfilePath + 'Sliderbar\\Menus\\YoutubeMenu.js');
include(fb.ProfilePath + 'Sliderbar\\Menus\\LegacyToolsMenu.js');
include(fb.ProfilePath + 'Sliderbar\\Commands\\MainMenuCommands.js');
