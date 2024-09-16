from prompt_toolkit.completion import Completion, FuzzyWordCompleter


class CustomFuzzyWordCompleter(FuzzyWordCompleter):
    def get_completions(self, document, complete_event):
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        for word in self.words:
            if word.lower().startswith(word_before_cursor.lower()):
                yield Completion(word, start_position=-len(word_before_cursor))
