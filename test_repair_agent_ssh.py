#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test RepairAgent SSH and Package Installation

Quick test to verify RepairAgent can:
1. Check SSH connection health
2. Repair SSH connection
3. Check production packages
4. Install missing packages

WITHOUT INTERACTIVE PROMPTS!
"""

import asyncio
import sys
import os
import logging

# Setup paths
sys.path.insert(0, os.path.dirname(__file__))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockOrchestrator:
    """Mock orchestrator for testing"""
    def __init__(self):
        self.is_running = True


async def test_repair_agent():
    """Test RepairAgent SSH and package installation"""

    from tester.repair_agent import RepairAgent

    logger.info("=" * 80)
    logger.info("TEST: RepairAgent SSH + Package Installation")
    logger.info("=" * 80)

    # Create mock orchestrator
    orchestrator = MockOrchestrator()

    # Initialize RepairAgent
    logger.info("\n1. Initializing RepairAgent...")
    repair_agent = RepairAgent(orchestrator)
    logger.info("✅ RepairAgent initialized")

    # Test SSH health check
    logger.info("\n2. Checking SSH health...")
    ssh_health = await repair_agent._check_production_ssh_health()
    logger.info(f"SSH Health: {ssh_health}")

    if not ssh_health['healthy']:
        logger.warning("⚠️ SSH unhealthy, attempting repair...")

        # Test SSH repair
        logger.info("\n3. Repairing SSH connection...")
        repair_success = await repair_agent._repair_ssh_connection(ssh_health)

        if repair_success:
            logger.info("✅ SSH repaired successfully")

            # Re-check SSH health
            ssh_health = await repair_agent._check_production_ssh_health()
            logger.info(f"SSH Health (after repair): {ssh_health}")
        else:
            logger.error("❌ SSH repair failed")
            logger.error("   Manual setup required:")
            logger.error("   1. Set PRODUCTION_SSH_PASSWORD in .env")
            logger.error("   2. Or manually copy SSH key to production")
            return False
    else:
        logger.info("✅ SSH already healthy")

    # Test packages health check
    logger.info("\n4. Checking production packages...")
    packages_health = await repair_agent._check_production_packages_health()
    logger.info(f"Packages Health: {packages_health}")

    if not packages_health['healthy']:
        logger.warning(f"⚠️ Missing packages: {packages_health['missing']}")

        # Test package installation
        logger.info("\n5. Installing missing packages...")
        install_success = await repair_agent._repair_production_packages(packages_health)

        if install_success:
            logger.info("✅ Packages installed successfully")

            # Re-check packages
            packages_health = await repair_agent._check_production_packages_health()
            logger.info(f"Packages Health (after install): {packages_health}")
        else:
            logger.error("❌ Package installation failed")
            return False
    else:
        logger.info("✅ All packages already installed")

    # Show repair statistics
    logger.info("\n6. Repair Statistics:")
    stats = repair_agent.get_repair_statistics()
    for key, value in stats.items():
        logger.info(f"   {key}: {value}")

    logger.info("\n" + "=" * 80)
    logger.info("✅ TEST PASSED - RepairAgent working correctly!")
    logger.info("=" * 80)

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_repair_agent())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        sys.exit(1)
