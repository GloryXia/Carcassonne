#!/usr/bin/env python3
"""内容交叉校验器：规则集清单 ↔ 地块目录 ↔ 场景测试 的引用一致性与场景盘面合法性。

用法：
    python tools/content-validator/validate_content.py

校验内容：
  1. 规则集清单引用的地块目录文件存在性（缺失降级为警告：可能尚未录入）。
  2. 场景引用的 tileDefinitionId 解析（目录缺失=错误；定义缺失=警告，视为待录入）。
  3. 场景盘面合法性：坐标不重复、相邻块共享边地貌一致（按 TILE_TOPOLOGY_SPEC
     的"每边单一地貌"口径，随旋转映射）。
  4. 随从放置：位于盘面上、角色与图案特征匹配（knight/thief/monk/farmer）。
  5. official-example 缺页码、contributesTiles 与实际不符等降级为警告。

退出码：存在错误=1；仅警告=0。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_tiles import EDGES, ROTATE_CW, edge_terrain  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
TILES_DIR = ROOT / "content" / "tiles"
RULESETS_DIR = ROOT / "content" / "rulesets"
SCENARIOS_DIR = ROOT / "content" / "scenarios"

# 共享边两侧区带镜像对接（L↔R），但"每边单一地貌"口径下只需比较边级地貌。
# 边级地貌判定顺序 city > river > road > field 与 validate_tiles.py 共享（规范 §13）。
ADJACENT = {"N": (0, 1, "S"), "E": (1, 0, "W"), "S": (0, -1, "N"), "W": (-1, 0, "E")}
ROLE_FEATURE = {"knight": "city", "thief": "road", "monk": "monastery", "farmer": "field", "abbot": "monastery"}

errors, warnings = [], []


def rotated_terrain(design, direction, rotation):
    """旋转 rotation（顺时针角度）后，direction 方向上的边级地貌。"""
    steps = (rotation // 90) % 4
    original = direction
    for _ in range((4 - steps) % 4):  # 逆向求原始边
        original = ROTATE_CW[original]
    return edge_terrain(design, original)


def load_jsons(directory):
    for path in sorted(directory.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            yield path, json.load(f)


def main():
    # ---- 1. 加载地块目录 ----
    catalogs = {}   # catalogId -> {definitionId -> design}
    catalog_files = {}
    for path, catalog in load_jsons(TILES_DIR):
        cid = catalog["catalogId"]
        catalogs[cid] = {d["tileDefinitionId"]: d for d in catalog["designs"]}
        catalog_files[cid] = path

    # ---- 2. 规则集清单 ----
    ruleset_ids = set()
    for path, manifest in load_jsons(RULESETS_DIR):
        rid = manifest["rulesetId"]
        ruleset_ids.add(rid)
        for ref in manifest["tileCatalogs"]:
            target = (path.parent / ref["path"]).resolve()
            if not target.exists():
                warnings.append(f"[{rid}] 引用的地块目录不存在（可能待录入）：{ref['path']}")
                continue
            with open(target, encoding="utf-8") as f:
                catalog = json.load(f)
            actual = sum(d["copiesInPool"] + d["startTileCopies"] for d in catalog["designs"])
            if actual != ref["contributesTiles"]:
                warnings.append(
                    f"[{rid}] {ref['path']} 实际 {actual} 块，"
                    f"与 contributesTiles={ref['contributesTiles']} 不符（录入中？）"
                )

    # ---- 3. 场景测试 ----
    for path, scenario_catalog in load_jsons(SCENARIOS_DIR):
        seen_ids = set()
        for sc in scenario_catalog["scenarios"]:
            sid = sc["scenarioId"]
            if sid in seen_ids:
                errors.append(f"[{sid}] scenarioId 重复")
            seen_ids.add(sid)

            if sc["rulesetId"] not in ruleset_ids:
                errors.append(f"[{sid}] 未知 rulesetId：{sc['rulesetId']}")

            src = sc["sourceReference"]
            if src.get("kind") == "official-example" and "page" not in src:
                warnings.append(f"[{sid}] official-example 缺页码，待复核补全")

            # 盘面
            board = {}
            ok = True
            for placed in sc["given"]["board"]:
                coord = (placed["x"], placed["y"])
                if coord in board:
                    errors.append(f"[{sid}] 坐标 {coord} 重复放置")
                    ok = False
                tid = placed["tileDefinitionId"]
                cid = tid.rsplit(".", 1)[0]
                if cid not in catalogs:
                    errors.append(f"[{sid}] 未知地块目录：{cid}")
                    ok = False
                    continue
                design = catalogs[cid].get(tid)
                if design is None:
                    warnings.append(f"[{sid}] 图案未录入（待 TASK-01）：{tid}")
                    board[coord] = None  # 占位，避免级联误报；邻接与随从检查跳过
                    continue
                board[coord] = (design, placed["rotation"])
            if not ok:
                continue

            # 邻接一致性（None 为未录入图案占位，跳过）
            for (x, y), entry in board.items():
                if entry is None:
                    continue
                design, rot = entry
                for direction, (dx, dy, opposite) in ADJACENT.items():
                    neighbor = board.get((x + dx, y + dy))
                    if neighbor is None or direction in ("S", "W"):
                        continue  # 每对邻接只查一次（N/E 方向）
                    nd, nrot = neighbor
                    t1 = rotated_terrain(design, direction, rot)
                    t2 = rotated_terrain(nd, opposite, nrot)
                    if t1 != t2:
                        errors.append(
                            f"[{sid}] ({x},{y}) {direction}边={t1} 与 "
                            f"({x+dx},{y+dy}) {opposite}边={t2} 不匹配"
                        )

            # 随从
            for meeple in sc["given"].get("meeples", []):
                coord = (meeple["x"], meeple["y"])
                if coord not in board:
                    errors.append(f"[{sid}] 随从位于空坐标 {coord}")
                    continue
                if board[coord] is None:
                    continue  # 图案未录入，占位跳过
                design, _ = board[coord]
                feature = ROLE_FEATURE[meeple["role"]]
                if feature == "monastery":
                    found = any(c["kind"] == "monastery" for c in design.get("centerFeatures", []))
                else:
                    found = any(s["featureType"] == feature for s in design["segments"])
                if not found:
                    errors.append(
                        f"[{sid}] {coord} 的 {design['tileDefinitionId']} 上没有 "
                        f"{meeple['role']} 可部署的 {feature} 特征"
                    )

            # when.at 引用
            action = sc["when"]["action"]
            if action in ("score-feature", "place-piece", "reclaim-abbot"):
                at = sc["when"].get("at")
                if at is None or (at["x"], at["y"]) not in board:
                    errors.append(f"[{sid}] {action} 的 at 不在盘面上")
            if action == "place-piece":
                if "piece" not in sc["when"]:
                    errors.append(f"[{sid}] place-piece 缺少 piece")
                elif sc["when"].get("at"):
                    at = sc["when"]["at"]
                    entry = board.get((at["x"], at["y"]))
                    if entry:
                        design, _ = entry
                        role = sc["when"]["piece"]["role"]
                        feature = ROLE_FEATURE[role]
                        if feature == "monastery":
                            found = any(c["kind"] in ("monastery", "garden") for c in design.get("centerFeatures", []))
                        else:
                            found = any(s["featureType"] == feature for s in design["segments"])
                        if not found:
                            errors.append(f"[{sid}] place-piece 目标图案不支持 {role}")
                if "actionAccepted" not in sc["expect"]:
                    errors.append(f"[{sid}] place-piece 缺少 actionAccepted 断言")
                if sc["expect"].get("actionAccepted") is False and "rejectionCode" not in sc["expect"]:
                    errors.append(f"[{sid}] 被拒绝的 place-piece 缺少 rejectionCode")
            if action == "reclaim-abbot":
                at = sc["when"].get("at")
                located = at and any(
                    m["role"] == "abbot" and (m["x"], m["y"]) == (at["x"], at["y"])
                    for m in sc["given"].get("meeples", [])
                )
                if not located:
                    errors.append(f"[{sid}] reclaim-abbot 的 at 没有修道院长")

    # ---- 输出 ----
    for w in warnings:
        print("警告：", w)
    if errors:
        print(f"\n发现 {len(errors)} 个错误：")
        for e in errors:
            print(" -", e)
        return 1
    print(f"交叉校验通过（{len(warnings)} 条警告）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
