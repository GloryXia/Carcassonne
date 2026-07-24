#!/usr/bin/env python3
"""依赖零第三方包的协议 fixture 校验器（覆盖本仓库契约使用的 2020-12 子集）。"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "contracts" / "protocol"
FIXTURE_DIR = SCHEMA_DIR / "fixtures"


def load(name):
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def validate(value, schema, path="$", errors=None):
    errors = [] if errors is None else errors
    for part in schema.get("allOf", []):
        validate(value, load(part["$ref"]) if "$ref" in part else part, path, errors)
    expected = schema.get("type")
    if expected:
        names = expected if isinstance(expected, list) else [expected]
        checks = {"object": lambda v: isinstance(v, dict), "array": lambda v: isinstance(v, list),
                  "string": lambda v: isinstance(v, str), "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
                  "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
                  "boolean": lambda v: isinstance(v, bool), "null": lambda v: v is None}
        if not any(checks[n](value) for n in names):
            errors.append(f"{path}: 类型应为 {names}")
            return errors
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} 不在允许值中")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0): errors.append(f"{path}: 字符串过短")
        if "pattern" in schema and not re.search(schema["pattern"], value): errors.append(f"{path}: 不匹配格式")
        if schema.get("format") == "date-time":
            try: datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError: errors.append(f"{path}: 不是 RFC 3339 时间")
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value < schema.get("minimum", value):
        errors.append(f"{path}: 小于最小值 {schema['minimum']}")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value: errors.append(f"{path}: 缺少 {key}")
        props = schema.get("properties", {})
        for key, child in value.items():
            if key in props: validate(child, props[key], f"{path}.{key}", errors)
            elif schema.get("additionalProperties") is False: errors.append(f"{path}: 未定义字段 {key}")
    return errors


def main():
    failures = 0
    for fixture_path in sorted(FIXTURE_DIR.glob("*.cases.json")):
        cases = json.loads(fixture_path.read_text(encoding="utf-8")); schema = load(cases["schema"])
        for i, item in enumerate(cases["valid"], 1):
            errors = validate(item, schema)
            print(f"PASS {fixture_path.name} valid#{i}" if not errors else f"FAIL {fixture_path.name} valid#{i}: {'; '.join(errors)}")
            failures += bool(errors)
        for i, item in enumerate(cases["invalid"], 1):
            errors = validate(item, schema)
            print(f"PASS {fixture_path.name} invalid#{i} rejected" if errors else f"FAIL {fixture_path.name} invalid#{i}: unexpectedly accepted")
            failures += not bool(errors)
    print(f"契约断言完成：{failures} 个失败")
    return 1 if failures else 0


if __name__ == "__main__": sys.exit(main())
