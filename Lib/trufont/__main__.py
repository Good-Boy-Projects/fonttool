import os
import sys

from PySide6.QtCore import QCommandLineParser, QLibraryInfo, QLocale, Qt, QTranslator
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

print("CHECKPOINT 0: PySide6 imports done", flush=True)

from defconQt import representationFactories as baseRepresentationFactories

print("CHECKPOINT 0a: defconQt.representationFactories imported", flush=True)

from trufont import __version__, representationFactories

print("CHECKPOINT 0b: trufont.representationFactories imported", flush=True)

from trufont.objects import settings

print("CHECKPOINT 0c: trufont.objects.settings imported", flush=True)

from trufont.objects.application import Application

print("CHECKPOINT 0d: trufont.objects.application.Application imported", flush=True)

from trufont.objects.extension import TExtension
from trufont.resources import icons_db  # noqa

print("CHECKPOINT 0e: icons_db imported", flush=True)

from trufont.tools import errorReports, platformSpecific
from trufont.windows.outputWindow import OutputWindow

print("CHECKPOINT 1: all imports complete", flush=True)


def main():
    global app

    # Exception handling
    sys.excepthook = errorReports.exceptionCallback
    print("CHECKPOINT 2: excepthook set", flush=True)

    # register representation factories
    baseRepresentationFactories.registerAllFactories()
    print("CHECKPOINT 3: baseRepresentationFactories registered", flush=True)

    representationFactories.registerAllFactories()
    print("CHECKPOINT 4: trufont representationFactories registered", flush=True)

    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    print("CHECKPOINT 5: high DPI attribute set", flush=True)

    platformSpecific.setAppName()
    print("CHECKPOINT 6: app name set", flush=True)

    # initialize the app
    app = Application(sys.argv)
    print("CHECKPOINT 7: Application constructed", flush=True)

    app.setOrganizationName("TruFont")
    app.setOrganizationDomain("trufont.github.io")
    app.setApplicationName("TruFont")
    app.setApplicationVersion(__version__)
    print("CHECKPOINT 8: app metadata set", flush=True)

    app.setWindowIcon(QIcon(":app.png"))
    print("CHECKPOINT 9: window icon set (first QIcon/QPixmap-adjacent call)", flush=True)

    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    appFont = platformSpecific.UIFontOverride()
    if appFont is not None:
        app.setFont(appFont)
    print("CHECKPOINT 10: font override applied", flush=True)

    app.setStyleSheet(platformSpecific.appStyleSheet())
    print("CHECKPOINT 11: stylesheet applied", flush=True)

    # Install stream redirection
    app.outputWindow = OutputWindow()
    print("CHECKPOINT 12: OutputWindow constructed", flush=True)

    # Qt's translation for itself. May not be installed.
    qtTranslator = QTranslator()
    qtTranslator.load(
        "qt_" + QLocale.system().name(),
        QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath),
    )
    app.installTranslator(qtTranslator)
    print("CHECKPOINT 13: qt translator installed", flush=True)

    appTranslator = QTranslator()
    appTranslator.load(
        "trufont_" + QLocale.system().name(),
        os.path.dirname(os.path.realpath(__file__)) + "/resources",
    )
    app.installTranslator(appTranslator)
    print("CHECKPOINT 14: app translator installed", flush=True)

    # parse options and open fonts
    parser = QCommandLineParser()
    parser.setApplicationDescription(
        QApplication.translate("Command-line parser", "The TruFont font editor.")
    )
    parser.addHelpOption()
    parser.addVersionOption()
    parser.addPositionalArgument(
        QApplication.translate("Command-line parser", "files"),
        QApplication.translate("Command-line parser", "The UFO files to open."),
    )
    parser.process(app)
    print("CHECKPOINT 15: command line parsed", flush=True)

    # load menu
    if platformSpecific.useGlobalMenuBar():
        app.fetchMenuBar()
        app.setQuitOnLastWindowClosed(False)
    print("CHECKPOINT 16: menu bar handled", flush=True)

    # bootstrap extensions
    folder = app.getExtensionsDirectory()
    for file in os.listdir(folder):
        if not file.rstrip("\\/ ").endswith(".tfExt"):
            continue
        path = os.path.join(folder, file)
        try:
            extension = TExtension(path)
            if extension.launchAtStartup:
                extension.run()
        except Exception as e:
            msg = QApplication.translate(
                "Extensions", f"The extension at {path} could not be run."
            )
            errorReports.showWarningException(e, msg)
            continue
        app.registerExtension(extension)
    print("CHECKPOINT 17: extensions bootstrapped", flush=True)

    # process files
    args = parser.positionalArguments()
    if not args:
        # maybe load recent file
        loadRecentFile = settings.loadRecentFile()
        if loadRecentFile:
            recentFiles = settings.recentFiles()
            if len(recentFiles) and os.path.exists(recentFiles[0]):
                app.openFile(recentFiles[0])
    else:
        for fontPath in args:
            app.openFile(fontPath)
    print("CHECKPOINT 18: files processed", flush=True)

    # if we did not open a font, spawn new font or go headless
    if not app.allFonts():
        if platformSpecific.shouldSpawnDocument():
            app.newFile()
        else:
            # HACK: on OSX we may want to trigger native QMenuBar display
            # without opening any window. Since Qt infers new menu bar on
            # focus change, fire the signal.
            app.focusWindowChanged.emit(None)
    print("CHECKPOINT 19: document spawned, entering event loop", flush=True)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()