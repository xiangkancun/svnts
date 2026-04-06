using System.IO;
using SvnTimestamp.Core;
using Xunit;

namespace SvnTimestamp.Core.Tests;

public class SvnWorkingCopyHelperTests
{
    [Fact]
    public void IsInWorkingCopy_WithSvnDir_ReturnsTrue()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"svnts_test_{Guid.NewGuid():N}");
        var svnDir = Path.Combine(tempDir, ".svn");
        try
        {
            Directory.CreateDirectory(svnDir);
            Assert.True(SvnWorkingCopyHelper.IsInWorkingCopy(tempDir));
        }
        finally
        {
            Directory.Delete(tempDir, true);
        }
    }

    [Fact]
    public void IsInWorkingCopy_WithoutSvnDir_ReturnsFalse()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"svnts_test_{Guid.NewGuid():N}");
        try
        {
            Directory.CreateDirectory(tempDir);
            Assert.False(SvnWorkingCopyHelper.IsInWorkingCopy(tempDir));
        }
        finally
        {
            Directory.Delete(tempDir, true);
        }
    }

    [Fact]
    public void IsInWorkingCopy_NestedInSvnDir_ReturnsTrue()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"svnts_test_{Guid.NewGuid():N}");
        var svnDir = Path.Combine(tempDir, ".svn");
        var subDir = Path.Combine(tempDir, "src", "project");
        try
        {
            Directory.CreateDirectory(svnDir);
            Directory.CreateDirectory(subDir);
            Assert.True(SvnWorkingCopyHelper.IsInWorkingCopy(subDir));
        }
        finally
        {
            Directory.Delete(tempDir, true);
        }
    }

    [Fact]
    public void IsInWorkingCopy_FileInWorkingCopy_ReturnsTrue()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"svnts_test_{Guid.NewGuid():N}");
        var svnDir = Path.Combine(tempDir, ".svn");
        var file = Path.Combine(tempDir, "test.txt");
        try
        {
            Directory.CreateDirectory(svnDir);
            File.WriteAllText(file, "test");
            Assert.True(SvnWorkingCopyHelper.IsInWorkingCopy(file));
        }
        finally
        {
            Directory.Delete(tempDir, true);
        }
    }

    [Fact]
    public void GetWorkingCopyRoot_ReturnsRoot()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"svnts_test_{Guid.NewGuid():N}");
        var svnDir = Path.Combine(tempDir, ".svn");
        try
        {
            Directory.CreateDirectory(svnDir);
            var root = SvnWorkingCopyHelper.GetWorkingCopyRoot(tempDir);
            Assert.Equal(tempDir, root);
        }
        finally
        {
            Directory.Delete(tempDir, true);
        }
    }

    [Fact]
    public void GetWorkingCopyRoot_NotInWorkingCopy_ReturnsNull()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"svnts_test_{Guid.NewGuid():N}");
        try
        {
            Directory.CreateDirectory(tempDir);
            var root = SvnWorkingCopyHelper.GetWorkingCopyRoot(tempDir);
            Assert.Null(root);
        }
        finally
        {
            Directory.Delete(tempDir, true);
        }
    }
}
