import { createHash } from "node:crypto";
import type { Direction, FeatureType, PlacedPiece, PlacedTile, Role, Rotation, RuleContent, Scenario, ScenarioResult, Segment, TileDefinition, Zone } from "./types.js";

const DIRECTIONS: Direction[] = ["N", "E", "S", "W"];
const DELTA: Record<Direction, readonly [number, number, Direction]> = {N:[0,1,"S"],E:[1,0,"W"],S:[0,-1,"N"],W:[-1,0,"E"]};
const ROLE_FEATURE: Record<Role, FeatureType | "center"> = {knight:"city",thief:"road",farmer:"field",monk:"center",abbot:"center"};
const MIRROR: Record<Zone, Zone> = {left:"right",center:"center",right:"left"};

interface TileRuntime extends PlacedTile { definition: TileDefinition }
interface Node { key:string; tile:TileRuntime; segment:Segment }
interface Component { id:string; featureType:FeatureType; nodes:Node[] }
interface Runtime { board:Map<string,TileRuntime>; nodes:Map<string,Node>; adjacency:Map<string,Set<string>>; components:Component[]; componentByNode:Map<string,Component> }

const posKey = (x:number,y:number) => `${x},${y}`;
const nodeKey = (x:number,y:number,id:string) => `${x},${y}:${id}`;

export function rotateDirection(direction: Direction, rotation: Rotation): Direction {
  return DIRECTIONS[(DIRECTIONS.indexOf(direction) + rotation / 90) % DIRECTIONS.length]!;
}

function rotatedPorts(segment: Segment, rotation: Rotation) {
  return segment.ports.map(port => ({edge: rotateDirection(port.edge, rotation), zones: port.zones}));
}

function terrainAtEdge(tile: TileRuntime, edge: Direction): FeatureType {
  const types = new Set(tile.definition.segments.filter(segment => rotatedPorts(segment,tile.rotation).some(port => port.edge === edge)).map(segment => segment.featureType));
  return types.has("city") ? "city" : types.has("river") ? "river" : types.has("road") ? "road" : "field";
}

export function validateTilePlacement(board: PlacedTile[], candidate: PlacedTile, content: RuleContent): string | null {
  if (board.some(tile => tile.x === candidate.x && tile.y === candidate.y)) return "RULE_TILE_POSITION_OCCUPIED";
  const definition = content.tiles.get(candidate.tileDefinitionId);
  if (!definition) return "RULE_TILE_NOT_CURRENT";
  const byPosition = new Map(board.map(tile => [posKey(tile.x,tile.y), {...tile,definition:content.tiles.get(tile.tileDefinitionId)!}]));
  const runtime: TileRuntime = {...candidate,definition};
  let neighbors = 0;
  for (const direction of DIRECTIONS) {
    const [dx,dy,opposite] = DELTA[direction];
    const neighbor = byPosition.get(posKey(candidate.x+dx,candidate.y+dy));
    if (!neighbor) continue;
    neighbors++;
    if (terrainAtEdge(runtime,direction) !== terrainAtEdge(neighbor,opposite)) return "RULE_TILE_EDGES_MISMATCH";
  }
  return board.length > 0 && neighbors === 0 ? "RULE_TILE_PLACEMENT_FORBIDDEN" : null;
}

function portsConnect(a:Node,b:Node,direction:Direction): boolean {
  const opposite = DELTA[direction][2];
  const ap = rotatedPorts(a.segment,a.tile.rotation).filter(port=>port.edge===direction);
  const bp = rotatedPorts(b.segment,b.tile.rotation).filter(port=>port.edge===opposite);
  return a.segment.featureType === b.segment.featureType && ap.some(left=>bp.some(right=>left.zones.some(zone=>right.zones.includes(MIRROR[zone]))));
}

function buildRuntime(board:PlacedTile[],content:RuleContent):Runtime {
  const placed = new Map<string,TileRuntime>();
  for (const tile of board) {
    const definition = content.tiles.get(tile.tileDefinitionId);
    if (!definition) throw new Error(`未知地块 ${tile.tileDefinitionId}`);
    if (placed.has(posKey(tile.x,tile.y))) throw new Error(`重复坐标 ${tile.x},${tile.y}`);
    placed.set(posKey(tile.x,tile.y), {...tile,definition});
  }
  const nodes = new Map<string,Node>();
  const adjacency = new Map<string,Set<string>>();
  for (const tile of placed.values()) for (const segment of tile.definition.segments) {
    const key=nodeKey(tile.x,tile.y,segment.localSegmentId); const node={key,tile,segment}; nodes.set(key,node); adjacency.set(key,new Set());
  }
  for (const node of nodes.values()) for (const direction of ["N","E"] as Direction[]) {
    const [dx,dy]=DELTA[direction]; const neighborTile=placed.get(posKey(node.tile.x+dx,node.tile.y+dy)); if(!neighborTile) continue;
    for(const segment of neighborTile.definition.segments){const other=nodes.get(nodeKey(neighborTile.x,neighborTile.y,segment.localSegmentId))!;if(portsConnect(node,other,direction)){adjacency.get(node.key)!.add(other.key);adjacency.get(other.key)!.add(node.key);}}
  }
  const components:Component[]=[]; const componentByNode=new Map<string,Component>(); const visited=new Set<string>();
  for(const node of nodes.values()){if(visited.has(node.key))continue;const stack=[node.key];const group:Node[]=[];visited.add(node.key);while(stack.length){const key=stack.pop()!;group.push(nodes.get(key)!);for(const next of adjacency.get(key)!)if(!visited.has(next)){visited.add(next);stack.push(next);}}group.sort((a,b)=>a.key.localeCompare(b.key));const component={id:group[0]!.key,featureType:group[0]!.segment.featureType,nodes:group};components.push(component);for(const n of group)componentByNode.set(n.key,component);}
  return {board:placed,nodes,adjacency,components,componentByNode};
}

function isComplete(component:Component,runtime:Runtime):boolean {
  if(component.featureType!=="road"&&component.featureType!=="city")return false;
  for(const node of component.nodes) for(const port of rotatedPorts(node.segment,node.tile.rotation)) {
    const [dx,dy]=DELTA[port.edge]; const neighbor=runtime.board.get(posKey(node.tile.x+dx,node.tile.y+dy));
    if(!neighbor)return false;
    const connected=neighbor.definition.segments.some(seg=>portsConnect(node,runtime.nodes.get(nodeKey(neighbor.x,neighbor.y,seg.localSegmentId))!,port.edge));
    if(!connected)return false;
  }
  return true;
}

function centerComplete(tile:TileRuntime,runtime:Runtime):boolean {
  for(let dx=-1;dx<=1;dx++)for(let dy=-1;dy<=1;dy++)if((dx!==0||dy!==0)&&!runtime.board.has(posKey(tile.x+dx,tile.y+dy)))return false;
  return true;
}
function adjacentCount(tile:TileRuntime,runtime:Runtime):number {let count=0;for(let dx=-1;dx<=1;dx++)for(let dy=-1;dy<=1;dy++)if((dx!==0||dy!==0)&&runtime.board.has(posKey(tile.x+dx,tile.y+dy)))count++;return count;}

function resolvePiece(piece:PlacedPiece,runtime:Runtime):{piece:PlacedPiece;component?:Component;center?:TileRuntime}{
  const tile=runtime.board.get(posKey(piece.x,piece.y));if(!tile)throw new Error("角色位于空坐标");const feature=ROLE_FEATURE[piece.role];
  if(feature==="center")return {piece,center:tile};
  const candidates=tile.definition.segments.filter(segment=>segment.featureType===feature);const segment=piece.segmentId?candidates.find(item=>item.localSegmentId===piece.segmentId):candidates[0];if(!segment)throw new Error(`角色 ${piece.role} 无目标段`);
  return {piece,component:runtime.componentByNode.get(nodeKey(tile.x,tile.y,segment.localSegmentId))!};
}

function winners(pieces:ReturnType<typeof resolvePiece>[]):number[]{const strength=new Map<number,number>();for(const entry of pieces)strength.set(entry.piece.player,(strength.get(entry.piece.player)??0)+1);const max=Math.max(...strength.values());return [...strength].filter(([,n])=>n===max).map(([p])=>p);}
function addPoints(target:Record<string,number>,players:number[],points:number){if(points===0)return;for(const player of players)target[String(player)]=(target[String(player)]??0)+points;}
function componentTileCount(component:Component){return new Set(component.nodes.map(node=>posKey(node.tile.x,node.tile.y))).size;}
function pennants(component:Component){return component.nodes.reduce((sum,node)=>sum+(node.segment.symbols?.filter(symbol=>symbol==="pennant").length??0),0);}

function scoreComponent(component:Component,entries:ReturnType<typeof resolvePiece>[],complete:boolean,endgame:boolean,content:RuleContent):number {
  const scoring=content.ruleset.scoring;
  if(component.featureType==="road")return componentTileCount(component)*(endgame&&!complete?scoring.endgame.roadPerTileIncomplete:scoring.roadPerTile);
  if(component.featureType==="city")return componentTileCount(component)*(endgame&&!complete?scoring.endgame.cityPerTileIncomplete:scoring.cityPerTileComplete)+pennants(component)*(endgame&&!complete?scoring.endgame.cityPerPennantIncomplete:scoring.cityPerPennantComplete);
  if(component.featureType==="field")return 0;
  return 0;
}

function scoreFields(runtime:Runtime,pieces:ReturnType<typeof resolvePiece>[],content:RuleContent,result:ScenarioResult){
  for(const field of runtime.components.filter(component=>component.featureType==="field")){
    const occupants=pieces.filter(entry=>entry.component===field);if(!occupants.length)continue;const cities=new Set<string>();
    for(const node of field.nodes)for(const segment of node.tile.definition.segments.filter(item=>item.featureType==="city")){const city=runtime.componentByNode.get(nodeKey(node.tile.x,node.tile.y,segment.localSegmentId))!;if(isComplete(city,runtime))cities.add(city.id);}
    addPoints(result.pointsAwarded,winners(occupants),cities.size*content.ruleset.scoring.farmerPerCompletedCity);
  }
}

export function executeScenario(scenario:Scenario,content:RuleContent):ScenarioResult {
  const runtime=buildRuntime(scenario.given.board,content);const resolved=(scenario.given.meeples??[]).map(piece=>resolvePiece(piece,runtime));const result:ScenarioResult={pointsAwarded:{},returned:[]};const action=scenario.when.action;
  if(action==="place-piece"){
    const at=scenario.when.at!;const candidate:{player:number;x:number;y:number;role:Role;segmentId?:string}={...scenario.when.piece!,x:at.x,y:at.y};const target=resolvePiece(candidate,runtime);const occupied=target.component?resolved.some(entry=>entry.component===target.component):resolved.some(entry=>entry.center===target.center);result.actionAccepted=!occupied;if(occupied)result.rejectionCode="FEATURE_OCCUPIED";return result;
  }
  if(action==="reclaim-abbot"){
    const at=scenario.when.at!;const entry=resolved.find(item=>item.piece.role==="abbot"&&item.piece.x===at.x&&item.piece.y===at.y);if(!entry?.center)throw new Error("召回位置没有修道院长");const score=content.ruleset.scoring.monasteryBase+adjacentCount(entry.center,runtime)*content.ruleset.scoring.monasteryPerAdjacentTile;addPoints(result.pointsAwarded,[entry.piece.player],score);result.returned.push({player:entry.piece.player,x:entry.piece.x,y:entry.piece.y});return result;
  }
  for(const component of runtime.components){const occupants=resolved.filter(entry=>entry.component===component);if(!occupants.length||component.featureType==="field")continue;const complete=isComplete(component,runtime);const includesAt=scenario.when.at?component.nodes.some(node=>node.tile.x===scenario.when.at!.x&&node.tile.y===scenario.when.at!.y):true;if(action==="score-feature"&&(!complete||!includesAt))continue;const score=scoreComponent(component,occupants,complete,action==="endgame",content);addPoints(result.pointsAwarded,winners(occupants),score);if(action==="score-feature")for(const entry of occupants)result.returned.push({player:entry.piece.player,x:entry.piece.x,y:entry.piece.y});}
  for(const entry of resolved.filter(item=>item.center)){
    const tile=entry.center!;const complete=centerComplete(tile,runtime);const relevant=scenario.when.at?Math.abs(tile.x-scenario.when.at.x)<=1&&Math.abs(tile.y-scenario.when.at.y)<=1:true;if(action==="score-feature"&&(!complete||!relevant))continue;const points=content.ruleset.scoring.monasteryBase+adjacentCount(tile,runtime)*content.ruleset.scoring.monasteryPerAdjacentTile;addPoints(result.pointsAwarded,[entry.piece.player],points);if(action==="score-feature")result.returned.push({player:entry.piece.player,x:entry.piece.x,y:entry.piece.y});}
  if(action==="endgame")scoreFields(runtime,resolved,content,result);
  result.returned.sort((a,b)=>a.player-b.player||a.y-b.y||a.x-b.x);return result;
}

function canonical(value:unknown):string {if(value===null||typeof value!=="object")return JSON.stringify(value);if(Array.isArray(value))return `[${value.map(canonical).join(",")}]`;return `{${Object.entries(value as Record<string,unknown>).sort(([a],[b])=>a.localeCompare(b)).map(([key,item])=>`${JSON.stringify(key)}:${canonical(item)}`).join(",")}}`;}
export function stateFingerprint(value:unknown):string{return createHash("sha256").update(canonical(value)).digest("hex");}
export function replay<T>(initial:T,events:((state:T)=>T)[]):T{return events.reduce((state,event)=>event(state),initial);}
