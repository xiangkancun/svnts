# SvnTimestamp

通过 SVN 自定义属性保存/恢复文件创建时间 (ctime) 和修改时间 (mtime)。

## 功能

- **右键菜单**: 保存/恢复文件时间戳
- **Pre-commit Hook**: 提交前自动保存时间戳
- **Post-update Hook**: 更新后自动恢复时间戳

## 安装 / 卸载

双击 `install.bat` 或 `uninstall.bat`。

自动完成：右键菜单 + TortoiseSVN Hooks（所有本地磁盘）+ 无需 pip。

## 命令行

```bash
python svnts.py save <path>       # 保存时间戳
python svnts.py restore <path>    # 恢复时间戳
python svnts.py install           # 注册菜单+钩子
python svnts.py uninstall         # 注销一切
```
