#!/usr/bin/env python3
"""
Test script to demonstrate comprehensive logging and tracing.
This script shows the complete flow with detailed logging at every step.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_engine.enhanced_topology_discovery import enhanced_discovery
from config_engine.bridge_domain_builder import BridgeDomainBuilder

def setup_logging():
    """Setup detailed logging for demonstration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('test_logging_demo.log')
        ]
    )
    return logging.getLogger(__name__)

def test_complete_flow():
    """Test the complete flow with detailed logging."""
    logger = setup_logging()
    
    logger.info("=" * 80)
    logger.info("🚀 STARTING COMPREHENSIVE LOGGING DEMO")
    logger.info("=" * 80)
    
    # Step 1: Enhanced Topology Discovery
    logger.info("\n📋 STEP 1: Enhanced Topology Discovery")
    logger.info("-" * 50)
    
    try:
        topology_data = enhanced_discovery.discover_topology_with_normalization()
        logger.info(f"✅ Enhanced topology discovery completed successfully")
        logger.info(f"📊 Topology contains {len(topology_data.get('devices', {}))} devices")
    except Exception as e:
        logger.error(f"❌ Enhanced topology discovery failed: {e}")
        return
    
    # Step 2: Bridge Domain Builder
    logger.info("\n📋 STEP 2: Bridge Domain Builder")
    logger.info("-" * 50)
    
    try:
        builder = BridgeDomainBuilder()
        logger.info(f"✅ Bridge domain builder initialized successfully")
        
        # Test path calculation
        logger.info("\n🔍 Testing path calculation...")
        path = builder.calculate_path('DNAAS-LEAF-D12', 'DNAAS-LEAF-F15')
        
        if path:
            logger.info(f"✅ Path calculation successful")
            logger.info(f"📊 Path type: {'2-tier' if path.get('superspine') is None else '3-tier'}")
            logger.info(f"📊 Path segments: {len(path.get('segments', []))}")
        else:
            logger.error(f"❌ Path calculation failed")
            return
        
        # Test bundle lookup
        logger.info("\n🔍 Testing bundle lookup...")
        test_devices = ['DNAAS-SPINE-D14', 'DNAAS-SPINE-F09']
        test_interfaces = ['ge100-0/0/36', 'ge100-4/0/15']
        
        for device, interface in zip(test_devices, test_interfaces):
            bundle = builder._find_bundle_for_device(device, interface)
            if bundle:
                logger.info(f"✅ Bundle found for {device}:{interface} -> {bundle.get('name')}")
            else:
                logger.warning(f"⚠️  No bundle found for {device}:{interface}")
        
        # Test bridge domain build
        logger.info("\n🔍 Testing bridge domain build...")
        configs = builder.build_bridge_domain_config(
            service_name='test_service_v100',
            vlan_id=100,
            source_leaf='DNAAS-LEAF-D12',
            source_port='ge100-0/0/1',
            dest_leaf='DNAAS-LEAF-F15',
            dest_port='ge100-0/0/2'
        )
        
        if configs:
            logger.info(f"✅ Bridge domain configuration built successfully")
            logger.info(f"📊 Devices configured: {list(configs.keys())}")
            
            # Show config summary
            for device, config in configs.items():
                logger.info(f"  {device}: {len(config)} commands")
        else:
            logger.error(f"❌ Bridge domain configuration build failed")
        
    except Exception as e:
        logger.error(f"❌ Bridge domain builder test failed: {e}")
        return
    
    logger.info("\n" + "=" * 80)
    logger.info("🎉 COMPREHENSIVE LOGGING DEMO COMPLETED")
    logger.info("📁 Check 'test_logging_demo.log' for detailed log output")
    logger.info("=" * 80)

def test_normalization_only():
    """Test just the normalization logging."""
    logger = setup_logging()
    
    logger.info("=" * 80)
    logger.info("🔧 TESTING DEVICE NAME NORMALIZATION LOGGING")
    logger.info("=" * 80)
    
    from config_engine.device_name_normalizer import normalizer
    
    test_names = [
        'DNAAS-LEAF-D12',
        'dnaas_leaf_d12',
        'DNAAS-SPINE-NCP1-B08',
        'DNAAS-SPINE-B08',
        'DNAAS-SUPERSPINE-D04-NCC1',
        'dnaas-superspine-d04-ncc1'
    ]
    
    for name in test_names:
        normalized = normalizer.normalize_device_name(name)
        canonical = normalizer.canonical_key(name)
        logger.info(f"Original: {name}")
        logger.info(f"Normalized: {normalized}")
        logger.info(f"Canonical: {canonical}")
        logger.info("-" * 30)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test comprehensive logging')
    parser.add_argument('--normalization-only', action='store_true', 
                       help='Test only normalization logging')
    
    args = parser.parse_args()
    
    if args.normalization_only:
        test_normalization_only()
    else:
        test_complete_flow() 