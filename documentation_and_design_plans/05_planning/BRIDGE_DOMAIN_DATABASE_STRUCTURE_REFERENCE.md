# Bridge Domain Database Structure Reference

**Date:** August 26, 2025  
**Purpose:** Comprehensive reference for developers to understand, troubleshoot, and optimize the bridge domain database structure  
**Status:** Current Production Structure

## 🎯 **Overview**

This document describes the **flat table structure** used to store bridge domain topology data. The design follows industry-standard relational database patterns used by Cisco, Juniper, VMware, and other major network vendors.

## 🏗️ **Database Architecture Principles**

### **Why Flat Tables?**
- **Data Integrity**: Foreign keys prevent orphaned records
- **Query Flexibility**: Can query any aspect of the data independently
- **Update Efficiency**: Change data in one place, affects everywhere
- **Industry Standard**: How professional network management systems work
- **Scalability**: Handles millions of records efficiently

### **Key Design Patterns**
- **Normalized Storage**: No data duplication, consistent relationships
- **Foreign Key Relationships**: Tables linked by IDs, not embedded data
- **Atomic Operations**: Each table stores one type of entity
- **Audit Trail**: Track when/how data was discovered, confidence levels

## 📊 **Table Structure & Relationships**

### **1. Bridge Domain Root Table**

```sql
-- Table: bridge_domains (was phase1_topology_data)
-- Purpose: Main container for each bridge domain service
-- Relationships: 1-to-many with all other tables

CREATE TABLE bridge_domains (
    id INTEGER PRIMARY KEY,                    -- Unique identifier
    bridge_domain_name VARCHAR(255) NOT NULL,  -- Service name (e.g., g_visaev_v251)
    topology_type VARCHAR(50) NOT NULL,        -- 'p2p' or 'p2mp'
    vlan_id INTEGER,                          -- VLAN ID (1-4094) or NULL
    discovered_at DATETIME NOT NULL,           -- When discovered
    scan_method VARCHAR(100),                  -- How discovered (cli_input, legacy_mapping, etc.)
    confidence_score FLOAT DEFAULT 0.0,       -- 0.0 to 1.0
    validation_status VARCHAR(50) DEFAULT 'pending', -- pending, valid, warning, error
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    legacy_config_id INTEGER,                  -- Link to legacy system (optional)
    legacy_bridge_domain_id INTEGER            -- Link to legacy system (optional)
);
```

**Key Fields:**
- `bridge_domain_name`: Unique identifier for the service
- `topology_type`: Point-to-point (P2P) or Point-to-multipoint (P2MP)
- `vlan_id`: VLAN assignment (required for single-VLAN BDs)
- `scan_method`: Discovery source (CLI input, legacy mapping, device scan, etc.)

### **2. Device Information Table**

```sql
-- Table: bd_devices (was phase1_device_info)
-- Purpose: Network devices involved in the bridge domain
-- Relationships: Belongs to bridge_domain, has-many interfaces

CREATE TABLE bd_devices (
    id INTEGER PRIMARY KEY,                    -- Unique identifier
    topology_id INTEGER NOT NULL,              -- Foreign key to bridge_domains
    name VARCHAR(255) NOT NULL,                -- Device name (e.g., DNAAS-LEAF-A05)
    device_type VARCHAR(50) NOT NULL,          -- 'leaf', 'spine', 'superspine'
    device_role VARCHAR(50) NOT NULL,          -- 'source', 'destination', 'transport'
    device_id VARCHAR(255),                    -- Device identifier (optional)
    row VARCHAR(10),                           -- Rack row (optional)
    rack VARCHAR(50),                          -- Rack identifier (optional)
    model VARCHAR(100),                        -- Device model (optional)
    serial_number VARCHAR(100),                -- Serial number (optional)
    discovered_at DATETIME NOT NULL,           -- When discovered
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    confidence_score FLOAT DEFAULT 0.0,       -- 0.0 to 1.0
    validation_status VARCHAR(50) DEFAULT 'pending'
);
```

**Key Fields:**
- `device_type`: LEAF (source), SPINE (transport), SUPERSPINE (transport)
- `device_role`: SOURCE (originates traffic), DESTINATION (receives traffic), TRANSPORT (carries traffic)
- `topology_id`: Links device to specific bridge domain

### **3. Interface Information Table**

```sql
-- Table: bd_interfaces (was phase1_interface_info)
-- Purpose: Network interfaces with VLAN assignments and configuration
-- Relationships: Belongs to bridge_domain and device

CREATE TABLE bd_interfaces (
    id INTEGER PRIMARY KEY,                    -- Unique identifier
    topology_id INTEGER NOT NULL,              -- Foreign key to bridge_domains
    device_id INTEGER NOT NULL,                -- Foreign key to bd_devices
    name VARCHAR(255) NOT NULL,                -- Interface name (e.g., ge100-0/0/20)
    interface_type VARCHAR(50) NOT NULL,       -- 'physical', 'bundle', 'subinterface'
    interface_role VARCHAR(50) NOT NULL,       -- 'access', 'uplink', 'transport'
    vlan_id INTEGER,                          -- VLAN ID assigned to interface
    l2_service_enabled BOOLEAN DEFAULT FALSE,  -- L2 service enabled
    outer_tag_imposition VARCHAR(50),          -- 'edge', 'core', 'none' (DNAAS-specific)
    bundle_id INTEGER,                         -- Bundle ID if part of bundle
    subinterface_id INTEGER,                   -- Subinterface ID if applicable
    speed VARCHAR(20),                         -- Interface speed (e.g., 10G, 100G)
    duplex VARCHAR(10),                        -- Duplex mode
    media_type VARCHAR(50),                    -- Media type
    description TEXT,                          -- Interface description
    mtu INTEGER,                               -- Maximum transmission unit
    connected_device VARCHAR(255),             -- Connected device name
    connected_interface VARCHAR(255),          -- Connected interface name
    connection_type VARCHAR(50) DEFAULT 'service', -- 'service', 'bundle', 'lag'
    discovered_at DATETIME NOT NULL,           -- When discovered
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    confidence_score FLOAT DEFAULT 0.0,       -- 0.0 to 1.0
    validation_status VARCHAR(50) DEFAULT 'pending'
);
```

**Key Fields:**
- `interface_type`: PHYSICAL (single port), BUNDLE (port channel), SUBINTERFACE (logical interface)
- `interface_role`: ACCESS (user traffic), UPLINK (network traffic), TRANSPORT (backbone)
- `vlan_id`: VLAN assignment (critical for bridge domain operation)
- `l2_service_enabled`: Whether interface participates in L2 services

### **4. Bridge Domain Configuration Table**

```sql
-- Table: bd_configs (was phase1_bridge_domain_config)
-- Purpose: Service configuration and source endpoint definition
-- Relationships: Belongs to bridge_domain, has-many destinations

CREATE TABLE bd_configs (
    id INTEGER PRIMARY KEY,                    -- Unique identifier
    topology_id INTEGER NOT NULL,              -- Foreign key to bridge_domains
    service_name VARCHAR(255) NOT NULL,        -- Service name (e.g., g_visaev_v251)
    bridge_domain_type VARCHAR(50) NOT NULL,   -- 'single_vlan', 'vlan_range', 'vlan_list', 'qinq'
    source_device VARCHAR(255) NOT NULL,       -- Source device name
    source_interface VARCHAR(255) NOT NULL,    -- Source interface name
    vlan_id INTEGER,                          -- VLAN ID (for single_vlan type)
    vlan_start INTEGER,                        -- Start VLAN (for vlan_range type)
    vlan_end INTEGER,                          -- End VLAN (for vlan_range type)
    vlan_list TEXT,                            -- JSON array of VLANs (for vlan_list type)
    outer_vlan INTEGER,                        -- Outer VLAN (for qinq type)
    inner_vlan INTEGER,                        -- Inner VLAN (for qinq type)
    outer_tag_imposition VARCHAR(50) DEFAULT 'edge', -- 'edge', 'core', 'none'
    bundle_id INTEGER,                         -- Bundle ID if applicable
    interface_number INTEGER,                  -- Interface number if applicable
    is_active BOOLEAN DEFAULT TRUE,            -- Whether BD is active
    is_deployed BOOLEAN DEFAULT FALSE,         -- Whether BD is deployed
    deployment_status VARCHAR(50) DEFAULT 'pending', -- pending, deploying, deployed, failed
    created_by VARCHAR(255),                   -- Who created this BD
    created_at DATETIME NOT NULL,              -- When created
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    confidence_score FLOAT DEFAULT 0.0,       -- 0.0 to 1.0
    validation_status VARCHAR(50) DEFAULT 'pending'
);
```

**Key Fields:**
- `bridge_domain_type`: Determines VLAN configuration requirements
- `source_device` + `source_interface`: Where traffic originates
- `vlan_*` fields: VLAN configuration based on BD type
- `outer_tag_imposition`: DNAAS-specific VLAN tagging behavior

### **5. Destination Endpoints Table**

```sql
-- Table: bd_destinations (was phase1_destinations)
-- Purpose: Target endpoints for bridge domain traffic
-- Relationships: Belongs to bridge domain configuration

CREATE TABLE bd_destinations (
    id INTEGER PRIMARY KEY,                    -- Unique identifier
    bridge_domain_config_id INTEGER NOT NULL,  -- Foreign key to bd_configs
    device VARCHAR(255) NOT NULL,              -- Destination device name
    port VARCHAR(255) NOT NULL,                -- Destination interface name
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Key Fields:**
- `device` + `port`: Destination endpoint specification
- `bridge_domain_config_id`: Links to specific BD configuration

### **6. Network Paths Table**

```sql
-- Table: bd_paths (was phase1_path_info)
-- Purpose: Network paths between source and destinations
-- Relationships: Belongs to bridge_domain, has-many segments

CREATE TABLE bd_paths (
    id INTEGER PRIMARY KEY,                    -- Unique identifier
    topology_id INTEGER NOT NULL,              -- Foreign key to bridge_domains
    path_name VARCHAR(255) NOT NULL,           -- Path identifier (e.g., LEAF-A05_to_SPINE-A09)
    path_type VARCHAR(50) NOT NULL,            -- 'p2p' or 'p2mp'
    source_device VARCHAR(255) NOT NULL,       -- Path source device
    dest_device VARCHAR(255) NOT NULL,         -- Path destination device
    total_hops INTEGER DEFAULT 0,              -- Number of hops in path
    path_cost FLOAT DEFAULT 0.0,              -- Path cost/metric
    is_active BOOLEAN DEFAULT TRUE,            -- Whether path is active
    is_redundant BOOLEAN DEFAULT FALSE,        -- Whether path is redundant
    discovered_at DATETIME NOT NULL,           -- When discovered
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    confidence_score FLOAT DEFAULT 0.0,       -- 0.0 to 1.0
    validation_status VARCHAR(50) DEFAULT 'pending'
);
```

**Key Fields:**
- `path_name`: Human-readable path identifier
- `source_device` + `dest_device`: Path endpoints
- `total_hops`: Path complexity (1 = direct, >1 = multi-hop)
- `is_redundant`: Whether this is a backup path

### **7. Path Segments Table**

```sql
-- Table: bd_path_segments (was phase1_path_segments)
-- Purpose: Individual hops/segments within network paths
-- Relationships: Belongs to path

CREATE TABLE bd_path_segments (
    id INTEGER PRIMARY KEY,                    -- Unique identifier
    path_id INTEGER NOT NULL,                  -- Foreign key to bd_paths
    source_device VARCHAR(255) NOT NULL,       -- Segment source device
    dest_device VARCHAR(255) NOT NULL,         -- Segment destination device
    source_interface VARCHAR(255) NOT NULL,    -- Source interface
    dest_interface VARCHAR(255) NOT NULL,      -- Destination interface
    segment_type VARCHAR(100) NOT NULL,        -- 'direct', 'leaf_to_spine', 'spine_to_spine'
    connection_type VARCHAR(50) DEFAULT 'direct', -- 'direct', 'bundle', 'lag'
    bundle_id INTEGER,                         -- Bundle ID if applicable
    bandwidth VARCHAR(20),                     -- Bandwidth (e.g., 10G, 100G)
    latency FLOAT,                             -- Latency in milliseconds
    discovered_at DATETIME NOT NULL,           -- When discovered
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    confidence_score FLOAT DEFAULT 0.0        -- 0.0 to 1.0
);
```

**Key Fields:**
- `segment_type`: Network segment classification
- `connection_type`: How devices are connected
- `bandwidth` + `latency`: Performance characteristics

## 🔗 **Relationship Diagram**

```
bridge_domains (1) ←→ (many) bd_devices
       ↓                    ↓
       ↓                    ↓
bd_configs (1) ←→ (many) bd_interfaces
       ↓
       ↓
bd_destinations (many)

bd_paths (many) ←→ (many) bd_path_segments
       ↓
       ↓
bridge_domains (1)
```

## 📋 **Data Population Requirements**

### **Minimum Required Data for Valid Bridge Domain**

1. **bridge_domains**: 1 row with `bridge_domain_name`, `topology_type`, `vlan_id`
2. **bd_devices**: At least 2 rows (source + at least 1 destination)
3. **bd_interfaces**: At least 2 rows (source + destination interfaces)
4. **bd_configs**: 1 row with `source_device`, `source_interface`
5. **bd_destinations**: At least 1 row with `device` + `port`
6. **bd_paths**: At least 1 row per destination
7. **bd_path_segments**: At least 1 row per path

### **Validation Rules**

- **VLAN Consistency**: All interfaces in same BD must have same VLAN ID
- **Device References**: All interfaces must reference valid devices
- **Path Continuity**: Path segments must form continuous routes
- **Role Assignment**: Source device must be LEAF, destinations typically SPINE/SUPERSPINE

## 🔍 **Common Query Patterns**

### **1. Get Complete Bridge Domain**
```sql
-- Get BD with all related data
SELECT * FROM bridge_domains bd
JOIN bd_devices dev ON dev.topology_id = bd.id
JOIN bd_interfaces intf ON intf.topology_id = bd.id
JOIN bd_configs cfg ON cfg.topology_id = bd.id
JOIN bd_destinations dest ON dest.bridge_domain_config_id = cfg.id
WHERE bd.bridge_domain_name = 'g_visaev_v251';
```

### **2. Find Devices by VLAN**
```sql
-- Find all devices using VLAN 251
SELECT DISTINCT dev.name, dev.device_type, dev.device_role
FROM bd_devices dev
JOIN bd_interfaces intf ON intf.device_id = dev.id
WHERE intf.vlan_id = 251;
```

### **3. Find P2MP Topologies**
```sql
-- Find all point-to-multipoint BDs
SELECT bd.bridge_domain_name, bd.vlan_id, COUNT(dest.id) as destination_count
FROM bridge_domains bd
JOIN bd_configs cfg ON cfg.topology_id = bd.id
JOIN bd_destinations dest ON dest.bridge_domain_config_id = cfg.id
WHERE bd.topology_type = 'p2mp'
GROUP BY bd.id, bd.bridge_domain_name, bd.vlan_id
HAVING COUNT(dest.id) > 1;
```

## 🚨 **Common Issues & Troubleshooting**

### **1. Missing VLAN ID**
```sql
-- Find BDs without VLAN assignment
SELECT bd.bridge_domain_name, bd.topology_type
FROM bridge_domains bd
WHERE bd.vlan_id IS NULL;
```

### **2. Orphaned Records**
```sql
-- Find interfaces without valid devices
SELECT intf.name, intf.device_id
FROM bd_interfaces intf
LEFT JOIN bd_devices dev ON intf.device_id = dev.id
WHERE dev.id IS NULL;
```

### **3. Inconsistent VLANs**
```sql
-- Find BDs with inconsistent VLAN assignments
SELECT bd.bridge_domain_name, bd.vlan_id, intf.vlan_id as interface_vlan
FROM bridge_domains bd
JOIN bd_interfaces intf ON intf.topology_id = bd.id
WHERE bd.vlan_id != intf.vlan_id;
```

## 🎯 **Optimization Opportunities**

### **1. Indexes for Performance**
```sql
-- Recommended indexes
CREATE INDEX idx_bd_name ON bridge_domains(bridge_domain_name);
CREATE INDEX idx_bd_vlan ON bridge_domains(vlan_id);
CREATE INDEX idx_dev_topology ON bd_devices(topology_id);
CREATE INDEX idx_intf_topology ON bd_interfaces(topology_id);
CREATE INDEX idx_intf_vlan ON bd_interfaces(vlan_id);
CREATE INDEX idx_path_topology ON bd_paths(topology_id);
```

### **2. Read Views for Common Queries**
```sql
-- View for BD summaries
CREATE VIEW v_bd_summary AS
SELECT 
    bd.id,
    bd.bridge_domain_name,
    bd.vlan_id,
    bd.topology_type,
    bd.validation_status,
    COUNT(DISTINCT dev.id) as device_count,
    COUNT(DISTINCT intf.id) as interface_count,
    COUNT(DISTINCT dest.id) as destination_count,
    COUNT(DISTINCT p.id) as path_count
FROM bridge_domains bd
LEFT JOIN bd_devices dev ON dev.topology_id = bd.id
LEFT JOIN bd_interfaces intf ON intf.topology_id = bd.id
LEFT JOIN bd_configs cfg ON cfg.topology_id = bd.id
LEFT JOIN bd_destinations dest ON dest.bridge_domain_config_id = cfg.id
LEFT JOIN bd_paths p ON p.topology_id = bd.id
GROUP BY bd.id, bd.bridge_domain_name, bd.vlan_id, bd.topology_type, bd.validation_status;
```

### **3. Denormalized Fields for Display**
```sql
-- Add summary fields to bridge_domains table
ALTER TABLE bridge_domains ADD COLUMN device_count INTEGER DEFAULT 0;
ALTER TABLE bridge_domains ADD COLUMN interface_count INTEGER DEFAULT 0;
ALTER TABLE bridge_domains ADD COLUMN destination_count INTEGER DEFAULT 0;
ALTER TABLE bridge_domains ADD COLUMN path_count INTEGER DEFAULT 0;
```

## 📚 **Related Documentation**

- **PHASE1_DEEP_DIVE_DESIGN.md**: Original design rationale
- **TEMPLATES_DESIGN.md**: Template system integration
- **LEGACY_TO_PHASE1_CONVERSION_RESEARCH.md**: Migration strategies
- **CLI_USER_INTERFACE_ANALYSIS_20250818_171500.md**: CLI integration patterns

## 🔄 **Future Enhancements**

### **Phase 2: Template System**
- Add `bd_templates` table for interface/BD template definitions
- Add `bd_template_assignments` for template-to-BD mappings
- Extend `bd_configs` with template-specific fields

### **Phase 3: Advanced Pathing**
- Add `bd_path_metrics` for performance data
- Add `bd_path_alerts` for path health monitoring
- Add `bd_path_history` for path change tracking

### **Phase 4: Integration & Monitoring**
- Add `bd_deployments` for deployment tracking
- Add `bd_audit_log` for change history
- Add `bd_health_checks` for validation results

---

**Note**: This structure follows industry best practices and is designed for scalability, maintainability, and data integrity. The complexity serves a purpose - providing a robust foundation for network automation and management.

## 📝 **Real-World Examples**

### **Example 1: Simple Point-to-Point Bridge Domain**

**Bridge Domain**: `g_visaev_v251` (Single VLAN, P2P topology)

**Database Storage**:
```sql
-- 1. Bridge Domain Root
INSERT INTO bridge_domains VALUES (
    1, 'g_visaev_v251', 'p2p', 251, '2025-08-26 10:00:00', 
    'legacy_mapping', 0.95, 'valid', '2025-08-26 10:00:00', '2025-08-26 10:00:00', 
    1001, 251
);

-- 2. Devices (Source + Destination)
INSERT INTO bd_devices VALUES (1, 1, 'DNAAS-LEAF-A05', 'leaf', 'source', 'LEAF-A05', 'A', '05', 'N9K-C93180YC-EX', 'ABC123', '2025-08-26 10:00:00', '2025-08-26 10:00:00', 0.95, 'valid');
INSERT INTO bd_devices VALUES (2, 1, 'DNAAS-SPINE-A09', 'spine', 'destination', 'SPINE-A09', 'A', '09', 'N9K-C93180YC-EX', 'DEF456', '2025-08-26 10:00:00', '2025-08-26 10:00:00', 0.95, 'valid');

-- 3. Interfaces
INSERT INTO bd_interfaces VALUES (1, 1, 1, 'ge100-0/0/20', 'physical', 'access', 251, TRUE, 'edge', NULL, NULL, '10G', 'full', 'SFP+', 'User access interface for VLAN 251', 1500, 'DNAAS-SPINE-A09', 'ge100-0/0/21', 'service', '2025-08-26 10:00:00', '2025-08-26 10:00:00', 0.95, 'valid');
INSERT INTO bd_interfaces VALUES (2, 1, 2, 'ge100-0/0/21', 'physical', 'uplink', 251, TRUE, 'core', NULL, NULL, '10G', 'full', 'SFP+', 'Uplink interface for VLAN 251', 1500, 'DNAAS-LEAF-A05', 'ge100-0/0/20', 'service', '2025-08-26 10:00:00', '2025-08-26 10:00:00', 0.95, 'valid');

-- 4. Bridge Domain Configuration
INSERT INTO bd_configs VALUES (1, 1, 'g_visaev_v251', 'single_vlan', 'DNAAS-LEAF-A05', 'ge100-0/0/20', 251, NULL, NULL, NULL, NULL, NULL, 'edge', NULL, NULL, TRUE, FALSE, 'pending', 'admin', '2025-08-26 10:00:00', '2025-08-26 10:00:00', 0.95, 'valid');

-- 5. Destination
INSERT INTO bd_destinations VALUES (1, 1, 'DNAAS-SPINE-A09', 'ge100-0/0/21', '2025-08-26 10:00:00');

-- 6. Network Path
INSERT INTO bd_paths VALUES (1, 1, 'LEAF-A05_to_SPINE-A09', 'p2p', 'DNAAS-LEAF-A05', 'DNAAS-SPINE-A09', 1, 1.0, TRUE, FALSE, '2025-08-26 10:00:00', '2025-08-26 10:00:00', 0.95, 'valid');

-- 7. Path Segment
INSERT INTO bd_path_segments VALUES (1, 1, 'DNAAS-LEAF-A05', 'DNAAS-SPINE-A09', 'ge100-0/0/20', 'ge100-0/0/21', 'direct', 'direct', NULL, '10G', 0.1, '2025-08-26 10:00:00', '2025-08-26 10:00:00', 0.95);
```

**What This Represents**:
- **Service**: `g_visaev_v251` (VLAN 251 service)
- **Source**: LEAF-A05 interface ge100-0/0/20
- **Destination**: SPINE-A09 interface ge100-0/0/21
- **Topology**: Direct connection (1 hop)
- **VLAN**: 251 on both interfaces

### **Example 2: Point-to-Multipoint Bridge Domain**

**Bridge Domain**: `g_visaev_v252` (Single VLAN, P2MP topology)

**Database Storage**:
```sql
-- 1. Bridge Domain Root
INSERT INTO bridge_domains VALUES (
    2, 'g_visaev_v252', 'p2mp', 252, '2025-08-26 10:00:00', 
    'legacy_mapping', 0.90, 'valid', '2025-08-26 10:00:00', '2025-08-26 10:00:00', 
    1002, 252
);

-- 2. Devices (1 Source + 3 Destinations)
INSERT INTO bd_devices VALUES (3, 2, 'DNAAS-LEAF-A06', 'leaf', 'source', 'LEAF-A06', 'A', '06', 'N9K-C93180YC-EX', 'GHI789', '2025-08-26 10:00:00', '2025-08-26 10:00:00', 0.90, 'valid');
INSERT INTO bd_devices VALUES (4, 2, 'DNAAS-SPINE-A10', 'spine', 'destination', 'SPINE-A10', 'A', '10', 'N9K-C93180YC-EX', 'JKL012', '2025-08-26 10:00:00', '2025-08-26 10:00:00', 0.90, 'valid');
INSERT INTO bd_devices VALUES (5, 2, 'DNAAS-SPINE-A11', 'spine', 'destination', 'SPINE-A11', 'A', '11', 'N9K-C93180YC-EX', 'MNO345', '2025-08-26 10:00:00', '2025-08-26 10:00:00', 0.90, 'valid');
INSERT INTO bd_devices VALUES (6, 2, 'DNAAS-SUPERSPINE-A01', 'superspine', 'destination', 'SUPERSPINE-A01', 'A', '01', 'N9K-C9500-32C', 'PQR678', '2025-08-26 10:00:00', '2025-08-26 10:00:00', 0.90, 'valid');

-- 3. Interfaces (1 Source + 3 Destinations)
INSERT INTO bd_interfaces VALUES (3, 2, 3, 'ge100-0/0/22', 'physical', 'access', 252, TRUE, 'edge', NULL, NULL, '10G', 'full', 'SFP+', 'User access interface for VLAN 252', 1500, NULL, NULL, 'service', '2025-08-26 10:00:00', '2025-08-26 10:00:00', 0.90, 'valid');
INSERT INTO bd_interfaces VALUES (4, 2, 4, 'ge100-0/0/23', 'physical', 'uplink', 252, TRUE, 'core', NULL, NULL, '10G', 'full', 'SFP+', 'Uplink interface for VLAN 252', 1500, 'DNAAS-LEAF-A06', 'ge100-0/0/22', 'service', '2025-08-26 10:00:00', '2025-08-26 10:00:00', 0.90, 'valid');
INSERT INTO bd_interfaces VALUES (5, 2, 5, 'ge100-0/0/24', 'physical', 'uplink', 252, TRUE, 'core', NULL, NULL, '10G', 'full', 'SFP+', 'Uplink interface for VLAN 252', 1500, 'DNAAS-LEAF-A06', 'ge100-0/0/22', 'service', '2025-08-26 10:00:00', '2025-08-26 10:00:00', 0.90, 'valid');
INSERT INTO bd_interfaces VALUES (6, 2, 6, 'ge100-0/0/25', 'physical', 'uplink', 252, TRUE, 'core', NULL, NULL, '100G', 'full', 'QSFP28', 'Uplink interface for VLAN 252', 1500, 'DNAAS-LEAF-A06', 'ge100-0/0/22', 'service', '2025-08-26 10:00:00', '2025-08-26 10:00:00', 0.90, 'valid');

-- 4. Bridge Domain Configuration
INSERT INTO bd_configs VALUES (2, 2, 'g_visaev_v252', 'single_vlan', 'DNAAS-LEAF-A06', 'ge100-0/0/22', 252, NULL, NULL, NULL, NULL, NULL, 'edge', NULL, NULL, TRUE, FALSE, 'pending', 'admin', '2025-08-26 10:00:00', '2025-08-26 10:00:00', 0.90, 'valid');

-- 5. Destinations (3 endpoints)
INSERT INTO bd_destinations VALUES (2, 2, 'DNAAS-SPINE-A10', 'ge100-0/0/23', '2025-08-26 10:00:00');
INSERT INTO bd_destinations VALUES (3, 2, 'DNAAS-SPINE-A11', 'ge100-0/0/24', '2025-08-26 10:00:00');
INSERT INTO bd_destinations VALUES (4, 2, 'DNAAS-SUPERSPINE-A01', 'ge100-0/0/25', '2025-08-26 10:00:00');

-- 6. Network Paths (3 paths)
INSERT INTO bd_paths VALUES (2, 2, 'LEAF-A06_to_SPINE-A10', 'p2p', 'DNAAS-LEAF-A06', 'DNAAS-SPINE-A10', 1, 1.0, TRUE, FALSE, '2025-08-26 10:00:00', '2025-08-26 10:00:00', 0.90, 'valid');
INSERT INTO bd_paths VALUES (3, 2, 'LEAF-A06_to_SPINE-A11', 'p2p', 'DNAAS-LEAF-A06', 'DNAAS-SPINE-A11', 1, 1.0, TRUE, FALSE, '2025-08-26 10:00:00', '2025-08-26 10:00:00', 0.90, 'valid');
INSERT INTO bd_paths VALUES (4, 2, 'LEAF-A06_to_SUPERSPINE-A01', 'p2p', 'DNAAS-LEAF-A06', 'DNAAS-SUPERSPINE-A01', 1, 1.0, TRUE, FALSE, '2025-08-26 10:00:00', '2025-08-26 10:00:00', 0.90, 'valid');

-- 7. Path Segments (3 direct connections)
INSERT INTO bd_path_segments VALUES (2, 2, 'DNAAS-LEAF-A06', 'DNAAS-SPINE-A10', 'ge100-0/0/22', 'ge100-0/0/23', 'direct', 'direct', NULL, '10G', 0.1, '2025-08-26 10:00:00', '2025-08-26 10:00:00', 0.90);
INSERT INTO bd_path_segments VALUES (3, 3, 'DNAAS-LEAF-A06', 'DNAAS-SPINE-A11', 'ge100-0/0/22', 'ge100-0/0/24', 'direct', 'direct', NULL, '10G', 0.1, '2025-08-26 10:00:00', '2025-08-26 10:00:00', 0.90);
INSERT INTO bd_path_segments VALUES (4, 4, 'DNAAS-LEAF-A06', 'DNAAS-SUPERSPINE-A01', 'ge100-0/0/22', 'ge100-0/0/25', 'direct', 'direct', NULL, '100G', 0.05, '2025-08-26 10:00:00', '2025-08-26 10:00:00', 0.90);
```

**What This Represents**:
- **Service**: `g_visaev_v252` (VLAN 252 service)
- **Source**: LEAF-A06 interface ge100-0/0/22
- **Destinations**: 3 different devices (2 SPINE, 1 SUPERSPINE)
- **Topology**: Star configuration (1 source, multiple destinations)
- **VLAN**: 252 on all interfaces

## 🖥️ **User/Admin Interaction Examples**

### **1. CLI Commands for Database Operations**

#### **View All Bridge Domains**
```bash
# Enhanced Database Menu → Option 1: View All Bridge Domains
python main.py
# Select: 8. Enhanced Database Operations
# Select: 1. View All Bridge Domains

# This shows:
# ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
# │ Bridge Domain Database Summary                                                           │
# ├─────────────────────────────────────────────────────────────────────────────────────────────┤
# │ Total Bridge Domains: 1,046                                                              │
# │ Valid: 1,042 | Warnings: 3 | Errors: 1                                                   │
# │ P2P: 856 | P2MP: 190                                                                    │
# │ VLANs: 1-4094 (251 unique VLANs)                                                        │
# └─────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### **View Specific Bridge Domain Details**
```bash
# Enhanced Database Menu → Option 2: View Specific Bridge Domain
# Enter BD name: g_visaev_v251

# This shows:
# ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
# │ Bridge Domain: g_visaev_v251                                                             │
# ├─────────────────────────────────────────────────────────────────────────────────────────────┤
# │ Status: ✅ Valid | Type: P2P | VLAN: 251                                                │
# │ Discovered: 2025-08-26 10:00:00 | Confidence: 95%                                      │
# │                                                                                           │
# │ Source Device: DNAAS-LEAF-A05 (ge100-0/0/20)                                            │
# │ Destination: DNAAS-SPINE-A09 (ge100-0/0/21)                                             │
# │                                                                                           │
# │ Path: LEAF-A05 → SPINE-A09 (1 hop, 10G, 0.1ms latency)                                 │
# │                                                                                           │
# │ Validation: ✅ VLAN consistency | ✅ Device references | ✅ Path continuity              │
# └─────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### **Search Bridge Domains by Criteria**
```bash
# Enhanced Database Menu → Option 3: Search Bridge Domains
# Search by: VLAN ID
# Enter VLAN: 251

# Results:
# ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
# │ VLAN 251 Bridge Domains                                                                  │
# ├─────────────────────────────────────────────────────────────────────────────────────────────┤
# │ 1. g_visaev_v251 (P2P) - LEAF-A05 → SPINE-A09                                          │
# │ 2. g_visaev_v251_backup (P2P) - LEAF-A05 → SPINE-A10                                   │
# │ 3. g_visaev_v251_redundant (P2P) - LEAF-A05 → SUPERSPINE-A01                            │
# └─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### **2. Web Frontend Views**

#### **Dashboard Overview**
```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ Bridge Domain Management Dashboard                                                        │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ 📊 Statistics                    🔍 Quick Search                                         │
│ • Total BDs: 1,046             • Search by name: [g_visaev_...] [Search]                │
│ • Active: 1,042                • Filter by VLAN: [251] [Filter]                         │
│ • Pending: 3                   • Filter by type: [P2P ▼] [Filter]                       │
│ • Errors: 1                    • Filter by status: [Valid ▼] [Filter]                   │
│                                                                                           │
│ 📋 Recent Bridge Domains                                                                  │
│ ┌─────────────────┬──────────┬─────────┬─────────────┬─────────────┬─────────────────────┐ │
│ │ Name            │ Type     │ VLAN    │ Status     │ Devices     │ Last Updated        │ │
│ ├─────────────────┼──────────┼─────────┼─────────────┼─────────────┼─────────────────────┤ │
│ │ g_visaev_v251   │ P2P      │ 251     │ ✅ Valid   │ 2           │ 2025-08-26 10:00    │ │
│ │ g_visaev_v252   │ P2MP     │ 252     │ ✅ Valid   │ 4           │ 2025-08-26 10:00    │ │
│ │ g_visaev_v253   │ P2P      │ 253     │ ⚠️ Warning │ 2           │ 2025-08-26 10:00    │ │
│ └─────────────────┴──────────┴─────────┴─────────────┴─────────────┴─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### **Bridge Domain Detail View**
```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ Bridge Domain: g_visaev_v251                    [Edit] [Deploy] [Delete] [Export]        │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ 📋 Basic Information                                                                      │
│ • Name: g_visaev_v251                                                                     │
│ • Type: Point-to-Point (P2P)                                                             │
│ • VLAN: 251                                                                               │
│ • Status: ✅ Valid                                                                        │
│ • Confidence: 95%                                                                         │
│ • Discovered: 2025-08-26 10:00:00                                                        │
│                                                                                           │
│ 🖥️ Devices & Interfaces                                                                   │
│ ┌─────────────────┬──────────┬─────────────┬─────────────┬───────────────────────────────┐ │
│ │ Device          │ Type     │ Role        │ Interface   │ VLAN    │ Status              │ │
│ ├─────────────────┼──────────┼─────────────┼─────────────┼─────────┼─────────────────────┤ │
│ │ DNAAS-LEAF-A05  │ LEAF     │ Source      │ ge100-0/0/20│ 251     │ ✅ Active           │ │
│ │ DNAAS-SPINE-A09 │ SPINE    │ Destination │ ge100-0/0/21│ 251     │ ✅ Active           │ │
│ └─────────────────┴──────────┴─────────────┴─────────────┴─────────┴─────────────────────┘ │
│                                                                                           │
│ 🛣️ Network Paths                                                                          │
│ • Path: LEAF-A05 → SPINE-A09                                                             │
│ • Hops: 1 (Direct connection)                                                             │
│ • Bandwidth: 10G                                                                          │
│ • Latency: 0.1ms                                                                          │
│ • Status: ✅ Active                                                                        │
│                                                                                           │
│ 📊 Validation Results                                                                     │
│ • VLAN Consistency: ✅ All interfaces use VLAN 251                                        │
│ • Device References: ✅ All interfaces reference valid devices                            │
│ • Path Continuity: ✅ Path segments form continuous route                                 │
│ • Role Assignment: ✅ Source is LEAF, destination is SPINE                                │
│                                                                                           │
│ 📝 Configuration                                                                           │
│ • Bridge Domain Type: Single VLAN                                                         │
│ • Outer Tag Imposition: Edge                                                              │
│ • L2 Service: Enabled on all interfaces                                                   │
│ • MTU: 1500 bytes                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### **3. API Endpoints for Programmatic Access**

#### **Get All Bridge Domains**
```bash
curl -X GET "http://localhost:5000/api/v1/bridge-domains" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Response:
{
  "status": "success",
  "data": {
    "total": 1046,
    "bridge_domains": [
      {
        "id": 1,
        "bridge_domain_name": "g_visaev_v251",
        "topology_type": "p2p",
        "vlan_id": 251,
        "validation_status": "valid",
        "confidence_score": 0.95,
        "device_count": 2,
        "interface_count": 2,
        "destination_count": 1,
        "path_count": 1
      }
    ]
  }
}
```

#### **Get Specific Bridge Domain with Full Details**
```bash
curl -X GET "http://localhost:5000/api/v1/bridge-domains/g_visaev_v251" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Response:
{
  "status": "success",
  "data": {
    "bridge_domain": {
      "id": 1,
      "bridge_domain_name": "g_visaev_v251",
      "topology_type": "p2p",
      "vlan_id": 251,
      "discovered_at": "2025-08-26T10:00:00Z",
      "validation_status": "valid",
      "confidence_score": 0.95,
      "devices": [
        {
          "id": 1,
          "name": "DNAAS-LEAF-A05",
          "device_type": "leaf",
          "device_role": "source",
          "interfaces": [
            {
              "id": 1,
              "name": "ge100-0/0/20",
              "interface_type": "physical",
              "interface_role": "access",
              "vlan_id": 251,
              "l2_service_enabled": true
            }
          ]
        }
      ],
      "paths": [
        {
          "id": 1,
          "path_name": "LEAF-A05_to_SPINE-A09",
          "source_device": "DNAAS-LEAF-A05",
          "dest_device": "DNAAS-SPINE-A09",
          "total_hops": 1,
          "segments": [
            {
              "source_device": "DNAAS-LEAF-A05",
              "dest_device": "DNAAS-SPINE-A09",
              "source_interface": "ge100-0/0/20",
              "dest_interface": "ge100-0/0/21",
              "bandwidth": "10G",
              "latency": 0.1
            }
          ]
        }
      ]
    }
  }
}
```

### **4. Database Direct Queries for Admins**

#### **Find All Bridge Domains Using Specific VLAN**
```sql
SELECT 
    bd.bridge_domain_name,
    bd.topology_type,
    bd.validation_status,
    COUNT(DISTINCT dev.id) as device_count,
    COUNT(DISTINCT dest.id) as destination_count
FROM bridge_domains bd
LEFT JOIN bd_devices dev ON dev.topology_id = bd.id
LEFT JOIN bd_configs cfg ON cfg.topology_id = bd.id
LEFT JOIN bd_destinations dest ON dest.bridge_domain_config_id = cfg.id
WHERE bd.vlan_id = 251
GROUP BY bd.id, bd.bridge_domain_name, bd.topology_type, bd.validation_status;
```

#### **Find Bridge Domains with Validation Issues**
```sql
SELECT 
    bd.bridge_domain_name,
    bd.validation_status,
    bd.confidence_score,
    COUNT(DISTINCT dev.id) as device_count,
    COUNT(DISTINCT intf.id) as interface_count
FROM bridge_domains bd
LEFT JOIN bd_devices dev ON dev.topology_id = bd.id
LEFT JOIN bd_interfaces intf ON intf.topology_id = bd.id
WHERE bd.validation_status IN ('warning', 'error')
GROUP BY bd.id, bd.bridge_domain_name, bd.validation_status, bd.confidence_score
ORDER BY bd.confidence_score ASC;
```

#### **Find Multi-Hop Paths**
```sql
SELECT 
    bd.bridge_domain_name,
    p.path_name,
    p.total_hops,
    COUNT(ps.id) as segment_count
FROM bridge_domains bd
JOIN bd_paths p ON p.topology_id = bd.id
JOIN bd_path_segments ps ON ps.path_id = p.id
WHERE p.total_hops > 1
GROUP BY bd.id, bd.bridge_domain_name, p.id, p.path_name, p.total_hops
ORDER BY p.total_hops DESC;
```

### **5. Export and Reporting**

#### **Export Bridge Domain to JSON**
```bash
# Enhanced Database Menu → Option 6: Export Bridge Domain
# Enter BD name: g_visaev_v251
# Export format: JSON

# Creates: g_visaev_v251_export_20250826.json
{
  "bridge_domain": "g_visaev_v251",
  "export_date": "2025-08-26T10:00:00Z",
  "topology": {
    "type": "p2p",
    "vlan": 251,
    "source": {
      "device": "DNAAS-LEAF-A05",
      "interface": "ge100-0/0/20"
    },
    "destinations": [
      {
        "device": "DNAAS-SPINE-A09",
        "interface": "ge100-0/0/21"
      }
    ]
  },
  "paths": [
    {
      "name": "LEAF-A05_to_SPINE-A09",
      "hops": 1,
      "bandwidth": "10G",
      "latency": "0.1ms"
    }
  ]
}
```

#### **Generate Topology Report**
```bash
# Enhanced Database Menu → Option 7: Generate Topology Report
# Report type: VLAN Summary
# VLAN range: 250-260

# Creates: vlan_summary_250-260_20250826.md
# Markdown report showing all BDs in VLAN range with:
# - Device counts
# - Topology types
# - Validation status
# - Performance metrics
```

## 🔧 **Troubleshooting and Maintenance**

### **1. Data Quality Checks**
```sql
-- Find BDs with missing VLAN assignments
SELECT bridge_domain_name, topology_type, validation_status
FROM bridge_domains 
WHERE vlan_id IS NULL;

-- Find interfaces without valid devices
SELECT intf.name, intf.device_id
FROM bd_interfaces intf
LEFT JOIN bd_devices dev ON intf.device_id = dev.id
WHERE dev.id IS NULL;

-- Find BDs with inconsistent VLANs
SELECT bd.bridge_domain_name, bd.vlan_id, intf.vlan_id as interface_vlan
FROM bridge_domains bd
JOIN bd_interfaces intf ON intf.topology_id = bd.id
WHERE bd.vlan_id != intf.vlan_id;
```

### **2. Performance Monitoring**
```sql
-- Find slow queries
SELECT 
    bd.bridge_domain_name,
    COUNT(*) as record_count,
    AVG(bd.confidence_score) as avg_confidence
FROM bridge_domains bd
GROUP BY bd.id, bd.bridge_domain_name
HAVING COUNT(*) > 100
ORDER BY record_count DESC;

-- Monitor validation performance
SELECT 
    validation_status,
    COUNT(*) as count,
    AVG(confidence_score) as avg_confidence
FROM bridge_domains
GROUP BY validation_status;
```

This comprehensive interaction model gives users and admins multiple ways to access, understand, and manage bridge domain data - from simple CLI commands to complex database queries, all while maintaining the robust flat table structure that ensures data integrity and performance.
