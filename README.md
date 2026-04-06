# SvnTimestamp

通过 SVN 自定义属性保存/恢复文件创建时间 (ctime) 和修改时间 (mtime)。

SVN 不跟踪文件时间戳，checkout/update 后时间会被重置。本工具在提交前自动保存时间戳到 SVN 属性，更新后自动恢复。

## 功能

- **Pre-commit Hook**: 提交前自动保存时间戳到 `svnts:ctime` / `svnts:mtime`
- **Post-update Hook**: 更新后自动恢复文件时间戳
- **右键菜单**: 手动保存/恢复（文件、文件夹、文件夹空白处）
- **全盘覆盖**: 自动检测所有本地磁盘

## 安装

```
python svnts.py install
```

或双击 `install.bat`。自动完成：复制文件到 `%USERPROFILE%\svnts\` + 右键菜单 + TortoiseSVN Hooks。

## 卸载

```
python svnts.py uninstall
```

或双击 `uninstall.bat`。移除右键菜单、Hooks 和安装目录。

## 手动使用

```
python svnts.py save <path>       # 保存时间戳
python svnts.py restore <path>    # 恢复时间戳
```

## 技术细节

- **属性存储**: 直接读写 `.svn/wc.db` (SQLite)，零子进程，零 Defender 影响
- **属性格式**: SVN skel 格式 `(key [len] value ...)`，值含空格时带长度前缀
- **时间格式**: `2026-04-06 23:19:58 +0800`（本地时间 + 时区偏移），跨机器一致
- **工作层**: 修改属性时自动创建 working layer (op_depth>0)，svn status/commit 正常识别
- **文件时间**: Win32 API (GetFileTime/SetFileTime)，FileShare.ReadWrite 避免锁定
- **Hook 参数**: pre-commit 第 6 个参数为文件列表路径；post-update 第 5 个参数为工作副本路径
