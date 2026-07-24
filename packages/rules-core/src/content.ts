import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { Ajv2020, type ValidateFunction } from "ajv/dist/2020.js";
import type { RuleContent, Ruleset, Scenario, ScenarioCatalog, TileCatalog, TileDefinition } from "./types.js";

function readJson<T>(path: string): T {
  return JSON.parse(readFileSync(path, "utf8")) as T;
}

const ajv = new Ajv2020({allErrors:true,strict:true,allowUnionTypes:true});
const validators = new Map<string,ValidateFunction>();

function schemaValidator(root:string,name:string):ValidateFunction {
  const cached=validators.get(name);if(cached)return cached;
  const schema=readJson<object>(resolve(root,"content/schemas",name));const validate=ajv.compile(schema);validators.set(name,validate);return validate;
}

function validateWithSchema(root:string,name:string,value:unknown):void {
  const validate=schemaValidator(root,name);if(!validate(value))throw new Error(`${name} 校验失败：${ajv.errorsText(validate.errors,{separator:"；"})}`);
}

function assertObject(value: unknown, label: string): asserts value is Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(`${label} 必须是对象`);
}

export function validateRuleset(value: unknown): asserts value is Ruleset {
  assertObject(value, "ruleset");
  if (typeof value.rulesetId !== "string") throw new Error("rulesetId 缺失");
  assertObject(value.scoring, "scoring");
  for (const key of ["roadPerTile", "cityPerTileComplete", "cityPerPennantComplete", "monasteryBase", "monasteryPerAdjacentTile", "farmerPerCompletedCity"] as const) {
    if (!Number.isSafeInteger(value.scoring[key])) throw new Error(`scoring.${key} 必须是安全整数`);
  }
}

export function validateCatalog(value: unknown): asserts value is TileCatalog {
  assertObject(value, "catalog");
  if (typeof value.catalogId !== "string" || !Array.isArray(value.designs)) throw new Error("无效地块目录");
  for (const design of value.designs as TileDefinition[]) {
    if (typeof design.tileDefinitionId !== "string" || !Array.isArray(design.segments) || !Array.isArray(design.meepleZones)) {
      throw new Error("无效地块定义");
    }
  }
}

export function loadContent(root = process.cwd()): RuleContent {
  const rulesetValue: unknown = readJson(resolve(root, "content/rulesets/base-current.json"));
  validateWithSchema(root,"ruleset-manifest.schema.json",rulesetValue);
  validateRuleset(rulesetValue);
  const tiles = new Map<string, TileDefinition>();
  for (const name of ["base-current.json", "river-current.json"]) {
    const catalogValue: unknown = readJson(resolve(root, "content/tiles", name));
    validateWithSchema(root,"tile-definition.schema.json",catalogValue);
    validateCatalog(catalogValue);
    for (const design of catalogValue.designs) tiles.set(design.tileDefinitionId, design);
  }
  return { ruleset: rulesetValue, tiles };
}

export function loadScenarios(root = process.cwd()): Scenario[] {
  const catalogValue:unknown=readJson(resolve(root,"content/scenarios/base-current-official-examples.json"));
  validateWithSchema(root,"scenario.schema.json",catalogValue);
  const catalog=catalogValue as ScenarioCatalog;
  if (!Array.isArray(catalog.scenarios)) throw new Error("无效场景目录");
  return catalog.scenarios;
}
