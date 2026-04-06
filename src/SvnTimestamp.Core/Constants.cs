using System.Globalization;

namespace SvnTimestamp.Core;

public static class Constants
{
    /// <summary>SVN custom property name for file creation time.</summary>
    public const string CtimePropertyName = "svnts:ctime";

    /// <summary>SVN custom property name for file modification time.</summary>
    public const string MtimePropertyName = "svnts:mtime";

    /// <summary>ISO 8601 UTC format string with millisecond precision.</summary>
    public const string Iso8601Format = "yyyy-MM-ddTHH:mm:ss.fffZ";

    /// <summary>Culture used for all formatting/parsing to ensure consistency.</summary>
    public static readonly CultureInfo InvariantCulture = CultureInfo.InvariantCulture;

    // Command-line exit codes
    public const int ExitSuccess = 0;
    public const int ExitError = 1;
    public const int ExitPartialError = 2;
}
