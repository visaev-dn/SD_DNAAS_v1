## Legacy Discovery → Phase 1 Conversion Research Plan

### Purpose
Document how to reliably convert legacy discovery outputs into Phase 1 topology structures, grounded in current code and aligned with template-driven goals. This will guide implementing a robust, low-error importer before expanding to full template support.

### What we need to answer (scope of this doc)
- VLAN source of truth and precedence across existing artifacts
- Destination resolution from discovery data (LLDP) with clear rules
- Safe interface normalization and matching policy
- Minimal viable template coverage now vs deferred (DOT1Q, ranges)
- Required-field gating and skip policy to avoid invalid Phase 1 objects
- Naming conventions parsing for fallback heuristics
- Where to integrate validation and reporting for traceability

### Constraints from Phase 1 data structures (enforced today)
- BridgeDomainConfig requirements (SINGLE_VLAN):
  - service_name, source_device, source_interface: non-empty
  - vlan_id: required (1–4094)
  - destinations: at least one {device, port}
- InterfaceInfo: name cannot be empty
- TopologyData: requires a non-null BridgeDomainConfig and lists of devices/interfaces/paths

### Current legacy discovery artifacts (where and what)
- Parsed outputs (by `scripts/collect_lacp_xml.py`):
  - `topology/configs/parsed_data/*_lacp_parsed_*.yaml`: LACP bundles with members
  - `topology/configs/parsed_data/*_lldp_parsed_*.yaml`: LLDP neighbors
  - `topology/configs/parsed_data/bridge_domain_parsed/*_bridge_domain_instance_parsed_*.yaml`: bridge-domain instance names and interfaces per device
  - `topology/configs/parsed_data/bridge_domain_parsed/*_vlan_config_parsed_*.yaml`: per-interface VLAN config details
- Discovery analysis engine:
  - `config_engine/bridge_domain_discovery.py` loads/analyzes instance and VLAN parsed files and can serve as a reference for interface/VLAN handling in the importer

### Signals we can leverage
- VLAN derivation
  - From VLAN parsed files: explicit `interface → vlan_id`
  - From interface naming: subinterface suffix (e.g., ge...X.Y → Y)
  - From service_name: patterns like `g_<user>_v<vid>` or `vlan<vid>_...`
- Source interface selection
  - Prefer first non-empty interface in BD instance; prefer subinterface when present
- Destination derivation (required)
  - From LLDP parsed files: neighbors where `local_interface` matches source interface (or its base without `.vid`)
  - Potentially multiple neighbors → P2MP destinations

### Interface normalization policy (initial)
- Base interface: strip subinterface suffix after last `.` for matching LLDP local_interface
- Accept both hyphenated and slash variants; normalize minimally (case-insensitive, collapse consecutive separators) while keeping original strings in output
- If no LLDP match on full subinterface, try base interface; otherwise skip BD as undetermined

### Template alignment and scope for first iteration
- Target now: TRUNK_SINGLE_VLAN_PER_BD (single VLAN per subinterface)
  - Requires: subinterface or clear VLAN association, no VLAN list
  - Map to Phase 1: BridgeDomainType.SINGLE_VLAN with `vlan_id`
- Defer (until more signals are integrated):
  - DOT1Q_* (push/pop detection not yet in parsed files)
  - VLAN_RANGE / VLAN_LIST (range/list parsing and consistency checks)

### Proposed conversion pipeline (V1)
1) Load parsed sets and build indexes:
   - vlan_by_device_interface: from `*_vlan_config_parsed_*.yaml`
   - lldp_by_device: from `*_lldp_parsed_*.yaml`
   - bd_instances: from `*_bridge_domain_instance_parsed_*.yaml`
2) For each device BD instance:
   - Choose source_interface: first valid; prefer subinterface
   - Derive vlan_id (precedence):
     1) vlan_by_device_interface[(device, source_interface)]
     2) subinterface suffix after `.`
     3) service_name pattern `v(\d{1,4})` or `vlan(\d{1,4})`
   - Derive destinations:
     - From LLDP: neighbors where `local_interface` equals source_interface; else equals base interface
     - Create one or many {device: neighbor_device, port: neighbor_interface}
   - Gate: require vlan_id, non-empty source_interface, ≥1 destination
   - Construct Phase 1 objects (DeviceInfo, InterfaceInfo, PathInfo, BridgeDomainConfig, TopologyData)
3) Validate Phase 1 structures via existing constructors or validator, log any violations
4) Persist via `Phase1DatabaseManager.save_topology_data`

### Skip policy and reporting (to ensure reliability)
- Skip BD records for any of the following, with counters and examples:
  - Missing VLAN after all heuristics
  - Empty source_interface
  - No LLDP destination match
- Produce a summary:
  - total BDs seen, converted, skipped (by reason)
  - top service-name patterns contributing to successful VLAN derivation
  - devices with the highest skip counts (to target data quality issues)

### Experiments and validation
- Dry-run on a representative subset (e.g., 5–10 devices) to verify:
  - Conversion success rate ≥ 80% for TRUNK_SINGLE_VLAN_PER_BD candidates
  - Zero Phase 1 validation errors at object construction time
  - LLDP-derived destinations look reasonable (spot-check)
- Metrics to collect per run:
  - Converted/Total, per device and overall
  - Reason distribution for skips
  - Average time per BD conversion

### Incremental roadmap
- Phase 1 (this doc): single-VLAN trunk conversion with LLDP destinations
- Phase 2: input normalization and alias maps (vendor variations), stronger interface matching
- Phase 3: introduce template detection fields (vlan_expression, push/pop flags) without schema changes
- Phase 4: enable DOT1Q variants by detecting push/pop from parsed configs
- Phase 5: support VLAN ranges/lists with template-aware validation

### Open questions to resolve with more study material
- Exact shapes of parsed YAMLs to finalize field names (LLDP, VLAN configs, BD instances)
- Known vendor alias mappings for interface names across LLDP vs config
- Presence and format of push/pop or manipulation signals in parsed outputs
- Additional service-name conventions beyond `v<vid>` and `vlan<vid>`

### Implementation notes (where to wire)
- Enhancements will live in `config_engine/enhanced_discovery_integration/auto_population_service.py`:
  - Build indexes from parsed files
  - Apply derivation heuristics and gating
  - Emit only valid Phase 1 objects to the database integration
- Keep importer robust: fail-soft (skip with reason), never write invalid Phase 1 structures

### Acceptance for V1
- Running the importer produces:
  - Non-zero number of saved topologies (SINGLE_VLAN cases)
  - Clear console/report summary with skip reasons
  - No Phase 1 validation exceptions during construction

---

## DNAAS Bridge-Domain Semantics and Their Impact on Conversion

This section distills the DNAAS "Bridge-Domains In-Depth" guidance into concrete detection rules and conversion implications. It aligns with the Template Design goals and informs our importer heuristics.

### Core DNAAS Concepts
- A bridge-domain forms an L2 broadcast domain; multiple BDs can exist per DN router.
- Interfaces (physical/bundle/subinterfaces) with `l2-service enabled` attach to BDs; VLAN behavior is applied at the interface, not the BD globally.
- Two BD types in DNAAS topology:
  - Local: intra-rack, configured only on LEAF; outer VLAN arbitrary per leaf.
  - Global: inter-rack, configured on LEAF and applied on uplinks (SPINE/Superspine); outer VLAN must be globally unique.
- Simplicity principle: prefer straightforward configurations; document with descriptive naming.

### Interface/VLAN Tagging Scenarios (mapping to templates)
1) Double-Tagged (outer-tag imposed at edge device)
   - Leaf matches on outer VLAN; subinterfaces use exact `vlan-id` (single).
   - Template alignment: TRUNK_SINGLE_VLAN_PER_BD (no push/pop on leaf).
   - Signals to detect:
     - Subinterface with single `vlan-id` equals outer tag
     - No push/pop configured on leaf interface

2A) Q-in-Q Tunnel (imposition on LEAF, all traffic to one BD)
   - Leaf subinterface `vlan-id list 1-4094` (full range), with `ingress push outer-tag X` and `egress pop`.
   - Template: DOT1Q_ALL_VLANS (LEAF imposition).
   - Signals:
     - Presence of push/pop on interface
     - `vlan-id list` equals full range

2B) Q-in-Q Tunnel (imposition on LEAF, split by original VLAN)
   - Multiple subinterfaces on same physical, each with a range mapping to distinct BDs; push/pop per subinterface.
   - Template: DOT1Q_SPLIT_VLAN_RANGES.
   - Signals:
     - Multiple subinterfaces on same base
     - Disjoint `vlan-id list` ranges
     - push/pop present

3) Hybrid
   - Mix of (1) on one side and (2A/2B) on the other.
   - Templates: combination (TRUNK_SINGLE + DOT1Q_*).
   - Signals:
     - As above, but across two interfaces within same BD

4) Single-tagged
   - Match by single-tag VLANs; often uses `vlan-id list` ranges (not full 1-4094) with no push/pop.
   - Template: TRUNK_MULTI_VLANS_PER_BD.
   - Signals:
     - `vlan-id list` with ranges
     - No push/pop

5) Port-Mode
   - Physical interfaces with `l2-service enabled`, no subinterface required; VLAN transported as-is.
   - Template: PORT_MODE.
   - Signals:
     - Physical interface (no subif) with `l2-service enabled`
     - No explicit `vlan-id` on subinterface because there is none

### Conversion Implications (Importer)
- The Phase 1 model requires a concrete `BridgeDomainConfig` with a type:
  - For SINGLE_VLAN (our current V1 scope), we must provide `vlan_id`.
  - For DOT1Q variants and TRUNK_MULTI (deferred), the `vlan_expression`/ranges and push/pop flags are needed.
- Given current parsed artifacts:
  - We can confidently target scenario (1) first: exact `vlan-id` on subinterfaces and no push/pop → TRUNK_SINGLE_VLAN_PER_BD.
  - Scenarios (2A/2B/4) require detecting `vlan-id list` plus push/pop (2A/2B) or ranges without push/pop (4). We will add once parser emits push/pop and list/range data in a normalized way.
  - Scenario (5) Port-Mode can be supported by detecting physical `l2-service enabled` with no subif; importer must allow BDs without `vlan_id` for PORT_MODE (requires Phase 1 support path or mapping to a compatible BD type).

### Heuristics to Derive Required Fields (refined)
- VLAN derivation (outer tag for TRUNK_SINGLE):
  1) From VLAN config parsed files (device+interface → vlan-id)
  2) From subinterface suffix (e.g., `.1360` → 1360)
  3) From service name (`g_<user>_v<vid>` or `vlan<vid>_*`)
- Push/Pop detection (for DOT1Q variants):
  - Presence of `vlan-manipulation ingress push` and `egress pop` in parsed data (deferred until available)
- Destinations via LLDP:
  - Match `local_interface == source_interface`; fallback to base interface (strip `.vid`)
  - Build ≥1 `{device, port}`; multiple neighbors → P2MP

### BD Type tagging (local vs global)
- Heuristic signals (optional metadata for Phase 1):
  - Local: interfaces remain on LEAF only; service_name prefix like `l_` may indicate local scope
  - Global: observed on uplinks (LEAF→SPINE/SSPINE) or names like `g_`
- Usage: populate optional metadata fields (when present) without gating conversion

### Gating Rules (to avoid invalid writes)
- For TRUNK_SINGLE_VLAN_PER_BD (V1): require
  - Non-empty `source_interface`
  - Valid `vlan_id` (1–4094)
  - ≥1 destination derived from LLDP
- Skip and report otherwise; defer DOT1Q or TRUNK_MULTI handling until parser signals are present

### Roadmap alignment with DNAAS
- V1 delivers reliable ingestion for scenario (1) and lays groundwork for (2A/2B/4/5) by:
  - Codifying interface normalization and LLDP destination discovery
  - Storing skip reasons to highlight where DOT1Q/push-pop detection is needed
- Future phases expand support as we ingest push/pop and `vlan-id list` details and integrate the template registry and matcher.


