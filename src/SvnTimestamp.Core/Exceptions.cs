namespace SvnTimestamp.Core;

public class SvnTimestampException : Exception
{
    public SvnTimestampException(string message) : base(message) { }
    public SvnTimestampException(string message, Exception inner) : base(message, inner) { }
}

public class NotInWorkingCopyException : SvnTimestampException
{
    public string Path { get; }

    public NotInWorkingCopyException(string path)
        : base($"Path is not in an SVN working copy: {path}")
    {
        Path = path;
    }
}
