# Sensync Agent Skills

东莞市智感机械电子科技有限公司（Dongguan Sensync Technology Ltd.）海外B2B客户开发与商业情报。

正式Skill：**sensync-lead-intelligence** · 版本 **v1.0.1**

覆盖自动化绕线设备、定制电子线圈、RFID玻璃管芯片、RFID动物耳标。统一企业档案，按具体产品机会研究；默认交付一个包含六张中文工作表的Excel，机会与证据列并入企业背调。国家、产品重点与数量由使用者指定。

## 交给Agent安装

将下面这段发给支持Agent Skills及文件访问的Agent：

```text
从 https://github.com/liuxuan90/sensync-agent-skills 的 stable 分支安装
skills/sensync-lead-intelligence，保留整个Skill目录及相对结构。
使用当前Agent实际支持的Skill安装目录，不要假定所有Agent使用Codex路径。
安装前阅读README和SKILL.md，安装后检查release-manifest.json全部SHA-256，
运行python scripts/manage_skill.py verify；刷新Skill索引或开启新会话后确认可调用。
不要修改Hispeed或其他Skill，不要把客户数据放进安装目录或GitHub仓库。
```

### Codex

使用Codex的Skill Installer：

```text
$skill-installer 安装 https://github.com/liuxuan90/sensync-agent-skills/tree/stable/skills/sensync-lead-intelligence
```

有官方安装脚本的环境也可运行（按实际环境替换路径）：

```text
python <Codex技能目录>/.system/skill-installer/scripts/install-skill-from-github.py --repo liuxuan90/sensync-agent-skills --ref stable --path skills/sensync-lead-intelligence
```

### 其他兼容Agent

用其原生Skill管理器安装上述GitHub子目录；或获取stable快照，仅把`skills/sensync-lead-intelligence`完整复制到其技能目录。不要把整个仓库当作一个Skill，不要只复制SKILL.md。若Agent不支持技能发现，可让其读取SKILL.md并按相对链接加载references。公开可下载不代表所有Agent都有搜索、文件写入、Python或Excel工具，运行时按实际能力记录限制。

纯研究指令无专有工具依赖。维护脚本要求Python3.10+和GitHub HTTPS；验证数据形状可选用JSON Schema工具。Excel可用Agent现有工作簿工具或库生成，不自动安装依赖或发送邮件。

## 使用

```text
使用 $sensync-lead-intelligence，研究巴西的RFID动物耳标品牌商及进口经销商，
审核10家候选企业，区分直接采购、渠道和竞争合作关系。
交付一个中文Excel，包含证据、联系人/邮箱状态和每公司一封英文首封草稿。
历史客户名单状态请按我本次提供的信息记录，缺失时不要假定已排查。
```

这是调用示例，巴西不是固定市场。可以指定其他国家、产品和客户角色。Skill只生成草稿，不发送、不自动跟进或分配业务员。

## 检查、更新与回滚

只有用户要求维护时才运行，普通研究不自动检查或安装更新。在已安装Skill目录运行：

```text
python scripts/manage_skill.py verify
python scripts/manage_skill.py check
python scripts/manage_skill.py update
```

如果变化要求复核，阅读实际文件变更和差异，在已审核授权范围内使用`update --accept-reviewed-changes`。更新只读取审核后的stable固定提交，校验完整包，备份前版，激活失败自动恢复。不覆盖本地改动/额外文件，备份不混入安装目录。回滚方法见[维护说明](skills/sensync-lead-intelligence/references/maintenance.md)。

main用于开发，stable用于安装，版本与CHANGELOG记录改动。更新后刷新索引或新会话加载。研究过程中固定批次版本。SHA-256证明包一致性，不证明发布者可信。

## 维护与边界

[发布流程](docs/RELEASE_PROCESS.md) · [跨设备验收清单](docs/ACCEPTANCE.md) · [变更日志](CHANGELOG.md)

公司资料主源：https://www.sensynctech.com/ 。通用证据、联系验证、安全写入和更新机制参考[Hispeed Agent Skills](https://github.com/liuxuan90/hispeed-agent-skills)，Sensync按自身制造工艺、供应链角色、多产品机会和六表要求独立设计。上游版本与复用边界见[来源说明](docs/PROVENANCE.md)。

**仓库只存规则、模板、结构和脚本。客户数据库、联系人导出、内部销售记录、价格、利润、账号、密码和API Key不得提交。** 运行输入/输出保存在仓库外，不用发布历史保存客户资料。
