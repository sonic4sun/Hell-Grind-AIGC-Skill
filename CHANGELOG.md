# Changelog

## 2.1.0-fork - 2026-09-16

### Added

- `references/vertical-episodic-series.md`：竖屏微短剧"爽剧"专属层——`01_story/episodes.csv` 集数分组、开场/结尾钩子词表、单集情绪节奏契约（压抑→假反转→打脸→钩子）、竖屏构图倾向、F-HOOK-WEAK 失败诊断类别。
- `init_project.py --resolution`：交付分辨率不再固定 1920x1080，可独立于 `--aspect-ratio` 指定（例如 `--resolution 1080x1920`），随 `RESOLUTION` 占位符写入 `project.yaml`。

### Changed

- SKILL.md 生产管理路由新增指向 `vertical-episodic-series.md` 的条目。

### Notes

- 本次改动均为增量扩展：不修改 `03_scenes/scenes.csv`／`04_shots/shots.csv` 既有表头，`episodes.csv` 不在 `validate_project.py` 必填文件清单内，`--resolution` 有默认值保持向后兼容。全部 40 项既有测试通过（含更新后的路由契约测试）。

## 2.0.0 - 2026-08-07

### Added

- 七层模型无关提示词架构。
- 资产状态、参考范围、空间调度、摄影、表演、动作物理、光色材质、对白声音、连续性、负向约束和多镜头专项方法。
- 生成批次、变量隔离、选片评分、停止条件和六类失败诊断。
- schema v2 项目模板及八张新增数据表。
- `audit_prompt.py` 确定性只读提示词审计器。
- `validate_project.py --strict-v2` 引用、状态、时间线、成本、选择和豁免校验。
- v1 项目兼容模式。
- 行为、包边界、提示词审计和项目完整性测试。

### Changed

- 父 Skill 路由扩展到生产管理、图片/视频从零生成与润色、失败诊断。
- 图片 11 类和视频 12 段从清单升级为包含公式、失败和检查门的操作手册。
- 初始化器默认创建 schema v2 项目并验证画幅。

### Safety

- 默认仍不调用生成模型、不扣费、不下载媒体、不上传、不发布。
- 本地三个工具保持 0 网络请求、0 数据库操作。
- 仓库不包含第三方原视频、资产、全量提示词或长篇项目提示词。
