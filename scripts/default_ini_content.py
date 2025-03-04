def get_default_ini_content():
    return """
    schemaVersion = 13
    [update]
      allowUsageStats = False
      askedAllowUsageStats = True
      autoCheck = False
      startupNotification = False
    [upgrade]
    [general]
      showWelcomeDialogAtStartup = True
      language = Windows
      saveConfigurationOnExit = True
      askToExit = True
      playStartAndExitSounds = True
      loggingLevel = INFO
    [development]
    [speech]
      synth = captureSpeech
      autoLanguageSwitching = True
      autoDialectSwitching = False
      symbolLevel = 100
      trustVoiceLanguage = True
      reportNormalizedForCharacterNavigation = True
      symbolDictionaries = cldr,
      includeCLDR = True
      delayedCharacterDescriptions = False
      excludedSpeechModes = ,
      outputDevice = Microsoft Sound Mapper
      [[oneCore]]
        voice = HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech_OneCore\Voices\Tokens\MSTTS_V110_enUS_DavidM
        rate = 50
        rateBoost = False
        pitch = 50
        volume = 100
        capPitchChange = 30
        sayCapForCapitals = False
        beepForCapitals = False
        useSpellingFunctionality = True
      [[captureSpeech]]
        voice = en
        variant = max
        rate = 30
        rateBoost = False
        pitch = 40
        inflection = 75
        volume = 100
        capPitchChange = 30
        sayCapForCapitals = False
        beepForCapitals = False
        useSpellingFunctionality = True
    [braille]
      display = auto
      translationTable = en-ueb-g1.ctb
      inputTable = en-ueb-g1.ctb
      mode = followCursors
      expandAtCursor = True
      showCursor = True
      cursorBlink = True
      cursorBlinkRate = 500
      cursorShapeFocus = 192
      cursorShapeReview = 128
      showMessages = 1
      messageTimeout = 4
      tetherTo = auto
      readByParagraph = False
      paragraphStartMarker = ""
      speakOnRouting = False
      wordWrap = True
      focusContextPresentation = changedContext
      [[noBraille]]
    [vision]
      [[NVDAHighlighter]]
        highlightFocus = False
        highlightNavigator = False
        highlightBrowseMode = False
      [[screenCurtain]]
        warnOnLoad = True
        playToggleSounds = True
    [keyboard]
      keyboardLayout = laptop
      NVDAModifierKeys = 6
      speakTypedCharacters = True
      speakTypedWords = False
      speechInterruptForCharacters = True
      speechInterruptForEnter = True
      allowSkimReadingInSayAll = False
      beepForLowercaseWithCapslock = True
      speakCommandKeys = False
      alertForSpellingErrors = True
      handleInjectedKeys = True
      multiPressTimeout = 500
    [addonStore]
      showWarning = True
      automaticUpdates = notify
    [uwpOcr]
      language = en-US
      autoRefresh = False
    [documentFormatting]
      detectFormatAfterCursor = False
      reportFontName = False
      reportFontSize = False
      fontAttributeReporting = 0
      reportFontAttributes = False
      reportSuperscriptsAndSubscripts = False
      reportColor = False
      reportComments = True
      reportBookmarks = True
      reportRevisions = True
      reportEmphasis = False
      reportHighlight = True
      reportAlignment = False
      reportStyle = False
      reportSpellingErrors = True
      reportPage = True
      reportLineNumber = False
      reportLineIndentation = 0
      ignoreBlankLinesForRLI = False
      reportParagraphIndentation = False
      reportLineSpacing = False
      reportTables = True
      reportTableHeaders = 1
      reportTableCellCoords = True
      reportCellBorders = 0
      reportLinks = True
      reportGraphics = True
      reportHeadings = True
      reportLists = True
      reportBlockQuotes = True
      reportGroupings = True
      reportLandmarks = True
      reportArticles = False
      reportFrames = True
      reportFigures = True
      reportClickable = True
      includeLayoutTables = False
    [virtualBuffers]
      maxLineLength = 100
      linesPerPage = 25
      useScreenLayout = True
      enableOnPageLoad = True
      autoSayAllOnPageLoad = True
      autoPassThroughOnFocusChange = True
      autoPassThroughOnCaretMove = False
      passThroughAudioIndication = True
      trapNonCommandGestures = True
      autoFocusFocusableElements = False
    [presentation]
      reportTooltips = False
      reportHelpBalloons = True
      reportKeyboardShortcuts = True
      reportObjectPositionInformation = True
      guessObjectPositionInformationWhenUnavailable = False
      reportObjectDescriptions = True
      reportDynamicContentChanges = True
      reportAutoSuggestionsWithSound = True
      [[progressBarUpdates]]
        progressBarOutputMode = beep
        reportBackgroundProgressBars = False
    [inputComposition]
      autoReportAllCandidates = True
      announceSelectedCandidate = True
      alwaysIncludeShortCharacterDescriptionInCandidateName = True
      reportReadingStringChanges = True
      reportCompositionStringChanges = True
    [reviewCursor]
      followFocus = True
      followCaret = True
      followMouse = False
      simpleReviewMode = True
    [mouse]
      reportMouseShapeChanges = False
      enableMouseTracking = True
      mouseTextUnit = paragraph
      reportObjectRoleOnMouseEnter = False
      audioCoordinatesOnMouseMove = False
      audioCoordinates_detectBrightness = False
      ignoreInjectedMouseInput = False
    [audio]
      soundVolumeFollowsVoice = False
      soundVolume = 100
      soundSplitState = 0
      includedSoundSplitModes = 0, 2, 3
      audioDuckingMode = 0
      audioAwakeTime = 30
    [speechViewer]
      x = 96
      y = 96
      width = 500
      height = 500
      displays = "(1920, 1080)",
      autoPositionWindow = False
      """
