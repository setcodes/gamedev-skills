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

The same Agent Skills files support Codex and Claude. `agents/openai.yaml` supplies optional Codex UI metadata; Claude reads `SKILL.md` and the supporting files. No external plugin dependency or MCP server is required. Running gameplay checks requires the project's engine and relevant tools.

## Install in Claude Code

Run these commands in your terminal:

```sh
claude plugin marketplace add setcodes/gamedev-skills
claude plugin install gamedev-skills@setcode-gamedev-skills
```

Start a new Claude Code session and invoke `/gamedev-skills:game-designer` or `/gamedev-skills:godot-gamedev`. The plugin includes every skill in this repository's `skills/` directory.

For an individual skill without the plugin, copy its complete folder from `skills/` into `~/.claude/skills/` for personal use, or `.claude/skills/` inside your game project for that project. Invoke it with `/game-designer` or `/godot-gamedev`. Back up existing folders before replacing them.

See the official [Claude Code skills guide](https://code.claude.com/docs/en/skills) and [marketplace guide](https://code.claude.com/docs/en/plugin-marketplaces).

## Install in Claude (claude.ai)

Build one ZIP per skill from this checkout with Python 3.9 or newer:

```sh
python3 scripts/package_skills.py
```

In Claude, open **Customize → Skills → + → Create skill → Upload a skill**, upload `dist/game-designer.zip` or `dist/godot-gamedev.zip`, and enable it. Upload the skills separately, using these archives rather than GitHub's ZIP of the whole repository. See [Claude's upload instructions](https://support.claude.com/en/articles/12512180-use-skills-in-claude) for account capabilities and current UI.

The website runs in Claude's environment, so it can review supplied project files and plan checks but cannot directly run the Godot installation on your computer. Use Claude Code in the local game project for local runtime verification. Uploading and running the skills in claude.ai has not been tested in an authenticated account.

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

Add the skill to the table above. The Claude Code plugin discovers the shared `skills/` directory, and `scripts/package_skills.py` builds each skill separately for upload. Before proposing a change, check its metadata and relative links, try representative requests, and state any verification limits. Feedback and contributions are welcome through GitHub issues and pull requests.

## На русском

Набор скиллов для геймдизайна и разработки игр от **Егора Максимова · [Setcode](https://setcode.ru)**. Коллекция открыта для других движков и инструментов; сейчас доступны два независимых навыка:

- **game-designer** — концепты, Vision, GDD, механики, прогрессия, экономика, уровни, плейтесты и обратная связь ученикам. Не привязан к движку.
- **godot-gamedev** — реализация, отладка и ревью игровых систем в Godot с учётом версии движка и проверкой поведения.

### Claude Code

Выполни в терминале:

```sh
claude plugin marketplace add setcodes/gamedev-skills
claude plugin install gamedev-skills@setcode-gamedev-skills
```

Начни новую сессию Claude Code. Команды: `/gamedev-skills:game-designer` и `/gamedev-skills:godot-gamedev`. Чтобы установить один скилл вручную, скопируй его папку из `skills/` в `~/.claude/skills/` или в `.claude/skills/` проекта; тогда команды будут `/game-designer` и `/godot-gamedev`.

### Claude в браузере

В скачанном репозитории выполни `python3 scripts/package_skills.py` (Python 3.9+). Через **Customize → Skills → + → Create skill → Upload a skill** загрузи нужный ZIP из `dist/` и включи скилл. Для каждого скилла нужен отдельный архив. Проверка загрузки в авторизованном аккаунте claude.ai не выполнялась.

### Codex

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

Инструкции написаны по-английски, ответы должны быть на языке пользователя. Дополнительные плагины и MCP-серверы не требуются. Для проверки игры нужны соответствующие движок, проект и инструменты; без них выводы ограничиваются доступной проверкой. Веб-версия Claude не запускает движок на твоём компьютере; для этого используй Claude Code в локальном проекте.

Можно использовать, изменять и распространять набор по лицензии [MIT](LICENSE), сохраняя уведомление об авторстве и текст лицензии.
