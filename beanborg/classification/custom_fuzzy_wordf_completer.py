"""Custom fuzzy completion module for prompt toolkit.

This module provides enhanced fuzzy word completion functionality,
extending the basic FuzzyWordCompleter with case-insensitive matching.
"""

from typing import Iterator, List

from prompt_toolkit.completion import Completion, FuzzyWordCompleter
from prompt_toolkit.document import Document


class CustomFuzzyWordCompleter(FuzzyWordCompleter):
    """Enhanced fuzzy word completer with case-insensitive matching.

    This completer extends the standard FuzzyWordCompleter to provide
    case-insensitive prefix matching for word completion suggestions.

    Attributes:
        words: List of words available for completion
    """

    def __init__(self, words: List[str]) -> None:
        """Initialize the completer with a list of words.

        Args:
            words: List of words to use for completion suggestions
        """
        super().__init__(words)

    def get_completions(
        self,
        document: Document,
        complete_event: bool
    ) -> Iterator[Completion]:
        """Get completion suggestions for the current input.

        Provides case-insensitive prefix matching for word completion,
        suggesting words that start with the current input prefix.

        Args:
            document: Current document containing input text
            complete_event: Whether this is a completion event

        Yields:
            Completion suggestions matching the current input

        Example:
            >>> completer = CustomFuzzyWordCompleter(['Apple', 'Application'])
            >>> document = Document('app')
            >>> list(completer.get_completions(document, True))
            [Completion('Apple'), Completion('Application')]
        """
        word_before_cursor = document.get_word_before_cursor(WORD=True)

        if not word_before_cursor:
            return

        lower_word = word_before_cursor.lower()

        for word in self.words:
            if word.lower().startswith(lower_word):
                yield Completion(
                    text=word,
                    start_position=-len(word_before_cursor),
                    display_meta=self._get_display_meta(word)
                )

    def _get_display_meta(self, word: str) -> str:
        """Get metadata to display with completion suggestion.

        Args:
            word: The completion word

        Returns:
            Metadata string for the completion
        """
        # Can be extended to provide more context about the completion
        return ""

