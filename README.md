# aria-at-automation-nvda-builds

This project is used to host the nvda portable zip files for the aria-at process.

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
  