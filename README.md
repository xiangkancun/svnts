# SvnTimestamp

TortoiseSVN 时间戳保存/恢复工具。通过 SVN 自定义属性保存文件的创建时间 (ctime) 和修改时间 (mtime)，在 checkout/update 后自动恢复。

## 功能

- **右键菜单 - 保存时间戳**: 将文件的 ctime/mtime 保存为 SVN 属性 (`svnts:ctime` / `svnts:mtime`)
- **右键菜单 - 恢复时间戳**: 从 SVN 属性恢复文件的 ctime/mtime
- **Pre-commit Hook**: 提交前自动保存时间戳属性
- **Post-update Hook**: 更新/检出后自动恢复时间戳

## 安装

以管理员身份运行项目根目录的 `install.bat`，自动完成：
1. `pip install -e .` 安装 Python 包
2. 注册右键菜单（文件 + 目录）

也可手动分步执行：
```bash
pip install -e .
scripts\registry\install-context-menu.bat   # 仅注册右键菜单
```

## 卸载

以管理员身份运行项目根目录的 `uninstall.bat`，自动完成：
1. 移除右键菜单注册表项
2. `pip uninstall svnts` 卸载 Python 包
3. 清理 pip 缓存

> 注意：TortoiseSVN Hook 配置需手动移除（Settings → Hook Scripts → 删除对应条目）。

## TortoiseSVN Hook 配置

1. 右键任意位置 → **TortoiseSVN** → **Settings**
2. 左侧选择 **Hook Scripts**
3. 点击 **Add...** 添加以下两个 Hook:

### Pre-commit Hook (提交前自动保存时间戳)

| 设置项 | 值 |
|--------|-----|
| Hook Type | `Pre-commit hook` |
| Working Copy Path | 选择工作副本根目录 |
| Command Line | `scripts\hooks\pre-commit-save.bat` |
| Wait for the script | 勾选 |

### Post-update Hook (更新后自动恢复时间戳)

| 设置项 | 值 |
|--------|-----|
| Hook Type | `Post-update hook` |
| Working Copy Path | 选择工作副本根目录 |
| Command Line | `scripts\hooks\post-update-restore.bat` |
| Wait for the script | 勾选 |

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
