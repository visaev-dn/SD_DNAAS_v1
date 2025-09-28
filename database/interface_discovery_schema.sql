-- Interface Discovery System - Simplified Database Schema
-- 
-- This schema supports the focused interface discovery system that uses
-- single command execution ("show interface description | no-more") to
-- discover and cache interface information from network devices.
--
-- Features:
-- - Simple interface data storage with timestamps
-- - Device reachability tracking
-- - Basic bundle detection support
-- - CLI integration focused design

-- Interface Discovery Data (Simplified Schema with Debug Support)
CREATE TABLE IF NOT EXISTS interface_discovery (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_name TEXT NOT NULL,
    interface_name TEXT NOT NULL,
    interface_type TEXT DEFAULT 'physical', -- physical, bundle, subinterface (inferred)
    description TEXT DEFAULT '',
    
    -- Status Information (from "show int desc")
    admin_status TEXT DEFAULT 'unknown', -- up, down, admin-down
    oper_status TEXT DEFAULT 'unknown',  -- up, down, testing
    
    -- Bundle Information (inferred from naming)
    bundle_id TEXT,                      -- Detected from interface name pattern
    is_bundle_member BOOLEAN DEFAULT 0,  -- If interface is part of a bundle
    
    -- Discovery Metadata
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    device_reachable BOOLEAN DEFAULT 1,
    discovery_errors TEXT DEFAULT '[]', -- JSON array of errors
    
    -- Debug Information (NEW)
    raw_command_output TEXT,             -- Store raw "show int desc" output for debugging
    parsing_method TEXT,                 -- Which parser method was used
    parsing_errors TEXT DEFAULT '[]',    -- JSON array of parsing errors
    
    -- Ensure unique device/interface combinations
    UNIQUE(device_name, interface_name)
);

-- Raw Discovery Data Storage (for debugging)
CREATE TABLE IF NOT EXISTS discovery_raw_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_name TEXT NOT NULL,
    command_executed TEXT NOT NULL,
    raw_output TEXT,                     -- Complete raw command output
    command_success BOOLEAN DEFAULT 1,
    execution_time_ms INTEGER,
    ssh_errors TEXT DEFAULT '[]',
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Index for efficient lookups on raw data
CREATE INDEX IF NOT EXISTS idx_discovery_raw_data_device ON discovery_raw_data(device_name, discovered_at);

-- Device Status Tracking (Simplified)
CREATE TABLE IF NOT EXISTS device_status (
    device_name TEXT PRIMARY KEY,
    last_reachable DATETIME,
    last_interface_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'unknown', -- reachable, unreachable, unknown
    last_error TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_interface_discovery_device ON interface_discovery(device_name);
CREATE INDEX IF NOT EXISTS idx_interface_discovery_status ON interface_discovery(admin_status, oper_status);
CREATE INDEX IF NOT EXISTS idx_interface_discovery_discovered_at ON interface_discovery(discovered_at);
CREATE INDEX IF NOT EXISTS idx_device_status_updated_at ON device_status(updated_at);

-- Create view for available interfaces (commonly used in CLI)
CREATE VIEW IF NOT EXISTS available_interfaces AS
SELECT 
    device_name,
    interface_name,
    interface_type,
    description,
    admin_status,
    oper_status,
    bundle_id,
    is_bundle_member,
    discovered_at
FROM interface_discovery 
WHERE 
    device_reachable = 1 
    AND admin_status != 'admin-down'
    AND discovery_errors = '[]'
ORDER BY device_name, interface_name;

-- Create view for device interface counts (for CLI menus)
CREATE VIEW IF NOT EXISTS device_interface_counts AS
SELECT 
    device_name,
    COUNT(*) as total_interfaces,
    COUNT(CASE WHEN admin_status != 'admin-down' THEN 1 END) as available_interfaces,
    MAX(discovered_at) as last_discovery,
    MAX(CASE WHEN device_reachable = 1 THEN 1 ELSE 0 END) as is_reachable
FROM interface_discovery 
GROUP BY device_name
ORDER BY device_name;

-- Cleanup function for old discovery data (can be called periodically)
-- Remove interface discovery data older than 7 days
CREATE TRIGGER IF NOT EXISTS cleanup_old_discovery_data 
AFTER INSERT ON interface_discovery
BEGIN
    DELETE FROM interface_discovery 
    WHERE discovered_at < datetime('now', '-7 days')
    AND device_name = NEW.device_name;
END;

-- Insert/Update trigger to maintain device_status table
CREATE TRIGGER IF NOT EXISTS update_device_status_on_discovery
AFTER INSERT ON interface_discovery
BEGIN
    INSERT OR REPLACE INTO device_status (
        device_name,
        last_reachable,
        last_interface_count,
        status,
        updated_at
    )
    SELECT 
        NEW.device_name,
        CASE WHEN NEW.device_reachable = 1 THEN datetime('now') ELSE 
            COALESCE((SELECT last_reachable FROM device_status WHERE device_name = NEW.device_name), datetime('now'))
        END,
        (SELECT COUNT(*) FROM interface_discovery WHERE device_name = NEW.device_name),
        CASE WHEN NEW.device_reachable = 1 THEN 'reachable' ELSE 'unreachable' END,
        datetime('now');
END;
