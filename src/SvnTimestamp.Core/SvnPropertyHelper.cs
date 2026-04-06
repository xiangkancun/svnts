using SharpSvn;

namespace SvnTimestamp.Core;

public static class SvnPropertyHelper
{
    /// <summary>
    /// Gets both svnts:ctime and svnts:mtime properties from a versioned file.
    /// Returns null for any property that does not exist.
    /// </summary>
    public static (string? ctime, string? mtime) GetTimestampProperties(string filePath)
    {
        using var client = new SvnClient();
        string? ctime = null;
        string? mtime = null;

        if (client.GetProperty(filePath, Constants.CtimePropertyName, out var ctimeData))
            ctime = ctimeData?.StringValue;

        if (client.GetProperty(filePath, Constants.MtimePropertyName, out var mtimeData))
            mtime = mtimeData?.StringValue;

        return (ctime, mtime);
    }

    /// <summary>
    /// Sets both svnts:ctime and svnts:mtime properties on a versioned file.
    /// </summary>
    public static void SetTimestampProperties(string filePath, string ctime, string mtime)
    {
        using var client = new SvnClient();
        client.SetProperty(filePath, Constants.CtimePropertyName, ctime);
        client.SetProperty(filePath, Constants.MtimePropertyName, mtime);
    }

    /// <summary>
    /// Checks if a file has at least one timestamp property set.
    /// </summary>
    public static bool HasTimestampProperties(string filePath)
    {
        using var client = new SvnClient();
        return client.GetProperty(filePath, Constants.CtimePropertyName, out _)
            || client.GetProperty(filePath, Constants.MtimePropertyName, out _);
    }
}
