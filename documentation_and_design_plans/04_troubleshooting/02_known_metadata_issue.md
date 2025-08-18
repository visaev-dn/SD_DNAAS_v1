# Known Issue: `_metadata` Key in P2MP Configuration Data

## **Symptoms**
- When generating P2MP bridge domain configurations, the returned config data sometimes contains a `_metadata` key alongside device configuration blocks.
- This results in UI output like:
  ```
  === DNAAS-LEAF-B13 ===
  ...
  === _metadata ===
  [object Object]
  ```
- The `_metadata` key should not be present in the config data returned to the UI or saved in the database.

## **Root Cause**
- The P2MP builder and config generator are designed to return a tuple `(configs, metadata)` where `configs` is a dict of device configs and `metadata` is a separate dict.
- However, in some scenarios (especially with mixed P2MP or legacy configs), the `_metadata` key is still present in the returned `configs` dict.
- This is likely due to merging or legacy code paths in the unified builder that do not remove `_metadata` after merging configs.
- Old database records may also still contain `_metadata` in the `config_data` column.

## **Impact**
- The UI displays `[object Object]` for the `_metadata` section, confusing users.
- The database may store redundant or unwanted metadata in the config data.

## **Next Steps / TODO**
- Audit all code paths in the unified builder and P2MP builder to ensure `_metadata` is never added to the config data dict.
- After merging configs (especially in `_build_mixed_p2mp_config`), always remove `_metadata`:
  ```python
  if '_metadata' in all_configs:
      del all_configs['_metadata']
  ```
- Consider running a migration to clean up old configs in the database.
- Add tests to ensure no config data ever contains `_metadata`.

## **Temporary Workaround**
- If you see `_metadata` in the UI, you can safely ignore it for now. The actual device configs are still correct.

---
*Last updated: 2025-08-03* 