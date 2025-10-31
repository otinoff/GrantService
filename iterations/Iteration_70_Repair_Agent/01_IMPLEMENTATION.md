# Iteration 70: Repair Agent - IMPLEMENTATION

**Date:** 2025-10-31
**Status:** In Progress
**Phase:** Phase 1 - Basic Structure ✅

---

## ✅ Completed (Phase 1)

### 1. Created `tester/repair_agent.py`

**File:** `C:\SnowWhiteAI\GrantService\tester\repair_agent.py`

**Class:** `RepairAgent`

**Implemented:**
- ✅ Basic class structure
- ✅ `__init__()` - initialization with orchestrator
- ✅ `start_monitoring()` - main monitoring loop (10 sec intervals)
- ✅ `stop_monitoring()` - graceful shutdown
- ✅ `_check_system_health()` - comprehensive health checks
- ✅ `_handle_health_issues()` - issue handling routing
- ✅ Health check methods for all components:
  - `_check_database_health()` - PostgreSQL connection check
  - `_check_gigachat_health()` - GigaChat API check (stub)
  - `_check_websearch_health()` - WebSearch API check (stub)
  - `_check_qdrant_health()` - Qdrant vector DB check (stub)
  - `_check_disk_space()` - Disk space monitoring
  - `_check_memory()` - Memory monitoring
- ✅ `_repair_database_connection()` - Basic database repair (partial)
- ✅ `_notify_admin()` - Admin notifications (logging for now)
- ✅ `get_repair_statistics()` - Statistics for morning report

**Statistics Tracking:**
- `repairs_performed[]` - list of all repairs
- `fallbacks_used[]` - list of fallback activations
- `health_checks[]` - periodic health snapshots

---

## 🔄 In Progress (Phase 2)

### Repair Strategies - PROACTIVE DEVELOPER MODE

Need to implement full rebuild cycle for each component:

#### Template: 7-Step Rebuild Process

```python
async def _repair_COMPONENT_connection(self):
    """PROACTIVE DEVELOPER MODE - Rebuild COMPONENT"""

    # STEP 1: ОСТАНОВИТЬ модуль
    await self._stop_component_module()

    # STEP 2: ДИАГНОСТИКА - Проверить ВСЁ
    diagnostics = {
        'dependency_1': await self._check_dependency_1(),
        'dependency_2': await self._check_dependency_2(),
        'config': self._check_config(),
        'network': await self._check_network(),
        'resources': self._check_resources()
    }

    # STEP 3: НАЙТИ рабочую конфигурацию
    working_config = await self._find_working_config(diagnostics)

    if not working_config:
        return await self._fallback_to_alternative()

    # STEP 4: ПЕРЕСОБРАТЬ модуль
    await self._rebuild_component_module(working_config)

    # STEP 5: ТЕСТИРОВАТЬ ВСЕ функции
    tests = {
        'test_1': await self._test_component_function_1(),
        'test_2': await self._test_component_function_2(),
    }

    if not all(tests.values()):
        return await self._fallback_to_alternative()

    # STEP 6: ЗАПУСТИТЬ модуль
    await self._start_component_module(working_config)

    # STEP 7: ФИНАЛЬНАЯ валидация
    if await self._validate_component_operational():
        logger.info("✅ Component REBUILT and OPERATIONAL!")
        return True
    else:
        return await self._fallback_to_alternative()
```

### 2. Database Rebuild (In Progress)

**File:** `tester/repair_agent.py:_repair_database_connection()`

**TODO:**
- [ ] Implement STEP 1: Stop all database connections
- [ ] Implement STEP 2: Complete diagnostics
  - [ ] Check .env file validity
  - [ ] Network ping to PGHOST
  - [ ] Check PostgreSQL service status
  - [ ] Check port availability
- [ ] Implement STEP 3: Find working configuration
  - [ ] Try reconnection with exponential backoff
  - [ ] Try alternative connection strings
- [ ] Implement STEP 4: Rebuild database module
  - [ ] Create new GrantServiceDatabase instance
  - [ ] Initialize connection pool
- [ ] Implement STEP 5: Test all functions
  - [ ] Test simple query
  - [ ] Test write operation
  - [ ] Test transaction
- [ ] Implement STEP 6: Start module
- [ ] Implement STEP 7: Final validation

### 3. GigaChat Rebuild (Not Started)

**File:** `tester/repair_agent.py:_repair_gigachat_connection()`

**TODO:**
- [ ] Implement STEP 1: Stop GigaChat client
- [ ] Implement STEP 2: Complete diagnostics
  - [ ] Check all API keys
  - [ ] Check all models (Plus, Pro, Max)
  - [ ] Check quotas per model
  - [ ] Check token validity
  - [ ] Network check
- [ ] Implement STEP 3: Find working configuration
  - [ ] Test all combinations (model + key)
  - [ ] Find combination with quota available
- [ ] Implement STEP 4: Rebuild GigaChat client
  - [ ] Create new client with working config
  - [ ] Initialize with new model/key
- [ ] Implement STEP 5: Test all functions
  - [ ] Test connection
  - [ ] Test simple request
  - [ ] Test quota check
  - [ ] Test error handling
- [ ] Implement STEP 6: Start module
- [ ] Implement STEP 7: Final validation
- [ ] Implement fallback to Claude Code

### 4. WebSearch Rebuild (Not Started)

**File:** `tester/repair_agent.py:_repair_websearch_connection()`

**TODO:**
- [ ] Implement STEP 1: Stop WebSearch client
- [ ] Implement STEP 2: Complete diagnostics
  - [ ] Check API availability
  - [ ] Check rate limits
  - [ ] Check timeout settings
  - [ ] Network check
- [ ] Implement STEP 3: Find working configuration
  - [ ] Try increased timeout (60s, 90s, 120s)
  - [ ] Try simple test query
- [ ] Implement STEP 4: Rebuild WebSearch client
  - [ ] Create new client with adjusted timeout
- [ ] Implement STEP 5: Test all functions
  - [ ] Test simple query
  - [ ] Test complex query
  - [ ] Test rate limiting
- [ ] Implement STEP 6: Start module
- [ ] Implement STEP 7: Final validation
- [ ] Implement fallback to Perplexity → Qdrant → Cache

### 5. Qdrant Rebuild (Not Started)

**File:** `tester/repair_agent.py:_repair_qdrant_connection()`

**TODO:**
- [ ] Implement full rebuild cycle
- [ ] Similar to database rebuild

---

## 📋 Next Steps (Phase 3)

### Integration with Night Orchestrator

This will be **Iteration 71**: Night Orchestrator + Repair Agent

**File:** `tester/night_orchestrator.py`

**Changes needed:**
1. Import RepairAgent
2. Initialize RepairAgent in `__init__()`
3. Start RepairAgent monitoring in parallel with test cycles
4. Add repair statistics to morning report
5. Handle RepairAgent failures gracefully

**Code skeleton:**
```python
class NightTestOrchestrator:
    def __init__(self, config):
        # ... existing init ...

        # NEW: Initialize Repair Agent
        self.repair_agent = RepairAgent(self)

    async def run(self, resume=False):
        # ... existing code ...

        # NEW: Start Repair Agent monitoring in parallel
        repair_task = asyncio.create_task(
            self.repair_agent.start_monitoring()
        )

        try:
            # Run test cycles
            await self._run_cycles()
        finally:
            # Stop Repair Agent
            await self.repair_agent.stop_monitoring()
            await repair_task

        # NEW: Add repair statistics to summary
        summary['repair_stats'] = self.repair_agent.get_repair_statistics()
```

---

## 🧪 Testing Plan (Phase 4)

### 1. Unit Tests

**File:** `tests/unit/test_repair_agent.py`

Test individual repair strategies:
- Test database reconnection
- Test GigaChat model switching
- Test WebSearch timeout handling
- Test health checks

### 2. Integration Tests with Simulated Failures

**File:** `tests/integration/test_repair_agent_e2e.py`

Simulate failures and verify repairs:
- Disconnect database mid-cycle → verify repair
- Exhaust GigaChat quota → verify switch to alternative model
- Trigger WebSearch timeout → verify increased timeout
- All scenarios should preserve business logic!

### 3. Production Test

Run on production server with:
- `--cycles 10`
- Monitor repair statistics
- Verify no degradation
- Check morning report

---

## 📊 Success Criteria

### Phase 1 (Basic Structure): ✅ COMPLETE
- [x] RepairAgent class created
- [x] Monitoring loop implemented
- [x] Health checks implemented
- [x] Statistics tracking implemented

### Phase 2 (Repair Strategies): 🔄 IN PROGRESS
- [ ] Database rebuild complete
- [ ] GigaChat rebuild complete
- [ ] WebSearch rebuild complete
- [ ] All 7 steps implemented for each

### Phase 3 (Integration): ⏳ PENDING (Iteration 71)
- [ ] Integrated into Night Orchestrator
- [ ] Parallel monitoring working
- [ ] Statistics in morning report

### Phase 4 (Testing): ⏳ PENDING
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Production test successful
- [ ] No degradation observed

---

## 📝 Implementation Notes

### Key Principles (From 00_CONCEPT.md)

1. **PROACTIVE DEVELOPER MODE** - не просто параметры, а ПЕРЕСБОРКА модуля
2. **STOP → CHECK ALL → REBUILD → TEST → START** - полный цикл
3. **Fallback LAST RESORT** - только если пересборка невозможна
4. **NO DEGRADATION** - сохранять бизнес-логику всегда!

### Example: GigaChat Quota Exceeded

**❌ Wrong approach:**
```python
gigachat.model = "GigaChat-Plus"  # Just change parameter
```

**✅ Right approach:**
```python
1. gigachat.stop()  # Остановить
2. diagnostics = check_all_keys_and_models()  # Проверить ВСЁ
3. working_config = find_working_combination()  # Найти рабочее
4. gigachat.rebuild(working_config)  # ПЕРЕСОБРАТЬ
5. gigachat.test_all_functions()  # Протестировать
6. gigachat.start()  # Запустить
7. validate()  # Проверить
```

---

**Status:** Phase 1 Complete, Phase 2 In Progress
**Next:** Complete database rebuild, then GigaChat and WebSearch
**After:** Iteration 71 - Integration with Night Orchestrator
