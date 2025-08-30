# Templates Design: Integrating Interface/BD Templates into Data Structure and Discovery

## Goal
Introduce a first-class Template system to standardize how Layer-2 interface/subinterface modes and VLAN combinations are represented, detected during discovery/reverse-engineering, validated, and generated in configuration.

## Template Taxonomy (from provided background)
- Interface/Attachment Modes (top-level):
  - PORT_MODE
  - ACCESS
  - TRUNK
  - DOT1Q_TUNNEL
- Sub-variants:
  - TRUNK_SINGLE_VLAN_PER_BD (3A)
  - TRUNK_MULTI_VLANS_PER_BD (3B)
  - DOT1Q_ALL_VLANS (4A)
  - DOT1Q_SPLIT_VLAN_RANGES (4B)

Each template captures:
- Traffic operations (ingress/egress behavior)
- Detection rules (patterns over configs/topology)
- Normalized attributes (e.g., vlan-id vs vlan-id list, subinterface usage)
- DNAAS config generation logic (builder inputs)
- Equivalency notes vs Arista

## Data Model Extensions

Augment existing Phase 1 dataclasses (names referenced from `PHASE1_DEEP_DIVE_DESIGN.md`).

```python
# New enums
class TemplateCategory(Enum):
    PORT_MODE = "port_mode"
    ACCESS = "access"
    TRUNK = "trunk"
    DOT1Q_TUNNEL = "dot1q_tunnel"

class TemplateVariant(Enum):
    DEFAULT = "default"
    TRUNK_SINGLE_VLAN_PER_BD = "trunk_single_vlan_per_bd"
    TRUNK_MULTI_VLANS_PER_BD = "trunk_multi_vlans_per_bd"
    DOT1Q_ALL_VLANS = "dot1q_all_vlans"
    DOT1Q_SPLIT_VLAN_RANGES = "dot1q_split_vlan_ranges"

# New structures
@dataclass(frozen=True)
class TrafficOperations:
    ingress: str  # human-readable description
    egress: str   # human-readable description

@dataclass(frozen=True)
class TemplateRef:
    template_id: str
    category: TemplateCategory
    variant: TemplateVariant
    traffic: TrafficOperations
    # normalized parameters used by generators and validators
    params: Dict[str, Any] = field(default_factory=dict)

# Extensions to core models
@dataclass(frozen=True)
class InterfaceInfo:
    # ... existing fields ...
    applied_template: Optional[TemplateRef] = None
    # normalized VLAN expression: single, list, or ranges, always parsed to a canonical form
    vlan_expression: Optional[str] = None  # e.g. "100", "100,200,300", "1-4094", "100-199,300-399"
    # explicit manipulation flags inferred during discovery
    ingress_push: Optional[Dict[str, Any]] = None  # {outer-tag: 100, outer-tpid: "0x8100"}
    egress_pop: Optional[bool] = None
    swap_behavior: Optional[bool] = None  # indicates swap-to-egress-vlan behavior is expected

@dataclass(frozen=True)
class BridgeDomainConfig:
    # ... existing fields ...
    # Summary of templates used by member interfaces
    interface_templates: Dict[str, TemplateRef] = field(default_factory=dict)  # key: interface name

@dataclass(frozen=True)
class TopologyData:
    # ... existing fields ...
    # High-level summary of template usage
    template_summary: Dict[str, int] = field(default_factory=dict)  # {template_id: count}
```

## Template Schema (File-based)
Templates will be defined as YAML files and loaded at runtime into a registry.

```yaml
# templates/trunk_single_vlan_per_bd.yaml
id: trunk_single_vlan_per_bd
name: "Trunk (single VLAN per BD)"
category: trunk
variant: trunk_single_vlan_per_bd
traffic:
  ingress: "Match VLAN-ID; frame remains unmodified"
  egress: "If no VLAN → impose egress VLAN; if different VLAN → swap to egress VLAN"
params:
  expects_subinterfaces: true
  requires_vlan_id: true
  allows_vlan_list: false
  vlan_list_full_range: false
  requires_l2_service: true
  swap_on_egress: true
  uses_push_pop: false
matching:
  any:
    - interface:
        subinterface: true
        has_vlan_id_exact: true
        l2_service_enabled: true
    - dnaas:
        config_contains:
          - "interfaces <if>.{vlan} vlan-id {vlan}"
          - "interfaces <if>.{vlan} l2-service enabled"
  none:
    - interface:
        vlan_id_list: true
        vlan_full_range: true
examples:
  arista: |
    vlan 100
      name example
    interface Ethernet1/1
      switchport mode trunk
      switchport trunk allowed vlan 100
  dnaas: |
    interfaces ge100-0/0/0.100 l2-service enabled
    interfaces ge100-0/0/0.100 vlan-id 100
validation:
  - rule: require_subinterface_when_trunk_single
  - rule: forbid_vlan_list
```

Additional YAMLs for:
- `port_mode.yaml`
- `access.yaml` (requires push/pop)
- `trunk_multi_vlans_per_bd.yaml` (requires vlan-id list)
- `dot1q_all_vlans.yaml` (requires full 1-4094 list + push/pop)
- `dot1q_split_vlan_ranges.yaml` (requires ranges + push/pop per range)

## Template Engine

```python
class Template:
    def __init__(self, spec: Dict[str, Any]):
        self.id = spec['id']
        self.name = spec['name']
        self.category = TemplateCategory(spec['category'])
        self.variant = TemplateVariant(spec.get('variant', 'default'))
        self.traffic = TrafficOperations(**spec['traffic'])
        self.params = spec.get('params', {})
        self.matching = spec.get('matching', {})
        self.examples = spec.get('examples', {})
        self.validation_rules = spec.get('validation', [])

class TemplateRegistry:
    def __init__(self, templates_dir: str = "templates"):
        self.templates: Dict[str, Template] = {}
        self._load(templates_dir)

    def _load(self, path: str):
        # load all yaml files into Template instances
        pass

    def list(self) -> List[Template]:
        return list(self.templates.values())

    def get(self, template_id: str) -> Template:
        return self.templates[template_id]

class TemplateMatcher:
    def __init__(self, registry: TemplateRegistry):
        self.registry = registry

    def detect_for_interface(self, iface: InterfaceInfo, device_conf: Dict[str, Any]) -> Optional[TemplateRef]:
        # Evaluate matching criteria per template; return best match
        pass

class TemplateValidator:
    def validate_interface(self, iface: InterfaceInfo, tpl: Template) -> List[str]:
        # Apply template-specific validation rules; return list of errors
        pass
```

## Detection Rules (per template)

- PORT_MODE
  - Indicators: `l2-service enabled`, no `vlan-id`, no `vlan-manipulation`, no subinterface
- ACCESS
  - Indicators: `l2-service enabled`, `vlan-manipulation ingress push` + `egress pop`, no subinterface
- TRUNK_SINGLE_VLAN_PER_BD (3A)
  - Indicators: subinterface `.vlan`, `vlan-id <vlan>`, no `vlan-id list`
- TRUNK_MULTI_VLANS_PER_BD (3B)
  - Indicators: subinterface `.vlan`, `vlan-id list <ranges>`
- DOT1Q_ALL_VLANS (4A)
  - Indicators: subinterface `.vlan`, `vlan-id list 1-4094`, with push/pop configured
- DOT1Q_SPLIT_VLAN_RANGES (4B)
  - Indicators: subinterface `.vlan`, `vlan-id list <range A>`, push/pop specific outer-tag; multiple subinterfaces covering distinct ranges

Tie-breakers: prefer more specific templates (e.g., DOT1Q over TRUNK when push/pop present + full range).

## Discovery Integration

- EnhancedTopologyScanner parsing step emits normalized `InterfaceInfo` with:
  - `vlan_expression` parsed from `vlan-id`, `vlan-id list`
  - `ingress_push`, `egress_pop`, `swap_behavior` inferred from `vlan-manipulation`
- `TemplateMatcher.detect_for_interface` assigns `applied_template` per interface
- `BridgeDomainConfig.interface_templates[iface.name] = applied_template`
- Populate `TopologyData.template_summary`

Pipeline insert points:
1) After config parse per device/interface → detect template
2) After BD membership determination → validate cross-interface consistency

## Reverse-Engineering Integration

- Use templates to derive builder inputs rapidly:
  - PORT_MODE: BD with member interfaces (no VLAN param)
  - ACCESS: BD with member interfaces + push/pop params
  - TRUNK_SINGLE: BD per outer VLAN; subinterface per VLAN
  - TRUNK_MULTI: BD with vlan ranges; single subinterface per range
  - DOT1Q: BD per outer VLAN/range + push/pop
- Template-driven generators produce `GeneratedConfig` consistently

## Editing Integration (future)

- Allow switching `applied_template` for an interface in editor
- On change, recompute normalized `vlan_expression`, manipulation flags
- Re-validate BD consistency; regenerate preview config

## Validation Rules (examples)

- `require_subinterface_when_trunk_single`: interface name contains `.<vid>`
- `forbid_vlan_list`: `vlan_expression` must be single ID
- `require_push_pop_for_access_and_dot1q`: presence of ingress push and egress pop
- `full_range_for_dot1q_all`: `vlan_expression == "1-4094"`
- `disjoint_ranges_for_dot1q_split`: ensure no overlap between ranges across subinterfaces

## API Additions (minimal)

- GET `/api/v1/templates` → list available templates
- POST `/api/v1/interfaces/:id/apply-template` → apply template to interface (optional server-side)
- GET `/api/v1/configurations/:id/template-summary` → summary

## Storage (DB) Additions

- `TopologyDataModel.templates_data` (JSON): summary and per-interface applied templates
- Extend `PersonalBridgeDomain.topology_data` to include `applied_template` fields

## Examples (normalized InterfaceInfo per case)

```json
// ACCESS example (normalized)
{
  "name": "ge100-0/0/1",
  "device": "leaf1",
  "interface_type": "ethernet",
  "role": "access",
  "vlan_expression": "100",
  "ingress_push": {"outer-tag": 100, "outer-tpid": "0x8100"},
  "egress_pop": true,
  "swap_behavior": false,
  "applied_template": {
    "template_id": "access",
    "category": "access",
    "variant": "default",
    "traffic": {"ingress": "push VLAN", "egress": "pop VLAN"},
    "params": {"requires_l2_service": true}
  }
}
```

## Implementation Plan (direct, no backward compatibility)

1) Create `config_engine/templates/` registry and YAML specs
2) Implement `TemplateRegistry`, `TemplateMatcher`, `TemplateValidator`
3) Extend config parser to emit normalized interface attributes
4) Integrate detection into EnhancedTopologyScanner
5) Extend dataclasses and DB serializations
6) Add minimal API to list templates and expose template summaries
7) Tests: unit (matcher/validator), integration (scanner → templates), golden samples per case

## Risks & Mitigations
- Ambiguous matches → scoring + tie-breakers; fall back to safest (TRUNK vs DOT1Q based on push/pop)
- Incomplete configs → mark template as unknown with warnings; allow manual override in editor
- Vendor differences → keep matching rules modular; allow per-vendor overrides in YAML

## Deliverables
- Template YAMLs for: `port_mode`, `access`, `trunk_single_vlan_per_bd`, `trunk_multi_vlans_per_bd`, `dot1q_all_vlans`, `dot1q_split_vlan_ranges`
- Template engine modules and integration into discovery
- Updated data models and serialization
- Minimal API exposure and tests

## Bridge-Domain Semantics and Mapping (DNAAS-aligned)

- Bridge-domain: L2 broadcast domain anchored on a DN router. Interfaces with `l2-service enabled` join a BD. VLAN operations are defined per interface, not per BD.
- BD types:
  - `LOCAL`: intra-rack; applied on LEAF only; outer VLAN can be arbitrary per leaf
  - `GLOBAL`: inter-rack; applied on uplinks (SPINE/Superspine); outer VLAN must be globally unique
- Outer tag imposition:
  - `EDGE`: double-tagging applied at edge device; leaf matches outer VLAN only (scenario 1)
  - `LEAF`: leaf pushes/pops outer tag (Q-in-Q, scenarios 2A/2B)

### Mapping scenarios → templates
- 1) Double-Tagged (outer-tag at edge): TRUNK_SINGLE_VLAN_PER_BD with `params.double_tagged_on_edge=true` and BD `outer_tag_imposition=EDGE`
- 2A) Q-in-Q (all VLANs to one BD): DOT1Q_ALL_VLANS (full range 1–4094 + push/pop), `outer_tag_imposition=LEAF`
- 2B) Q-in-Q (split by original VLAN-ID): DOT1Q_SPLIT_VLAN_RANGES (disjoint ranges + push/pop), `outer_tag_imposition=LEAF`
- 3) Hybrid: mixture of the above on different interfaces within same BD
- 4) Single-tagged (range match, no manipulation): TRUNK_MULTI_VLANS_PER_BD
- 5) Port-Mode: PORT_MODE

## Data Model Additions (BD semantics)

```python
class BridgeDomainType(Enum):
    LOCAL = "local"
    GLOBAL = "global"

class OuterTagImposition(Enum):
    EDGE = "edge"
    LEAF = "leaf"

# Extend BridgeDomainConfig
@dataclass(frozen=True)
class BridgeDomainConfig:
    # ... existing fields ...
    bd_type: Optional[BridgeDomainType] = None
    outer_tag_imposition: Optional[OuterTagImposition] = None
    interface_templates: Dict[str, TemplateRef] = field(default_factory=dict)

# Topology-wide template usage summary
@dataclass(frozen=True)
class TopologyData:
    # ... existing fields ...
    template_summary: Dict[str, int] = field(default_factory=dict)
```

## Template params (outer-tag support)

Augment template `params` where relevant:
- `double_tagged_on_edge: bool` (scenario 1)
- `outer_tag_value: Optional[int]` (for DOT1Q variants)
- `outer_tpid: Optional[str]` (e.g., `0x8100`)

Example addition:
```yaml
params:
  expects_subinterfaces: true
  requires_vlan_id: true
  double_tagged_on_edge: true  # informs generators/validators
```

## Detection updates
- If push/pop found → prefer DOT1Q variants; if vlan list is `1-4094` → DOT1Q_ALL_VLANS.
- If multiple subifs with disjoint ranges + push/pop → DOT1Q_SPLIT_VLAN_RANGES.
- If subif with exact `vlan-id` and no push/pop → TRUNK_SINGLE.
- If vlan-id list (ranges) and no push/pop → TRUNK_MULTI.
- If physical `l2-service`, no VLAN constructs → PORT_MODE.
- Set BD `bd_type` by placement (leaf-only vs applied uplinks) and naming/policy. Set `outer_tag_imposition` by presence of push/pop (LEAF) vs none (EDGE).
