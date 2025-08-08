## Reverse Engineering Improvements and Integration Plan

### Goals
- Make reverse-engineered bridge domains first-class, editable configurations alongside manual ones
- Ensure end-to-end flow: import → scan → reverse-engineer → edit → validate → deploy → refresh-from-scan
- Provide observability, safety, and versioning for iterative refinement

### Current strengths
- Reverse-engineering core maps/scans to builder-ready format and generates configs
- API endpoint in place; scanner stabilized; DebugWindow wired

### Gaps to address
- Fragmented listing of imported BDs vs configurations
- Limited metadata (vlan_id, builder_input) to support editing round-trip
- No idempotent refresh from latest scan / version history
- Session/transaction boundaries can detach ORM instances

### Key improvements
- **Unify data model**
  - Add fields on `Configuration`: `config_source` (manual|reverse_engineered), `builder_type`, `topology_type`, `derived_from_scan_id`
  - Keep `Configuration.original_bridge_domain_id` linking back to `PersonalBridgeDomain`
  - Persist normalized `builder_input` JSON (source device, vlan_id, destinations, interfaces)

- **Combined listing and filtering**
  - `GET /api/configurations`: return one combined list with `type`=`configuration|imported_bridge_domain` and `source`=`manual|reverse_engineered`
  - Filters: `?source=reverse_engineered|manual`, `?bridgeDomain=<name>`

- **Reverse-engineer engine quality**
  - Canonical source/destination selection: prefer leaf as source; prefer ge* over bundle*; strip `.vlan` suffixes
  - Persist metadata: `vlan_id`, device roles, path summary, confidence/coverage
  - Idempotency: if a reverse-engineered config for BD exists, return it; allow `force=true` to rebuild from latest scan

- **Update/refresh flow**
  - “Refresh from latest scan”: compute diff against editor state, propose non-destructive updates
  - Versioning: `version`, `parent_config_id`; maintain change history

- **Editor UX**
  - Open reverse-engineered configs in same editor via stored `builder_input`
  - Validate on edit (device/port existence, vlan access, topology constraints); show per-device CLI preview

- **API additions**
  - `GET /api/configurations?source=reverse_engineered`
  - `POST /api/configurations/<bridge_domain>/reverse-engineer?force=true`
  - `GET /api/configurations/<id>/builder-input`
  - `PUT /api/configurations/<id>/builder-input`
  - `POST /api/configurations/<id>/refresh-from-scan`

- **Robustness & safety**
  - Single transaction: create `Configuration` + update `PersonalBridgeDomain` then commit (avoid detached instances)
  - Strict schema for `path_data`/`topology_data` with explicit errors
  - Enforce VLAN-range and ownership on import/reverse-engineer/edit

- **Observability**
  - Attach `logs[]` and `metrics{}` to reverse-engineer responses; stream via WebSocket to DebugWindow
  - Store last reverse-engineer logs in `config_metadata`

- **Performance**
  - Cache latest scan per BD; recompute only with `force=true`
  - Summarize heavy `topology_data` for UI; lazy-load details

### Schema changes (proposed)
- Table `configurations`:
  - Add: `config_source VARCHAR(32)`, `builder_type VARCHAR(32)`, `topology_type VARCHAR(32)`, `derived_from_scan_id INTEGER`, `builder_input TEXT`
- Table `personal_bridge_domains`:
  - Add: `builder_type`, `topology_type`, `config_source` persisted when reverse-engineered

Migration considerations
- Backfill existing configs with `config_source='manual'`
- For existing reverse-engineered configs, populate `config_source='reverse_engineered'` when identifiable

### Endpoints (details)
- `POST /api/configurations/<bridge_domain>/reverse-engineer?force=true`
  - If existing reverse-engineered config and `force` not set: return existing with 200
  - With `force=true`: create new version; link to BD; set `derived_from_scan_id`

- `GET/PUT /api/configurations/<id>/builder-input`
  - Get or update normalized builder input used by editor and generators

- `POST /api/configurations/<id>/refresh-from-scan`
  - Load latest scan for linked BD, compute diff vs current `builder_input`, return suggested changes (no auto-apply)

### Implementation plan (phased)

#### Phase 4.26 – Data model + API surface
- [ ] DB migration: new fields on `configurations` and `personal_bridge_domains`
- [ ] Update reverse-engineer engine to persist `vlan_id`, `builder_input`, `config_source`, `derived_from_scan_id`
- [ ] Extend `GET /api/configurations` response with `type`, `source`, filters support
- [ ] Add `GET/PUT /api/configurations/<id>/builder-input`

#### Phase 4.27 – Editor integration
- [ ] Add “Reverse Engineer to Editable Config” action on Configurations list
- [ ] Editor opens with `builder_input`; validation and CLI preview
- [ ] Enforce VLAN-range and ownership in editor save

#### Phase 4.28 – Refresh and versioning
- [ ] Implement `POST /api/configurations/<id>/refresh-from-scan` diffing
- [ ] Version fields (`version`, `parent_config_id`), history view on UI
- [ ] Idempotent reverse-engineer with `force=true` and link updates

#### Phase 4.29 – Observability & UX polish
- [ ] Log/metrics stream to DebugWindow during reverse-engineer
- [ ] Badges in UI: Reverse-engineered, Draft/Active/Deployed
- [ ] Performance: scan cache, lazy details

### Testing
- Unit: topology mapper (device/interface/vlan extraction), generator (P2P/P2MP/unified), API validation
- Integration: reverse-engineer endpoint behavior (existing vs force), builder-input GET/PUT
- E2E: import → scan → reverse-engineer → edit → validate → deploy → refresh-from-scan

### Risks and mitigations
- Detached ORM/session issues → single transaction, consistent app context
- Incomplete scan data → strict schema validation and actionable errors
- Overwriting user edits on refresh → diff-only suggestions, explicit user approval

### Alignment to main plan
- Extends Phase 4.25 (Reverse Engineering) with 4.26–4.29 increments
- Keeps unified builder as the common execution path; reverse-engineered entries become first-class citizens

### Success criteria
- Reverse-engineered items appear alongside manual configs with clear source metadata
- Editor can open, validate, and deploy reverse-engineered configs
- Refresh-from-scan provides safe, auditable updates without losing user edits 