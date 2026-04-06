# SvnTimestamp

TortoiseSVN 时间戳保存/恢复工具。通过 SVN 自定义属性保存文件的创建时间 (ctime) 和修改时间 (mtime)，在 checkout/update 后自动恢复。

## 功能

- **右键菜单 - 保存时间戳**: 将文件的 ctime/mtime 保存为 SVN 属性 (`svnts:ctime` / `svnts:mtime`)
- **右键菜单 - 恢复时间戳**: 从 SVN 属性恢复文件的 ctime/mtime
- **Pre-commit Hook**: 提交前自动保存时间戳属性
- **Post-update Hook**: 更新/检出后自动恢复时间戳

## 安装

双击项目根目录的 `install.bat`，自动完成：
1. `pip install -e .` 安装 Python 包
2. 注册右键菜单（文件 + 目录）
3. 配置 TortoiseSVN Hooks（pre-commit + post-update）

## 卸载

双击项目根目录的 `uninstall.bat`，自动完成：
1. 移除右键菜单注册表项
2. 移除 TortoiseSVN Hooks
3. `pip uninstall svnts` 卸载 Python 包

## 命令行用法

```bash
svnts save <path>              # 保存文件时间戳为 SVN 属性
svnts restore <path>           # 从 SVN 属性恢复文件时间戳
svnts hook-save <args>         # Pre-commit hook 入口
svnts hook-restore <args>      # Post-update hook 入口
svnts --help                   # 显示帮助
```

## 运行测试

```bash
python -m pytest tests/ -v
```

## 技术细节

- **语言**: Python 3.8+
- **文件时间**: Windows API (GetFileTime / SetFileTime) via ctypes
- **SVN 操作**: svn 命令行
- **时间格式**: ISO 8601 UTC (`yyyy-MM-ddTHH:mm:ss.ffffffZ`)
- **SVN 属性**: `svnts:ctime`, `svnts:mtime`
