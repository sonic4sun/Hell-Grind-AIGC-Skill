import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skill" / "hell-grind-aigc-skill"
INIT_SCRIPT = SKILL_ROOT / "scripts" / "init_project.py"
VALIDATE_SCRIPT = SKILL_ROOT / "scripts" / "validate_project.py"
IMPORT_SCRIPT = SKILL_ROOT / "scripts" / "import_storyboard.py"

HEADER = ["鏡號", "場", "段落", "影片段", "地點", "時間", "景別", "機位／運鏡", "光色", "畫面", "對白／OS／音效", "秒", "變速"]
ROWS = [
    ["S001-01", "SC001", "1", "SC001-V01", "便利商店", "夜", "全景", "固定", "冷白日光燈", "阿潤補貨", "音效：日光燈嗡嗡聲", "3", ""],
    ["S001-02", "SC001", "2", "SC001-V01", "便利商店", "夜", "中景", "推軌", "冷白", "客人拿起過期便當", "客人（低聲）：這個……過期了吧？／阿潤：過期的不能賣喔。", "4.5", "慢動作"],
    ["S002-01", "第二場", "3", "第二場-V01", "後巷", "夜", "特寫", "手持", "", "空無一人", "BGM：低頻嗡鳴", "", ""],
]


def run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(script), *args], text=True, capture_output=True, check=False)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ImportStoryboardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.project = self.root / "project"
        result = run(INIT_SCRIPT, "--name", "Expired Lunch", "--output", str(self.project))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.csv = self.root / "storyboard.csv"
        with self.csv.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle)
            writer.writerow(HEADER)
            writer.writerows(ROWS)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_import_produces_valid_project(self) -> None:
        result = run(IMPORT_SCRIPT, str(self.project), str(self.csv))
        self.assertEqual(result.returncode, 0, result.stderr)

        scenes = read_rows(self.project / "03_scenes" / "scenes.csv")
        shots = read_rows(self.project / "04_shots" / "shots.csv")
        cues = read_rows(self.project / "04_shots" / "audio-cues.csv")
        self.assertEqual([s["scene_id"] for s in scenes], ["SC001", "SC002"])
        self.assertEqual([s["shot_id"] for s in shots], ["SC001-SH001", "SC001-SH002", "SC002-SH001"])
        self.assertEqual(shots[1]["duration_seconds"], "4.5")
        self.assertEqual(shots[2]["duration_seconds"], "3")  # missing seconds get a placeholder
        self.assertIn("原鏡號：S001-02", shots[1]["notes"])
        self.assertEqual([c["category"] for c in cues], ["foley", "dialogue", "dialogue", "music"])
        self.assertEqual(cues[1]["source"], "客人")

        validation = run(VALIDATE_SCRIPT, str(self.project), "--json")
        report = json.loads(validation.stdout)
        self.assertTrue(report["valid"], report)

    def test_refuses_to_overwrite_without_flag(self) -> None:
        self.assertEqual(run(IMPORT_SCRIPT, str(self.project), str(self.csv)).returncode, 0)
        again = run(IMPORT_SCRIPT, str(self.project), str(self.csv))
        self.assertNotEqual(again.returncode, 0)
        self.assertEqual(run(IMPORT_SCRIPT, str(self.project), str(self.csv), "--replace").returncode, 0)

    def test_rejects_unrelated_csv(self) -> None:
        other = self.root / "other.csv"
        other.write_text("a,b\n1,2\n", encoding="utf-8")
        result = run(IMPORT_SCRIPT, str(self.project), str(other))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("缺少欄位", result.stderr)
        self.assertEqual(read_rows(self.project / "04_shots" / "shots.csv"), [])


if __name__ == "__main__":
    unittest.main()
