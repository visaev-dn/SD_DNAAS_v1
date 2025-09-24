-- ============================================================================
-- UNIFIED BRIDGE DOMAIN SCHEMA
-- ============================================================================
-- Single source of truth for all bridge domain data
-- Replaces fragmented schemas with clean, unified design

-- ============================================================================
-- MAIN BRIDGE DOMAINS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS bridge_domains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) UNIQUE NOT NULL,
    
    -- Source Information
    source VARCHAR(50) NOT NULL,           -- 'discovered', 'created', 'imported', 'edited'
    source_id VARCHAR(255),                -- Reference to original source
    source_metadata TEXT,                  -- Additional source information
    
    -- Core Bridge Domain Information
    username VARCHAR(100),
    vlan_id INTEGER,
    outer_vlan INTEGER,                    -- For QinQ configurations
    inner_vlan INTEGER,                    -- For QinQ configurations
    topology_type VARCHAR(50),             -- p2p, p2mp, etc.
    dnaas_type VARCHAR(100),              -- DNAAS_TYPE_1_SINGLE_TAGGED, etc.
    bridge_domain_scope VARCHAR(50),      -- global, local
    
    -- Configuration Data (JSON)
    configuration_data TEXT NOT NULL,      -- Complete JSON configuration
    raw_cli_config TEXT,                  -- Raw CLI commands
    interface_data TEXT,                  -- Interface configuration details
    
    -- Discovery Metadata (JSON)
    discovery_data TEXT,                  -- Original discovery data
    consolidation_info TEXT,              -- Consolidation metadata
    classification_info TEXT,             -- DNAAS classification details
    
    -- Deployment Status
    deployment_status VARCHAR(50) DEFAULT 'pending',  -- pending, deployed, failed, archived
    deployed_at TIMESTAMP,
    deployment_log TEXT,                  -- Deployment results and logs
    deployment_devices TEXT,              -- JSON list of target devices
    
    -- Version Control
    version INTEGER DEFAULT 1,
    parent_version_id INTEGER,            -- For tracking edits
    is_latest_version BOOLEAN DEFAULT TRUE,
    
    -- Audit Trail
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER DEFAULT 1,
    updated_by INTEGER DEFAULT 1,
    
    -- Constraints
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (updated_by) REFERENCES users(id),
    FOREIGN KEY (parent_version_id) REFERENCES bridge_domains(id)
);

-- ============================================================================
-- BRIDGE DOMAIN INTERFACES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS bridge_domain_interfaces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bridge_domain_id INTEGER NOT NULL,
    
    -- Interface Information
    device_name VARCHAR(100) NOT NULL,
    interface_name VARCHAR(100) NOT NULL,
    interface_type VARCHAR(50),            -- physical, bundle, subinterface
    interface_role VARCHAR(50),            -- access, uplink, downlink, transport
    
    -- VLAN Configuration
    interface_vlan_id INTEGER,
    interface_outer_vlan INTEGER,
    interface_inner_vlan INTEGER,
    vlan_manipulation TEXT,               -- VLAN manipulation commands
    
    -- Interface Metadata
    admin_state VARCHAR(20) DEFAULT 'enabled',
    interface_config TEXT,                -- Complete interface configuration
    raw_cli_commands TEXT,                -- Raw CLI for this interface
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    FOREIGN KEY (bridge_domain_id) REFERENCES bridge_domains(id) ON DELETE CASCADE,
    UNIQUE(bridge_domain_id, device_name, interface_name)
);

-- ============================================================================
-- BRIDGE DOMAIN DEPLOYMENTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS bridge_domain_deployments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bridge_domain_id INTEGER NOT NULL,
    
    -- Deployment Information
    deployment_type VARCHAR(50) NOT NULL, -- 'create', 'update', 'delete', 'rollback'
    deployment_method VARCHAR(50),        -- 'ssh', 'api', 'manual'
    target_devices TEXT,                  -- JSON list of target devices
    
    -- Deployment Status
    deployment_status VARCHAR(50) NOT NULL, -- 'pending', 'in_progress', 'success', 'failed', 'rolled_back'
    deployment_log TEXT,                  -- Detailed deployment logs
    error_message TEXT,                   -- Error details if failed
    
    -- Timing
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    
    -- Audit
    deployed_by INTEGER DEFAULT 1,
    
    -- Constraints
    FOREIGN KEY (bridge_domain_id) REFERENCES bridge_domains(id) ON DELETE CASCADE,
    FOREIGN KEY (deployed_by) REFERENCES users(id)
);

-- ============================================================================
-- BRIDGE DOMAIN TEMPLATES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS bridge_domain_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    
    -- Template Data
    template_type VARCHAR(50),            -- 'p2p', 'p2mp', 'qinq', 'custom'
    template_data TEXT NOT NULL,          -- JSON template configuration
    default_parameters TEXT,              -- Default parameter values
    
    -- Usage Tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER DEFAULT 1,
    
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- ============================================================================
-- PERFORMANCE INDEXES
-- ============================================================================

-- Bridge Domains indexes
CREATE INDEX IF NOT EXISTS idx_bridge_domains_name ON bridge_domains(name);
CREATE INDEX IF NOT EXISTS idx_bridge_domains_username ON bridge_domains(username);
CREATE INDEX IF NOT EXISTS idx_bridge_domains_vlan_id ON bridge_domains(vlan_id);
CREATE INDEX IF NOT EXISTS idx_bridge_domains_source ON bridge_domains(source);
CREATE INDEX IF NOT EXISTS idx_bridge_domains_deployment_status ON bridge_domains(deployment_status);
CREATE INDEX IF NOT EXISTS idx_bridge_domains_dnaas_type ON bridge_domains(dnaas_type);
CREATE INDEX IF NOT EXISTS idx_bridge_domains_created_at ON bridge_domains(created_at);

-- Interfaces indexes
CREATE INDEX IF NOT EXISTS idx_bd_interfaces_bridge_domain_id ON bridge_domain_interfaces(bridge_domain_id);
CREATE INDEX IF NOT EXISTS idx_bd_interfaces_device_name ON bridge_domain_interfaces(device_name);
CREATE INDEX IF NOT EXISTS idx_bd_interfaces_interface_name ON bridge_domain_interfaces(interface_name);

-- Deployments indexes
CREATE INDEX IF NOT EXISTS idx_bd_deployments_bridge_domain_id ON bridge_domain_deployments(bridge_domain_id);
CREATE INDEX IF NOT EXISTS idx_bd_deployments_status ON bridge_domain_deployments(deployment_status);
CREATE INDEX IF NOT EXISTS idx_bd_deployments_started_at ON bridge_domain_deployments(started_at);

-- Templates indexes
CREATE INDEX IF NOT EXISTS idx_bd_templates_name ON bridge_domain_templates(name);
CREATE INDEX IF NOT EXISTS idx_bd_templates_type ON bridge_domain_templates(template_type);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Active Bridge Domains (latest versions only)
CREATE VIEW IF NOT EXISTS active_bridge_domains AS
SELECT * FROM bridge_domains 
WHERE is_latest_version = TRUE 
AND deployment_status != 'archived';

-- Deployed Bridge Domains
CREATE VIEW IF NOT EXISTS deployed_bridge_domains AS
SELECT * FROM bridge_domains 
WHERE deployment_status = 'deployed' 
AND is_latest_version = TRUE;

-- Bridge Domains with Interface Count
CREATE VIEW IF NOT EXISTS bridge_domains_summary AS
SELECT 
    bd.*,
    COUNT(bdi.id) as interface_count,
    COUNT(DISTINCT bdi.device_name) as device_count
FROM bridge_domains bd
LEFT JOIN bridge_domain_interfaces bdi ON bd.id = bdi.bridge_domain_id
WHERE bd.is_latest_version = TRUE
GROUP BY bd.id;

-- Recent Deployments
CREATE VIEW IF NOT EXISTS recent_deployments AS
SELECT 
    bd.name as bridge_domain_name,
    bd.username,
    bd.vlan_id,
    dep.deployment_type,
    dep.deployment_status,
    dep.started_at,
    dep.completed_at,
    dep.duration_seconds
FROM bridge_domain_deployments dep
JOIN bridge_domains bd ON dep.bridge_domain_id = bd.id
ORDER BY dep.started_at DESC;


