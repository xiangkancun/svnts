using System.IO;
using SvnTimestamp.Core;

namespace SvnTimestamp.CLI;

class Program
{
    static int Main(string[] args)
    {
        if (args.Length == 0)
        {
            PrintUsage();
            return Constants.ExitError;
        }

        try
        {
            return args[0].ToLowerInvariant() switch
            {
                "save" => HandleSave(args.Skip(1).ToArray()),
                "restore" => HandleRestore(args.Skip(1).ToArray()),
                "hook-save" => HandleHookSave(args.Skip(1).ToArray()),
                "hook-restore" => HandleHookRestore(args.Skip(1).ToArray()),
                "--help" or "-h" or "help" => PrintUsageReturn(),
                _ => UnknownCommand(args[0])
            };
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"Fatal error: {ex.Message}");
            return Constants.ExitError;
        }
    }

    /// <summary>
    /// Context menu "Save Timestamps": svnts save "C:\path\to\file"
    /// </summary>
    static int HandleSave(string[] paths)
    {
        if (paths.Length == 0)
        {
            PrintUsage();
            return Constants.ExitError;
        }

        var manager = new TimestampManager();
        manager.Log += msg => Console.WriteLine(msg);

        var (success, fail) = manager.ProcessFiles(paths, save: true);
        Console.WriteLine($"Done: {success} saved, {fail} failed.");
        return fail > 0 ? Constants.ExitPartialError : Constants.ExitSuccess;
    }

    /// <summary>
    /// Context menu "Restore Timestamps": svnts restore "C:\path\to\file"
    /// </summary>
    static int HandleRestore(string[] paths)
    {
        if (paths.Length == 0)
        {
            PrintUsage();
            return Constants.ExitError;
        }

        var manager = new TimestampManager();
        manager.Log += msg => Console.WriteLine(msg);

        var (success, fail) = manager.ProcessFiles(paths, save: false);
        Console.WriteLine($"Done: {success} restored, {fail} failed.");
        return fail > 0 ? Constants.ExitPartialError : Constants.ExitSuccess;
    }

    /// <summary>
    /// Pre-commit hook entry point.
    /// TortoiseSVN passes: PATH DEPTH MESSAGEFILE CWD
    /// PATH = temp file with newline-delimited file list
    /// Always returns 0 (never block a commit).
    /// </summary>
    static int HandleHookSave(string[] hookArgs)
    {
        if (hookArgs.Length < 1)
        {
            Console.Error.WriteLine("hook-save requires PATH argument from TortoiseSVN");
            return Constants.ExitSuccess; // don't block commit
        }

        string pathFile = hookArgs[0];

        if (!File.Exists(pathFile))
            return Constants.ExitSuccess;

        var filePaths = File.ReadAllLines(pathFile)
            .Where(p => !string.IsNullOrWhiteSpace(p))
            .ToArray();

        if (filePaths.Length == 0) return Constants.ExitSuccess;

        var manager = new TimestampManager();
        manager.Log += msg => Console.WriteLine(msg);

        var (success, fail) = manager.ProcessFiles(filePaths, save: true);
        Console.WriteLine($"Pre-commit: saved {success} files ({fail} skipped)");
        return Constants.ExitSuccess; // always succeed
    }

    /// <summary>
    /// Post-update hook entry point.
    /// TortoiseSVN passes: PATH DEPTH REVISION ERROR CWD RESULTPATH
    /// RESULTPATH (index 5) = temp file with actually updated file list.
    /// </summary>
    static int HandleHookRestore(string[] hookArgs)
    {
        string? resultPathFile = null;

        if (hookArgs.Length >= 6)
            resultPathFile = hookArgs[5];
        else if (hookArgs.Length >= 1)
            resultPathFile = hookArgs[0]; // fallback

        if (resultPathFile == null || !File.Exists(resultPathFile))
            return Constants.ExitSuccess;

        var filePaths = File.ReadAllLines(resultPathFile)
            .Where(p => !string.IsNullOrWhiteSpace(p))
            .ToArray();

        if (filePaths.Length == 0) return Constants.ExitSuccess;

        var manager = new TimestampManager();
        manager.Log += msg => Console.WriteLine(msg);

        var (success, fail) = manager.ProcessFiles(filePaths, save: false);
        Console.WriteLine($"Post-update: restored {success} files ({fail} skipped)");
        return Constants.ExitSuccess;
    }

    static void PrintUsage()
    {
        Console.WriteLine(@"SvnTimestamp - Save/Restore file timestamps via SVN properties

Usage:
  svnts save <path> [path2 ...]             Save ctime/mtime as SVN properties
  svnts restore <path> [path2 ...]          Restore ctime/mtime from SVN properties
  svnts hook-save <PATH> <DEPTH> <MSG> <CWD>            Pre-commit hook
  svnts hook-restore <PATH> <DEPTH> <REV> <ERR> <CWD> <RESULT>  Post-update hook
  svnts --help                               Show this help

Hook configuration (TortoiseSVN Settings > Hook Scripts):
  Pre-commit:  svnts.exe hook-save %1 %2 %3 %4
  Post-update: svnts.exe hook-restore %1 %2 %3 %4 %5 %6");
    }

    static int PrintUsageReturn() { PrintUsage(); return Constants.ExitSuccess; }
    static int UnknownCommand(string cmd) { Console.Error.WriteLine($"Unknown command: {cmd}"); PrintUsage(); return Constants.ExitError; }
}
