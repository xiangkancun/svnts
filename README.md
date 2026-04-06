# SvnTimestamp

通过 SVN 自定义属性保存/恢复文件创建时间 (ctime) 和修改时间 (mtime)。

SVN 不跟踪文件时间戳，checkout/update 后时间会被重置。本工具在提交前自动保存时间戳到 SVN 属性，更新后自动恢复。

## 功能

- **Pre-commit Hook**: 提交前自动保存时间戳到 `svnts:ctime` / `svnts:mtime`
- **Post-update Hook**: 更新后自动恢复文件时间戳
- **右键菜单**: 手动保存/恢复时间戳（文件、文件夹、文件夹空白处）
- **全盘覆盖**: 自动检测所有本地磁盘，无需手动配置路径

## 安装

```
python svnts.py install
```

或双击 `install.bat`。

自动完成：复制文件到 `%USERPROFILE%\svnts\` + 右键菜单 + TortoiseSVN Hooks。

## 卸载

```
python svnts.py uninstall
```

或双击 `uninstall.bat`。移除右键菜单、TortoiseSVN Hooks 和安装目录。

## 手动使用

```
python svnts.py save <path>       # 保存时间戳
python svnts.py restore <path>    # 恢复时间戳
```

## 时间戳格式

`2026-04-06 23:19:58 +0800`（本地时间 + 时区偏移），跨机器一致。
