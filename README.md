# SvnTimestamp

TortoiseSVN 时间戳保存/恢复工具。通过 SVN 自定义属性保存文件的创建时间 (ctime) 和修改时间 (mtime)，在 checkout/update 后自动恢复。

## 功能

- **右键菜单 - 保存时间戳**: 将文件的 ctime/mtime 保存为 SVN 属性 (`svnts:ctime` / `svnts:mtime`)
- **右键菜单 - 恢复时间戳**: 从 SVN 属性恢复文件的 ctime/mtime
- **Pre-commit Hook**: 提交前自动保存时间戳属性
- **Post-update Hook**: 更新/检出后自动恢复时间戳

## 构建

```bash
dotnet build -c Release
dotnet publish src/SvnTimestamp.CLI -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:PublishTrimmed=false
```

构建产物: `src/SvnTimestamp.CLI/bin/Release/net8.0/win-x64/publish/svnts.exe`

## 安装

1. 以管理员身份运行 `scripts\install.bat`
2. 配置 TortoiseSVN Hook (见下方)
3. 右键菜单自动注册

## 卸载

以管理员身份运行 `scripts\uninstall.bat`

## TortoiseSVN Hook 配置

1. 右键任意位置 → **TortoiseSVN** → **Settings**
2. 左侧选择 **Hook Scripts**
3. 点击 **Add...** 添加以下两个 Hook:

### Pre-commit Hook (提交前自动保存时间戳)

| 设置项 | 值 |
|--------|-----|
| Hook Type | `Pre-commit hook` |
| Working Copy Path | 选择工作副本根目录 |
| Command Line | `C:\Program Files\SvnTimestamp\hooks\pre-commit-save.bat` |
| Wait for the script | 勾选 |

### Post-update Hook (更新后自动恢复时间戳)

| 设置项 | 值 |
|--------|-----|
| Hook Type | `Post-update hook` |
| Working Copy Path | 选择工作副本根目录 |
| Command Line | `C:\Program Files\SvnTimestamp\hooks\post-update-restore.bat` |
| Wait for the script | 勾选 |

## 命令行用法

```bash
svnts save <path>              # 保存文件时间戳为 SVN 属性
svnts restore <path>           # 从 SVN 属性恢复文件时间戳
svnts hook-save <args>         # Pre-commit hook 入口
svnts hook-restore <args>      # Post-update hook 入口
svnts --help                   # 显示帮助
```

## 技术细节

- **语言**: C# / .NET 8
- **SVN 操作**: SharpSvn
- **文件时间**: Windows API P/Invoke (GetFileTime / SetFileTime)
- **时间格式**: ISO 8601 UTC (`yyyy-MM-ddTHH:mm:ss.fffZ`)
- **SVN 属性**: `svnts:ctime`, `svnts:mtime`
