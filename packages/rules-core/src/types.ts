export type Direction = "N" | "E" | "S" | "W";
export type Rotation = 0 | 90 | 180 | 270;
export type FeatureType = "field" | "road" | "city" | "river";
export type Role = "knight" | "thief" | "monk" | "farmer" | "abbot";
export type Zone = "left" | "center" | "right";

export interface Port { edge: Direction; zones: Zone[] }
export interface Segment {
  localSegmentId: string;
  featureType: FeatureType;
  ports: Port[];
  endsAtCenter?: boolean;
  symbols?: string[];
}
export interface CenterFeature { centerFeatureId: string; kind: "monastery" | "garden" }
export interface MeepleZone { targetRef: string; allowedPieces: ("meeple" | "abbot")[] }
export interface TileDefinition {
  tileDefinitionId: string;
  segments: Segment[];
  centerFeatures?: CenterFeature[];
  meepleZones: MeepleZone[];
}
export interface TileCatalog { catalogId: string; designs: TileDefinition[] }
export interface Ruleset {
  rulesetId: string;
  scoring: {
    roadPerTile: number;
    cityPerTileComplete: number;
    cityPerPennantComplete: number;
    monasteryBase: number;
    monasteryPerAdjacentTile: number;
    farmerPerCompletedCity: number;
    endgame: {
      roadPerTileIncomplete: number;
      cityPerTileIncomplete: number;
      cityPerPennantIncomplete: number;
      monasteryScoresAsPlaced: boolean;
      fieldScores: boolean;
      pennantsInIncompleteCitiesScore: boolean;
    };
    tieRule: "并列全分";
  };
}
export interface PlacedTile { x: number; y: number; tileDefinitionId: string; rotation: Rotation }
export interface PlacedPiece { player: number; x: number; y: number; role: Role; segmentId?: string }
export interface Scenario {
  scenarioId: string;
  given: { board: PlacedTile[]; meeples?: PlacedPiece[]; scores?: Record<string, number> };
  when: { action: "score-feature" | "endgame" | "place-piece" | "reclaim-abbot"; at?: {x:number;y:number}; piece?: {player:number;role:Role;segmentId?:string} };
  expect: { pointsAwarded: Record<string, number>; meeplesReturned?: {player:number;x:number;y:number}[]; actionAccepted?: boolean; rejectionCode?: string };
}
export interface ScenarioCatalog { scenarios: Scenario[] }
export interface RuleContent { ruleset: Ruleset; tiles: Map<string, TileDefinition> }
export interface ScenarioResult {
  pointsAwarded: Record<string, number>;
  returned: {player:number;x:number;y:number}[];
  actionAccepted?: boolean;
  rejectionCode?: string;
}
