using System.ComponentModel;
using System.Globalization;
using System.Runtime.InteropServices;

namespace SvnTimestamp.Core;

public static class FileTimeHelper
{
    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetFileTime(
        IntPtr hFile,
        out long lpCreationTime,
        out long lpLastAccessTime,
        out long lpLastWriteTime);

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool SetFileTime(
        IntPtr hFile,
        in long lpCreationTime,
        in long lpLastAccessTime,
        in long lpLastWriteTime);

    /// <summary>
    /// Reads file creation time and modification time using Win32 API.
    /// Returns UTC DateTime values.
    /// </summary>
    public static void GetFileTimes(string filePath, out DateTime creationTime, out DateTime modificationTime)
    {
        using var fs = new FileStream(filePath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite);
        var handle = fs.SafeFileHandle.DangerousGetHandle();
        if (!GetFileTime(handle, out var ctime, out var atime, out var mtime))
            throw new Win32Exception(Marshal.GetLastWin32Error());

        creationTime = DateTime.FromFileTimeUtc(ctime);
        modificationTime = DateTime.FromFileTimeUtc(mtime);
    }

    /// <summary>
    /// Sets file creation time and modification time using Win32 API.
    /// Input DateTime values should be UTC.
    /// </summary>
    public static void SetFileTimes(string filePath, DateTime creationTime, DateTime modificationTime)
    {
        using var fs = new FileStream(filePath, FileMode.Open, FileAccess.Write, FileShare.ReadWrite);
        var handle = fs.SafeFileHandle.DangerousGetHandle();

        long ctime = creationTime.ToFileTimeUtc();
        long atime = DateTime.UtcNow.ToFileTimeUtc(); // keep current access time
        long mtime = modificationTime.ToFileTimeUtc();

        if (!SetFileTime(handle, in ctime, in atime, in mtime))
            throw new Win32Exception(Marshal.GetLastWin32Error());
    }

    /// <summary>
    /// Converts a DateTime to ISO 8601 UTC string (e.g. "2024-01-15T14:30:00.123Z").
    /// </summary>
    public static string ToIso8601(DateTime dateTime)
        => dateTime.ToUniversalTime().ToString(Constants.Iso8601Format, Constants.InvariantCulture);

    /// <summary>
    /// Parses an ISO 8601 UTC string to DateTime.
    /// </summary>
    public static DateTime FromIso8601(string isoString)
        => DateTime.Parse(isoString, Constants.InvariantCulture,
            DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal);
}
