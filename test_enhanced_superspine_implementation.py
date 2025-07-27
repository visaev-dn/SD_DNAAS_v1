#!/usr/bin/env python3
"""
Comprehensive Tests for Enhanced Superspine Implementation
Tests all aspects of the enhanced Superspine destination feature.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
import yaml
from pathlib import Path

# Import the enhanced modules
from config_engine.enhanced_device_types import (
    DeviceType, InterfaceType, enhanced_classifier, EnhancedDeviceClassifier
)
from config_engine.enhanced_bridge_domain_builder import EnhancedBridgeDomainBuilder
from config_engine.enhanced_menu_system import EnhancedMenuSystem

class TestEnhancedDeviceTypes(unittest.TestCase):
    """Test enhanced device type classification."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.classifier = EnhancedDeviceClassifier()
    
    def test_device_type_detection(self):
        """Test device type detection for different device names."""
        test_cases = [
            ("DNAAS-LEAF-A01", DeviceType.LEAF),
            ("DNAAS-SPINE-B08", DeviceType.SPINE),
            ("DNAAS-SUPERSPINE-01", DeviceType.SUPERSPINE),
            ("DNAAS-SS-01", DeviceType.SUPERSPINE),  # SS abbreviation
            ("UNKNOWN-DEVICE", DeviceType.UNKNOWN),
        ]
        
        for device_name, expected_type in test_cases:
            with self.subTest(device_name=device_name):
                detected_type = self.classifier.detect_device_type(device_name)
                self.assertEqual(detected_type, expected_type)
    
    def test_interface_validation_for_leaf(self):
        """Test interface validation for leaf devices."""
        # Valid interfaces for leaf
        valid_interfaces = [
            "ge1-0/0/1",      # Access interface
            "ge10-0/0/5",     # 10GE transport
            "ge100-0/0/10",   # 100GE transport
            "bundle-100",      # Bundle interface
        ]
        
        for interface in valid_interfaces:
            with self.subTest(interface=interface):
                self.assertTrue(
                    self.classifier.validate_interface_for_device(interface, DeviceType.LEAF)
                )
        
        # Invalid interfaces for leaf (none should be invalid for leaf)
        invalid_interfaces = []
        
        for interface in invalid_interfaces:
            with self.subTest(interface=interface):
                self.assertFalse(
                    self.classifier.validate_interface_for_device(interface, DeviceType.LEAF)
                )
    
    def test_interface_validation_for_superspine(self):
        """Test interface validation for Superspine devices."""
        # Valid interfaces for Superspine
        valid_interfaces = [
            "ge10-0/0/5",     # 10GE transport
            "ge100-0/0/10",   # 100GE transport
            "bundle-100",      # Bundle interface
        ]
        
        for interface in valid_interfaces:
            with self.subTest(interface=interface):
                self.assertTrue(
                    self.classifier.validate_interface_for_device(interface, DeviceType.SUPERSPINE)
                )
        
        # Invalid interfaces for Superspine (access interfaces not allowed)
        invalid_interfaces = [
            "ge1-0/0/1",      # Access interface - NOT allowed
            "ge2-0/0/5",      # Access interface - NOT allowed
        ]
        
        for interface in invalid_interfaces:
            with self.subTest(interface=interface):
                self.assertFalse(
                    self.classifier.validate_interface_for_device(interface, DeviceType.SUPERSPINE)
                )
    
    def test_topology_constraints(self):
        """Test topology constraint validation."""
        # Valid topologies
        valid_topologies = [
            (DeviceType.LEAF, DeviceType.LEAF),      # Leaf → Leaf
            (DeviceType.LEAF, DeviceType.SUPERSPINE), # Leaf → Superspine
        ]
        
        for source_type, dest_type in valid_topologies:
            with self.subTest(f"{source_type.value} → {dest_type.value}"):
                self.assertTrue(
                    self.classifier.validate_topology_constraints(source_type, dest_type)
                )
        
        # Invalid topologies
        invalid_topologies = [
            (DeviceType.SUPERSPINE, DeviceType.LEAF),      # Superspine → Leaf
            (DeviceType.SUPERSPINE, DeviceType.SUPERSPINE), # Superspine → Superspine
        ]
        
        for source_type, dest_type in invalid_topologies:
            with self.subTest(f"{source_type.value} → {dest_type.value}"):
                self.assertFalse(
                    self.classifier.validate_topology_constraints(source_type, dest_type)
                )
    
    def test_interface_parsing(self):
        """Test interface parsing functionality."""
        # Test 10GE interface parsing
        interface_10ge = "ge10-0/0/5"
        parsed_10ge = self.classifier.parse_10ge_interface(interface_10ge)
        self.assertIsNotNone(parsed_10ge)
        self.assertEqual(parsed_10ge['interface_type'], InterfaceType.TRANSPORT_10GE)
        self.assertEqual(parsed_10ge['slot'], 0)
        self.assertEqual(parsed_10ge['module'], 0)
        self.assertEqual(parsed_10ge['port'], 5)
        
        # Test 100GE interface parsing
        interface_100ge = "ge100-0/0/10"
        parsed_100ge = self.classifier.parse_100ge_interface(interface_100ge)
        self.assertIsNotNone(parsed_100ge)
        self.assertEqual(parsed_100ge['interface_type'], InterfaceType.TRANSPORT_100GE)
        self.assertEqual(parsed_100ge['slot'], 0)
        self.assertEqual(parsed_100ge['module'], 0)
        self.assertEqual(parsed_100ge['port'], 10)
        
        # Test invalid interface parsing
        invalid_interface = "ge1-0/0/1"
        parsed_invalid = self.classifier.parse_10ge_interface(invalid_interface)
        self.assertIsNone(parsed_invalid)
    
    def test_device_type_icons(self):
        """Test device type icon generation."""
        icons = {
            DeviceType.LEAF: "🌿",
            DeviceType.SPINE: "🌲",
            DeviceType.SUPERSPINE: "🌐",
            DeviceType.UNKNOWN: "❓"
        }
        
        for device_type, expected_icon in icons.items():
            with self.subTest(device_type=device_type.value):
                icon = self.classifier.get_device_type_icon(device_type)
                self.assertEqual(icon, expected_icon)
    
    def test_interface_type_detection(self):
        """Test interface type detection."""
        test_cases = [
            ("ge1-0/0/1", InterfaceType.ACCESS),
            ("ge10-0/0/5", InterfaceType.TRANSPORT_10GE),
            ("ge100-0/0/10", InterfaceType.TRANSPORT_100GE),
            ("bundle-100", InterfaceType.TRANSPORT_100GE),  # Bundles are high-speed
            ("invalid-interface", InterfaceType.UNKNOWN),
        ]
        
        for interface, expected_type in test_cases:
            with self.subTest(interface=interface):
                detected_type = self.classifier.get_interface_type(interface)
                self.assertEqual(detected_type, expected_type)

class TestEnhancedBridgeDomainBuilder(unittest.TestCase):
    """Test enhanced bridge domain builder."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary topology data
        self.temp_dir = tempfile.mkdtemp()
        self.topology_data = {
            "devices": {
                "DNAAS-LEAF-A01": {
                    "name": "DNAAS-LEAF-A01",
                    "type": "leaf",
                    "connected_spines": ["DNAAS-SPINE-B08"]
                },
                "DNAAS-LEAF-A02": {
                    "name": "DNAAS-LEAF-A02",
                    "type": "leaf",
                    "connected_spines": ["DNAAS-SPINE-B08"]
                },
                "DNAAS-SUPERSPINE-01": {
                    "name": "DNAAS-SUPERSPINE-01",
                    "type": "superspine",
                    "connected_spines": ["DNAAS-SPINE-B08"]
                },
                "DNAAS-SPINE-B08": {
                    "name": "DNAAS-SPINE-B08",
                    "type": "spine",
                    "connected_leaves": ["DNAAS-LEAF-A01", "DNAAS-LEAF-A02"],
                    "connected_superspines": ["DNAAS-SUPERSPINE-01"]
                }
            },
            "available_leaves": ["DNAAS-LEAF-A01", "DNAAS-LEAF-A02"],
            "superspine_devices": ["DNAAS-SUPERSPINE-01"],
            "spine_devices": ["DNAAS-SPINE-B08"]
        }
        
        # Create topology file
        topology_file = Path(self.temp_dir) / "complete_topology_v2.json"
        with open(topology_file, 'w') as f:
            json.dump(self.topology_data, f)
        
        # Create bundle mapping file
        bundle_file = Path(self.temp_dir) / "bundle_mapping_v2.yaml"
        bundle_data = {
            "DNAAS-LEAF-A01": {
                "bundle-100": ["ge100-0/0/1", "ge100-0/0/2"]
            }
        }
        with open(bundle_file, 'w') as f:
            yaml.dump(bundle_data, f)
        
        # Initialize builder with temp directory
        with patch('config_engine.enhanced_bridge_domain_builder.Path') as mock_path:
            mock_path.return_value = Path(self.temp_dir)
            self.builder = EnhancedBridgeDomainBuilder(topology_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_device_type_detection(self):
        """Test device type detection in builder."""
        test_cases = [
            ("DNAAS-LEAF-A01", DeviceType.LEAF),
            ("DNAAS-SPINE-B08", DeviceType.SPINE),
            ("DNAAS-SUPERSPINE-01", DeviceType.SUPERSPINE),
        ]
        
        for device_name, expected_type in test_cases:
            with self.subTest(device_name=device_name):
                detected_type = self.builder.get_device_type(device_name)
                self.assertEqual(detected_type, expected_type)
    
    def test_available_sources(self):
        """Test available source devices (leafs only)."""
        available_sources = self.builder.get_available_sources()
        
        # Should only include leaf devices
        source_names = [source['name'] for source in available_sources]
        self.assertIn("DNAAS-LEAF-A01", source_names)
        self.assertIn("DNAAS-LEAF-A02", source_names)
        
        # Should not include spine or superspine devices
        self.assertNotIn("DNAAS-SPINE-B08", source_names)
        self.assertNotIn("DNAAS-SUPERSPINE-01", source_names)
        
        # Check device types
        for source in available_sources:
            self.assertEqual(source['device_type'], DeviceType.LEAF)
    
    def test_available_destinations(self):
        """Test available destination devices (leafs + superspines)."""
        source_device = "DNAAS-LEAF-A01"
        available_destinations = self.builder.get_available_destinations(source_device)
        
        # Should include leaf and superspine devices
        dest_names = [dest['name'] for dest in available_destinations]
        self.assertIn("DNAAS-LEAF-A02", dest_names)
        self.assertIn("DNAAS-SUPERSPINE-01", dest_names)
        
        # Should not include source device
        self.assertNotIn(source_device, dest_names)
        
        # Should not include spine devices as destinations
        self.assertNotIn("DNAAS-SPINE-B08", dest_names)
        
        # Check device types
        for dest in available_destinations:
            self.assertIn(dest['device_type'], [DeviceType.LEAF, DeviceType.SUPERSPINE])
    
    def test_interface_validation(self):
        """Test interface validation for different device types."""
        # Test leaf device interfaces
        self.assertTrue(self.builder.validate_interface_for_device("ge1-0/0/1", "DNAAS-LEAF-A01"))
        self.assertTrue(self.builder.validate_interface_for_device("ge100-0/0/10", "DNAAS-LEAF-A01"))
        self.assertTrue(self.builder.validate_interface_for_device("bundle-100", "DNAAS-LEAF-A01"))
        
        # Test Superspine device interfaces
        self.assertFalse(self.builder.validate_interface_for_device("ge1-0/0/1", "DNAAS-SUPERSPINE-01"))  # Access not allowed
        self.assertTrue(self.builder.validate_interface_for_device("ge10-0/0/5", "DNAAS-SUPERSPINE-01"))
        self.assertTrue(self.builder.validate_interface_for_device("ge100-0/0/10", "DNAAS-SUPERSPINE-01"))
        self.assertTrue(self.builder.validate_interface_for_device("bundle-100", "DNAAS-SUPERSPINE-01"))
    
    def test_topology_validation(self):
        """Test topology constraint validation."""
        # Valid topologies
        self.assertTrue(self.builder.validate_path_topology("DNAAS-LEAF-A01", "DNAAS-LEAF-A02"))
        self.assertTrue(self.builder.validate_path_topology("DNAAS-LEAF-A01", "DNAAS-SUPERSPINE-01"))
        
        # Invalid topologies
        self.assertFalse(self.builder.validate_path_topology("DNAAS-SUPERSPINE-01", "DNAAS-LEAF-A01"))  # Superspine as source
        self.assertFalse(self.builder.validate_path_topology("DNAAS-SUPERSPINE-01", "DNAAS-SUPERSPINE-01"))  # Superspine → Superspine
    
    def test_bridge_domain_config_building(self):
        """Test bridge domain configuration building."""
        # Test valid configuration
        configs = self.builder.build_bridge_domain_config(
            "g_test_v253", 253,
            "DNAAS-LEAF-A01", "ge100-0/0/10",
            "DNAAS-SUPERSPINE-01", "ge10-0/0/5"
        )
        
        self.assertIsNotNone(configs)
        self.assertIn("DNAAS-LEAF-A01", configs)
        self.assertIn("DNAAS-SUPERSPINE-01", configs)
        self.assertIn("_metadata", configs)
        
        # Check metadata
        metadata = configs["_metadata"]
        self.assertEqual(metadata["service_name"], "g_test_v253")
        self.assertEqual(metadata["vlan_id"], 253)
        self.assertEqual(metadata["source_device"], "DNAAS-LEAF-A01")
        self.assertEqual(metadata["dest_device"], "DNAAS-SUPERSPINE-01")
        self.assertEqual(metadata["source_device_type"], "leaf")
        self.assertEqual(metadata["dest_device_type"], "superspine")
        self.assertEqual(metadata["topology_type"], "P2P")
    
    def test_invalid_configuration_errors(self):
        """Test error handling for invalid configurations."""
        # Test Superspine as source (should fail)
        with self.assertRaises(ValueError) as context:
            self.builder.build_bridge_domain_config(
                "g_test_v253", 253,
                "DNAAS-SUPERSPINE-01", "ge10-0/0/5",  # Superspine as source
                "DNAAS-LEAF-A01", "ge100-0/0/10"
            )
        
        self.assertIn("Invalid topology", str(context.exception))
        
        # Test invalid interface for Superspine (should fail)
        with self.assertRaises(ValueError) as context:
            self.builder.build_bridge_domain_config(
                "g_test_v253", 253,
                "DNAAS-LEAF-A01", "ge100-0/0/10",
                "DNAAS-SUPERSPINE-01", "ge1-0/0/1"  # Access interface on Superspine
            )
        
        self.assertIn("Invalid destination interface", str(context.exception))

class TestEnhancedMenuSystem(unittest.TestCase):
    """Test enhanced menu system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.menu_system = EnhancedMenuSystem()
    
    def test_device_selection_menu_display(self):
        """Test device selection menu display."""
        devices = [
            {"name": "DNAAS-LEAF-A01", "device_type": DeviceType.LEAF},
            {"name": "DNAAS-SUPERSPINE-01", "device_type": DeviceType.SUPERSPINE},
        ]
        
        # This test mainly checks that the method doesn't raise exceptions
        try:
            self.menu_system.display_device_selection_menu(devices, "test")
            # If we get here, the method executed successfully
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"display_device_selection_menu raised an exception: {e}")
    
    def test_service_configuration_parsing(self):
        """Test service configuration parsing."""
        # Mock input for testing
        with patch('builtins.input', side_effect=["testuser", "253"]):
            service_name, vlan_id = self.menu_system.get_service_configuration()
            
            self.assertEqual(service_name, "g_testuser_v253")
            self.assertEqual(vlan_id, 253)
    
    def test_interface_validation_in_menu(self):
        """Test interface validation in menu system."""
        # Test valid interface for leaf
        with patch.object(self.menu_system.builder, 'validate_interface_for_device', return_value=True):
            with patch('builtins.input', return_value="ge100-0/0/10"):
                interface = self.menu_system.get_interface_input("DNAAS-LEAF-A01", "source")
                self.assertEqual(interface, "ge100-0/0/10")
        
        # Test invalid interface for Superspine
        with patch.object(self.menu_system.builder, 'validate_interface_for_device', return_value=False):
            with patch('builtins.input', return_value="ge1-0/0/1"):
                with patch('builtins.print'):  # Suppress print output
                    interface = self.menu_system.get_interface_input("DNAAS-SUPERSPINE-01", "destination")
                    self.assertIsNone(interface)  # Should return None for invalid interface

class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios for the enhanced implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create comprehensive test topology
        self.temp_dir = tempfile.mkdtemp()
        self.topology_data = {
            "devices": {
                "DNAAS-LEAF-A01": {"name": "DNAAS-LEAF-A01", "type": "leaf"},
                "DNAAS-LEAF-A02": {"name": "DNAAS-LEAF-A02", "type": "leaf"},
                "DNAAS-SUPERSPINE-01": {"name": "DNAAS-SUPERSPINE-01", "type": "superspine"},
                "DNAAS-SUPERSPINE-02": {"name": "DNAAS-SUPERSPINE-02", "type": "superspine"},
                "DNAAS-SPINE-B08": {"name": "DNAAS-SPINE-B08", "type": "spine"},
            }
        }
        
        # Create topology file
        topology_file = Path(self.temp_dir) / "complete_topology_v2.json"
        with open(topology_file, 'w') as f:
            json.dump(self.topology_data, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_leaf_to_superspine_scenario(self):
        """Test complete Leaf → Superspine scenario."""
        with patch('config_engine.enhanced_bridge_domain_builder.Path') as mock_path:
            mock_path.return_value = Path(self.temp_dir)
            builder = EnhancedBridgeDomainBuilder(topology_dir=self.temp_dir)
            
            # Test configuration building
            configs = builder.build_bridge_domain_config(
                "g_test_v253", 253,
                "DNAAS-LEAF-A01", "ge100-0/0/10",
                "DNAAS-SUPERSPINE-01", "ge10-0/0/5"
            )
            
            # Verify configuration
            self.assertIn("DNAAS-LEAF-A01", configs)
            self.assertIn("DNAAS-SUPERSPINE-01", configs)
            
            metadata = configs["_metadata"]
            self.assertEqual(metadata["topology_type"], "P2P")
            self.assertEqual(metadata["source_device_type"], "leaf")
            self.assertEqual(metadata["dest_device_type"], "superspine")
    
    def test_leaf_to_leaf_scenario(self):
        """Test complete Leaf → Leaf scenario (should still work)."""
        with patch('config_engine.enhanced_bridge_domain_builder.Path') as mock_path:
            mock_path.return_value = Path(self.temp_dir)
            builder = EnhancedBridgeDomainBuilder(topology_dir=self.temp_dir)
            
            # Test configuration building
            configs = builder.build_bridge_domain_config(
                "g_test_v253", 253,
                "DNAAS-LEAF-A01", "ge100-0/0/10",
                "DNAAS-LEAF-A02", "ge100-0/0/20"
            )
            
            # Verify configuration
            self.assertIn("DNAAS-LEAF-A01", configs)
            self.assertIn("DNAAS-LEAF-A02", configs)
            
            metadata = configs["_metadata"]
            self.assertEqual(metadata["source_device_type"], "leaf")
            self.assertEqual(metadata["dest_device_type"], "leaf")
    
    def test_superspine_constraint_violations(self):
        """Test that Superspine constraint violations are properly caught."""
        with patch('config_engine.enhanced_bridge_domain_builder.Path') as mock_path:
            mock_path.return_value = Path(self.temp_dir)
            builder = EnhancedBridgeDomainBuilder(topology_dir=self.temp_dir)
            
            # Test Superspine as source (should fail)
            with self.assertRaises(ValueError) as context:
                builder.build_bridge_domain_config(
                    "g_test_v253", 253,
                    "DNAAS-SUPERSPINE-01", "ge10-0/0/5",  # Superspine as source
                    "DNAAS-LEAF-A01", "ge100-0/0/10"
                )
            
            self.assertIn("Invalid topology", str(context.exception))
            
            # Test Superspine → Superspine (should fail)
            with self.assertRaises(ValueError) as context:
                builder.build_bridge_domain_config(
                    "g_test_v253", 253,
                    "DNAAS-SUPERSPINE-01", "ge10-0/0/5",
                    "DNAAS-SUPERSPINE-02", "ge10-0/0/6"
                )
            
            self.assertIn("Invalid topology", str(context.exception))

def run_comprehensive_tests():
    """Run all comprehensive tests."""
    print("🧪 Running Comprehensive Superspine Implementation Tests")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestEnhancedDeviceTypes,
        TestEnhancedBridgeDomainBuilder,
        TestEnhancedMenuSystem,
        TestIntegrationScenarios,
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  • {test}: {traceback}")
    
    if result.errors:
        print("\n❌ Errors:")
        for test, traceback in result.errors:
            print(f"  • {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
        return True
    else:
        print("\n❌ Some tests failed!")
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    exit(0 if success else 1) 