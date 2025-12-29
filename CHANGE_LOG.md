# Changelog - v.MAJOR.MINOR.PATCH
All notable changes to this project will be documented in this file.

## [Unreleased]
 - tweak hover feature so that it continously follows the mouse instead of just disappearing and reappearing when the mouse stops moving!
 - Add Zoom in/out feature
 - Add settings page to allow user to tweak color, size, shapes of the diagram!

## [v2.2.3] - 29/12/2025
### Added
- Removed parameter text on edges, No more (...args...) drawn between function calls, so large graphs won’t have overlapping argument labels anymore.
- When you hover a node, a small rounded tooltip box appears (grey background + orange border/text) showing:
    ◦  Called with: unique argument lists used to call that function
    ◦  Assigned to: variables that the function call result is assigned to (e.g. result = foo())
- Small UI changed -> All nodes are now rounded rectangles instead of ovals. Custom Logo applied too!
- Added a Hide built-ins checkbox in the top bar.
    •  When enabled, nodes whose names match Python built-ins (e.g. print, len, range, etc.) are filtered out to reduce clutter.

## [v2.1.2] - 18/12/2025
### Added
- Removed Graphviz dependency so flow diagram created would not be image based and instead the app now parses the .py file and renders the flow diagram directly inside the Tkinter window (nodes + arrows + argument labels). It’s not “click/hover interactive” yet, but it is displayed in-app and you can click + drag to pan, plus scrollbars are available.
- Revamped UI Theme, grey background /w orange text. 

### Fixed
- Nothing yet...

## [v1.1.1] - 15/12/2025
### Added
- Added a simple GUI allowing user to drag & drop or upload python files directly. Still produces a .png image however instead of displaying the flow diagram instead the application. 

### Fixed
- Issue with watermark cutting out behind text, removed it all together since on-screen text was sufficient lol!

## [v1.0.1] - 14/12/2025
### Added
- Initial release of ProFlow! Program reads a dummy test script, analyses contents and print out .png image showing program flow!

### Fixed
- Nothing yet...