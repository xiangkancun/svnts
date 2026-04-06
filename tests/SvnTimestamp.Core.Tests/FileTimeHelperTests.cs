using System;
using System.IO;
using SvnTimestamp.Core;
using Xunit;

namespace SvnTimestamp.Core.Tests;

public class FileTimeHelperTests
{
    [Fact]
    public void ToIso8601_And_FromIso8601_RoundTrip()
    {
        var original = new DateTime(2024, 6, 15, 14, 30, 45, 123, DateTimeKind.Utc);
        var iso = FileTimeHelper.ToIso8601(original);
        var result = FileTimeHelper.FromIso8601(iso);

        Assert.Equal(original, result);
        Assert.EndsWith("Z", iso);
    }

    [Fact]
    public void ToIso8601_LocalTime_ConvertsToUtc()
    {
        var local = new DateTime(2024, 1, 1, 0, 0, 0, DateTimeKind.Local);
        var iso = FileTimeHelper.ToIso8601(local);
        var parsed = FileTimeHelper.FromIso8601(iso);

        Assert.Equal(DateTimeKind.Utc, parsed.Kind);
    }

    [Fact]
    public void FromIso8601_ValidFormat_Parses()
    {
        var result = FileTimeHelper.FromIso8601("2024-06-15T14:30:45.123Z");
        Assert.Equal(new DateTime(2024, 6, 15, 14, 30, 45, 123, DateTimeKind.Utc), result);
    }

    [Fact]
    public void GetFileTimes_And_SetFileTimes_RoundTrip()
    {
        var tempFile = Path.GetTempFileName();
        try
        {
            // Set known times
            var targetCtime = new DateTime(2023, 3, 15, 10, 20, 30, DateTimeKind.Utc);
            var targetMtime = new DateTime(2023, 5, 20, 14, 25, 35, DateTimeKind.Utc);
            FileTimeHelper.SetFileTimes(tempFile, targetCtime, targetMtime);

            // Read back
            FileTimeHelper.GetFileTimes(tempFile, out var ctime, out var mtime);

            // ctime may not be settable on all filesystems, so check mtime at minimum
            Assert.Equal(targetMtime, mtime);
        }
        finally
        {
            File.Delete(tempFile);
        }
    }

    [Fact]
    public void GetFileTimes_NonExistentFile_Throws()
    {
        Assert.Throws<FileNotFoundException>(() =>
            FileTimeHelper.GetFileTimes("C:\\__nonexistent_file_12345__", out _, out _));
    }

    [Fact]
    public void ToIso8601_ContainsMilliseconds()
    {
        var dt = new DateTime(2024, 1, 1, 12, 0, 0, 500, DateTimeKind.Utc);
        var iso = FileTimeHelper.ToIso8601(dt);
        Assert.Contains(".500", iso);
    }
}
