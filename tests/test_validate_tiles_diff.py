#!/usr/bin/env python3
import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "content-validator" / "validate_tiles.py"
SPEC = importlib.util.spec_from_file_location("validate_tiles", MODULE_PATH)
validate_tiles = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_tiles)


class SemanticDiffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / "content" / "tiles" / "base-current.json").read_text(encoding="utf-8"))

    def test_self_comparison_is_equal(self):
        for design in self.catalog["designs"]:
            self.assertEqual(validate_tiles.semantic_design(design), validate_tiles.semantic_design(copy.deepcopy(design)))

    def test_segment_and_json_order_do_not_matter(self):
        design = copy.deepcopy(self.catalog["designs"][0])
        reordered = copy.deepcopy(design)
        reordered["segments"].reverse()
        for segment in reordered["segments"]:
            segment["ports"].reverse()
        self.assertEqual(validate_tiles.semantic_design(design), validate_tiles.semantic_design(reordered))

    def test_changed_port_is_detected(self):
        original = copy.deepcopy(self.catalog["designs"][0])
        changed = copy.deepcopy(original)
        changed["segments"][0]["ports"][0]["zones"] = ["left"]
        self.assertNotEqual(validate_tiles.semantic_design(original), validate_tiles.semantic_design(changed))

    def test_changed_copy_count_is_detected(self):
        original = copy.deepcopy(self.catalog["designs"][0])
        changed = copy.deepcopy(original)
        changed["copiesInPool"] += 1
        self.assertNotEqual(validate_tiles.semantic_design(original), validate_tiles.semantic_design(changed))


if __name__ == "__main__":
    unittest.main()
