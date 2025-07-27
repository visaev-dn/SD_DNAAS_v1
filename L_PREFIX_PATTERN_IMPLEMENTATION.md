# L-Prefix Pattern Implementation

## Overview

This document describes the implementation of L-prefix pattern support in the bridge domain discovery system. L-prefix patterns represent **local scope** bridge domains that are configured locally on leaf devices and bridge local AC interfaces.

## L-Prefix Pattern Types

### 1. Basic L-Prefix Pattern
**Pattern**: `l_username_description`
**Example**: `l_gshafir_ISIS_R51_to_IXIA02`
**Scope**: Local
**VLAN ID**: None (null)
**Purpose**: Local configuration without VLAN ID

### 2. L-Prefix with VLAN Pattern
**Pattern**: `l_username_vvlan_description`
**Example**: `l_cchiriac_v1285_sysp65-kmv94_mxvmx5`
**Scope**: Local
**VLAN ID**: Extracted from pattern (e.g., 1285)
**Purpose**: Local configuration with VLAN ID

### 3. L-Prefix Simple VLAN Pattern
**Pattern**: `l_username_vvlan`
**Example**: `l_user_v123`
**Scope**: Local
**VLAN ID**: Extracted from pattern (e.g., 123)
**Purpose**: Simple local configuration with VLAN ID

## Implementation Details

### Service Name Analyzer Updates

The `ServiceNameAnalyzer` class has been enhanced with:

1. **New L-Prefix Patterns**:
   ```python
   # More specific patterns first (order matters)
   {
       'pattern': r'^l_([a-zA-Z0-9_-]+?)_v(\d+)_(.+)$',
       'method': 'l_prefix_vlan_pattern',
       'confidence': 90,
       'description': 'L-prefix with VLAN: l_username_vvlan_description (Local scope)',
       'scope': 'local'
   },
   {
       'pattern': r'^l_([a-zA-Z0-9_-]+?)_v(\d+)$',
       'method': 'l_prefix_simple_vlan_pattern',
       'confidence': 90,
       'description': 'L-prefix simple VLAN: l_username_vvlan (Local scope)',
       'scope': 'local'
   },
   {
       'pattern': r'^l_([a-zA-Z0-9_-]+?)_(.+)$',
       'method': 'l_prefix_pattern',
       'confidence': 90,
       'description': 'L-prefix format: l_username_description (Local scope)',
       'scope': 'local'
   }
   ```

2. **Scope Information**:
   - All L-prefix patterns are marked with `scope: 'local'`
   - Scope descriptions explain the local configuration purpose
   - Validation logic accounts for local scope (no penalty for missing VLAN ID)

3. **Enhanced Validation**:
   ```python
   def _validate_extracted_data(self, username: str, vlan_id: Optional[int], scope: str) -> int:
       # L-prefix patterns don't have VLAN IDs, which is expected for local scope
       if scope == 'local':
           score -= 0  # No penalty for local scope without VLAN ID
       else:
           score -= 5  # Small penalty for missing VLAN ID in other scopes
   ```

### Bridge Domain Discovery Updates

The `BridgeDomainDiscovery` class has been updated to include scope information:

1. **Enhanced Analysis**:
   ```python
   analyzed_bridge_domain = {
       'service_name': bridge_domain_name,
       'detected_username': service_analysis.get('username'),
       'detected_vlan': service_analysis.get('vlan_id'),
       'confidence': service_analysis.get('confidence', 0),
       'detection_method': service_analysis.get('method', 'unknown'),
       'scope': service_analysis.get('scope', 'unknown'),
       'scope_description': self.service_analyzer.get_scope_description(service_analysis.get('scope', 'unknown')),
       'interfaces': analyzed_interfaces,
       'admin_state': bridge_domain.get('admin_state', 'unknown'),
       'vlan_manipulation': None
   }
   ```

2. **JSON Structure Integration**:
   ```json
   {
     "bridge_domains": {
       "l_gshafir_ISIS_R51_to_IXIA02": {
         "service_name": "l_gshafir_ISIS_R51_to_IXIA02",
         "detected_username": "gshafir",
         "detected_vlan": null,
         "confidence": 90,
         "detection_method": "l_prefix_pattern",
         "scope": "local",
         "scope_description": "Local scope - configured locally on a leaf and bridge local AC interfaces",
         "topology_type": "p2p",
         "devices": {
           "DNAAS-LEAF-A11-2": {
             "interfaces": [
               {
                 "name": "ge100-0/0/10",
                 "type": "physical",
                 "vlan_id": null,
                 "role": "access"
               }
             ],
             "admin_state": "enabled",
             "device_type": "leaf"
           }
         }
       }
     }
   }
   ```

## Scope Classification

### Global Scope (G-Prefix)
- **Pattern**: `g_username_vvlan` or `g_username_vvlan_description`
- **Purpose**: Globally significant VLAN ID, can be configured everywhere
- **Example**: `g_visaev_v253`

### Local Scope (L-Prefix)
- **Pattern**: `l_username_description`, `l_username_vvlan_description`, or `l_username_vvlan`
- **Purpose**: Configured locally on a leaf and bridge local AC interfaces
- **Examples**: 
  - `l_gshafir_ISIS_R51_to_IXIA02` (no VLAN)
  - `l_cchiriac_v1285_sysp65-kmv94_mxvmx5` (with VLAN)

### Manual Scope (M-Prefix)
- **Pattern**: `M_username_vlan`
- **Purpose**: Manually configured bridge domains
- **Example**: `M_kazakov_1360`

### Unknown Scope
- **Pattern**: Other patterns that don't match known conventions
- **Purpose**: Unrecognized formats

## Testing

### Test Cases
The implementation includes comprehensive test cases:

```python
test_cases = [
    {
        'name': 'l_gshafir_ISIS_R51_to_IXIA02',
        'expected_username': 'gshafir',
        'expected_vlan': None,
        'expected_scope': 'local',
        'description': 'L-prefix without VLAN - local scope'
    },
    {
        'name': 'l_cchiriac_v1285_sysp65-kmv94_mxvmx5',
        'expected_username': 'cchiriac',
        'expected_vlan': 1285,
        'expected_scope': 'local',
        'description': 'L-prefix with VLAN - local scope'
    }
]
```

### Test Results
All L-prefix pattern tests pass successfully:
- ✅ Username extraction
- ✅ VLAN ID extraction (when present)
- ✅ Scope classification
- ✅ Confidence scoring
- ✅ Method identification

## Benefits

### 1. **Scope-Based Analysis**
```python
# Find all local scope bridge domains
local_bds = [bd for bd in data["bridge_domains"] 
             if data["bridge_domains"][bd]["scope"] == "local"]

# Find all global scope bridge domains
global_bds = [bd for bd in data["bridge_domains"] 
              if data["bridge_domains"][bd]["scope"] == "global"]
```

### 2. **Configuration Management**
- Distinguish between global and local configurations
- Apply appropriate configuration templates
- Validate scope-specific requirements

### 3. **Topology Analysis**
- Local scope bridge domains typically have `topology_type: "p2p"`
- Path complexity is usually "local" for single-device configurations
- Device count is typically 1 for local configurations

### 4. **Network Planning**
- Identify local vs global bridge domains
- Plan VLAN assignments appropriately
- Understand configuration scope and impact

## Usage Examples

### 1. **Pattern Recognition**
```python
analyzer = ServiceNameAnalyzer()
result = analyzer.extract_service_info('l_gshafir_ISIS_R51_to_IXIA02')

print(f"Username: {result['username']}")  # gshafir
print(f"VLAN ID: {result['vlan_id']}")   # None
print(f"Scope: {result['scope']}")       # local
print(f"Confidence: {result['confidence']}%")  # 90
```

### 2. **Scope Distribution Analysis**
```python
stats = analyzer.get_pattern_statistics(bridge_domain_names)
print(f"Local scope: {stats['scope_distribution']['local']}")
print(f"Global scope: {stats['scope_distribution']['global']}")
```

### 3. **JSON Structure Integration**
```python
# The bridge domain discovery engine automatically includes scope information
mapping = discovery_engine.run_discovery()

# Access scope information
for service_name, bridge_domain in mapping['bridge_domains'].items():
    scope = bridge_domain['scope']
    scope_desc = bridge_domain['scope_description']
    print(f"{service_name}: {scope} - {scope_desc}")
```

## Future Enhancements

### 1. **Enhanced L-Prefix Patterns**
- Support for more complex L-prefix patterns
- Better handling of special characters in descriptions
- Improved confidence scoring for edge cases

### 2. **Configuration Templates**
- Generate appropriate configuration templates based on scope
- Local scope templates for single-device configurations
- Global scope templates for multi-device configurations

### 3. **Validation Rules**
- Scope-specific validation rules
- Local scope: typically single device, no spine involvement
- Global scope: typically multi-device, spine involvement

### 4. **Reporting and Analytics**
- Scope-based reporting
- Configuration impact analysis
- Network planning recommendations

## Conclusion

The L-prefix pattern implementation successfully handles local scope bridge domains with proper scope classification, VLAN ID extraction, and JSON structure integration. The implementation provides:

- ✅ Accurate pattern recognition for L-prefix patterns
- ✅ Proper scope classification (local vs global)
- ✅ VLAN ID extraction when present
- ✅ Integration with bridge domain discovery system
- ✅ Comprehensive testing and validation
- ✅ Clear documentation and usage examples

This enhancement enables better network automation by distinguishing between global and local bridge domain configurations, improving configuration management and topology analysis. 