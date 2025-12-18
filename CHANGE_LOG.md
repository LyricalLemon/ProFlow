# Changelog - v.MAJOR.MINOR.PATCH
All notable changes to this project will be documented in this file.

## [Unreleased]
 - Clean up edge variables, implement mouse-hover feature to display variables/parameters instead. 
 - Add Zoom in/out feature
 - Add Cleaner UI, use rectangles with rounded edges instead of pure ovals for cleaner look.
 - Add settings page to allow user to tweak color, size, shapes of the diagram!

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