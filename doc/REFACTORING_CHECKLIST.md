# ✅ Admin Panel Refactoring Checklist

**Project:** GrantService Admin Panel Refactoring
**Version:** 1.0.0
**Start Date:** TBD
**Target Completion:** 3 weeks from start

---

## 📋 Phase 1: Foundation (Week 1)

**Goal:** Eliminate code duplication and create shared utilities
**Effort:** 40 hours (1 week)
**Risk:** 🟢 Low

### Day 1-2: Shared Components Module

- [ ] **Task 1.1:** Create `web-admin/utils/agent_components.py`
  - [ ] Set up file structure and imports
  - [ ] Define module docstring
  - [ ] Add type hints

- [ ] **Task 1.2:** Implement `render_agent_header(agent_info: Dict)`
  - [ ] Title with emoji
  - [ ] Description
  - [ ] Status badge
  - [ ] Test with sample data

- [ ] **Task 1.3:** Implement `render_prompt_management(agent_type: str)`
  - [ ] Copy from `✍️_Writer_Agent.py` (line 68-183)
  - [ ] Extract to shared function
  - [ ] Add error handling
  - [ ] Test with all 5 agent types

- [ ] **Task 1.4:** Implement `render_agent_stats(agent_type: str, stats: Dict)`
  - [ ] Extract common stats display logic
  - [ ] Create metric cards
  - [ ] Add charts
  - [ ] Test with real data

- [ ] **Task 1.5:** Implement `render_agent_testing(agent_type: str)`
  - [ ] Test prompt interface
  - [ ] Manual execution controls
  - [ ] Result display
  - [ ] Test with sample agent

- [ ] **Task 1.6:** Add unit tests
  - [ ] Create `tests/test_agent_components.py`
  - [ ] Test each function
  - [ ] Test error cases
  - [ ] Achieve >80% coverage

**Deliverables:**
- ✅ New file: `utils/agent_components.py` (~200 lines)
- ✅ Unit tests: `tests/test_agent_components.py`
- ✅ Documentation in docstrings

---

### Day 3: Database Centralization

- [ ] **Task 2.1:** Update `web-admin/utils/database.py`
  - [ ] Move `get_db_connection()` from pages
  - [ ] Add `@st.cache_resource` decorator
  - [ ] Add error handling
  - [ ] Add docstring

- [ ] **Task 2.2:** Create `DatabaseManager` class
  - [ ] Singleton pattern
  - [ ] Connection pooling
  - [ ] Health check method
  - [ ] Test connectivity

- [ ] **Task 2.3:** Update pages to use centralized connection
  - [ ] Update `🎯_Pipeline_Dashboard.py`
    - [ ] Import from utils.database
    - [ ] Remove local get_db_connection
    - [ ] Test all queries
  - [ ] Update `📋_Управление_грантами.py`
    - [ ] Import from utils.database
    - [ ] Remove local get_db_connection
    - [ ] Test all queries
  - [ ] Update `🤖_AI_Agents.py`
    - [ ] Import from utils.database
    - [ ] Remove local get_db_connection
    - [ ] Test all queries

- [ ] **Task 2.4:** Integration testing
  - [ ] Test all pages load correctly
  - [ ] Test database queries work
  - [ ] Test error handling
  - [ ] Monitor for connection leaks

**Deliverables:**
- ✅ Updated: `utils/database.py`
- ✅ Updated: 3 pages
- ✅ Removed: 3 duplicate functions

---

### Day 4: Authentication Decorator

- [ ] **Task 3.1:** Create `@require_auth` decorator
  - [ ] Open `web-admin/utils/auth.py`
  - [ ] Implement decorator function
  - [ ] Add error handling
  - [ ] Test with sample function

- [ ] **Task 3.2:** Update ALL pages to use decorator (17 pages)

  **Main Pages:**
  - [ ] `🏠_Главная.py`
  - [ ] `🎯_Pipeline_Dashboard.py`

  **User Management:**
  - [ ] `👥_Пользователи.py`
  - [ ] `📋_Анкеты_пользователей.py`
  - [ ] `📄_Просмотр_заявки.py`
  - [ ] `❓_Вопросы_интервью.py`

  **AI Agents:**
  - [ ] `🤖_AI_Agents.py`
  - [ ] `✍️_Writer_Agent.py`
  - [ ] `🔍_Researcher_Agent.py`
  - [ ] `🔬_Исследования_исследователя.py`
  - [ ] `🔬_Аналитика_исследователя.py`

  **Grants:**
  - [ ] `📄_Грантовые_заявки.py`
  - [ ] `📋_Управление_грантами.py`

  **Analytics:**
  - [ ] `📊_Общая_аналитика.py`
  - [ ] `📋_Мониторинг_логов.py`

  **Auth:**
  - [ ] `🔐_Вход.py` (skip, this is login page)

- [ ] **Task 3.3:** Test authentication flow
  - [ ] Test with valid token
  - [ ] Test with invalid token
  - [ ] Test with expired token
  - [ ] Test redirect to login

**Deliverables:**
- ✅ Updated: `utils/auth.py` with decorator
- ✅ Updated: 16 pages (all except login)
- ✅ Removed: ~170 lines of duplicate auth code

---

### Day 5: Testing & Cleanup

- [ ] **Task 4.1:** Run full test suite
  - [ ] Unit tests pass
  - [ ] Integration tests pass
  - [ ] Manual testing of all pages
  - [ ] Fix any failures

- [ ] **Task 4.2:** Code cleanup
  - [ ] Remove unused imports
  - [ ] Remove commented code
  - [ ] Fix linting errors
  - [ ] Format code

- [ ] **Task 4.3:** Update documentation
  - [ ] Add docstrings to new functions
  - [ ] Update ARCHITECTURE.md
  - [ ] Update CHANGELOG.md
  - [ ] Create migration notes

- [ ] **Task 4.4:** Create PR and review
  - [ ] Create feature branch
  - [ ] Commit changes with clear messages
  - [ ] Push to remote
  - [ ] Create pull request
  - [ ] Code review
  - [ ] Address feedback

**Deliverables:**
- ✅ All tests passing
- ✅ Clean code (no linting errors)
- ✅ Updated documentation
- ✅ PR ready for merge

---

## 🎯 Phase 1 Completion Criteria

**Code:**
- ✅ New file: `utils/agent_components.py` created
- ✅ Updated: `utils/database.py` centralized
- ✅ Updated: `utils/auth.py` with decorator
- ✅ Updated: 16 pages use new utilities
- ✅ Removed: ~500 lines of duplicate code

**Tests:**
- ✅ Unit tests: >80% coverage for new components
- ✅ Integration tests: All pages load and function
- ✅ Manual tests: No regression in functionality

**Documentation:**
- ✅ All new functions have docstrings
- ✅ ARCHITECTURE.md updated
- ✅ CHANGELOG.md updated
- ✅ Migration notes created

**Quality:**
- ✅ No linting errors
- ✅ Code formatted consistently
- ✅ No duplicate code patterns
- ✅ PR approved and merged

---

## 📋 Phase 2: Restructuring (Week 2-3)

**Goal:** Consolidate pages into unified architecture
**Effort:** 80 hours (2 weeks)
**Risk:** 🟡 Medium

### Week 2: Agent Consolidation

#### Day 1-2: Create Unified AI Agents Page

- [ ] **Task 5.1:** Create tabbed structure
  - [ ] Open `🤖_AI_Agents.py`
  - [ ] Create 5 main tabs (Interviewer, Auditor, Planner, Researcher, Writer)
  - [ ] Set up tab content areas
  - [ ] Test tab switching

- [ ] **Task 5.2:** Implement Interviewer tab
  - [ ] Stats section
  - [ ] Prompt management (use shared component)
  - [ ] Testing interface
  - [ ] Verify functionality

- [ ] **Task 5.3:** Implement Auditor tab
  - [ ] Stats section
  - [ ] Prompt management (use shared component)
  - [ ] Scoring criteria display
  - [ ] Testing interface
  - [ ] Verify functionality

- [ ] **Task 5.4:** Implement Planner tab
  - [ ] Stats section
  - [ ] Prompt management (use shared component)
  - [ ] Template management
  - [ ] Testing interface
  - [ ] Verify functionality

**Deliverables:**
- ✅ Updated: `🤖_AI_Agents.py` with 3 agent tabs working
- ✅ All tabs use shared components

---

#### Day 3: Migrate Writer Agent

- [ ] **Task 6.1:** Create Writer tab in `🤖_AI_Agents.py`
  - [ ] Copy content from `✍️_Writer_Agent.py`
  - [ ] Adapt to tabbed structure
  - [ ] Use shared components
  - [ ] Remove duplicate code

- [ ] **Task 6.2:** Add Writer-specific features
  - [ ] Generated texts viewer
  - [ ] Quality metrics
  - [ ] Writing samples
  - [ ] Test generation

- [ ] **Task 6.3:** Test Writer tab
  - [ ] Test prompt management
  - [ ] Test text generation
  - [ ] Test all features
  - [ ] Compare with old page

- [ ] **Task 6.4:** Archive old Writer page
  - [ ] Move `✍️_Writer_Agent.py` → `pages/archived/`
  - [ ] Update navigation
  - [ ] Add deprecation notice (if keeping temporarily)
  - [ ] Verify redirect works

**Deliverables:**
- ✅ Writer tab functional in unified page
- ✅ Old page archived
- ✅ All features migrated

---

#### Day 4: Migrate Researcher Agent

- [ ] **Task 7.1:** Create Researcher tab in `🤖_AI_Agents.py`
  - [ ] Copy content from `🔍_Researcher_Agent.py`
  - [ ] Adapt to tabbed structure
  - [ ] Use shared components
  - [ ] Remove duplicate code

- [ ] **Task 7.2:** Create Researcher sub-tabs
  - [ ] Sub-tab: ⚙️ Настройки (Settings)
  - [ ] Sub-tab: 🔬 Исследования (Research)
  - [ ] Sub-tab: 📊 Аналитика (Analytics)

- [ ] **Task 7.3:** Migrate Settings sub-tab
  - [ ] Prompt management
  - [ ] API configuration
  - [ ] Test execution

- [ ] **Task 7.4:** Test Researcher tab structure
  - [ ] Test sub-tab switching
  - [ ] Test prompt management
  - [ ] Compare with old pages

**Deliverables:**
- ✅ Researcher tab with sub-tabs created
- ✅ Settings sub-tab functional

---

#### Day 5: Integrate Researcher Sub-pages

- [ ] **Task 8.1:** Migrate Research data (Исследования)
  - [ ] Copy from `🔬_Исследования_исследователя.py`
  - [ ] Adapt to sub-tab format
  - [ ] Update filters and display
  - [ ] Test data loading

- [ ] **Task 8.2:** Migrate Analytics (Аналитика)
  - [ ] Copy from `🔬_Аналитика_исследователя.py`
  - [ ] Adapt to sub-tab format
  - [ ] Update charts and metrics
  - [ ] Test cost tracking

- [ ] **Task 8.3:** Test full Researcher integration
  - [ ] Test all 3 sub-tabs
  - [ ] Test data flow between tabs
  - [ ] Test performance
  - [ ] Compare with old pages

- [ ] **Task 8.4:** Archive old Researcher pages
  - [ ] Move `🔍_Researcher_Agent.py` → `archived/`
  - [ ] Move `🔬_Исследования_исследователя.py` → `archived/`
  - [ ] Move `🔬_Аналитика_исследователя.py` → `archived/`
  - [ ] Update navigation
  - [ ] Add deprecation notices

**Deliverables:**
- ✅ Researcher fully integrated (3 sub-tabs)
- ✅ 3 old pages archived
- ✅ All features working

---

### Week 3: Grant & Application Consolidation

#### Day 1-2: Merge Grant Pages

- [ ] **Task 9.1:** Plan grant page merge
  - [ ] Analyze features in both pages
  - [ ] Design tab structure
  - [ ] Plan data migration
  - [ ] Create mockup

- [ ] **Task 9.2:** Update `📋_Управление_грантами.py`
  - [ ] Create 4 tabs structure
  - [ ] Tab 1: Все заявки (from Грантовые_заявки)
  - [ ] Tab 2: Готовые гранты (existing)
  - [ ] Tab 3: Отправка (existing)
  - [ ] Tab 4: Архив (existing)

- [ ] **Task 9.3:** Migrate "Все заявки" tab
  - [ ] Copy grant listing from `📄_Грантовые_заявки.py`
  - [ ] Integrate filters
  - [ ] Integrate search
  - [ ] Test functionality

- [ ] **Task 9.4:** Test unified grant page
  - [ ] Test all 4 tabs
  - [ ] Test tab switching
  - [ ] Test all features
  - [ ] Compare with old pages

- [ ] **Task 9.5:** Archive old grant page
  - [ ] Move `📄_Грантовые_заявки.py` → `archived/`
  - [ ] Update navigation links
  - [ ] Add redirect if needed
  - [ ] Verify all links work

**Deliverables:**
- ✅ Unified grant management page (4 tabs)
- ✅ Old page archived
- ✅ All features migrated

---

#### Day 3: Merge Questionnaire/Application Pages

- [ ] **Task 10.1:** Plan application pages merge
  - [ ] Analyze current separation
  - [ ] Design integrated workflow
  - [ ] Plan tab structure

- [ ] **Task 10.2:** Create `📋_Анкеты_и_заявки.py`
  - [ ] Rename `📋_Анкеты_пользователей.py`
  - [ ] Create 3 tabs
  - [ ] Tab 1: Список анкет (existing)
  - [ ] Tab 2: Просмотр заявки (from Просмотр_заявки)
  - [ ] Tab 3: Поиск (new)

- [ ] **Task 10.3:** Integrate application viewer
  - [ ] Copy from `📄_Просмотр_заявки.py`
  - [ ] Adapt to tab format
  - [ ] Add selection from Tab 1
  - [ ] Test navigation flow

- [ ] **Task 10.4:** Create search tab
  - [ ] Advanced filters
  - [ ] Search by criteria
  - [ ] Quick access links
  - [ ] Test search

- [ ] **Task 10.5:** Archive old application viewer
  - [ ] Move `📄_Просмотр_заявки.py` → `archived/`
  - [ ] Update links
  - [ ] Test navigation

**Deliverables:**
- ✅ Unified questionnaire/application page (3 tabs)
- ✅ Old page archived
- ✅ Improved workflow

---

#### Day 4: Update Navigation & Links

- [ ] **Task 11.1:** Update all internal links
  - [ ] Find all references to archived pages
  - [ ] Update to new unified pages
  - [ ] Update breadcrumbs
  - [ ] Test all navigation

- [ ] **Task 11.2:** Update sidebar navigation
  - [ ] Verify page order (emoji sorting)
  - [ ] Check page titles
  - [ ] Test sidebar collapse/expand
  - [ ] Verify icons display correctly

- [ ] **Task 11.3:** Update documentation
  - [ ] Update ARCHITECTURE.md (page structure)
  - [ ] Update CLAUDE.md (quick start)
  - [ ] Create user migration guide
  - [ ] Update screenshots if any

**Deliverables:**
- ✅ All links updated
- ✅ Navigation working
- ✅ Documentation current

---

#### Day 5: User Acceptance Testing

- [ ] **Task 12.1:** Prepare UAT plan
  - [ ] Define test scenarios
  - [ ] Select test users (2-3 power users)
  - [ ] Prepare test data
  - [ ] Create feedback form

- [ ] **Task 12.2:** Conduct UAT sessions
  - [ ] Session 1: Agent management tasks
  - [ ] Session 2: Grant management tasks
  - [ ] Session 3: Application workflow
  - [ ] Collect feedback

- [ ] **Task 12.3:** Address feedback
  - [ ] Fix critical issues
  - [ ] Log enhancement requests
  - [ ] Update UI based on feedback
  - [ ] Retest with users

- [ ] **Task 12.4:** Prepare for deployment
  - [ ] Create deployment checklist
  - [ ] Prepare rollback plan
  - [ ] Create release notes
  - [ ] Schedule deployment

**Deliverables:**
- ✅ UAT completed
- ✅ Feedback addressed
- ✅ Ready for deployment

---

## 🎯 Phase 2 Completion Criteria

**Structure:**
- ✅ 17 pages → 10 pages (41% reduction)
- ✅ All agent pages merged into 1 unified page
- ✅ Researcher 3 pages → 1 page with 3 sub-tabs
- ✅ Grant 2 pages → 1 page with 4 tabs
- ✅ Application 2 pages → 1 page with 3 tabs

**Migration:**
- ✅ 7 pages moved to `archived/`
- ✅ All features preserved
- ✅ No broken links
- ✅ Navigation updated

**Testing:**
- ✅ All pages load correctly
- ✅ All features functional
- ✅ UAT passed
- ✅ No regression

**Documentation:**
- ✅ User migration guide created
- ✅ ARCHITECTURE.md updated
- ✅ Release notes prepared
- ✅ Changelog updated

---

## 📋 Phase 3: Optimization (Week 4+)

**Goal:** Performance and advanced features
**Effort:** 80+ hours (4+ weeks)
**Risk:** 🟢 Low
**Priority:** Optional

### Component Library

- [ ] **Task 13.1:** Create component structure
  - [ ] Create `web-admin/components/` directory
  - [ ] Create `__init__.py`
  - [ ] Set up imports

- [ ] **Task 13.2:** Build core components
  - [ ] `cards.py` - Metric cards, info cards
  - [ ] `tables.py` - Data tables with filtering
  - [ ] `forms.py` - Form components
  - [ ] `charts.py` - Chart wrappers
  - [ ] `agent_widgets.py` - Agent-specific widgets

- [ ] **Task 13.3:** Document components
  - [ ] Create `COMPONENT_LIBRARY.md`
  - [ ] Add usage examples
  - [ ] Create Storybook-style demo
  - [ ] Add API reference

---

### Smart Caching

- [ ] **Task 14.1:** Create cache manager
  - [ ] Create `utils/cache_manager.py`
  - [ ] Implement CacheManager class
  - [ ] Add cache invalidation methods
  - [ ] Add cache statistics

- [ ] **Task 14.2:** Implement caching strategies
  - [ ] Cache agent stats (5 min TTL)
  - [ ] Cache pipeline overview (1 min TTL)
  - [ ] Cache user data (10 min TTL)
  - [ ] Cache grant lists (5 min TTL)

- [ ] **Task 14.3:** Add cache monitoring
  - [ ] Cache hit/miss metrics
  - [ ] Cache size monitoring
  - [ ] Performance comparison
  - [ ] Optimization recommendations

---

### API Layer

- [ ] **Task 15.1:** Design API structure
  - [ ] Create `utils/api/` directory
  - [ ] Define API contracts
  - [ ] Plan versioning strategy

- [ ] **Task 15.2:** Implement API modules
  - [ ] `agents.py` - AgentAPI class
  - [ ] `grants.py` - GrantAPI class
  - [ ] `users.py` - UserAPI class
  - [ ] `analytics.py` - AnalyticsAPI class

- [ ] **Task 15.3:** Migrate pages to use API
  - [ ] Update pages to use API layer
  - [ ] Remove direct DB access
  - [ ] Test all functionality
  - [ ] Measure performance impact

---

## 🎯 Phase 3 Completion Criteria

**Components:**
- ✅ Component library created
- ✅ All common UI patterns extracted
- ✅ Documentation complete
- ✅ Pages use components

**Caching:**
- ✅ Smart caching implemented
- ✅ Cache hit rate >70%
- ✅ Page load time <1.5s
- ✅ Monitoring in place

**API:**
- ✅ API layer created
- ✅ All pages use API
- ✅ No direct DB access in UI
- ✅ Performance maintained

---

## 📊 Overall Project Metrics

### Code Quality Targets

- [ ] Code duplication < 5% (baseline: 26%)
- [ ] Test coverage > 60% (baseline: ~10%)
- [ ] Linting score > 9/10
- [ ] No critical security issues

### Performance Targets

- [ ] Page load time < 1.5s (baseline: ~2.5s)
- [ ] Database queries per page < 5 (baseline: ~15)
- [ ] Cache hit rate > 70% (baseline: ~20%)
- [ ] Memory usage reduced by 30%

### User Experience Targets

- [ ] Time to find feature < 15s (baseline: ~45s)
- [ ] Task completion rate > 85% (baseline: 65%)
- [ ] User satisfaction > 8/10 (baseline: 6/10)
- [ ] Navigation clarity > 9/10 (baseline: 5/10)

### Developer Productivity Targets

- [ ] Time to add new agent < 2h (baseline: 8h)
- [ ] Bug fix propagation 100% (baseline: ~33%)
- [ ] Onboarding time < 2h (baseline: ~8h)
- [ ] Code review time < 30min (baseline: ~2h)

---

## 🚦 Risk Mitigation Checklist

### Before Starting

- [ ] Backup current codebase
- [ ] Tag current version in git
- [ ] Create feature branch
- [ ] Set up test environment
- [ ] Notify users of upcoming changes

### During Development

- [ ] Commit frequently with clear messages
- [ ] Run tests after each major change
- [ ] Keep rollback plan updated
- [ ] Monitor user feedback
- [ ] Document decisions

### Before Deployment

- [ ] Full test suite passes
- [ ] UAT approved
- [ ] Documentation updated
- [ ] Rollback plan tested
- [ ] Deployment window scheduled

### After Deployment

- [ ] Monitor error logs
- [ ] Track performance metrics
- [ ] Collect user feedback
- [ ] Fix critical issues immediately
- [ ] Plan next iteration

---

## ✅ Final Sign-off

### Phase 1: Foundation
- [ ] Code reviewed and approved
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Deployed to production
- [ ] No critical issues

### Phase 2: Restructuring
- [ ] Code reviewed and approved
- [ ] UAT passed
- [ ] Documentation updated
- [ ] Deployed to production
- [ ] User feedback positive

### Phase 3: Optimization
- [ ] Performance targets met
- [ ] Component library complete
- [ ] API layer functional
- [ ] Monitoring in place
- [ ] Project complete

---

**Project Status:** ⏳ Not Started
**Last Updated:** 2025-10-02
**Next Review:** After Phase 1 completion
