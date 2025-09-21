#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test imports for Streamlit pages
"""

import streamlit as st
import sys
import os
from pathlib import Path

st.title("🔬 Import Test Page")

# Show current working directory
st.write("**Current Working Directory:**", os.getcwd())

# Add paths for imports
current_file = Path(__file__).resolve()
st.write("**Current File:**", str(current_file))

base_dir = current_file.parent  # GrantService directory
web_admin_dir = base_dir / "web-admin"

st.write("**Base Directory:**", str(base_dir))
st.write("**Web Admin Directory:**", str(web_admin_dir))

# Check if directories exist
st.write("**Base Dir Exists:**", base_dir.exists())
st.write("**Web Admin Dir Exists:**", web_admin_dir.exists())

# Check utils directory
utils_dir = web_admin_dir / "utils"
st.write("**Utils Directory:**", str(utils_dir))
st.write("**Utils Dir Exists:**", utils_dir.exists())

# Check auth.py file
auth_file = utils_dir / "auth.py"
st.write("**Auth File:**", str(auth_file))
st.write("**Auth File Exists:**", auth_file.exists())

st.markdown("---")
st.subheader("sys.path before adding:")
for i, p in enumerate(sys.path[:10]):
    st.write(f"{i}: {p}")

# Add to sys.path if not already there
if str(web_admin_dir) not in sys.path:
    sys.path.insert(0, str(web_admin_dir))
    st.success(f"✅ Added to sys.path: {web_admin_dir}")
else:
    st.info(f"ℹ️ Already in sys.path: {web_admin_dir}")

if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))
    st.success(f"✅ Added to sys.path: {base_dir}")
else:
    st.info(f"ℹ️ Already in sys.path: {base_dir}")

st.markdown("---")
st.subheader("sys.path after adding:")
for i, p in enumerate(sys.path[:10]):
    st.write(f"{i}: {p}")

st.markdown("---")
st.subheader("Testing Imports:")

# Try importing utils.auth
try:
    from utils.auth import is_user_authorized
    st.success("✅ Successfully imported utils.auth")
    st.write("Function is_user_authorized:", is_user_authorized)
except ImportError as e:
    st.error(f"❌ Failed to import utils.auth: {e}")
    
    # Try alternative import
    st.info("Trying alternative import with importlib...")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("auth", str(auth_file))
        if spec and spec.loader:
            auth_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(auth_module)
            st.success("✅ Loaded auth module via importlib")
            st.write("Has is_user_authorized:", hasattr(auth_module, 'is_user_authorized'))
    except Exception as e2:
        st.error(f"❌ Alternative import also failed: {e2}")

# Try importing data.database
try:
    from data.database import GrantServiceDatabase
    st.success("✅ Successfully imported data.database")
except ImportError as e:
    st.error(f"❌ Failed to import data.database: {e}")

st.markdown("---")
st.info("Test complete!")