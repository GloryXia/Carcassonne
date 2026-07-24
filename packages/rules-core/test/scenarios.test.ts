import assert from "node:assert/strict";
import test from "node:test";
import { executeScenario, loadContent, loadScenarios, replay, stateFingerprint, validateTilePlacement } from "../src/index.js";

const content = loadContent();
const scenarios = loadScenarios();

for (const scenario of scenarios) {
  test(`官方场景：${scenario.scenarioId}`, () => {
    const actual = executeScenario(scenario, content);
    assert.deepEqual(actual.pointsAwarded, scenario.expect.pointsAwarded);
    if (scenario.expect.meeplesReturned) {
      const expected = [...scenario.expect.meeplesReturned].sort((a,b)=>a.player-b.player||a.y-b.y||a.x-b.x);
      assert.deepEqual(actual.returned, expected);
    }
    if (scenario.expect.actionAccepted !== undefined) assert.equal(actual.actionAccepted, scenario.expect.actionAccepted);
    if (scenario.expect.rejectionCode !== undefined) assert.equal(actual.rejectionCode, scenario.expect.rejectionCode);
  });
}

test("地块放置拒绝不匹配边缘", () => {
  const board = [{x:0,y:0,tileDefinitionId:"base-current.road-straight",rotation:0 as const}];
  assert.equal(validateTilePlacement(board,{x:1,y:0,tileDefinitionId:"base-current.city-cap",rotation:0},content),"RULE_TILE_EDGES_MISMATCH");
});

test("规范指纹忽略对象键插入顺序", () => {
  assert.equal(stateFingerprint({a:1,b:{c:2}}),stateFingerprint({b:{c:2},a:1}));
});

test("一万次相同重放得到同一指纹", () => {
  const events = [(state:{revision:number;score:number})=>({...state,revision:state.revision+1,score:state.score+2})];
  const expected = stateFingerprint(replay({revision:0,score:0},events));
  for(let index=0;index<10_000;index++) assert.equal(stateFingerprint(replay({revision:0,score:0},events)),expected);
});
