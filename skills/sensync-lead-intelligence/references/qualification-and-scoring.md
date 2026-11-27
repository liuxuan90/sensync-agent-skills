# 资格、机会与评分 v1

## 身份和机会

company_identity以规范化域名为主要去重信号，并核对法定主体/国家/集团多品牌/共享域名。每企业可有多个opportunities；用稳定opportunity_id连接contacts、sources和draft。合作类型为DIRECT_PURCHASE、DESIGN_IN、CHANNEL、OEM_ODM、SYSTEM_INTEGRATION。竞争关系与合作类型独立，记录涉及产品线、竞争点和证据，状态CONFIRMED/POSSIBLE/NONE_EVIDENCED/UNKNOWN。

## 硬门槛

每个机会的以下门槛填PASS/FAIL/UNKNOWN，保存判断与来源ID：

1. identity：真实企业身份与当前经营；
2. market：符合用户指定总部/生产/市场存在要求；
3. application：窄应用和具体产品吻合；
4. buyer_role：实际采购、设计指定、制造、集成或渠道职责吻合；
5. product_fit：按分线playbook证明具体结构/工艺/协议/采购层级匹配；
6. feasibility：已证适配或列出不影响初步匹配的明确工程验证条件；关键工艺/协议未知不能用sample_test_required绕过；
7. independent_evidence：至少两份独立证据，不能只依赖S5；重复转载为一份；
8. exclusions：按本批用户排除核对；
9. known_customer：提供名单且核对(PROVIDED_AND_CHECKED)，或用户明确无名单(USER_CONFIRMED_NONE)才PASS；未提供(NOT_PROVIDED)为UNKNOWN，不把无市场限制当无历史名单；
10. negative_review：已主动检查关停、错误角色/工艺、技术不兼容、竞争限制等反面证据。

关键UNKNOWN：REVIEW，score=null；确认FAIL：REJECTED，score=null。重复企业单独记DUPLICATE与匹配ID，不把新增机会当新企业重复交付。

## 通过门槛后评分

初版沿用成熟100分框架，按机会和产品线重建解释：ICP/应用25；可观察采购/设计/渠道逻辑30；具体产品/工艺适配25；证据独立性/质量/时效15；可证实个性化信号5。每项附证据和理由，合计存score；这是初始待校准模型，不是Sensync实际成交率。

- 设备：30分评价实际绕线/集成/销售活动与适配采购路径，不要求正在买机器；25分评价工件与工艺，不泛评“电机行业”。
- 线圈：30分评价独立线圈采购或设计指定权，区别成品/模块外购；25分评价结构、电气与装配接口，不能只凭无线充/NFC业务。
- 玻璃管：30分评价对应识别产品的品牌/OEM/进口渠道路径；25分评价具体转发器/注射器、协议、包装与应用。
- 耳标：30分评价电子标签采购/配套职责，25分评价型号协议、动物应用与系统适配；不把读写器/软件业务泛化为买标签。

75–100：QUALIFIED；75–79标BORDERLINE，低于同批80+优先级，列最弱证据待办。60–74：REVIEW；低于60：REJECTED。门槛未知时禁止分数掩盖。所有阈值为初始标尺，用户反馈后版本化校准，不跨线直接比较数值强弱。

当前采购意向单列EXPLICIT_SIGNAL/NOT_FOUND/UNKNOWN与来源；NOT_FOUND只表示搜索未发现，不证明没有需求。采购信号可影响优先级，但不能虚构预算、订单或痛点。无统一员工数/采购量/金额硬门槛；小批和研发机会可评估，实际MOQ按项目确认。

## 企业汇总与完成状态

本批scope内至少一条QUALIFIED机会才可计入合格企业数；仅其他线合格不补本批数量。无合格但有REVIEW则企业REVIEW；全为明确淘汰则REJECTED。客户汇总展示主机会结论，不创造一个混合总分。COMPLETE仅在要求的研究已实际完成、必要门槛和重要证据完整、联系人时效合格且无实质阻塞时使用；诚实E0不自动造成PARTIAL，未执行NOT_EVALUATED或未解决重要缺口会造成PARTIAL。write_status独立于资格，未写成功不能称已写入。
