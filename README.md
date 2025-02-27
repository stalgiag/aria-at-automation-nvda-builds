# NVDA AT Automation Builds

This repository contains packaged NVDA screen reader builds with the AT Automation Plugin pre-installed and configured for use with AT-Driver in CI workflows.

## Automated Build Process

This repository includes a GitHub Actions workflow that automates the process of creating NVDA portable builds with the AT Automation Plugin. The workflow:

1. Downloads the latest NVDA version (or a specified version)
2. Prepares the AT Automation Plugin
3. Installs NVDA and the plugin
4. Configures NVDA settings:
   - Disables automatic update checking
   - Sets "Capture Speech" as the synthesizer
5. Creates a portable copy of NVDA
6. Tests the portable copy to ensure the AT Automation server works
7. Packages the portable copy as a ZIP file
8. Creates a GitHub release with the packaged NVDA

## Using the Automated Workflow

To create a new NVDA build:

1. Go to the "Actions" tab in the repository
2. Select the "Build NVDA Portable with AT Automation" workflow
3. Click "Run workflow"
4. Optionally specify an NVDA version (leave empty for latest)
5. Click "Run workflow" to start the build process

The workflow will create a new release with the packaged NVDA when complete.

## Manual Build Process (Legacy)

If you need to manually create an NVDA build:

1. Check Prerequisites: Windows installed, NVDA and AT Automation Plugin ready
2. Navigate to 'NVDAPlugin' in the [nvda-at-automation repository](https://github.com/Prime-Access-Consulting/nvda-at-automation) and create a ZIP archive excluding the directory itself
3. Rename ZIP file from .zip to .nvda-addon
4. Install AT Automation Plugin via NVDA menu - navigate to 'Tools' -> 'Add-on store..', click 'Install from external source', select nvda-addon
5. Configure NVDA Settings - disable auto-check for updates, set 'Capture Speech' as synthesizer
6. Create Portable Copy - NVDA menu -> Tools -> Create portable copy, use version number as folder name
7. Package for Distribution - Locate portable NVDA, compress to ZIP, create new release with NVDA version number tag, upload ZIP

## Available Builds

The releases section contains all available NVDA builds with the AT Automation Plugin.

## Releases

The output zip files are hosted in the "Releases" section.

## How to build

* Install NVDA on the local system
* Install the [NVDA Plugin](https://github.com/Prime-Access-Consulting/nvda-at-automation) for speech automation.
* Settings (Ins+N -> Preferences -> Settings):
  * Ensure plugin is loaded.
  * General: Ensure "Automatically check for updates" is disabled.
  * General: Ensure "Notify for pending update on startup" is disabled.
  * Speech: Ensure "Capture Speech" is being used.

* Goto Tools -> Create portable copy from the NVDA task bar icon (or Ins+N)
  * Name the folder the version number from the about screen (I.E. 2023.3.3)
  * Check the "Copy current user configuration" checkbox
  * Use the windows explorer right click -> "Compress to Folder" option.

* Create a [new release on github](https://github.com/bocoup/aria-at-automation-nvda-builds/releases/new).
  * "Choose a tag" -> put in the version number and "create new tag"
  * Release Title: put in the version number
  * Drag the zip file into the "Attach binaries by dropping them here" section of the page.
  