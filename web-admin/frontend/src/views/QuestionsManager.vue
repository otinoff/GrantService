<template>
  <div class="questions-manager">
    <!-- Заголовок и действия -->
    <div class="questions-header">
      <h1>📝 Управление вопросами интервью</h1>
      <div class="header-actions">
        <button class="btn btn-primary" @click="openAddModal">
          ➕ Добавить вопрос
        </button>
        <button class="btn btn-secondary" @click="importQuestions">
          📥 Импорт из файла
        </button>
        <button class="btn btn-info" @click="exportQuestions">
          📤 Экспорт в Excel
        </button>
      </div>
    </div>

    <!-- Статистика -->
    <div class="stats-panel" v-if="statistics">
      <div class="stat-card">
        <h4>Всего вопросов</h4>
        <span class="stat-number">{{ statistics.total_questions }}</span>
      </div>
      <div class="stat-card">
        <h4>Активных</h4>
        <span class="stat-number">{{ statistics.active_questions }}</span>
      </div>
      <div class="stat-card">
        <h4>Обязательных</h4>
        <span class="stat-number">{{ statistics.required_questions }}</span>
      </div>
      <div class="stat-card">
        <h4>Необязательных</h4>
        <span class="stat-number">{{ statistics.optional_questions }}</span>
      </div>
    </div>

    <!-- Фильтры и поиск -->
    <div class="filters-panel">
      <input 
        type="text" 
        v-model="filters.search" 
        placeholder="🔍 Поиск по тексту вопроса..." 
        class="search-input"
        @input="debounceSearch"
      >
      <select v-model="filters.question_type" class="filter-type" @change="loadQuestions">
        <option value="">Все типы</option>
        <option value="text">Текстовые</option>
        <option value="select">Выбор</option>
        <option value="number">Числовые</option>
        <option value="date">Даты</option>
        <option value="textarea">Многострочные</option>
      </select>
      <select v-model="filters.active_only" class="filter-status" @change="loadQuestions">
        <option :value="true">Только активные</option>
        <option :value="false">Все вопросы</option>
      </select>
    </div>

    <!-- Таблица вопросов -->
    <div class="table-container">
      <table class="questions-table">
        <thead>
          <tr>
            <th width="50">№</th>
            <th>Вопрос</th>
            <th width="100">Тип</th>
            <th width="100">Обязательный</th>
            <th width="100">Статус</th>
            <th width="150">Действия</th>
          </tr>
        </thead>
        <tbody id="question-list" ref="questionList">
          <tr 
            v-for="question in questions" 
            :key="question.id" 
            :data-id="question.id"
            class="question-row"
          >
            <td>{{ question.question_number }}</td>
            <td>
              <div class="question-text">{{ question.question_text }}</div>
              <div v-if="question.hint_text" class="hint-text">
                💡 {{ question.hint_text }}
              </div>
            </td>
            <td>
              <span :class="getTypeBadgeClass(question.question_type)">
                {{ getTypeLabel(question.question_type) }}
              </span>
            </td>
            <td>
              <span :class="question.is_required ? 'badge badge-success' : 'badge badge-secondary'">
                {{ question.is_required ? '✅' : '❌' }}
              </span>
            </td>
            <td>
              <span :class="question.is_active ? 'badge badge-active' : 'badge badge-inactive'">
                {{ question.is_active ? 'Активен' : 'Неактивен' }}
              </span>
            </td>
            <td>
              <button class="btn btn-sm btn-edit" @click="editQuestion(question)">
                ✏️
              </button>
              <button class="btn btn-sm btn-duplicate" @click="duplicateQuestion(question.id)">
                📋
              </button>
              <button class="btn btn-sm btn-delete" @click="deleteQuestion(question.id)">
                🗑️
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Пагинация -->
    <div class="pagination" v-if="totalPages > 1">
      <button 
        class="btn btn-sm" 
        :disabled="currentPage === 1"
        @click="changePage(currentPage - 1)"
      >
        ←
      </button>
      <span class="page-info">
        Страница {{ currentPage }} из {{ totalPages }}
      </span>
      <button 
        class="btn btn-sm" 
        :disabled="currentPage === totalPages"
        @click="changePage(currentPage + 1)"
      >
        →
      </button>
    </div>

    <!-- Модальное окно редактирования -->
    <div class="modal" v-if="showModal" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ editingQuestion ? '✏️ Редактирование вопроса' : '➕ Добавление вопроса' }}</h3>
          <button class="close-btn" @click="closeModal">×</button>
        </div>
        
        <div class="modal-body">
          <form @submit.prevent="saveQuestion">
            <div class="form-row">
              <div class="form-group">
                <label>Номер вопроса:</label>
                <input 
                  type="number" 
                  v-model="questionForm.question_number" 
                  min="1" 
                  required
                >
              </div>
              <div class="form-group">
                <label>Тип вопроса:</label>
                <select v-model="questionForm.question_type" @change="toggleOptionsField">
                  <option value="text">Текстовое поле</option>
                  <option value="select">Выбор из вариантов</option>
                  <option value="number">Число</option>
                  <option value="date">Дата</option>
                  <option value="textarea">Многострочный текст</option>
                </select>
              </div>
            </div>
            
            <div class="form-group">
              <label>Текст вопроса:</label>
              <textarea 
                v-model="questionForm.question_text" 
                rows="3" 
                required
                placeholder="Введите текст вопроса..."
              ></textarea>
            </div>
            
            <div class="form-group">
              <label>Название поля в БД:</label>
              <input 
                type="text" 
                v-model="questionForm.field_name" 
                placeholder="project_name" 
                required
              >
            </div>
            
            <div class="form-group" v-if="questionForm.question_type === 'select'">
              <label>Варианты ответов:</label>
              <div class="options-list">
                <div 
                  v-for="(option, index) in questionForm.options" 
                  :key="index"
                  class="option-item"
                >
                  <input 
                    type="text" 
                    v-model="questionForm.options[index]" 
                    :placeholder="`Вариант ${index + 1}`"
                  >
                  <button 
                    type="button" 
                    @click="removeOption(index)"
                    class="btn btn-sm btn-danger"
                  >
                    🗑️
                  </button>
                </div>
              </div>
              <button type="button" @click="addOption" class="btn btn-secondary">
                ➕ Добавить вариант
              </button>
            </div>
            
            <div class="form-group">
              <label>Подсказка/пример:</label>
              <textarea 
                v-model="questionForm.hint_text" 
                rows="2" 
                placeholder="Пример ответа..."
              ></textarea>
            </div>
            
            <div class="form-group">
              <label>Уточняющий вопрос:</label>
              <textarea 
                v-model="questionForm.follow_up_question" 
                rows="2" 
                placeholder="Дополнительный вопрос..."
              ></textarea>
            </div>
            
            <div class="form-group">
              <label>Правила валидации:</label>
              <div class="validation-rules">
                <label>
                  <input 
                    type="checkbox" 
                    v-model="validationRules.min_length_enabled"
                  > 
                  Минимальная длина:
                </label>
                <input 
                  type="number" 
                  v-model="validationRules.min_length" 
                  min="1" 
                  :disabled="!validationRules.min_length_enabled"
                  style="width:80px;"
                >
                
                <label>
                  <input 
                    type="checkbox" 
                    v-model="validationRules.max_length_enabled"
                  > 
                  Максимальная длина:
                </label>
                <input 
                  type="number" 
                  v-model="validationRules.max_length" 
                  min="1" 
                  :disabled="!validationRules.max_length_enabled"
                  style="width:80px;"
                >
                
                <label>
                  <input 
                    type="checkbox" 
                    v-model="questionForm.is_required"
                  > 
                  Обязательное поле
                </label>
              </div>
            </div>
            
            <div class="form-group">
              <label>
                <input 
                  type="checkbox" 
                  v-model="questionForm.is_active"
                > 
                Активный вопрос
              </label>
            </div>
          </form>
        </div>
        
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">Отмена</button>
          <button class="btn btn-primary" @click="saveQuestion">
            💾 Сохранить
          </button>
          <button class="btn btn-success" @click="saveAndTest">
            🧪 Сохранить и протестировать
          </button>
        </div>
      </div>
    </div>

    <!-- Модальное окно тестирования -->
    <div class="modal" v-if="showTestModal" @click="closeTestModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>🧪 Тестирование вопроса</h3>
          <button class="close-btn" @click="closeTestModal">×</button>
        </div>
        
        <div class="modal-body">
          <div class="test-question">
            <h4>Вопрос:</h4>
            <p>{{ testQuestion.question_text }}</p>
            <div v-if="testQuestion.hint_text" class="hint-text">
              💡 {{ testQuestion.hint_text }}
            </div>
          </div>
          
          <div class="test-answer">
            <label>Тестовый ответ:</label>
            <textarea 
              v-model="testAnswer" 
              rows="3" 
              placeholder="Введите тестовый ответ..."
            ></textarea>
          </div>
          
          <div v-if="testResult" class="test-result">
            <div :class="testResult.is_valid ? 'alert alert-success' : 'alert alert-danger'">
              {{ testResult.validation_result.message }}
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeTestModal">Закрыть</button>
          <button class="btn btn-primary" @click="runTest">
            🧪 Запустить тест
          </button>
        </div>
      </div>
    </div>

    <!-- Уведомления -->
    <div v-if="notification" :class="`notification ${notification.type}`">
      {{ notification.message }}
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import Sortable from 'sortablejs'

export default {
  name: 'QuestionsManager',
  setup() {
    // Состояние
    const questions = ref([])
    const statistics = ref(null)
    const showModal = ref(false)
    const showTestModal = ref(false)
    const editingQuestion = ref(null)
    const testQuestion = ref(null)
    const testAnswer = ref('')
    const testResult = ref(null)
    const currentPage = ref(1)
    const totalPages = ref(1)
    const questionList = ref(null)

    // Фильтры
    const filters = reactive({
      search: '',
      question_type: '',
      active_only: true
    })

    // Форма вопроса
    const questionForm = reactive({
      question_number: 1,
      question_text: '',
      field_name: '',
      question_type: 'text',
      options: [''],
      hint_text: '',
      is_required: true,
      follow_up_question: '',
      is_active: true
    })

    // Правила валидации
    const validationRules = reactive({
      min_length_enabled: false,
      min_length: 1,
      max_length_enabled: false,
      max_length: 100
    })

    // Уведомления
    const notification = ref(null)

    // Вычисляемые свойства
    const questionFormData = computed(() => {
      const data = { ...questionForm }
      
      // Обработка вариантов ответов
      if (data.question_type === 'select') {
        data.options = data.options.filter(opt => opt.trim())
      } else {
        data.options = null
      }
      
      // Правила валидации
      data.validation_rules = {}
      if (validationRules.min_length_enabled) {
        data.validation_rules.min_length = validationRules.min_length
      }
      if (validationRules.max_length_enabled) {
        data.validation_rules.max_length = validationRules.max_length
      }
      
      return data
    })

    // Методы
    const loadQuestions = async () => {
      try {
        const params = new URLSearchParams({
          skip: (currentPage.value - 1) * 20,
          limit: 20,
          active_only: filters.active_only,
          ...(filters.search && { search: filters.search }),
          ...(filters.question_type && { question_type: filters.question_type })
        })

        const response = await fetch(`/api/questions?${params}`)
        const data = await response.json()
        
        questions.value = data
        totalPages.value = Math.ceil(data.length / 20)
      } catch (error) {
        showNotification('Ошибка загрузки вопросов: ' + error.message, 'error')
      }
    }

    const loadStatistics = async () => {
      try {
        const response = await fetch('/api/questions/statistics/summary')
        statistics.value = await response.json()
      } catch (error) {
        console.error('Ошибка загрузки статистики:', error)
      }
    }

    const openAddModal = () => {
      editingQuestion.value = null
      resetForm()
      showModal.value = true
    }

    const editQuestion = (question) => {
      editingQuestion.value = question
      fillForm(question)
      showModal.value = true
    }

    const fillForm = (question) => {
      questionForm.question_number = question.question_number
      questionForm.question_text = question.question_text
      questionForm.field_name = question.field_name
      questionForm.question_type = question.question_type
      questionForm.options = question.options || ['']
      questionForm.hint_text = question.hint_text || ''
      questionForm.is_required = question.is_required
      questionForm.follow_up_question = question.follow_up_question || ''
      questionForm.is_active = question.is_active

      // Правила валидации
      const rules = question.validation_rules || {}
      validationRules.min_length_enabled = 'min_length' in rules
      validationRules.min_length = rules.min_length || 1
      validationRules.max_length_enabled = 'max_length' in rules
      validationRules.max_length = rules.max_length || 100
    }

    const resetForm = () => {
      questionForm.question_number = 1
      questionForm.question_text = ''
      questionForm.field_name = ''
      questionForm.question_type = 'text'
      questionForm.options = ['']
      questionForm.hint_text = ''
      questionForm.is_required = true
      questionForm.follow_up_question = ''
      questionForm.is_active = true

      validationRules.min_length_enabled = false
      validationRules.min_length = 1
      validationRules.max_length_enabled = false
      validationRules.max_length = 100
    }

    const saveQuestion = async () => {
      try {
        const url = editingQuestion.value 
          ? `/api/questions/${editingQuestion.value.id}` 
          : '/api/questions/'
        const method = editingQuestion.value ? 'PUT' : 'POST'

        const response = await fetch(url, {
          method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(questionFormData.value)
        })

        if (response.ok) {
          showNotification('Вопрос успешно сохранен!', 'success')
          closeModal()
          loadQuestions()
        } else {
          const error = await response.json()
          showNotification('Ошибка сохранения: ' + error.detail, 'error')
        }
      } catch (error) {
        showNotification('Ошибка сохранения: ' + error.message, 'error')
      }
    }

    const saveAndTest = async () => {
      await saveQuestion()
      if (editingQuestion.value) {
        testQuestion.value = editingQuestion.value
        showTestModal.value = true
      }
    }

    const deleteQuestion = async (questionId) => {
      if (!confirm('Вы уверены, что хотите удалить этот вопрос?')) return

      try {
        const response = await fetch(`/api/questions/${questionId}`, {
          method: 'DELETE'
        })

        if (response.ok) {
          showNotification('Вопрос успешно удален!', 'success')
          loadQuestions()
        } else {
          const error = await response.json()
          showNotification('Ошибка удаления: ' + error.detail, 'error')
        }
      } catch (error) {
        showNotification('Ошибка удаления: ' + error.message, 'error')
      }
    }

    const duplicateQuestion = async (questionId) => {
      try {
        const response = await fetch(`/api/questions/${questionId}/duplicate`, {
          method: 'POST'
        })

        if (response.ok) {
          showNotification('Вопрос успешно продублирован!', 'success')
          loadQuestions()
        } else {
          const error = await response.json()
          showNotification('Ошибка дублирования: ' + error.detail, 'error')
        }
      } catch (error) {
        showNotification('Ошибка дублирования: ' + error.message, 'error')
      }
    }

    const runTest = async () => {
      if (!testAnswer.value.trim()) {
        showNotification('Введите тестовый ответ', 'error')
        return
      }

      try {
        const response = await fetch(`/api/questions/${testQuestion.value.id}/test`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ test_answer: testAnswer.value })
        })

        testResult.value = await response.json()
      } catch (error) {
        showNotification('Ошибка тестирования: ' + error.message, 'error')
      }
    }

    const closeModal = () => {
      showModal.value = false
      editingQuestion.value = null
      resetForm()
    }

    const closeTestModal = () => {
      showTestModal.value = false
      testQuestion.value = null
      testAnswer.value = ''
      testResult.value = null
    }

    const toggleOptionsField = () => {
      if (questionForm.question_type === 'select' && questionForm.options.length === 0) {
        questionForm.options = ['']
      }
    }

    const addOption = () => {
      questionForm.options.push('')
    }

    const removeOption = (index) => {
      if (questionForm.options.length > 1) {
        questionForm.options.splice(index, 1)
      }
    }

    const changePage = (page) => {
      currentPage.value = page
      loadQuestions()
    }

    const debounceSearch = () => {
      clearTimeout(searchTimeout)
      searchTimeout = setTimeout(() => {
        currentPage.value = 1
        loadQuestions()
      }, 300)
    }

    const showNotification = (message, type = 'info') => {
      notification.value = { message, type }
      setTimeout(() => {
        notification.value = null
      }, 5000)
    }

    const getTypeLabel = (type) => {
      const labels = {
        text: 'text',
        select: 'select',
        number: 'number',
        date: 'date',
        textarea: 'textarea'
      }
      return labels[type] || type
    }

    const getTypeBadgeClass = (type) => {
      return `badge badge-${type}`
    }

    const exportQuestions = async () => {
      try {
        const response = await fetch('/api/questions/export/json')
        const data = await response.json()
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'interview_questions.json'
        a.click()
        URL.revokeObjectURL(url)
        
        showNotification('Вопросы экспортированы!', 'success')
      } catch (error) {
        showNotification('Ошибка экспорта: ' + error.message, 'error')
      }
    }

    const importQuestions = () => {
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = '.json'
      input.onchange = async (e) => {
        const file = e.target.files[0]
        if (!file) return

        try {
          const text = await file.text()
          const data = JSON.parse(text)
          
          const response = await fetch('/api/questions/import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data.questions || data)
          })

          const result = await response.json()
          showNotification(result.message, 'success')
          loadQuestions()
        } catch (error) {
          showNotification('Ошибка импорта: ' + error.message, 'error')
        }
      }
      input.click()
    }

    // Drag & Drop
    const initDragAndDrop = () => {
      if (questionList.value) {
        new Sortable(questionList.value, {
          animation: 150,
          handle: '.drag-handle',
          onEnd: async function(evt) {
            const newOrder = Array.from(questionList.value.children).map((item, index) => ({
              id: parseInt(item.dataset.id),
              new_number: index + 1
            }))
            
            try {
              const response = await fetch('/api/questions/reorder', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newOrder)
              })

              if (response.ok) {
                showNotification('Порядок вопросов обновлен!', 'success')
                loadQuestions()
              } else {
                const error = await response.json()
                showNotification('Ошибка обновления порядка: ' + error.detail, 'error')
              }
            } catch (error) {
              showNotification('Ошибка обновления порядка: ' + error.message, 'error')
            }
          }
        })
      }
    }

    // Жизненный цикл
    onMounted(() => {
      loadQuestions()
      loadStatistics()
      initDragAndDrop()
    })

    let searchTimeout = null

    return {
      // Состояние
      questions,
      statistics,
      showModal,
      showTestModal,
      editingQuestion,
      testQuestion,
      testAnswer,
      testResult,
      currentPage,
      totalPages,
      questionList,
      filters,
      questionForm,
      validationRules,
      notification,

      // Методы
      loadQuestions,
      openAddModal,
      editQuestion,
      saveQuestion,
      saveAndTest,
      deleteQuestion,
      duplicateQuestion,
      runTest,
      closeModal,
      closeTestModal,
      toggleOptionsField,
      addOption,
      removeOption,
      changePage,
      debounceSearch,
      getTypeLabel,
      getTypeBadgeClass,
      exportQuestions,
      importQuestions
    }
  }
}
</script>

<style scoped>
.questions-manager {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.questions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.stats-panel {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.stat-card {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  text-align: center;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  color: #007bff;
}

.filters-panel {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  align-items: center;
}

.search-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.filter-type,
.filter-status {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.table-container {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.questions-table {
  width: 100%;
  border-collapse: collapse;
}

.questions-table th,
.questions-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.questions-table th {
  background: #f8f9fa;
  font-weight: 600;
}

.question-text {
  font-weight: 500;
  margin-bottom: 5px;
}

.hint-text {
  font-size: 12px;
  color: #666;
  font-style: italic;
}

.badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.badge-text { background: #e3f2fd; color: #1976d2; }
.badge-select { background: #f3e5f5; color: #7b1fa2; }
.badge-number { background: #e8f5e8; color: #388e3c; }
.badge-date { background: #fff3e0; color: #f57c00; }
.badge-textarea { background: #fce4ec; color: #c2185b; }
.badge-success { background: #e8f5e8; color: #388e3c; }
.badge-secondary { background: #f5f5f5; color: #666; }
.badge-active { background: #e8f5e8; color: #388e3c; }
.badge-inactive { background: #ffebee; color: #d32f2f; }

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 12px;
}

.btn-primary { background: #007bff; color: white; }
.btn-secondary { background: #6c757d; color: white; }
.btn-info { background: #17a2b8; color: white; }
.btn-success { background: #28a745; color: white; }
.btn-danger { background: #dc3545; color: white; }

.btn:hover {
  opacity: 0.8;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  padding: 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  padding: 20px;
  border-top: 1px solid #eee;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.options-list {
  margin-bottom: 10px;
}

.option-item {
  display: flex;
  gap: 10px;
  margin-bottom: 5px;
  align-items: center;
}

.option-item input {
  flex: 1;
}

.validation-rules {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  align-items: center;
}

.validation-rules label {
  display: flex;
  align-items: center;
  gap: 5px;
  margin: 0;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  margin-top: 20px;
}

.page-info {
  font-weight: 500;
}

.notification {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 15px 20px;
  border-radius: 4px;
  color: white;
  z-index: 1001;
  max-width: 300px;
}

.notification.success { background: #28a745; }
.notification.error { background: #dc3545; }
.notification.info { background: #17a2b8; }

.test-question {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 4px;
}

.test-answer {
  margin-bottom: 20px;
}

.test-result {
  margin-top: 15px;
}

.alert {
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 15px;
}

.alert-success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.alert-danger {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}
</style> 