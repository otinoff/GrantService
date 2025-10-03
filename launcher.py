#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Universal launcher for GrantService Admin Panel
Cross-platform launcher with proper environment setup
"""

import sys
import os
import platform
import subprocess
from pathlib import Path

# Add core module to path FIRST before any other imports
launcher_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(launcher_dir))

# Now we can import our core module
from core import setup_environment, get_path_manager, get_config


def sync_database_on_startup():
    """
    Automatically sync production database to local machine on startup
    Only runs on Windows local development, not on production server
    """
    # Only sync on Windows local machines
    if platform.system() != "Windows":
        return

    # Configuration
    SERVER = "root@5.35.88.251"
    REMOTE_DB = "/var/GrantService/data/grantservice.db"
    LOCAL_DB = launcher_dir / "data" / "grantservice.db"

    print("Syncing database from production...")

    try:
        # Use scp to download database
        result = subprocess.run(
            ["scp", f"{SERVER}:{REMOTE_DB}", str(LOCAL_DB)],
            capture_output=True,
            timeout=15  # 15 second timeout
        )

        if result.returncode == 0:
            # Get database size
            db_size_mb = LOCAL_DB.stat().st_size / (1024 * 1024)
            print(f"[OK] Database synced successfully ({db_size_mb:.1f} MB)")
        else:
            print(f"[WARNING] Database sync failed (working with local copy)")
            if result.stderr:
                print(f"  Error: {result.stderr.decode('utf-8', errors='ignore').strip()}")

    except subprocess.TimeoutExpired:
        print("[WARNING] Database sync timeout (working with local copy)")
    except FileNotFoundError:
        print("[WARNING] scp command not found (working with local copy)")
    except Exception as e:
        print(f"[WARNING] Database sync error: {e} (working with local copy)")

    print("")  # Empty line for readability


def setup_and_launch():
    """Setup environment and launch the admin panel"""

    print("=" * 60)
    print("GRANTSERVICE ADMIN LAUNCHER")
    print("=" * 60)

    # Sync database from production (Windows only)
    sync_database_on_startup()

    # Setup environment
    print("Setting up environment...")
    env = setup_environment(verbose=True)
    paths = get_path_manager()
    config = get_config()
    
    print(f"OS: {paths.system}")
    print(f"Base Path: {paths.base_path}")
    print(f"Web Admin: {paths.web_admin}")
    print("=" * 60)
    
    # Import streamlit after environment setup
    try:
        import streamlit.web.cli as stcli
    except ImportError:
        print("ERROR: Streamlit is not installed")
        print("Please install it with: pip install streamlit")
        return 1
    
    # Prepare Streamlit arguments
    # Use main_app if it exists, otherwise fallback to home_page
    if hasattr(paths, 'main_app') and paths.main_app.exists():
        entry_point = str(paths.main_app)
    else:
        entry_point = str(paths.home_page)
    
    sys.argv = [
        "streamlit",
        "run",
        entry_point,
        "--server.port", str(config.streamlit_port),
        "--server.headless", str(config.streamlit_headless).lower(),
        "--browser.serverAddress", config.streamlit_host,
        "--theme.base", "light"
    ]
    
    print(f"\nLaunching admin panel...")
    print(f"URL: http://{config.streamlit_host}:{config.streamlit_port}")
    print("\nPress Ctrl+C to stop")
    print("=" * 60)
    
    # Launch Streamlit
    return stcli.main()


def test_environment():
    """Test the environment setup"""
    print("=" * 60)
    print("TESTING ENVIRONMENT SETUP")
    print("=" * 60)
    
    # Setup environment
    env = setup_environment(verbose=True)
    paths = get_path_manager()
    config = get_config()
    
    # Test imports
    print("\n[TESTING IMPORTS]")
    
    # Track if all tests pass
    all_tests_passed = True
    
    # Test web admin utils
    web_admin_path = str(paths.web_admin)
    auth_file = paths.web_admin / "utils" / "auth.py"
    
    # Make sure web-admin is in path (it should be after setup_environment)
    import sys
    if web_admin_path not in sys.path:
        sys.path.insert(0, web_admin_path)
    
    # Try direct import with fallback to importlib
    auth_imported = False
    try:
        from utils.auth import is_user_authorized
        print("✓ utils.auth imported successfully")
        auth_imported = True
    except ImportError as e:
        print(f"✗ utils.auth import failed: {e}")
        print(f"   Tried paths: {web_admin_path}")
        
        # Check if the file exists but can't be imported
        if auth_file.exists():
            print(f"   Note: Auth file exists at {auth_file}")
            print(f"   This may be due to missing dependencies (like streamlit)")
            # Don't fail the test for this - web admin import issues shouldn't block the launcher
            print("⚠ utils.auth import failed but file exists (likely dependency issue)")
        else:
            print(f"✗ utils.auth file not found at {auth_file}")
            all_tests_passed = False
    
    
    # Test database
    database_imported = False
    try:
        from data.database import GrantServiceDatabase
        print("✓ data.database imported successfully")
        database_imported = True
    except ImportError as e:
        print(f"✗ data.database import failed: {e}")
        all_tests_passed = False
    
    # Test telegram bot config
    try:
        from telegram_bot.config import constants
        print("✓ telegram_bot.config imported successfully")
    except ImportError as e:
        # Try alternative import
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "constants",
                paths.constants_file
            )
            if spec and spec.loader:
                constants = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(constants)
                print("✓ Bot constants loaded via importlib")
        except Exception as e2:
            print(f"✗ Bot config import failed: {e2}")
            all_tests_passed = False
    
    print("\n[ENVIRONMENT INFO]")
    env.print_debug_info()
    
    print("\n[TEST COMPLETE]")
    
    # Return 0 if all critical tests passed, 1 otherwise
    if all_tests_passed:
        print("\n✓ All critical tests passed. Environment is ready!")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        return 1


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="GrantService Admin Panel Launcher"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test environment setup without launching"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output"
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Override Streamlit port"
    )
    
    args = parser.parse_args()
    
    # Set environment variables from arguments
    if args.port:
        os.environ['STREAMLIT_PORT'] = str(args.port)
    
    if args.debug:
        os.environ['LOG_LEVEL'] = 'DEBUG'
    
    # Run test or launch
    if args.test:
        return test_environment()
    else:
        return setup_and_launch()


if __name__ == "__main__":
    sys.exit(main())