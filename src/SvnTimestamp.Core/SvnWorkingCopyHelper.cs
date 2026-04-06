using System.IO;

namespace SvnTimestamp.Core;

public static class SvnWorkingCopyHelper
{
    /// <summary>
    /// Checks if a path is inside an SVN working copy by looking for .svn directory.
    /// Walks up parent directories to find the working copy root.
    /// </summary>
    public static bool IsInWorkingCopy(string path)
    {
        var dirInfo = new DirectoryInfo(path);
        if (!dirInfo.Exists) return false;
        if (dirInfo.Attributes.HasFlag(FileAttributes.Directory))
            return ContainsSvnDir(dirInfo);
        return dirInfo.Parent != null && ContainsSvnDir(dirInfo.Parent);
    }

    /// <summary>
    /// Gets the SVN working copy root directory.
    /// Returns null if not in a working copy.
    /// </summary>
    public static string? GetWorkingCopyRoot(string path)
    {
        var dirInfo = new DirectoryInfo(path);
        if (!dirInfo.Exists) return null;
        if (!dirInfo.Attributes.HasFlag(FileAttributes.Directory))
            dirInfo = dirInfo.Parent!;

        while (dirInfo != null)
        {
            if (Directory.Exists(Path.Combine(dirInfo.FullName, ".svn")))
                return dirInfo.FullName;
            dirInfo = dirInfo.Parent;
        }
        return null;
    }

    private static bool ContainsSvnDir(DirectoryInfo dir)
    {
        var current = dir;
        while (current != null)
        {
            if (Directory.Exists(Path.Combine(current.FullName, ".svn")))
                return true;
            current = current.Parent;
        }
        return false;
    }
}
