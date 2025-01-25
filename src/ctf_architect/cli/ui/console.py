from rich.console import Console
from rich.style import Style
from rich.theme import Theme

THEME_STYLES = {
    "ctfa.info": Style(color="cyan"),
    "ctfa.success": Style(color="green"),
    "ctfa.warning": Style(color="yellow"),
    "ctfa.error": Style(color="red"),
    "ctfa.title": Style(color="bright_cyan"),
    "ctfa.lint.passed": Style(color="green", reverse=False),
    "ctfa.lint.skipped": Style(color="yellow", dim=True, reverse=False),
    "ctfa.lint.ignored": Style(color="white", dim=True, reverse=False),
    "ctfa.lint.failed": Style(color="red", reverse=False),
    "ctfa.lint.error": Style(color="red", reverse=True),
    "ctfa.lint.level.info": Style(color="cyan"),
    "ctfa.lint.level.warning": Style(color="yellow"),
    "ctfa.lint.level.error": Style(color="red"),
    "ctfa.lint.level.fatal": Style(color="red", reverse=True),
    "ctfa.prompt.message": Style(color="blue"),
    "ctfa.prompt.default": Style(color="bright_black"),
    "ctfa.prompt.options": Style(color="cyan"),
    "ctfa.prompt.pointer": Style(color="bright_cyan"),
    "ctfa.prompt.selected": Style(color="bright_cyan"),
    "ctfa.prompt.unselected": Style(color="cyan"),
    "ctfa.prompt.toggled_on": Style(color="bright_green"),
    "ctfa.prompt.toggled_off": Style(color="bright_red"),
    "ctfa.prompt.input": Style(color="cyan"),
    "ctfa.prompt.error": Style(color="red"),
}


THEME = Theme(styles=THEME_STYLES)

console = Console(highlight=False, theme=THEME)
