# Setcode Gamedev Skills

Reusable AI agent skills for game design and development across engines and tools. By [Setcode](https://setcode.ru).

A growing collection of focused skills. The current set covers engine-neutral game design and Godot gameplay engineering; future skills can target other engines and production tools. Each skill is independent and includes its own instructions, references, and MIT license.

**Author:** Egor Maximov · [setcode.ru](https://setcode.ru)

**License:** [MIT](LICENSE) · **Current skill version:** 1.0.0

[Русская инструкция](#на-русском)

## Available skills

| Skill | Purpose |
| --- | --- |
| [game-designer](skills/game-designer/SKILL.md) | Concepts, Vision, GDD, mechanics, progression, economies, levels, encounters, playtest plans, and teaching feedback. Engine-neutral. |
| [godot-gamedev](skills/godot-gamedev/SKILL.md) | Gameplay implementation, debugging, and review in Godot, with project-version awareness, scene/resource handling, and meaningful verification. |

The instructions and UI metadata are prepared for Codex. Other agents may be able to read the Markdown instructions, but their discovery and installation formats can differ; compatibility with other agents has not been tested. No external plugin or MCP server is required. Running gameplay checks requires the project's engine and relevant tools.

## Install in Codex

Ask Codex:

```text
Use $skill-installer to install these skills from setcodes/gamedev-skills:
skills/game-designer and skills/godot-gamedev.
```

You can install either skill separately. Direct skill links:

- [game-designer](https://github.com/setcodes/gamedev-skills/tree/main/skills/game-designer)
- [godot-gamedev](https://github.com/setcodes/gamedev-skills/tree/main/skills/godot-gamedev)

For manual installation, download or clone this repository and copy the desired folder from `skills/` into your Codex skills directory: `$CODEX_HOME/skills`, or `~/.codex/skills` if `CODEX_HOME` is unset. Copy the entire skill folder, including `agents/`, `references/`, and `LICENSE`; do not copy the repository as an extra nesting level. Back up an existing folder before replacing it.

```text
~/.codex/skills/
  game-designer/
    SKILL.md
    LICENSE
    agents/openai.yaml
    references/
  godot-gamedev/
    SKILL.md
    LICENSE
    agents/openai.yaml
    references/
```

Installed skills are available on the next turn. Explicitly invoke a skill with `$game-designer` or `$godot-gamedev`, or let Codex select it for a relevant task.

## Example prompts

```text
Use $game-designer to review this concept. Are the player activities,
main hook, and prototype scope clear? Return findings without rewriting it.

Use $game-designer to design progression for the first three sessions.
State assumptions, map resource sources and sinks, and propose a playtest.

Use $game-designer to give concise feedback on this student's submission
against the supplied assignment and rubric. Do not rewrite the submission.

Use $godot-gamedev to fix repeated damage after a scene restart.
Preserve the existing architecture and verify the affected behavior.
```

Skills should answer in the user's language. Keep project-specific paths, approved decisions, the current milestone, and the source of truth in project instructions and documents. A skill does not supply evidence that a game is fun, balanced, or working without the relevant observation or test.

## Add a skill

Place it in `skills/<skill-name>/` with a clear `SKILL.md`, MIT license notice, and only the supporting resources it needs. Use a lowercase name with hyphens, describe when the skill applies, and keep project-specific data out of shared instructions. Add optional `agents/openai.yaml` metadata when useful for Codex.

An engine or tool skill should use that project's version and conventions. General design guidance belongs in an engine-neutral skill. Skills should work independently; document any actual dependency rather than assuming another skill is installed.

Add the skill to the table above. Before proposing a change, check its metadata and relative links, try representative requests, and state any verification limits. Feedback and contributions are welcome through GitHub issues and pull requests.

## На русском

Набор скиллов для геймдизайна и разработки игр от **Егора Максимова · [Setcode](https://setcode.ru)**. Коллекция открыта для других движков и инструментов; сейчас доступны два независимых навыка:

- **game-designer** — концепты, Vision, GDD, механики, прогрессия, экономика, уровни, плейтесты и обратная связь ученикам. Не привязан к движку.
- **godot-gamedev** — реализация, отладка и ревью игровых систем в Godot с учётом версии движка и проверкой поведения.

Для установки попроси Codex:

```text
Используй $skill-installer. Установи из репозитория setcodes/gamedev-skills
скиллы skills/game-designer и skills/godot-gamedev.
```

Можно установить только один навык. При ручной установке скопируй нужную папку из `skills/` целиком в `$CODEX_HOME/skills` или, если переменная не задана, в `~/.codex/skills`. Перед заменой существующего скилла сохрани его копию. Установленные скиллы доступны со следующего хода.

Примеры использования:

```text
Используй $game-designer. Проверь этот концепт: понятны ли действия
игрока, основной крючок и объём первого прототипа? Дай замечания,
сам документ пока не переписывай.

Используй $game-designer. Спроектируй прогрессию на первые три сессии.
Обозначь допущения, покажи источники и траты ресурсов и предложи плейтест.

Используй $godot-gamedev. Исправь повторное нанесение урона после
перезапуска сцены. Сохрани архитектуру проекта и проверь сценарий.
```

Инструкции написаны по-английски, ответы должны быть на языке пользователя. Плагины и MCP-серверы не требуются. Для проверки игры нужны соответствующие движок, проект и инструменты; без них выводы ограничиваются доступной проверкой. Поддержка других AI-агентов отдельно не тестировалась.

Можно использовать, изменять и распространять набор по лицензии [MIT](LICENSE), сохраняя уведомление об авторстве и текст лицензии.
