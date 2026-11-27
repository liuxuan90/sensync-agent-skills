# 显式维护

仅用户要求检查、更新或优化时执行；不创建后台任务，不在普通研究中途切换规则。用户提出反馈后，先明确需改行为，修改最小必要模块，记录版本、依据、测试和回滚点，再按授权发布。维护原Skill目录，不生成版本命名的重复安装。

在当前安装目录：

```text
python scripts/manage_skill.py verify
python scripts/manage_skill.py check
python scripts/manage_skill.py update
python scripts/manage_skill.py self-test
python scripts/manage_skill.py backups
python scripts/manage_skill.py rollback --backup <列表中的备份目录名>
```

源固定为liuxuan90/sensync-agent-skills、stable、skills/sensync-lead-intelligence。下载固定提交，校验manifest/文件集合/版本与所有SHA-256，备份在安装同级.sensync-skill-backups。更新不允许覆盖本地改动或额外文件；先把业务文件移出并由维护者审查差异，不用force逃避。备份不自动清理，以免误删恢复点；空间清理由维护者另行处理。

check报告实际变更文件；脚本、Schema、openai配置、SKILL入口与重要资格/证据/联系人/邮件/工作簿流程变更都要求复核，不仅信任远端review声明。在已审查且用户授权范围内使用update --accept-reviewed-changes。拒绝降级，确需旧版可使用经校验备份rollback；回滚前会保留当前版本。

修改文件或回滚后刷新Skill索引/启动新会话；确认版本与实际加载。脚本要求Python3.10+与公网GitHubHTTPS，不需要API Key。无Python的Agent可用原生安装器，需独立核对目录、manifest、可用权限和重载方式；不得声称所有Agent自动兼容。

首次新设备安装按README完成。直接从远端运行下载脚本之前先阅读来源与脚本；校验一致性不消除发布者信任问题。
