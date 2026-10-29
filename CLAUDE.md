# hell-grind-aigc-skill（地獄磨坊 AIGC 影片 skill）專案筆記

上游的公開 skill 的 fork：AI 影片製作的專案模板、驗證器、提示詞審計。程式碼註解與文件沿用上游（英文／簡體），改動要跟上游風格一致。

## 這個專案特有的注意事項

- 專案模板 `skill/hell-grind-aigc-skill/assets/project-template/` 的欄位由 `scripts/validate_project.py` 嚴格檢查，**不要直接改模板欄位**；要接外部格式就寫轉換器。
- `scripts/import_storyboard.py`（這個 fork 加的）：吃長劇本分鏡／漫畫工作室的分鏡 CSV，寫入 scenes／shots／audio-cues，全部 `planned`；分鏡欄位和那兩個工具共用，改欄位要三邊一起改。
- 驗證器必須維持唯讀；初始化器必須拒絕非空目錄（測試有檢查）。
- `tests/test_skill_contract.py` 會檢查 SKILL.md 的內容（skill 契約），改 SKILL.md 後一定要跑測試；新增腳本記得寫進 README 和 SKILL.md。

## 常用指令

```bash
python3 -m unittest discover -s tests
```
