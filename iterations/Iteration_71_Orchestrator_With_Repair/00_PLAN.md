# Iteration 71: Night Orchestrator + Repair Agent Integration

**Date:** 2025-10-31
**Status:** Planning
**Previous:** Iteration 70 - Repair Agent (Phase 1 complete)

---

## 🎯 Goal

Integrate Repair Agent into Night Test Orchestrator for parallel monitoring and proactive repair.

**Expected Result:**
- Night Orchestrator runs test cycles
- Repair Agent monitors in parallel (every 10 seconds)
- When problems detected → Repair Agent fixes proactively
- NO degradation of business logic
- Morning report includes repair statistics

---

## 📋 Plan

### Phase 1: Integration

**File:** `tester/night_orchestrator.py`

**Changes:**
1. Import RepairAgent
2. Initialize RepairAgent in `__init__()`
3. Start RepairAgent monitoring as parallel task
4. Handle RepairAgent errors gracefully
5. Stop RepairAgent when orchestrator stops
6. Add repair statistics to summary

**Code:**
```python
from tester.repair_agent import RepairAgent

class NightTestOrchestrator:
    def __init__(self, config):
        # ... existing init ...

        # NEW: Initialize Repair Agent
        self.repair_agent = RepairAgent(self)
        self.logger.info("🔧 Repair Agent initialized")

    async def run(self, resume=False):
        # ... existing setup ...

        # NEW: Start Repair Agent monitoring in parallel
        self.logger.info("🔧 Starting Repair Agent monitoring...")
        repair_task = asyncio.create_task(
            self.repair_agent.start_monitoring()
        )

        try:
            # Run test cycles (existing code)
            await self._run_cycles()

        except Exception as e:
            self.logger.error(f"Orchestrator error: {e}")
            raise

        finally:
            # NEW: Stop Repair Agent
            self.logger.info("🔧 Stopping Repair Agent...")
            await self.repair_agent.stop_monitoring()

            try:
                await repair_task
            except asyncio.CancelledError:
                pass

        # NEW: Add repair statistics to summary
        summary = self._generate_summary()
        summary['repair_stats'] = self.repair_agent.get_repair_statistics()

        return summary
```

### Phase 2: Morning Report Integration

**File:** `tester/morning_report_generator.py`

**Changes:**
1. Add repair statistics section
2. Show total repairs, success rate
3. Show repairs by component
4. Show fallback usage
5. Show degradation prevented count

**Report Section:**
```markdown
## 🔧 REPAIR AGENT REPORT

### System Health
- Database: ✅ Healthy (1 repair performed)
- GigaChat: ✅ Healthy
- WebSearch: ✅ Healthy
- Qdrant: ✅ Healthy

### Repairs Performed: 3 total

1. **Database Connection Lost** (Cycle 23)
   - Time: 23:05:20
   - Strategy: Proactive rebuild
   - Duration: 15 seconds
   - Result: ✅ Success

2. **GigaChat Quota Exceeded** (Cycle 45)
   - Time: 02:15:10
   - Strategy: Switched to GigaChat-Plus
   - Duration: 10 seconds
   - Result: ✅ Success

3. **WebSearch Timeout** (Cycle 78)
   - Time: 05:23:45
   - Strategy: Increased timeout to 90s
   - Duration: 8 seconds
   - Result: ✅ Success

### Degradation Prevented: 3 instances
- ✅ Database NOT disabled (would break data persistence)
- ✅ Quality thresholds NOT lowered (would break validation)
- ✅ Business logic NOT modified (would break production parity)

### Fallbacks Used: 0
- No fallbacks activated (all repairs successful!)

### Recommendations:
- ✅ All repairs successful. No manual intervention needed.
```

### Phase 3: Testing

#### 3.1 Local Test (1 cycle)
```bash
python run_night_tests.py --cycles 1 --mock-websearch
```

**Expected:**
- Orchestrator starts
- Repair Agent starts monitoring in parallel
- 1 cycle completes
- Repair Agent shows "0 repairs" (everything healthy)
- Morning report includes repair section

#### 3.2 Production Test (1 cycle)
```bash
ssh root@5.35.88.251
cd /var/GrantService
python3 run_night_tests.py --cycles 1 --mock-websearch
```

**Expected:**
- Same as local test
- Verify no degradation
- Check artifacts
- Check morning report

#### 3.3 Simulated Failure Test

Temporarily modify code to simulate failures:
- Disconnect database mid-cycle
- Verify Repair Agent detects and repairs
- Check morning report shows repair

---

## ✅ Success Criteria

### Integration Working:
- [x] RepairAgent imported successfully
- [ ] RepairAgent initialized in orchestrator
- [ ] Monitoring starts in parallel
- [ ] Monitoring stops gracefully
- [ ] No errors in logs

### Repair Statistics:
- [ ] Statistics captured correctly
- [ ] Morning report includes repair section
- [ ] Format is clear and readable

### Production Test:
- [ ] 1 cycle completes successfully
- [ ] No errors
- [ ] Artifacts generated
- [ ] Morning report generated
- [ ] Repair section shows "0 repairs" (healthy system)

---

## 🚀 Next Steps (Iteration 72+)

After integration working:

### Iteration 72: Complete Repair Strategies
- Finish Phase 2 of Iteration 70
- Implement full GigaChat rebuild
- Implement full WebSearch rebuild
- Implement full Database rebuild

### Iteration 73: Failure Simulation Testing
- Test with simulated database failure
- Test with simulated API quota exceeded
- Test with simulated network timeout
- Verify all repairs work correctly

### Iteration 74: 100 Cycle Production Run
- Run 100 cycles overnight
- Collect real repair statistics
- Analyze common issues
- Optimize repair strategies

---

**Status:** Ready to start Phase 1 - Integration
**Next:** Modify `tester/night_orchestrator.py`
