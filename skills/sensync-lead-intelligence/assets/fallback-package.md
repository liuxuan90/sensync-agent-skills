# 工作簿不可用时的降级

具备Excel/在线工作簿能力时不得使用此方案代替单一六表。只有实际能力不足或写入失败且已向用户说明时，交付可恢复包：run-brief.md、run-report.md、company-records.json、lead-summary.csv、contacts.csv、email-drafts.md、rejected.csv以及列明文件/计数/阻塞的manifest。用户要求的完整草稿不得缺失或只引用其他Agent文件。

展示表头与说明默认中文，机器JSON保持Schema键与代码。来源/联系人/草稿完整保留；write_status报告真实结果，不称已成功写入。所有运行文件必须留在仓库外。
