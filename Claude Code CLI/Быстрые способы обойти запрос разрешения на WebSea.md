<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Быстрые способы обойти запрос разрешения на WebSearch в Claude Code CLI

**Главный вывод:** достаточно воспользоваться встроенными флагами и настройками Claude Code, добавив инструмент WebSearch в список разрешённых или запуская с пропуском всех запросов на разрешение.

## 1. Флаг `--dangerously-skip-permissions`

Запуск Claude Code с этим флагом сразу отключает все запросы на подтверждение действий:

```
claude --dangerously-skip-permissions
```

После этого Claude Code не будет спрашивать разрешения на использование WebSearch или других инструментов.[^1]

## 2. Флаг `--allowedTools`

При запуске можно явно разрешить только нужные инструменты, включая WebSearch:

```
claude --allowedTools "WebSearch" "Read" "Write" …
```

Так вы дадите Claude Code право искать в вебе без дополнительных запросов.

## 3. Редактирование `settings.json`

В файле конфигурации (`~/.claude/settings.json` или `.claude/settings.local.json`) добавьте в блок `permissions.allow` инструмент WebSearch:

```json
{
  "permissions": {
    "allow": [
      "Bash",
      "Read",
      "Write",
      "WebFetch",
      "WebSearch"
      // …другие необходимые инструменты
    ]
  }
}
```

После сохранения Claude Code перестанет запрашивать разрешение на WebSearch.[^2]

***

Используя любой из этих методов, вы сможете полноценно использовать WebSearch в CLI-режиме без дополнительных обходных путей или сторонних решений.
<span style="display:none">[^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^20][^3][^4][^5][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://www.reddit.com/r/ClaudeAI/comments/1l45dcr/how_to_stop_claude_code_from_asking_for/

[^2]: https://www.youtube.com/watch?v=hd9iw72vrJA

[^3]: https://docs.claude.com/en/docs/claude-code/settings

[^4]: https://www.anthropic.com/engineering/claude-code-best-practices

[^5]: https://github.com/anthropics/claude-code/issues/600

[^6]: https://www.codeant.ai/blogs/claude-code-cli-vs-codex-cli-vs-gemini-cli-best-ai-cli-tool-for-developers-in-2025

[^7]: https://shipyard.build/blog/claude-code-cheat-sheet/

[^8]: https://github.com/anthropics/claude-code/issues/2560

[^9]: https://thediscourse.co/p/claude-code

[^10]: https://aiengineerguide.com/blog/claude-code-prompt/

[^11]: https://intuitionlabs.ai/articles/mcp-servers-claude-code-internet-search

[^12]: https://www.reddit.com/r/ClaudeAI/comments/1kouc2z/claude_code_how_to_grant_it_permission_to_search/

[^13]: https://github.com/anthropics/claude-code

[^14]: https://stevekinney.com/courses/ai-development/claude-code-permissions

[^15]: https://github.com/anthropics/claude-code/issues/2647

[^16]: https://docs.claude.com/en/docs/claude-code/overview

[^17]: https://docs.claude.com/en/docs/claude-code/cli-reference

[^18]: https://www.siddharthbharath.com/claude-code-the-complete-guide/

[^19]: https://anthropic.com/news/enabling-claude-code-to-work-more-autonomously

[^20]: https://www.claude.com/product/claude-code

