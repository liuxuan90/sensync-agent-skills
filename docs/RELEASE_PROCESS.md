# 发布流程

1. 在main修改规则；保持用户授权范围，更新SKILL metadata.version和CHANGELOG，使用SemVer。兼容修复patch、兼容扩展minor、不兼容结构/行为major。
2. 更新结构版本/评分版本仅在其语义实际改变时进行，不机械跟随Skill版本。更新示例、引用与公司资料来源。
3. `python tools/build_skill_manifest.py --change-types rules,scripts --review-required`生成清单；普通资料修订用准确类型，不能隐瞒脚本/权限/流程变更。
4. 检查命名/frontmatter、Schema、相对链接、`manage_skill.py verify`和`self-test`、业务验证器；条件允许用真实小样本与Excel验收。记录实际检查，不把计划当结果。
5. 按`publish-files.json`明确允许清单审查全部提交文件与diff。禁止客户/联系人/价格利润/销售记录/凭据；.gitignore不是全部保障。
6. 审核具体变更，尤其脚本、依赖、权限、资格和流程，将审核提交推进stable，建立vX.Y.Z标签。不能强推抹历史。公开发布与用户授权保持一致。
7. 远端回读stable，验证固定提交manifest与实际包SHA-256，隔离安装/检查/更新与加载。当前会话读取文件不等于新会话发现成功。

回滚：本地激活失败自动恢复；成功更新的备份由维护脚本列出并显式恢复。发布错误以纠正提交/补丁版处理，不强推删除发布历史。保留上一已知良好包，绝不把客户资料放进安装目录。
