/** The versioned Studio facade. XDL and runtime decisions remain on the server. */
export type Data = Record<string, any>;
export interface Diagnostic {
  code: string;
  message: string;
  severity?: string;
  elementRef?: string;
  remediation?: string;
  source?: Data;
  [key: string]: any;
}
export interface Document {
  content: string;
  format: string;
  path: string;
}
export interface Project {
  projectId: string;
  name: string;
  revision: number;
  documents: Record<string, Document | string>;
  layout?: Data;
  presentationRevision?: number;
  manifest?: Data;
  [key: string]: any;
}
export interface CatalogEntry {
  id?: string;
  entryId?: string;
  name: string;
  description?: string;
  scope?: string;
  maturity?: string;
  limitations?: string[];
  expectedObservations?: string[];
  parameters?: Parameter[];
  [key: string]: any;
}
export interface Parameter {
  documentId?: string;
  scenarioRef?: string;
  id: string;
  label?: string;
  valueType?: string;
  type?: string;
  unit?: string;
  default?: unknown;
  value?: unknown;
  minimum?: number;
  maximum?: number;
  description?: string;
  source?: string;
  enum?: string[];
}
export interface Run {
  runId: string;
  snapshotId: string;
  projectId?: string;
  status?: string;
  state?: string;
  stateVersion: number;
  cleanup?: any;
  evidenceStatus?: string;
  capabilities?: any;
  [key: string]: any;
}
export interface RunEvent {
  schemaVersion?: string;
  eventId: string;
  runId: string;
  snapshotId: string;
  sequence: string;
  type: string;
  recordedAt: string;
  sourceTime?: Data;
  source?: Data;
  elementRefs?: string[];
  evidenceClass: string;
  payload: Data;
  evidenceRefs?: any[];
}
export interface Preflight {
  preflightId: string;
  snapshotId: string;
  status: string;
  diagnostics: Diagnostic[];
  expiresAt?: string;
  planDigest?: string;
  [key: string]: any;
}
export interface Page<T> {
  items: T[];
  nextCursor?: string | null;
}
