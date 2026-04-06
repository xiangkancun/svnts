namespace SvnTimestamp.Core;

public class TimestampResult
{
    public string FilePath { get; }
    public bool Success { get; }
    public string? ErrorMessage { get; }

    private TimestampResult(string filePath, bool success, string? errorMessage)
    {
        FilePath = filePath;
        Success = success;
        ErrorMessage = errorMessage;
    }

    public static TimestampResult Ok(string filePath) => new(filePath, true, null);

    public static TimestampResult Fail(string filePath, string error) => new(filePath, false, error);
}
