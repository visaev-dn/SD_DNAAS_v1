# COMPLETE LAB AUTOMATION PROJECT FILE MAP
## EXHAUSTIVE DIRECTORY & FILE CATALOG

**Total Project Files**: 1,109 (excluding dependencies, git objects, node_modules)

---

## 📁 ROOT LEVEL FILES (31 files)

```
├── .DS_Store
├── .gitignore
├── INTERFACE_DISCOVERY_INTEGRATION_COMPLETE.md
├── POST_REFACTORING_CLEANUP_ANALYSIS.md
├── PROJECT_FILE_MAP.md
├── api_server.py                    # API server implementation
├── auth.py                         # Authentication system
├── bd_assignment_manager.py        # Bridge domain assignment manager
├── bd_editor_api.py               # Bridge domain editor API
├── bd_editor_week2.py             # Bridge domain editor v2
├── bd_editor_week3.py             # Bridge domain editor v3
├── database_manager.py            # Database management
├── database_migration_v2.py       # Database migration v2
├── demo_enhanced_interface_status.py  # Demo interface status
├── deployment_manager.py          # Deployment management
├── devices.yaml                   # Device configuration
├── init_db.py                     # Database initialization
├── lab_automation_backup_cleanup_20250924_144258.tar.gz  # Backup archive
├── main.py                        # Main application entry point
├── models.py                      # Data models
├── populate_sample_interfaces.py  # Sample interface populator
├── port_manager.py                # Port management
├── quick_ports.sh                 # Quick port script
├── requirements.txt               # Python dependencies
├── run_tests.py                   # Test runner
├── setup.py                       # Setup script
├── smart_start.py                 # Smart startup script
├── start_servers.sh               # Server startup script
├── test_debug_discovery.py        # Discovery debugging tests
├── test_device_commands.py        # Device command tests
└── test_device_shell.py           # Device shell tests
```

---

## 🔧 API LAYER (20 files)

### `api/` Directory
```
api/
├── __init__.py
├── middleware/
│   ├── __init__.py
│   ├── auth_middleware.py          # Authentication middleware
│   ├── caching.py                  # Caching middleware
│   ├── error_middleware.py         # Error handling middleware
│   ├── logging_middleware.py       # Logging middleware
│   ├── monitoring.py               # Monitoring middleware
│   └── rate_limiting.py            # Rate limiting middleware
├── v1/
│   ├── __init__.py
│   ├── admin.py                    # Admin endpoints
│   ├── auth.py                     # Authentication endpoints
│   ├── bridge_domains.py           # Bridge domain endpoints
│   ├── configurations.py           # Configuration endpoints
│   ├── dashboard.py                # Dashboard endpoints
│   ├── deployments.py              # Deployment endpoints
│   ├── devices.py                  # Device endpoints
│   └── files.py                    # File management endpoints
├── v2/
│   └── __init__.py
└── websocket/
    ├── __init__.py
    └── websocket_handlers.py       # WebSocket handlers
```

---

## ⚙️ CONFIG ENGINE (102 files)

### `config_engine/` Directory - Core Business Logic
```
config_engine/
├── __init__.py
├── bd_proc_pipeline.py             # Bridge domain processing pipeline
├── bridge_domain_builder.py        # Bridge domain builder
├── bridge_domain_classifier.py     # Bridge domain classifier
├── bridge_domain_visualization.py  # Bridge domain visualization
├── config_generator.py             # Configuration generator
├── configuration_diff_engine.py    # Configuration diff engine
├── device_name_normalizer.py       # Device name normalizer
├── device_scanner.py               # Device scanner
├── duplicate_cleanup.py            # Duplicate cleanup utility
├── enhanced_bridge_domain_builder.py  # Enhanced bridge domain builder
├── enhanced_device_types.py        # Enhanced device types
├── enhanced_menu_system.py         # Enhanced menu system
├── enhanced_topology_discovery.py  # Enhanced topology discovery
├── enhanced_topology_scanner.py    # Enhanced topology scanner
├── p2mp_bridge_domain_builder.py   # P2MP bridge domain builder
├── p2mp_config_generator.py        # P2MP configuration generator
├── p2mp_path_calculator.py         # P2MP path calculator
├── reverse_engineering_engine.py   # Reverse engineering engine
├── rollback_manager.py             # Rollback manager
├── service_name_analyzer.py        # Service name analyzer
├── service_signature.py            # Service signature
├── smart_deployment_manager.py     # Smart deployment manager
├── smart_deployment_types.py       # Smart deployment types
├── topology_mapper.py              # Topology mapper
├── unified_bridge_domain_builder.py # Unified bridge domain builder
├── validation_framework.py         # Validation framework
├── vlan_configuration_collector.py # VLAN configuration collector
│
├── bridge_domain/                  # Bridge domain processing (6 files)
│   ├── __init__.py
│   ├── base_builder.py             # Base builder class
│   ├── builder_factory.py          # Builder factory
│   ├── p2mp_builder.py             # P2MP builder
│   ├── p2p_builder.py              # P2P builder
│   └── unified_builder.py          # Unified builder
│
├── configuration/                  # Configuration management (3 files)
│   ├── __init__.py
│   ├── base_configuration_manager.py  # Base configuration manager
│   └── configuration_manager.py    # Configuration manager
│
├── discovery/                      # Network discovery (19 files)
│   ├── __init__.py
│   ├── advanced/
│   │   └── components/
│   │       ├── __init__.py
│   │       ├── bridge_domain_detector.py      # Bridge domain detector
│   │       ├── consolidation_engine.py        # Consolidation engine
│   │       ├── database_populator.py          # Database populator
│   │       ├── device_type_classifier.py      # Device type classifier
│   │       ├── discovery_orchestrator.py      # Discovery orchestrator
│   │       ├── global_identifier_extractor.py # Global identifier extractor
│   │       ├── interface_role_analyzer.py     # Interface role analyzer
│   │       ├── lldp_analyzer.py               # LLDP analyzer
│   │       └── path_generator.py              # Path generator
│   ├── legacy/
│   │   ├── bridge_domain_discovery.py         # Legacy bridge domain discovery
│   │   └── enhanced_bridge_domain_discovery.py # Legacy enhanced discovery
│   └── simplified/
│       ├── __init__.py
│       ├── cli_integration.py                 # CLI integration
│       ├── data_structures.py                # Data structures
│       ├── data_sync_manager.py               # Data sync manager
│       ├── enhanced_cli_display.py           # Enhanced CLI display
│       └── simplified_bridge_domain_discovery.py # Simplified discovery
│
├── path_validation/                # Path validation (4 files)
│   ├── __init__.py
│   ├── error_types.py              # Error types
│   ├── validation_result.py        # Validation result
│   └── validator.py                # Validator
│
├── phase1_api/                     # Phase 1 API (3 files)
│   ├── __init__.py
│   ├── endpoints.py                # API endpoints
│   └── router.py                   # API router
│
├── phase1_data_structures/         # Phase 1 data structures (9 files)
│   ├── __init__.py
│   ├── bridge_domain_config.py     # Bridge domain configuration
│   ├── bridge_domain_signature.py  # Bridge domain signature
│   ├── device_info.py              # Device information
│   ├── enums.py                    # Enumerations
│   ├── interface_info.py           # Interface information
│   ├── path_info.py                # Path information
│   ├── topology_data.py            # Topology data
│   └── validator.py                # Validator
│
├── phase1_database/                # Phase 1 database (14 files)
│   ├── __init__.py
│   ├── add_path_segment_constraints.py        # Path segment constraints
│   ├── bulletproof_consolidation_manager.py   # Bulletproof consolidation
│   ├── consolidation_manager.py               # Consolidation manager
│   ├── consolidation_manager_old.py           # Old consolidation manager
│   ├── constraints_migration.py               # Constraints migration
│   ├── final_schema_migration.py              # Final schema migration
│   ├── manager.py                             # Database manager
│   ├── migrations.py                          # Database migrations
│   ├── models.py                              # Database models
│   ├── root_consolidation_manager.py          # Root consolidation manager
│   ├── serializers.py                         # Data serializers
│   ├── service_signature_migration.py         # Service signature migration
│   └── simple_consolidation_manager.py        # Simple consolidation manager
│
├── phase1_integration/             # Phase 1 integration (4 files)
│   ├── __init__.py
│   ├── cli_wrapper.py              # CLI wrapper
│   ├── data_transformers.py        # Data transformers
│   └── legacy_adapter.py           # Legacy adapter
│
├── simplified_discovery/           # Simplified discovery (6 files)
│   ├── __init__.py
│   ├── cli_integration.py          # CLI integration
│   ├── data_structures.py          # Data structures
│   ├── data_sync_manager.py        # Data sync manager
│   ├── enhanced_cli_display.py     # Enhanced CLI display
│   └── simplified_bridge_domain_discovery.py # Simplified discovery
│
└── topology/                       # Topology management (6 files)
    ├── __init__.py
    ├── base_topology_manager.py    # Base topology manager
    ├── models/
    │   ├── __init__.py
    │   ├── device_types.py          # Device types
    │   ├── network_models.py        # Network models
    │   └── topology_models.py       # Topology models
    └── topology/
        └── discovery/               # Topology discovery
```

---

## 🔧 SERVICES ARCHITECTURE (49 files)

### `services/` Directory
```
services/
├── __init__.py
├── service_container.py            # Service container
│
├── bd_editor/                      # Bridge domain editor services (19 files)
│   ├── __init__.py
│   ├── change_tracker.py           # Change tracker
│   ├── config_preview.py           # Configuration preview
│   ├── config_templates.py         # Configuration templates
│   ├── data_models.py              # Data models
│   ├── deployment_integration.py   # Deployment integration
│   ├── error_handler.py            # Error handler
│   ├── health_checker.py           # Health checker
│   ├── impact_analyzer.py          # Impact analyzer
│   ├── integration_fallbacks.py    # Integration fallbacks
│   ├── intelligent_menu.py         # Intelligent menu
│   ├── interface_analyzer.py       # Interface analyzer
│   ├── menu_adapters.py            # Menu adapters
│   ├── menu_system.py              # Menu system
│   ├── performance_monitor.py      # Performance monitor
│   ├── session_manager.py          # Session manager
│   ├── template_validator.py       # Template validator
│   ├── universal_deployment_adapter.py # Universal deployment adapter
│   └── validation_system.py        # Validation system
│
├── configuration_drift/            # Configuration drift detection (7 files)
│   ├── __init__.py
│   ├── data_models.py              # Data models
│   ├── database_updater.py         # Database updater
│   ├── db_population_adapter.py    # Database population adapter
│   ├── deployment_integration.py   # Deployment integration
│   ├── drift_detector.py           # Drift detector
│   ├── sync_resolver.py            # Sync resolver
│   └── targeted_discovery.py       # Targeted discovery
│
├── implementations/                # Service implementations (2 files)
│   ├── __init__.py
│   └── mock_bridge_domain_service.py # Mock bridge domain service
│
├── interface_discovery/            # Interface discovery services (7 files)
│   ├── __init__.py
│   ├── cli_integration.py          # CLI integration
│   ├── data_models.py              # Data models
│   ├── description_parser.py       # Description parser
│   ├── enhanced_cli_display.py     # Enhanced CLI display
│   ├── simple_discovery.py         # Simple discovery
│   └── smart_filter.py             # Smart filter
│
├── interfaces/                     # Interface management (6 files)
│   ├── __init__.py
│   ├── bridge_domain_service.py    # Bridge domain service
│   ├── discovery_service.py        # Discovery service
│   ├── ssh_service.py              # SSH service
│   ├── topology_service.py         # Topology service
│   └── user_workflow_service.py    # User workflow service
│
└── universal_ssh/                  # SSH connectivity (5 files)
    ├── __init__.py
    ├── command_executor.py         # Command executor
    ├── data_models.py              # Data models
    ├── deployment_orchestrator.py  # Deployment orchestrator
    └── device_manager.py           # Device manager
```

---

## 🗄️ DATABASE LAYER (4 files + 14 instance files)

### `database/` Directory
```
database/
├── interface_discovery_schema.sql  # Interface discovery schema
├── migration_script.py             # Migration utilities
├── unified_manager.py              # Database manager
└── unified_schema.sql              # Main database schema
```

### `instance/` Directory - Database Files
```
instance/
├── lab_automation.db               # Main active database
├── lab_automation.db.backup_v2_20250828_125851        # Backup v2
├── lab_automation.db.backup_v2_20250828_131803        # Backup v2
├── lab_automation.db.backup_v2_20250828_131818        # Backup v2
├── lab_automation_backup_20250901_113506.db           # Backup
├── lab_automation_backup_20250901_133822.db           # Backup
├── lab_automation_backup_20250901_135918.db           # Backup
├── lab_automation_backup_20250901_161118.db           # Backup
├── lab_automation_backup_20250920_223541.db           # Backup
├── lab_automation_backup_assignment_20250925_150848.db # Assignment backup
├── lab_automation_backup_cleanup_20250925_090348.db   # Cleanup backup
├── lab_automation_backup_foundation_20250924_155902.db # Foundation backup
├── lab_automation_backup_migration_20250924_160027.db  # Migration backup
└── lab_automation_backup_migration_20250924_160058.db  # Migration backup
```

---

## 🎨 FRONTEND APPLICATIONS (113 + 116 files)

### `frontend/` Directory - Main React Frontend (113 files)
```
frontend/
├── .gitignore
├── README.md
├── bun.lockb                       # Bun lock file
├── components.json                 # Components configuration
├── eslint.config.js                # ESLint configuration
├── index.html                      # Main HTML file
├── package-lock.json               # NPM lock file
├── package.json                    # Package configuration
├── postcss.config.js               # PostCSS configuration
├── tailwind.config.ts              # Tailwind configuration
├── tsconfig.app.json               # TypeScript app configuration
├── tsconfig.json                   # TypeScript configuration
├── tsconfig.node.json              # TypeScript node configuration
├── vite.config.ts                  # Vite configuration
│
├── dist/                           # Distribution files
│   ├── assets/
│   │   ├── index-BzCjha55.css      # Compiled CSS
│   │   └── index-DSWHYeNG.js       # Compiled JavaScript
│   ├── favicon.ico
│   ├── index.html
│   ├── placeholder.svg
│   └── robots.txt
│
├── public/                         # Public assets
│   ├── favicon.ico
│   ├── placeholder.svg
│   └── robots.txt
│
└── src/                            # Source code (90 files)
    ├── App.css                     # App styles
    ├── App.tsx                     # Main App component
    ├── index.css                   # Global styles
    ├── main.tsx                    # Main entry point
    ├── vite-env.d.ts               # Vite environment types
    │
    ├── components/                 # React components
    │   ├── Bridge_Domain_Editor_V2.tsx      # Bridge domain editor v2
    │   ├── DataChainVisualization.tsx       # Data chain visualization
    │   ├── DebugWindow.tsx                  # Debug window
    │   ├── EnhancedBridgeDomainBrowser.tsx  # Enhanced BD browser
    │   ├── ErrorBoundary.tsx                # Error boundary
    │   ├── Header.tsx                       # Header component
    │   ├── Layout.tsx                       # Layout component
    │   ├── ProtectedRoute.tsx               # Protected route
    │   ├── Sidebar.tsx                      # Sidebar component
    │   ├── SmartDeploymentWizard.tsx        # Smart deployment wizard
    │   ├── TopologyCanvas.tsx               # Topology canvas
    │   ├── TopologyComparisonView.tsx       # Topology comparison view
    │   ├── UserInfoWidget.tsx               # User info widget
    │   ├── UserWorkspace.tsx                # User workspace
    │   ├── WorkspaceEditor.tsx              # Workspace editor
    │   │
    │   └── ui/                              # UI components (50+ files)
    │       ├── accordion.tsx                # Accordion component
    │       ├── alert-dialog.tsx             # Alert dialog
    │       ├── alert.tsx                    # Alert component
    │       ├── aspect-ratio.tsx             # Aspect ratio
    │       ├── avatar.tsx                   # Avatar component
    │       ├── badge.tsx                    # Badge component
    │       ├── breadcrumb.tsx               # Breadcrumb component
    │       ├── button.tsx                   # Button component
    │       ├── calendar.tsx                 # Calendar component
    │       ├── card.tsx                     # Card component
    │       ├── carousel.tsx                 # Carousel component
    │       ├── chart.tsx                    # Chart component
    │       ├── checkbox.tsx                 # Checkbox component
    │       ├── collapsible.tsx              # Collapsible component
    │       ├── command.tsx                  # Command component
    │       ├── context-menu.tsx             # Context menu
    │       ├── dialog.tsx                   # Dialog component
    │       ├── drawer.tsx                   # Drawer component
    │       ├── dropdown-menu.tsx            # Dropdown menu
    │       ├── form.tsx                     # Form component
    │       ├── hover-card.tsx               # Hover card
    │       ├── input-otp.tsx                # OTP input
    │       ├── input.tsx                    # Input component
    │       ├── label.tsx                    # Label component
    │       ├── menubar.tsx                  # Menubar component
    │       ├── navigation-menu.tsx          # Navigation menu
    │       ├── pagination.tsx               # Pagination component
    │       ├── popover.tsx                  # Popover component
    │       ├── progress.tsx                 # Progress component
    │       ├── radio-group.tsx              # Radio group
    │       ├── resizable.tsx                # Resizable component
    │       ├── scroll-area.tsx              # Scroll area
    │       ├── searchable-select.tsx        # Searchable select
    │       ├── select.tsx                   # Select component
    │       ├── separator.tsx                # Separator component
    │       ├── sheet.tsx                    # Sheet component
    │       ├── sidebar.tsx                  # Sidebar component
    │       ├── skeleton.tsx                 # Skeleton component
    │       ├── slider.tsx                   # Slider component
    │       ├── sonner.tsx                   # Sonner component
    │       ├── switch.tsx                   # Switch component
    │       ├── table.tsx                    # Table component
    │       ├── tabs.tsx                     # Tabs component
    │       ├── textarea.tsx                 # Textarea component
    │       ├── toast.tsx                    # Toast component
    │       ├── toaster.tsx                  # Toaster component
    │       ├── toggle-group.tsx             # Toggle group
    │       ├── toggle.tsx                   # Toggle component
    │       ├── tooltip.tsx                  # Tooltip component
    │       └── use-toast.ts                 # Toast hook
    │
    ├── config/                             # Configuration
    │   └── api.ts                          # API configuration
    │
    ├── contexts/                           # React contexts
    │   └── AuthContext.tsx                 # Authentication context
    │
    ├── hooks/                              # Custom hooks
    │   ├── use-mobile.tsx                  # Mobile hook
    │   ├── use-theme.ts                    # Theme hook
    │   └── use-toast.ts                    # Toast hook
    │
    ├── lib/                                # Utility libraries
    │   └── utils.ts                        # Utility functions
    │
    ├── pages/                              # Page components
    │   ├── BridgeBuilder.tsx               # Bridge builder page
    │   ├── Configurations.tsx              # Configurations page
    │   ├── Dashboard.tsx                   # Dashboard page
    │   ├── Deployments.tsx                 # Deployments page
    │   ├── Files.tsx                       # Files page
    │   ├── Index.tsx                       # Index page
    │   ├── Login.tsx                       # Login page
    │   ├── NotFound.tsx                    # Not found page
    │   ├── Topology.tsx                    # Topology page
    │   ├── UserManagement.tsx              # User management page
    │   └── Workspace.tsx                   # Workspace page
    │
    ├── services/                           # Frontend services
    │   ├── api.ts                          # API service
    │   └── websocket.ts                    # WebSocket service
    │
    └── utils/                              # Utility functions
        └── bridgeDomainEditorHelpers.ts    # Bridge domain editor helpers
```

### `lovable-frontend/` Directory - Alternative React Frontend (116 files)
*Similar structure to main frontend with additional features*

---

## 🗂️ CONFIGURATION MANAGEMENT (37 files)

### `configurations/` Directory
```
configurations/
├── active/
│   ├── deployed/                           # Live configurations (1 file)
│   │   └── unified_bridge_domain_g_mkazakov_v1369.yaml
│   └── pending/                            # Pending deployments (35 files)
│       ├── bridge_domain_g_oalfasi_v105.yaml
│       ├── bridge_domain_g_visaev-Newest_v290.yaml
│       ├── bridge_domain_g_visaev-test1_v257.yaml
│       ├── bridge_domain_g_visaev-test99_v99.yaml
│       ├── bridge_domain_g_visaev-test_v258.yaml
│       ├── bridge_domain_g_visaev_v253.yaml
│       ├── bridge_domain_g_visaev_v255.yaml
│       ├── bridge_domain_g_visaev_v258.yaml
│       ├── bridge_domain_g_visaev_v259.yaml
│       ├── bridge_domain_test_restore_v100.yaml
│       ├── unified_bridge_domain_g_db_manager_test_v777.yaml
│       ├── unified_bridge_domain_g_debug_test2_v998.yaml
│       ├── unified_bridge_domain_g_debug_test_v999.yaml
│       ├── unified_bridge_domain_g_direct_save_test_v666.yaml
│       ├── unified_bridge_domain_g_direct_sql_test_v222.yaml
│       ├── unified_bridge_domain_g_enhanced_log_test_v888.yaml
│       ├── unified_bridge_domain_g_enhanced_test_v333.yaml
│       ├── unified_bridge_domain_g_final_debug_test_v111.yaml
│       ├── unified_bridge_domain_g_final_test_v555.yaml
│       ├── unified_bridge_domain_g_fixed_test_v555.yaml
│       ├── unified_bridge_domain_g_health_test_v666.yaml
│       ├── unified_bridge_domain_g_http_test_v777.yaml
│       ├── unified_bridge_domain_g_log_test_456_v333.yaml
│       ├── unified_bridge_domain_g_test_user2_v261.yaml
│       ├── unified_bridge_domain_g_test_user3_v262.yaml
│       ├── unified_bridge_domain_g_test_user4_v263.yaml
│       ├── unified_bridge_domain_g_test_user5_v264.yaml
│       ├── unified_bridge_domain_g_test_user_v253.yaml
│       ├── unified_bridge_domain_g_test_user_v260.yaml
│       ├── unified_bridge_domain_g_test_v100.yaml
│       ├── unified_bridge_domain_g_unique_test_123_v444.yaml
│       ├── unified_bridge_domain_g_visaev-Newest_v290.yaml
│       ├── unified_bridge_domain_g_visaev-test99_v99.yaml
│       ├── unified_bridge_domain_g_visaev_v253.yaml
│       └── unified_bridge_domain_g_visaev_v259.yaml
└── imports/
    └── discovery/                          # Discovery imports (1 file)
        └── g_visaev_v251_20250808_203038.yaml
```

---

## 📚 DOCUMENTATION (77 files total)

### `documentation_and_design_plans/` Directory (52 files)
```
documentation_and_design_plans/
├── README.md
├── BRIDGE_DOMAIN_SUPERSPINE_ANALYSIS.md
│
├── 01_architecture_designs/                # Architecture documents (5 files)
│   ├── 02_bridge_domain_config_parser_design.md
│   ├── 03_netconf_integration_design.md
│   ├── 04_user_management_system_design.md
│   ├── 05_overall_system_design.md
│   └── 06_terminal_web_app_design.txt
│
├── 02_feature_designs/                     # Feature specifications (12 files)
│   ├── 01_smart_deployment_system_design.md
│   ├── 02_simple_wizard_edit_window_design.md
│   ├── 03_integrated_smart_deployment_wizard_design.md
│   ├── 04_phase4_scan_feature_design.md
│   ├── 05_phase4_25_reverse_engineering_design.md
│   ├── 06_p2mp_design_plan.md
│   ├── 07_bridge_domain_discovery_design.md
│   ├── 08_superspine_destination_design_plan.md
│   ├── 09_bridge_domain_json_structure_proposal.md
│   ├── 10_simple_topology_editor_design.md
│   ├── 10_ssh_push_design_plan.md
│   └── 11_bridge_domain_editor_design.md
│
├── 03_implementation_summaries/            # Implementation documents (7 files)
│   ├── 01_simple_wizard_implementation_summary.md
│   ├── 02_tabless_implementation_summary.md
│   ├── 03_bridge_domain_topology_implementation.md
│   ├── 04_bridge_domain_discovery_phase1_implementation.md
│   ├── 05_superspine_implementation_summary.md
│   ├── 06_l_prefix_pattern_implementation.md
│   └── 07_streamlined_flow_implementation.md
│
├── 04_troubleshooting/                     # Troubleshooting guides (11 files)
│   ├── 01_scan_troubleshooting_analysis.md
│   ├── 02_known_metadata_issue.md
│   ├── 03_reverse_engineering_improvements_and_plan.md
│   ├── 04_superspine_auto_selection_fix.md
│   ├── 05_superspine_chassis_consolidation_fix.md
│   ├── 06_access_interface_visualization_fix.md
│   ├── 07_vlan_consolidation_solution.md
│   ├── 08_enhanced_bridge_domain_solution.md
│   ├── 09_interface_handling_update.md
│   ├── 10_enhanced_menu_system_row_rack_update.md
│   └── 11_superspine_interface_validation_solution.md
│
├── 05_planning/                            # Planning documents (9 files)
│   ├── 01_project_vision_and_goals.md
│   ├── 02_current_status_and_next_steps.md
│   ├── 03_lessons_learned.md
│   ├── 04_integration_plan.md
│   ├── 05_workflow.md
│   ├── 06_normalization_workflow_guide.md
│   ├── 07_workspace_cleanup_summary.md
│   ├── BRIDGE_DOMAIN_DATABASE_STRUCTURE_REFERENCE.md
│   └── LEGACY_TO_PHASE1_CONVERSION_RESEARCH.md
│
└── 06_quick_references/                    # Quick reference guides (6 files)
    ├── 01_quick_reference.md
    ├── 02_quick_reference_bugs.md
    ├── 03_react_hooks_troubleshooting.md
    ├── 04_technical_datasheet.md
    ├── 05_sharing_guide.md
    └── 06_lovable_prompt.md
```

### `frontend_docs/` Directory (25 files)
```
frontend_docs/
├── README.md
├── WORKSPACE_IMPLEMENTATION_SUMMARY.md
├── WORKSPACE_MINIMIZED_DESIGN.md
├── WORKSPACE_REDESIGN_IMPROVEMENTS.md
├── components.md
├── layouts-matrix.md
├── sitemap.md
├── tokens.md
│
├── analysis/                               # Analysis documents (4 files)
│   ├── bd-builder-deployment-analysis.md
│   ├── bridge-domain-database-population-analysis.md
│   ├── database-reality-sync-analysis.md
│   └── traditional-vs-targeted-bridge-domain-discovery.md
│
├── architecture/                           # Architecture documents (1 file)
│   └── universal-ssh-deployment-framework.md
│
├── decisions/                              # Decision records (1 file)
│   └── ADR-0001-bd-editor-architecture.md
│
├── flows/                                  # Flow documents (1 file)
│   └── bd-discovery-flow.md
│
├── implementation/                         # Implementation documents (2 files)
│   ├── bd-editor-menu-implementation-plan.md
│   └── configuration-drift-handler-implementation.md
│
├── pages/                                  # Page documentation (3 files)
│   ├── configurations.md
│   ├── workspace-edit.md
│   └── workspace.md
│
├── specifications/                         # Specifications (1 file)
│   └── database-population-use-cases.md
│
└── systems/                                # System documentation (4 files)
    ├── enhanced-cli-presentation.md
    ├── intelligent-bd-editor-menu.md
    ├── interface-discovery-system.md
    └── smart-interface-selection.md
```

### Additional Documentation Directories
```
z_Doc_Discovery-System/                     # Discovery system docs (10 files)
├── ADR-001-BRIDGE_DOMAIN_DISCOVERY_ARCHITECTURE.md
├── AUTHORITATIVE_BRIDGE_DOMAIN_SYSTEM.md
├── BD-PROC_FLOW.md
├── BRIDGE_DOMAIN_PROCESSING_DETAILED.md
├── CLASSIFICATION_LOGIC_FLAWS_ANALYSIS.md
├── FINAL_IMPLEMENTATION_VALIDATION_REPORT.md
├── IMPLEMENTATION_COMPLETE_SUMMARY.md
├── LAB_ENVIRONMENT_AND_USER_NEEDS_OVERVIEW.md
├── REFACTORED_DISCOVERY_WORKFLOW_REVISED.md
└── REFACTORING_PROPOSAL_SEPARATED_CONCERNS.md

zz_Doc_Editor/                              # Editor documentation (7 files)
├── BD_EDITOR_ANALYSIS.md
├── BD_EDITOR_IMPLEMENTATION_PLAN.md
├── CURRENT_SYSTEM_FOUNDATION_ANALYSIS.md
├── DIRECTORY_STRUCTURE_CLARIFICATION.md
├── DNAAS_AWARE_EDITOR_DESIGN.md
├── FRONTEND_BD_EDITOR_INTEGRATION_PLAN.md
└── USER_WORKSPACE_BD_ASSIGNMENT_PLAN.md

zz_Doc_Frontend/                            # Frontend documentation (3 files)
├── FRONTEND_CLEANUP_ANALYSIS.md
├── UI_DESIGN_TRACKING_SYSTEM.md
└── VISUAL_LAYOUT_MAPS.md
```

---

## 📊 TOPOLOGY & DATA FILES (571 files)

### `topology/` Directory - Network Topology Data
```
topology/
├── bundle_mapping_v2.yaml                 # Bundle mapping
├── collection_summary.txt                 # Collection summary
├── complete_topology_v2.json              # Complete topology
├── comprehensive_bridge_domain_test_report.txt # Test report
├── device_mappings.json                   # Device mappings
├── device_status.json                     # Device status
├── device_summary_v2.yaml                 # Device summary
├── topology_tree_v2.yaml                  # Topology tree
├── topology_bridge_domain_validation_report.txt # Validation report
│
├── bridge_domain_discovery/               # Bridge domain discovery (69 files)
│   ├── bridge_domain_mapping_20250724_162935.json
│   ├── bridge_domain_mapping_20250724_162943.json
│   ├── bridge_domain_mapping_20250724_164441.json
│   ├── bridge_domain_mapping_20250724_164546.json
│   ├── bridge_domain_mapping_20250724_164701.json
│   ├── bridge_domain_mapping_20250724_182050.json
│   ├── bridge_domain_mapping_20250724_183108.json
│   ├── bridge_domain_mapping_20250725_125252.json
│   ├── bridge_domain_mapping_20250725_125259.json
│   ├── bridge_domain_mapping_20250725_220328.json
│   ├── bridge_domain_mapping_20250725_221201.json
│   ├── bridge_domain_mapping_20250727_093810.json
│   ├── bridge_domain_mapping_20250727_174413.json
│   ├── bridge_domain_mapping_20250727_174803.json
│   ├── bridge_domain_mapping_20250728_114936.json
│   ├── bridge_domain_mapping_20250728_164316.json
│   ├── bridge_domain_mapping_20250728_170649.json
│   ├── bridge_domain_mapping_20250728_170744.json
│   ├── bridge_domain_mapping_20250728_170805.json
│   ├── bridge_domain_mapping_20250728_170840.json
│   ├── bridge_domain_mapping_20250728_170912.json
│   ├── bridge_domain_mapping_20250728_170951.json
│   ├── bridge_domain_mapping_20250728_171056.json
│   ├── bridge_domain_mapping_20250728_171110.json
│   ├── bridge_domain_mapping_20250728_171115.json
│   ├── bridge_domain_mapping_20250730_115842.json
│   ├── bridge_domain_mapping_20250801_194413.json
│   ├── bridge_domain_mapping_20250803_100711.json
│   ├── bridge_domain_mapping_20250803_172648.json
│   ├── bridge_domain_mapping_20250828_171931.json
│   ├── bridge_domain_mapping_20250831_101202.json
│   ├── bridge_domain_mapping_20250901_110051.json
│   ├── bridge_domain_mapping_20250901_174019.json
│   ├── bridge_domain_mapping_CORRECTED_20250828_171639.json
│   └── [35 corresponding summary .txt files]
│
├── bridge_domain_visualization/           # Bridge domain visualization (33 files)
│   ├── bridge_domain_visualization_M_kazakov_1361_20250725_222548.txt
│   ├── bridge_domain_visualization_g_mochiu_v1430_20250725_225401.txt
│   ├── bridge_domain_visualization_g_mochiu_v1433_20250725_222558.txt
│   ├── bridge_domain_visualization_g_oalfasi_v100_20250724_173623.txt
│   ├── bridge_domain_visualization_g_oshaboo_v192_20250724_180805.txt
│   ├── bridge_domain_visualization_g_oshaboo_v193_20250724_180746.txt
│   ├── bridge_domain_visualization_g_oshaboo_v193_20250724_182107.txt
│   ├── bridge_domain_visualization_g_oshaboo_v194_20250725_220500.txt
│   ├── bridge_domain_visualization_g_oshaboo_v195_20250724_180731.txt
│   ├── bridge_domain_visualization_g_oshaboo_v195_20250725_220517.txt
│   ├── bridge_domain_visualization_g_visaev_v250_to_Spirent_20250725_221218.txt
│   ├── bridge_domain_visualization_g_visaev_v250_to_Spirent_20250725_222502.txt
│   ├── bridge_domain_visualization_g_visaev_v251_20250725_124013.txt
│   ├── bridge_domain_visualization_g_visaev_v251_20250725_221525.txt
│   ├── bridge_domain_visualization_g_visaev_v251_20250727_101122.txt
│   ├── bridge_domain_visualization_g_visaev_v251_20250727_102305.txt
│   ├── bridge_domain_visualization_g_visaev_v251_20250727_174822.txt
│   ├── bridge_domain_visualization_g_visaev_v251_20250727_175104.txt
│   ├── bridge_domain_visualization_g_visaev_v251_20250803_171450.txt
│   ├── bridge_domain_visualization_g_visaev_v251_20250827_131136.txt
│   ├── bridge_domain_visualization_g_visaev_v251_20250827_163144.txt
│   ├── bridge_domain_visualization_g_visaev_v251_20250828_095216.txt
│   ├── bridge_domain_visualization_g_visaev_v251_to_Spirent_20250725_220401.txt
│   ├── bridge_domain_visualization_g_visaev_v253_Spirent_20250725_220412.txt
│   ├── bridge_domain_visualization_g_yotamk_v2314_20250724_183449.txt
│   ├── bridge_domain_visualization_g_yotamk_v2314_20250724_184637.txt
│   ├── bridge_domain_visualization_g_yotamk_v2314_20250724_184700.txt
│   ├── bridge_domain_visualization_g_yotamk_v2314_20250724_184723.txt
│   ├── bridge_domain_visualization_g_zkeiserman_v150_20250725_221747.txt
│   ├── bridge_domain_visualization_g_zkeiserman_v150_20250725_222306.txt
│   ├── bridge_domain_visualization_g_zkeiserman_v150_20250725_222529.txt
│   ├── bridge_domain_visualization_g_zkeiserman_v150_20250726_184906.txt
│   ├── bridge_domain_visualization_g_zkeiserman_v150_20250727_101110.txt
│   ├── bridge_domain_visualization_g_zkeiserman_v150_20250727_175215.txt
│   ├── bridge_domain_visualization_g_zkeiserman_v150_20250728_115123.txt
│   ├── bridge_domain_visualization_g_zkeiserman_v150_20250803_171737.txt
│   ├── bridge_domain_visualization_g_zkeiserman_v151_20250725_123948.txt
│   ├── bridge_domain_visualization_l_akdoshay_v463_20250728_115030.txt
│   └── bridge_domain_visualization_l_yotamk_v381_20250823_173807.txt
│
├── configs/                               # Configuration data (390+ files)
│   ├── parsed_data/                       # Parsed configuration data (130+ files)
│   │   ├── DNAAS-LEAF-A01_lacp_parsed_20250901_174140.yaml
│   │   ├── DNAAS-LEAF-A01_lldp_parsed_20250901_174140.yaml
│   │   ├── DNAAS-LEAF-A02_lacp_parsed_20250901_174140.yaml
│   │   ├── DNAAS-LEAF-A02_lldp_parsed_20250901_174140.yaml
│   │   └── [126+ more parsed LACP/LLDP files for all devices]
│   │   └── bridge_domain_parsed/          # Bridge domain parsed (130+ files)
│   │       ├── DNAAS-LEAF-A01_bridge_domain_instance_parsed_20250901_174140.yaml
│   │       ├── DNAAS-LEAF-A01_vlan_config_parsed_20250901_174147.yaml
│   │       ├── DNAAS-LEAF-A02_bridge_domain_instance_parsed_20250901_174143.yaml
│   │       ├── DNAAS-LEAF-A02_vlan_config_parsed_20250901_174147.yaml
│   │       └── [126+ more bridge domain parsed files for all devices]
│   └── raw-config/                        # Raw configuration data (260+ files)
│       ├── DNAAS-LEAF-A01_lacp_raw_20250901_163158.xml
│       ├── DNAAS-LEAF-A01_lldp_raw_20250901_163159.txt
│       ├── DNAAS-LEAF-A02_lacp_raw_20250901_163158.xml
│       ├── DNAAS-LEAF-A02_lldp_raw_20250901_163159.txt
│       └── [126+ more raw LACP/LLDP files for all devices]
│       └── bridge_domain_raw/             # Raw bridge domain (130+ files)
│           ├── DNAAS-LEAF-A01_bridge_domain_instance_raw_20250901_163201.txt
│           ├── DNAAS-LEAF-A01_vlan_config_raw_20250901_163202.txt
│           ├── DNAAS-LEAF-A02_bridge_domain_instance_raw_20250901_163201.txt
│           ├── DNAAS-LEAF-A02_vlan_config_raw_20250901_163202.txt
│           └── [126+ more raw bridge domain files for all devices]
│
├── enhanced_bridge_domain_discovery/      # Enhanced discovery (16 files)
│   ├── enhanced_bridge_domain_mapping_debug_20250913_184405.json
│   ├── enhanced_bridge_domain_summary_20250901_174514.txt
│   ├── enhanced_bridge_domain_summary_20250901_180821.txt
│   ├── enhanced_bridge_domain_summary_20250901_192853.txt
│   ├── enhanced_bridge_domain_summary_20250901_193326.txt
│   ├── enhanced_bridge_domain_summary_20250901_194553.txt
│   ├── enhanced_bridge_domain_summary_20250901_195144.txt
│   ├── enhanced_bridge_domain_summary_20250901_200456.txt
│   ├── enhanced_bridge_domain_summary_20250901_200644.txt
│   ├── enhanced_bridge_domain_summary_20250901_200659.txt
│   ├── enhanced_bridge_domain_summary_20250901_203559.txt
│   ├── enhanced_bridge_domain_summary_20250901_203814.txt
│   ├── enhanced_bridge_domain_summary_20250901_204011.txt
│   ├── enhanced_bridge_domain_summary_20250901_204022.txt
│   ├── enhanced_bridge_domain_summary_20250913_182246.txt
│   ├── enhanced_bridge_domain_summary_20250913_184145.txt
│   └── enhanced_bridge_domain_summary_20250913_184405.txt
│
├── simplified_discovery_results/          # Simplified discovery (33 files)
│   ├── bridge_domain_mapping_20250920_192354.json
│   ├── bridge_domain_mapping_20250920_192637.json
│   ├── bridge_domain_mapping_20250920_200517.json
│   ├── bridge_domain_mapping_20250920_222626.json
│   ├── bridge_domain_mapping_20250920_223726.json
│   ├── bridge_domain_mapping_20250920_223812.json
│   ├── bridge_domain_mapping_20250920_230121.json
│   ├── bridge_domain_mapping_20250920_230128.json
│   ├── bridge_domain_mapping_20250920_230135.json
│   ├── bridge_domain_mapping_20250920_230143.json
│   ├── bridge_domain_mapping_20250920_230203.json
│   ├── bridge_domain_mapping_20250920_230224.json
│   ├── bridge_domain_mapping_20250920_230256.json
│   ├── bridge_domain_mapping_20250920_230317.json
│   ├── bridge_domain_mapping_20250920_230659.json
│   ├── bridge_domain_mapping_20250920_231101.json
│   ├── bridge_domain_mapping_20250920_231249.json
│   ├── bridge_domain_mapping_20250920_231250.json
│   ├── bridge_domain_mapping_20250920_231813.json
│   ├── bridge_domain_mapping_20250920_231814.json
│   ├── bridge_domain_mapping_20250920_232847.json
│   ├── bridge_domain_mapping_20250920_233404.json
│   ├── bridge_domain_mapping_20250920_233425.json
│   ├── bridge_domain_mapping_20250920_233554.json
│   ├── bridge_domain_mapping_20250920_233652.json
│   ├── bridge_domain_mapping_20250920_234308.json
│   ├── bridge_domain_mapping_20250920_234424.json
│   ├── bridge_domain_mapping_20250924_155851.json
│   ├── bridge_domain_mapping_20250924_160436.json
│   ├── bridge_domain_mapping_20250924_160930.json
│   ├── bridge_domain_mapping_20250924_171203.json
│   ├── bridge_domain_mapping_20250924_171512.json
│   └── bridge_domain_mapping_20250924_171633.json
│
└── visualizations/                        # Visualization files (2 files)
    ├── topology_bundle_aware_tree.txt
    └── topology_minimized_tree.txt
```

---

## 📋 LOGS & MONITORING (41 files)

### `logs/` Directory
```
logs/
├── enhanced_discovery_detailed.log        # Enhanced discovery detailed log
├── enhanced_discovery_detailed.log.1      # Log rotation file
├── enhanced_discovery_operations.log      # Operations log
├── enhanced_discovery_operations.log.1    # Log rotation file
├── enhanced_discovery_performance.log     # Performance log
├── enhanced_discovery_performance.log.1   # Log rotation file
│
└── consolidation/                          # Consolidation logs (35 files)
    ├── FAILURES_ONLY_044c89de_20250831_113817.txt
    ├── FAILURES_ONLY_2bd6a0c9_20250831_114305.txt
    ├── FAILURES_ONLY_42b5c8c0_20250831_085126.txt
    ├── FAILURES_ONLY_4aeef273_20250831_083738.txt
    ├── FAILURES_ONLY_6d2339d5_20250831_114338.txt
    ├── FAILURES_ONLY_76f852d1_20250831_082005.txt
    ├── FAILURES_ONLY_81d20509_20250831_082600.txt
    ├── FAILURES_ONLY_98781104_20250831_093022.txt
    ├── FAILURES_ONLY_ad8d8a14_20250831_095748.txt
    ├── FAILURES_ONLY_c8c4e59e_20250831_095017.txt
    ├── FAILURES_ONLY_d0b462ff_20250831_114650.txt
    ├── FAILURES_ONLY_d10b82dd_20250831_084032.txt
    ├── SUMMARY_044c89de_20250831_113817.txt
    ├── SUMMARY_2bd6a0c9_20250831_114305.txt
    ├── SUMMARY_42b5c8c0_20250831_085126.txt
    ├── SUMMARY_4aeef273_20250831_083738.txt
    ├── SUMMARY_6d2339d5_20250831_114338.txt
    ├── SUMMARY_76f852d1_20250831_082005.txt
    ├── SUMMARY_81d20509_20250831_082600.txt
    ├── SUMMARY_98781104_20250831_093022.txt
    ├── SUMMARY_ad8d8a14_20250831_095748.txt
    ├── SUMMARY_c8c4e59e_20250831_095017.txt
    ├── SUMMARY_d0b462ff_20250831_114650.txt
    ├── SUMMARY_d10b82dd_20250831_084032.txt
    ├── parsing_failures_044c89de_20250831_113817.json
    ├── parsing_failures_2bd6a0c9_20250831_114305.json
    ├── parsing_failures_42b5c8c0_20250831_085126.json
    ├── parsing_failures_4aeef273_20250831_083738.json
    ├── parsing_failures_6d2339d5_20250831_114338.json
    ├── parsing_failures_76f852d1_20250831_082005.json
    ├── parsing_failures_98781104_20250831_093022.json
    ├── parsing_failures_ad8d8a14_20250831_095748.json
    ├── parsing_failures_c8c4e59e_20250831_095017.json
    ├── parsing_failures_d0b462ff_20250831_114650.json
    └── parsing_failures_d10b82dd_20250831_084032.json
```

---

## 🛠️ SCRIPTS & UTILITIES (13 files)

### `scripts/` Directory
```
scripts/
├── ascii_topology_tree.py                 # ASCII topology tree generator
├── collect_lacp_xml.py                     # LACP XML collector
├── comprehensive_normalization_workflow.py # Normalization workflow
├── device_status_viewer.py                # Device status viewer
├── enhanced_topology_discovery.py         # Enhanced topology discovery
├── inventory_manager.py                   # Inventory manager
├── manual_normalization_workflow.sh       # Manual normalization workflow
├── minimized_topology_tree.py             # Minimized topology tree
├── ssh_push_menu.py                       # SSH push menu
│
├── configs/                               # Script configurations
│   └── deployment_logs/                   # Deployment logs (2 files)
│       ├── bridge_domain_g_visaev-Newest_v290_20250802_220744.log
│       └── bridge_domain_g_visaev-Newest_v290_20250802_221116.log
│
└── topology/                              # Topology scripts
    ├── collection_summary.txt             # Collection summary
    └── device_status.json                 # Device status
```

---

## 🧩 CORE UTILITIES (9 files)

### `core/` Directory
```
core/
├── __init__.py
│
├── config/                                # Configuration utilities (2 files)
│   ├── __init__.py
│   └── config_manager.py                  # Configuration manager
│
├── exceptions/                            # Exception handling (2 files)
│   ├── __init__.py
│   └── base_exceptions.py                 # Base exceptions
│
├── logging/                               # Logging utilities (2 files)
│   ├── __init__.py
│   └── logger_factory.py                 # Logger factory
│
└── validation/                            # Validation utilities (2 files)
    ├── __init__.py
    └── validators.py                      # Validators
```

---

## 🔧 UTILITIES (6 files)

### `utils/` Directory
```
utils/
├── __init__.py
├── cli_parser.py                          # CLI parser
├── cli_topology_discovery.py             # CLI topology discovery
├── dnos_ssh.py                           # DNOS SSH utilities
├── inventory.py                          # Inventory utilities
└── topology_discovery.py                # Topology discovery utilities
```

---

## 📦 DEPLOYMENT & INVENTORY

### `deployment/` Directory (1 file)
```
deployment/
└── ssh_manager.py                        # SSH manager
```

### `inventory/` Directory (1 file)
```
inventory/
└── DNAAS Inventory.xlsx                  # DNAAS inventory spreadsheet
```

---

## 🚨 CRITICAL FINDINGS & CLEANUP PRIORITIES

### 🔴 **IMMEDIATE CLEANUP REQUIRED**

1. **Database Backup Explosion** (14 files)
   - 1 active database + 13 backup files
   - Consuming significant disk space
   - **Action**: Keep only 3 most recent backups

2. **Duplicate Frontend Projects** (229 files total)
   - `frontend/` (113 files)
   - `lovable-frontend/` (116 files)
   - **Action**: Choose one and remove the other

3. **Topology Data Overload** (571 files)
   - Hundreds of timestamped discovery results
   - Raw and parsed configuration files
   - **Action**: Archive old discovery results (>30 days)

4. **Scattered Test Files** (3 files)
   - Root-level test files not in dedicated directory
   - **Action**: Create `tests/` directory structure

### 🟡 **MEDIUM PRIORITY CLEANUP**

5. **Version Proliferation** (Multiple files)
   - `bd_editor_week2.py`, `bd_editor_week3.py`, `bd_editor_api.py`
   - `phase1_*` vs `enhanced_*` vs `unified_*` components
   - **Action**: Consolidate to single versioned modules

6. **Log File Accumulation** (41 files)
   - Multiple log rotation files
   - Consolidation failure logs
   - **Action**: Implement log rotation and cleanup

7. **Documentation Fragmentation** (77 files across 4 directories)
   - Multiple documentation directories
   - **Action**: Consolidate into unified docs structure

### 🟢 **LOW PRIORITY OPTIMIZATION**

8. **Configuration Test Proliferation** (35 pending configs)
   - Multiple test configurations in pending state
   - **Action**: Archive old test configurations

9. **Git Object Accumulation** (Excluded from count)
   - Large `.git/objects` directories in frontend projects
   - **Action**: Git garbage collection

---

## 📈 **PROJECT HEALTH METRICS**

- **File Organization**: 5/10 (needs major cleanup)
- **Code Structure**: 7/10 (well-organized business logic)
- **Documentation**: 6/10 (comprehensive but fragmented)
- **Data Management**: 4/10 (excessive data accumulation)
- **Version Control**: 6/10 (multiple versions need consolidation)

---

## 🎯 **RECOMMENDED CLEANUP SEQUENCE**

1. **Week 1**: Database backup cleanup (keep 3 most recent)
2. **Week 2**: Choose and consolidate frontend projects
3. **Week 3**: Archive old topology discovery results
4. **Week 4**: Organize test files and documentation
5. **Week 5**: Consolidate versioned components
6. **Week 6**: Implement log rotation and cleanup automation

This comprehensive file map catalogs all 1,109 project files and provides a clear roadmap for optimization and cleanup.
