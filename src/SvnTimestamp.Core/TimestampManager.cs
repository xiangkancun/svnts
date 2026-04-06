using System.IO;

namespace SvnTimestamp.Core;

public class TimestampManager
{
    public delegate void LogMessageHandler(string message);

    public event LogMessageHandler? Log;

    /// <summary>
    /// Saves ctime/mtime of a single file as SVN properties.
    /// </summary>
    public TimestampResult SaveTimestamps(string filePath)
    {
        if (!File.Exists(filePath))
            return TimestampResult.Fail(filePath, "File does not exist");

        if (!SvnWorkingCopyHelper.IsInWorkingCopy(filePath))
            return TimestampResult.Fail(filePath, "Not in SVN working copy");

        try
        {
            FileTimeHelper.GetFileTimes(filePath, out var ctime, out var mtime);
            var ctimeStr = FileTimeHelper.ToIso8601(ctime);
            var mtimeStr = FileTimeHelper.ToIso8601(mtime);
            SvnPropertyHelper.SetTimestampProperties(filePath, ctimeStr, mtimeStr);
            Log?.Invoke($"Saved: {filePath} (ctime={ctimeStr}, mtime={mtimeStr})");
            return TimestampResult.Ok(filePath);
        }
        catch (UnauthorizedAccessException ex)
        {
            return TimestampResult.Fail(filePath, $"Permission denied: {ex.Message}");
        }
        catch (Exception ex)
        {
            return TimestampResult.Fail(filePath, $"Error: {ex.Message}");
        }
    }

    /// <summary>
    /// Restores ctime/mtime of a single file from SVN properties.
    /// </summary>
    public TimestampResult RestoreTimestamps(string filePath)
    {
        if (!File.Exists(filePath))
            return TimestampResult.Fail(filePath, "File does not exist");

        var (ctimeStr, mtimeStr) = SvnPropertyHelper.GetTimestampProperties(filePath);
        if (ctimeStr == null && mtimeStr == null)
            return TimestampResult.Fail(filePath, "No timestamp properties found");

        try
        {
            var ctime = ctimeStr != null ? FileTimeHelper.FromIso8601(ctimeStr) : DateTime.UtcNow;
            var mtime = mtimeStr != null ? FileTimeHelper.FromIso8601(mtimeStr) : DateTime.UtcNow;
            FileTimeHelper.SetFileTimes(filePath, ctime, mtime);
            Log?.Invoke($"Restored: {filePath} (ctime={ctimeStr}, mtime={mtimeStr})");
            return TimestampResult.Ok(filePath);
        }
        catch (UnauthorizedAccessException ex)
        {
            return TimestampResult.Fail(filePath, $"Permission denied: {ex.Message}");
        }
        catch (Exception ex)
        {
            return TimestampResult.Fail(filePath, $"Error: {ex.Message}");
        }
    }

    /// <summary>
    /// Processes a list of file/directory paths.
    /// Returns the count of successes and failures.
    /// </summary>
    public (int successCount, int failCount) ProcessFiles(string[] filePaths, bool save)
    {
        int success = 0, fail = 0;
        foreach (var path in filePaths)
        {
            var trimmed = path.Trim();
            if (string.IsNullOrEmpty(trimmed)) continue;

            if (File.Exists(trimmed))
            {
                var result = save ? SaveTimestamps(trimmed) : RestoreTimestamps(trimmed);
                if (result.Success) success++; else fail++;
            }
            else if (Directory.Exists(trimmed))
            {
                var (s, f) = ProcessDirectory(trimmed, save);
                success += s;
                fail += f;
            }
            else
            {
                Log?.Invoke($"Skipped (not found): {trimmed}");
                fail++;
            }
        }
        return (success, fail);
    }

    /// <summary>
    /// Recursively processes all files in a directory (skips .svn directories).
    /// </summary>
    private (int successCount, int failCount) ProcessDirectory(string dirPath, bool save)
    {
        int success = 0, fail = 0;
        var svnDir = $"{Path.DirectorySeparatorChar}.svn{Path.DirectorySeparatorChar}";

        foreach (var file in Directory.EnumerateFiles(dirPath, "*", SearchOption.AllDirectories))
        {
            if (file.Contains(svnDir)) continue;

            var result = save ? SaveTimestamps(file) : RestoreTimestamps(file);
            if (result.Success) success++; else fail++;
        }
        return (success, fail);
    }
}
