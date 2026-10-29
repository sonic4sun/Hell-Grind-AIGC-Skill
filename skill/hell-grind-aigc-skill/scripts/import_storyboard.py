#!/usr/bin/env python3
"""Import a storyboard CSV into a project's scene, shot and audio-cue tables.

Accepts the storyboard export used by long-script-storyboard and ai-comic-studio:
鏡號,場,段落,影片段,地點,時間,景別,機位／運鏡,光色,畫面,對白／OS／音效,秒,變速

Only 03_scenes/scenes.csv, 04_shots/shots.csv and 04_shots/audio-cues.csv are written.
Rows are imported as `planned` so the normal contract/prompt workflow still applies.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


REQUIRED_COLUMNS = ["鏡號", "場", "畫面"]
SCENE_ID_PATTERN = re.compile(r"^SC\d{3}$")
DEFAULT_SHOT_SECONDS = "3"
AUDIO_SPLIT = re.compile(r"\n|／(?=[^／：:]{1,12}[：:])")
ROLE_LINE = re.compile(r"^([^：:]{1,14})[：:]\s*(.+)$")
CATEGORY_BY_LABEL = [
    (re.compile(r"^(音效|SFX|效果|擬音)", re.I), "foley"),
    (re.compile(r"^(環境音|環境)", re.I), "ambience"),
    (re.compile(r"^(BGM|配樂|音樂|MUSIC)", re.I), "music"),
    (re.compile(r"^(靜音|無聲|SILENCE)", re.I), "silence"),
]


def read_storyboard(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"分鏡表缺少欄位：{'、'.join(missing)}（需要長劇本分鏡或漫畫工作室匯出的 CSV）")
        return [{key: (value or "").strip() for key, value in row.items() if key} for row in reader]


def table_headers(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return next(csv.reader(handle))


def has_rows(path: Path) -> bool:
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.reader(handle)) > 1


def write_table(path: Path, rows: list[dict[str, str]]) -> None:
    headers = table_headers(path)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})


def seconds(raw: str) -> str:
    try:
        value = float(raw)
    except ValueError:
        return ""
    return f"{value:g}" if value > 0 else ""


def audio_category(label: str) -> str:
    for pattern, category in CATEGORY_BY_LABEL:
        if pattern.match(label):
            return category
    return "dialogue"


def audio_cues(text: str, shot_id: str, duration: str) -> list[dict[str, str]]:
    cues = []
    for piece in AUDIO_SPLIT.split(text):
        piece = piece.strip()
        if not piece:
            continue
        match = ROLE_LINE.match(piece)
        label, content = (match.group(1).strip(), match.group(2).strip()) if match else ("", piece)
        category = audio_category(label) if label else "dialogue"
        source = "" if category != "dialogue" else re.sub(r"[（(][^）)]*[）)]", "", label).strip()
        cues.append({
            "audio_cue_id": f"AUD-{shot_id}-{len(cues) + 1:02d}",
            "shot_id": shot_id,
            "start_seconds": "0",
            "end_seconds": duration,
            "category": category,
            "source": source,
            "content_or_effect": content,
            "notes": "從分鏡表匯入，時間點待剪輯時對齊",
        })
    return cues


def convert(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    scene_ids: dict[str, str] = {}
    scenes: list[dict[str, str]] = []
    shots: list[dict[str, str]] = []
    cues: list[dict[str, str]] = []
    shot_counts: dict[str, int] = {}

    for row in rows:
        label = row.get("場") or "未分場"
        if label not in scene_ids:
            scene_id = label if SCENE_ID_PATTERN.match(label) and label not in scene_ids.values() else f"SC{len(scene_ids) + 1:03d}"
            scene_ids[label] = scene_id
            scenes.append({
                "scene_id": scene_id,
                "scene_order": str(len(scenes) + 1),
                "title": row.get("地點") or label,
                "time_of_day": row.get("時間", ""),
                "status": "planned",
                "notes": "；".join(filter(None, [f"原場號：{label}", f"地點：{row.get('地點')}" if row.get("地點") else ""])),
            })
        scene_id = scene_ids[label]
        shot_counts[scene_id] = shot_counts.get(scene_id, 0) + 1
        shot_id = f"{scene_id}-SH{shot_counts[scene_id]:03d}"
        duration = seconds(row.get("秒", ""))
        notes = [
            f"原鏡號：{row.get('鏡號')}" if row.get("鏡號") else "",
            f"景別：{row.get('景別')}" if row.get("景別") else "",
            f"光色：{row.get('光色')}" if row.get("光色") else "",
            f"變速：{row.get('變速')}" if row.get("變速") else "",
            f"影片段：{row.get('影片段')}" if row.get("影片段") else "",
            f"劇本段落：{row.get('段落')}" if row.get("段落") else "",
            "" if duration else f"秒數未填，暫定 {DEFAULT_SHOT_SECONDS} 秒",
        ]
        duration = duration or DEFAULT_SHOT_SECONDS
        shots.append({
            "shot_id": shot_id,
            "scene_id": scene_id,
            "shot_order": str(shot_counts[scene_id]),
            "duration_seconds": duration,
            "status": "planned",
            "narrative_goal": row.get("畫面", ""),
            "camera_path": row.get("機位／運鏡", ""),
            "notes": "；".join(filter(None, notes)),
        })
        cues.extend(audio_cues(row.get("對白／OS／音效", ""), shot_id, duration))
    return scenes, shots, cues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import a storyboard CSV (long-script-storyboard / ai-comic-studio) into a project")
    parser.add_argument("project", type=Path, help="Project directory created by init_project.py")
    parser.add_argument("storyboard", type=Path, help="Storyboard CSV export")
    parser.add_argument("--replace", action="store_true", help="Overwrite existing scenes, shots and audio cues")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tables = {
        "scenes": args.project / "03_scenes" / "scenes.csv",
        "shots": args.project / "04_shots" / "shots.csv",
        "audio": args.project / "04_shots" / "audio-cues.csv",
    }
    missing = [str(path) for path in tables.values() if not path.is_file()]
    if missing:
        print(f"找不到專案表格：{', '.join(missing)}（先用 init_project.py 建立專案）", file=sys.stderr)
        return 2
    if not args.replace and any(has_rows(path) for path in tables.values()):
        print("專案裡已經有場景／鏡頭資料；確定要覆蓋就加上 --replace", file=sys.stderr)
        return 2
    try:
        rows = read_storyboard(args.storyboard)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    if not rows:
        print("分鏡表是空的", file=sys.stderr)
        return 2

    scenes, shots, cues = convert(rows)
    write_table(tables["scenes"], scenes)
    write_table(tables["shots"], shots)
    write_table(tables["audio"], cues)
    print(f"已匯入 {len(scenes)} 場、{len(shots)} 個鏡頭、{len(cues)} 條聲音提示")
    return 0


if __name__ == "__main__":
    sys.exit(main())
