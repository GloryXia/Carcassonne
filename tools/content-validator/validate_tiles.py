#!/usr/bin/env python3
"""地块目录录入校验器（TILE_TOPOLOGY_SPEC §9 不变量 + §13 河流扩展）。

用法：
    python tools/content-validator/validate_tiles.py content/tiles/base-current.json
    python tools/content-validator/validate_tiles.py content/tiles/base-current.json --expect-complete
    python tools/content-validator/validate_tiles.py content/tiles/river-current.json --expect-complete

默认校验单地块不变量并输出聚合统计；--expect-complete 额外按目录档案断言
整盒地块数与聚合边缘校验值（见 EXPECTED_PROFILES）。
"""
import json
import sys
import argparse
from copy import deepcopy
from collections import Counter

ZONES = ("left", "center", "right")
EDGES = ("N", "E", "S", "W")
ROTATE_CW = {"N": "E", "E": "S", "S": "W", "W": "N"}  # 每步顺时针 90°

# 边级地貌判定顺序：city > river > road > field（规范 §13）。
# 论证：城市恒占整边（三区带），与河流/道路（仅占 center）不可能共存于同一边；
# 道路与河流同占 center 亦不可能共边。三者先后次序因此不影响判定结果，仅为约定。
TERRAIN_PRIORITY = ("city", "river", "road")
TERRAIN_NAMES = ("field", "road", "city", "river")
TERRAIN_ZH = {"field": "田野", "road": "道路", "city": "城市", "river": "河流"}

# 整盒完整性档案（--expect-complete 按 catalogId 选用，各盒独立统计，互不并入）：
# base-current：72 块，边缘合计 田野 115 / 道路 94 / 城市 79（社区交叉校验值）。
# river-current：12 块（源头 1 + 湖泊 1 + 其余 10），边缘合计 田野 15 / 道路 6 / 城市 5 / 河流 22
# （按 CAR Standard ver.7.3 p.267–269 The River 组件表逐块转写后汇总得出）。
EXPECTED_PROFILES = {
    "base-current": {"tiles": 72, "edges": {"field": 115, "road": 94, "city": 79}},
    "river-current": {"tiles": 12, "edges": {"field": 15, "road": 6, "city": 5, "river": 22}},
}


def edge_terrain(design, edge):
    """图案在 rotation=0 时某条边的边级地貌（city > river > road > field）。"""
    terrains = {
        seg["featureType"]
        for seg in design["segments"]
        for port in seg["ports"]
        if port["edge"] == edge
    }
    for terrain in TERRAIN_PRIORITY:
        if terrain in terrains:
            return terrain
    return "field"


def fail(errors, design_id, message):
    errors.append(f"[{design_id}] {message}")


def segment_signature(segments, rotation_steps):
    """将端口按旋转步数映射后的段集合签名，用于对称性检查。"""
    sig = []
    for seg in segments:
        ports = []
        for port in seg["ports"]:
            edge = port["edge"]
            for _ in range(rotation_steps):
                edge = ROTATE_CW[edge]
            ports.append((edge, frozenset(port["zones"])))
        sig.append(
            (
                seg["featureType"],
                frozenset(ports),
                bool(seg.get("endsAtCenter", False)),
                tuple(sorted(seg.get("symbols", []))),
            )
        )
    return frozenset(sig)


def _normalized_segments(design):
    """忽略 localSegmentId 后返回可排序的段语义签名及旧 ID 映射。"""
    signatures = {}
    normalized = []
    for seg in design.get("segments", []):
        signature = (
            seg.get("featureType"),
            tuple(sorted((p.get("edge"), tuple(sorted(p.get("zones", [])))) for p in seg.get("ports", []))),
            bool(seg.get("endsAtCenter", False)),
            tuple(sorted(seg.get("symbols", []))),
        )
        signatures[seg.get("localSegmentId")] = signature
        normalized.append(signature)
    return tuple(sorted(normalized)), signatures


def semantic_design(design):
    """生成与 JSON/数组顺序及 localSegmentId 命名无关的图案表示。"""
    segments, id_to_signature = _normalized_segments(design)
    center_features = tuple(sorted(
        (c.get("kind"), tuple(sorted((k, json.dumps(v, sort_keys=True, ensure_ascii=False))
                                     for k, v in c.items() if k != "centerFeatureId")))
        for c in design.get("centerFeatures", [])
    ))
    center_ids = {c.get("centerFeatureId"): ("center", c.get("kind"))
                  for c in design.get("centerFeatures", [])}
    meeple_zones = []
    for zone in design.get("meepleZones", []):
        target = id_to_signature.get(zone.get("targetRef"), center_ids.get(zone.get("targetRef"), ("missing", zone.get("targetRef"))))
        meeple_zones.append((target, tuple(sorted(zone.get("allowedPieces", [])))))
    return {
        "segments": segments,
        "centerFeatures": center_features,
        "meepleZones": tuple(sorted(meeple_zones, key=repr)),
        "copiesInPool": design.get("copiesInPool"),
        "startTileCopies": design.get("startTileCopies"),
        "footprint": json.dumps(design.get("footprint"), sort_keys=True, ensure_ascii=False),
        "allowedRotations": tuple(sorted(design.get("allowedRotations", []))),
        "distinctRotations": design.get("distinctRotations"),
        "placementTags": tuple(sorted(design.get("placementTags", []))),
    }


def diff_catalogs(primary, review):
    """逐图案输出独立录入结果的语义差异，返回差异数量。"""
    left = {d["tileDefinitionId"]: d for d in primary.get("designs", [])}
    right = {d["tileDefinitionId"]: d for d in review.get("designs", [])}
    differences = 0
    matching = []
    for did in sorted(set(left) | set(right)):
        if did not in left:
            print(f" - [{did}] 仅复核文件存在")
            differences += 1
            continue
        if did not in right:
            print(f" - [{did}] 复核文件缺失")
            differences += 1
            continue
        a, b = semantic_design(left[did]), semantic_design(right[did])
        changed = [key for key in a if a[key] != b[key]]
        if not changed:
            matching.append(did)
            continue
        differences += 1
        print(f" - [{did}] 差异字段：{', '.join(changed)}")
        for key in changed:
            print(f"     主文件 {key}: {a[key]!r}")
            print(f"     复核件 {key}: {b[key]!r}")
    print(f"一致图案（{len(matching)}）：" + ("、".join(matching) if matching else "无"))
    print(f"语义差异：{differences} 个图案")
    return differences


def check_design(design, errors):
    did = design.get("tileDefinitionId", "<unknown>")

    for key in (
        "tileDefinitionId", "copiesInPool", "startTileCopies", "footprint",
        "allowedRotations", "distinctRotations", "segments", "meepleZones",
        "sourceReference", "verificationStatus",
    ):
        if key not in design:
            fail(errors, did, f"缺少必填字段 {key}")
    if errors:
        return

    # 1. 段 ID 唯一；端口结构
    seg_ids = [s["localSegmentId"] for s in design["segments"]]
    if len(seg_ids) != len(set(seg_ids)):
        fail(errors, did, "localSegmentId 重复")

    # 2. 每条边三区带不重不漏
    coverage = {e: Counter() for e in EDGES}
    for seg in design["segments"]:
        stype = seg["featureType"]
        for port in seg["ports"]:
            zones = port["zones"]
            if len(set(zones)) != len(zones):
                fail(errors, did, f"{seg['localSegmentId']} 在 {port['edge']} 边区带重复")
            if stype == "city" and set(zones) != set(ZONES):
                fail(errors, did, f"城市段 {seg['localSegmentId']} 必须占满 {port['edge']} 整边")
            if stype == "road" and set(zones) != {"center"}:
                fail(errors, did, f"道路段 {seg['localSegmentId']} 在 {port['edge']} 必须只占 center")
            if stype == "river" and set(zones) != {"center"}:
                fail(errors, did, f"河流段 {seg['localSegmentId']} 在 {port['edge']} 必须只占 center")
            for z in zones:
                if z not in ZONES:
                    fail(errors, did, f"未知区带 {z}")
                coverage[port["edge"]][z] += 1
    for edge in EDGES:
        for z in ZONES:
            n = coverage[edge][z]
            if n == 0:
                fail(errors, did, f"{edge}.{z} 无段覆盖")
            elif n > 1:
                fail(errors, did, f"{edge}.{z} 被 {n} 个段重复覆盖")

    # 3. 盾徽只能附着城市段
    for seg in design["segments"]:
        if seg.get("symbols") and seg["featureType"] != "city":
            fail(errors, did, f"非城市段 {seg['localSegmentId']} 不得携带盾徽")

    # 4. endsAtCenter 仅允许道路段，且必须存在中心特征
    center_ids = {c["centerFeatureId"] for c in design.get("centerFeatures", [])}
    for seg in design["segments"]:
        if seg.get("endsAtCenter"):
            if seg["featureType"] != "road":
                fail(errors, did, f"endsAtCenter 仅允许道路段：{seg['localSegmentId']}")
            if not center_ids:
                fail(errors, did, f"{seg['localSegmentId']} 声明 endsAtCenter 但无中心特征")

    # 5. meepleZones 引用与角色规则
    valid_refs = set(seg_ids) | center_ids
    center_kinds = {c["centerFeatureId"]: c["kind"] for c in design.get("centerFeatures", [])}
    seg_types = {s["localSegmentId"]: s["featureType"] for s in design["segments"]}
    for zone in design["meepleZones"]:
        ref = zone["targetRef"]
        pieces = set(zone["allowedPieces"])
        if ref not in valid_refs:
            fail(errors, did, f"meepleZone {zone['zoneId']} 引用不存在的 {ref}")
            continue
        if ref in seg_types:
            if seg_types[ref] == "river":
                fail(errors, did, f"河流段 {ref} 不得放置随从（CAR p.27：河流上不可部署随从）")
            elif pieces != {"meeple"}:
                fail(errors, did, f"区域段 {ref} 基础游戏只允许普通随从")
        else:
            kind = center_kinds[ref]
            if kind == "monastery" and pieces != {"meeple", "abbot"}:
                fail(errors, did, "修道院应允许 meeple 与 abbot")
            if kind == "garden" and pieces != {"abbot"}:
                fail(errors, did, "花园只允许 abbot")

    # 6. 旋转对称性与 distinctRotations 一致
    distinct = len({segment_signature(design["segments"], k) for k in range(4)})
    if distinct != design["distinctRotations"]:
        fail(errors, did, f"distinctRotations={design['distinctRotations']} 与实际对称性 {distinct} 不符")

    # 7. 起始地块唯一性在目录级检查；此处限制单图案数量
    if design["startTileCopies"] not in (0, 1):
        fail(errors, did, "startTileCopies 必须为 0 或 1")


def check_river_profile(designs, errors):
    """河流目录（river-current）的目录级完整性断言（规范 §13）：

    1. 源头块唯一且为模块起始块（river-source + startTileCopies=1、copiesInPool=0）；
    2. 湖泊块唯一（river-lake，在抽取池中 1 块，收尾放置）；
    3. 源头/湖泊块恰有 1 个河流端口，其余图案每块恰有 2 个河流端口；
    4. 弯河块（两河流端口相邻）必须携带 river-curve 标签，直河块不得携带
       （U 型回折禁止的放置校验由 TASK-04 规则引擎依据该标签实现）。
    """
    sources = [d for d in designs if "river-source" in d.get("placementTags", [])]
    lakes = [d for d in designs if "river-lake" in d.get("placementTags", [])]
    if len(sources) != 1:
        errors.append(f"[catalog] 河流源头块数量为 {len(sources)}，必须唯一")
    elif sources[0]["startTileCopies"] != 1 or sources[0]["copiesInPool"] != 0:
        errors.append("[catalog] 源头块必须 startTileCopies=1 且 copiesInPool=0")
    if len(lakes) != 1 or lakes[0]["copiesInPool"] != 1:
        errors.append("[catalog] 河流湖泊块必须唯一且在抽取池中恰有 1 块")

    for d in designs:
        did = d["tileDefinitionId"]
        river_edges = {
            port["edge"]
            for seg in d["segments"]
            if seg["featureType"] == "river"
            for port in seg["ports"]
        }
        tags = d.get("placementTags", [])
        if "river-source" in tags or "river-lake" in tags:
            if len(river_edges) != 1:
                errors.append(f"[{did}] 源头/湖泊块应恰有 1 个河流端口，实际 {len(river_edges)}")
            continue
        if len(river_edges) != 2:
            errors.append(f"[{did}] 普通河流块应恰有 2 个河流端口，实际 {len(river_edges)}")
            continue
        e1, e2 = sorted(river_edges)
        is_curve = ROTATE_CW[e1] == e2 or ROTATE_CW[e2] == e1  # 相邻边 = 弯道
        if is_curve and "river-curve" not in tags:
            errors.append(f"[{did}] 弯河块缺少 river-curve 标签")
        if not is_curve and "river-curve" in tags:
            errors.append(f"[{did}] 直河块不得携带 river-curve 标签")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="主地块目录 JSON")
    parser.add_argument("--expect-complete", action="store_true", help="校验整盒统计")
    parser.add_argument("--diff", metavar="REVIEW_JSON", help="与第二人独立录入文件做语义比对")
    args = parser.parse_args()
    path = args.path
    expect_complete = args.expect_complete

    with open(path, encoding="utf-8") as f:
        catalog = json.load(f)

    errors = []
    designs = catalog["designs"]

    ids = [d["tileDefinitionId"] for d in designs]
    if len(ids) != len(set(ids)):
        errors.append("[catalog] tileDefinitionId 重复")
    prefix = catalog["catalogId"] + "."
    for did in ids:
        if not did.startswith(prefix):
            errors.append(f"[catalog] {did} 与 catalogId 前缀不一致")
    if catalog.get("status") == "frozen":
        for d in designs:
            if d["verificationStatus"] != "已测试":
                errors.append(f"[catalog] 冻结目录中存在未测试图案 {d['tileDefinitionId']}")

    for d in designs:
        check_design(d, errors)

    total_tiles = sum(d["copiesInPool"] + d["startTileCopies"] for d in designs)
    start_tiles = sum(d["startTileCopies"] for d in designs)
    if start_tiles > 1:
        errors.append(f"[catalog] 起始地块数量为 {start_tiles}，必须唯一")

    # 聚合边缘统计采用"每边单一地貌"口径（与社区交叉校验值一致）：
    # 按 TERRAIN_PRIORITY（city > river > road > field）判定边级地貌，每边只计一次。
    edge_units = Counter()
    for d in designs:
        copies = d["copiesInPool"] + d["startTileCopies"]
        for edge in EDGES:
            edge_units[edge_terrain(d, edge)] += copies

    profile = EXPECTED_PROFILES.get(catalog["catalogId"])
    counts = " / ".join(f"{TERRAIN_ZH[t]} {edge_units[t]}" for t in TERRAIN_NAMES)
    print(f"目录：{catalog['catalogId']}（{catalog['status']}）")
    if profile:
        expected = " / ".join(f"{TERRAIN_ZH[t]} {profile['edges'][t]}" for t in TERRAIN_NAMES if t in profile["edges"])
        print(f"图案 {len(designs)} 种，地块 {total_tiles} 块（目标 {profile['tiles']}）")
        print(f"边缘合计：{counts}（整盒校验值 {expected}）")
    else:
        print(f"图案 {len(designs)} 种，地块 {total_tiles} 块（无整盒完整性档案）")
        print(f"边缘合计：{counts}")

    if expect_complete:
        if profile is None:
            errors.append(f"[catalog] 无 {catalog['catalogId']} 的完整性档案，无法执行 --expect-complete")
        else:
            if total_tiles != profile["tiles"]:
                errors.append(f"[catalog] 地块总数 {total_tiles} != {profile['tiles']}")
            for terrain, expected_n in profile["edges"].items():
                if edge_units[terrain] != expected_n:
                    errors.append(f"[catalog] {TERRAIN_ZH[terrain]} 边缘合计 {edge_units[terrain]} != {expected_n}")
            if catalog["catalogId"] == "river-current":
                check_river_profile(designs, errors)

    if errors:
        print(f"\n发现 {len(errors)} 个问题：")
        for e in errors:
            print(" -", e)
        return 1
    print("校验通过。")
    if args.diff:
        with open(args.diff, encoding="utf-8") as f:
            review = json.load(f)
        print(f"\n语义复核：{path} ↔ {args.diff}")
        if diff_catalogs(catalog, review):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
