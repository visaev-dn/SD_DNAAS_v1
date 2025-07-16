#!/usr/bin/env python3
"""
Test script for Network LAB Automation Framework
Tests basic functionality without requiring actual network devices
"""

import json
import yaml
import logging
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import from config_engine and utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_topology_loading():
    """Test topology YAML loading"""
    try:
        with open('topology.yaml', 'r') as f:
            topology = yaml.safe_load(f)
        
        # Check required fields
        assert 'leaf01' in topology
        assert 'mgmt_ip' in topology['leaf01']
        assert 'spines' in topology
        
        logger.info("✓ Topology loading test passed")
        return True
    except Exception as e:
        logger.error(f"✗ Topology loading test failed: {e}")
        return False

def test_request_loading():
    """Test request JSON loading"""
    try:
        with open('user_input/request.json', 'r') as f:
            request = json.load(f)
        
        # Check required fields
        required_fields = ['service_type', 'source_leaf', 'source_port', 
                          'destination_leaf', 'destination_port', 'vlans']
        for field in required_fields:
            assert field in request
        
        logger.info("✓ Request loading test passed")
        return True
    except Exception as e:
        logger.error(f"✗ Request loading test failed: {e}")
        return False

def test_template_rendering():
    """Test Jinja2 template rendering"""
    try:
        from jinja2 import Environment, FileSystemLoader
        
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('qinq_template.j2')
        
        # Test data
        context = {
            'port': 'Ethernet1',
            'remote_leaf': 'leaf02',
            'outer_vlan': 3001,
            'inner_vlans': [100, 101, 102],
            'description': 'Test Q-in-Q service',
            'local_leaf': 'leaf01'
        }
        
        rendered = template.render(**context)
        
        # Check if key elements are present
        assert 'interface Ethernet1' in rendered
        assert 'switchport mode dot1q-tunnel' in rendered
        assert 'vlan 3001' in rendered
        
        logger.info("✓ Template rendering test passed")
        return True
    except Exception as e:
        logger.error(f"✗ Template rendering test failed: {e}")
        return False

def test_config_builder():
    """Test configuration builder"""
    try:
        from config_engine.builder import ConfigBuilder
        
        # Load test data
        with open('topology.yaml', 'r') as f:
            topology = yaml.safe_load(f)
        
        with open('user_input/request.json', 'r') as f:
            request = json.load(f)
        
        # Test builder
        builder = ConfigBuilder()
        config = builder.build_config(request, topology, is_source=True)
        
        # Check if configuration was generated
        assert len(config) > 0
        assert 'interface' in config.lower()
        
        logger.info("✓ Configuration builder test passed")
        return True
    except Exception as e:
        logger.error(f"✗ Configuration builder test failed: {e}")
        return False

def test_inventory_manager():
    """Test inventory manager"""
    try:
        from utils.inventory import InventoryManager
        
        manager = InventoryManager()
        
        # Test device listing
        devices = manager.list_devices()
        assert len(devices) > 0
        assert 'leaf01' in devices
        
        # Test device info retrieval
        device_info = manager.get_device_info('leaf01')
        assert device_info is not None
        assert 'mgmt_ip' in device_info
        
        logger.info("✓ Inventory manager test passed")
        return True
    except Exception as e:
        logger.error(f"✗ Inventory manager test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("Starting Network LAB Automation Framework Tests")
    logger.info("=" * 50)
    
    tests = [
        test_topology_loading,
        test_request_loading,
        test_template_rendering,
        test_config_builder,
        test_inventory_manager
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    logger.info("=" * 50)
    logger.info(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Framework is ready to use.")
        return True
    else:
        logger.error("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 