#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test prompt_manager functionality"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "web-admin"))

from utils.prompt_manager import get_agent_prompts

def main():
    print("=" * 60)
    print("Testing Prompt Manager")
    print("=" * 60)

    # Test getting prompts for each agent
    agents = ['interviewer', 'auditor', 'planner', 'researcher', 'writer']

    for agent in agents:
        print(f"\n{agent.upper()} Prompts:")
        try:
            prompts = get_agent_prompts(agent)
            if prompts:
                print(f"  Found {len(prompts)} prompt(s)")
                for p in prompts:
                    default_mark = " [DEFAULT]" if p.get('is_default') else ""
                    print(f"    - {p.get('prompt_key')} (v{p.get('version', 1)}){default_mark}")
            else:
                print(f"  No prompts found")
        except Exception as e:
            print(f"  ERROR: {e}")

    print("\n" + "=" * 60)
    print("Test complete")
    print("=" * 60)

if __name__ == "__main__":
    main()
