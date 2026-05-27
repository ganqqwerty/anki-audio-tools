from __future__ import annotations

from types import SimpleNamespace


class FakeNote:
    def __init__(self, note_id: int) -> None:
        self.id = note_id
        self.fields = {"Audio": "[sound:clip.mp3]", "Image": ""}

    def note_type(self) -> dict:
        return {"name": "Basic"}

    def items(self) -> list[tuple[str, str]]:
        return list(self.fields.items())

    def __setitem__(self, key: str, value: str) -> None:
        self.fields[key] = value


class FakeCol:
    def __init__(self) -> None:
        self.notes = {1: FakeNote(1), 2: FakeNote(2)}
        self.updated: list[int] = []
        self.merged: list[int] = []
        self.media = SimpleNamespace(write_data=lambda name, data: name)

    def get_note(self, note_id: int) -> FakeNote:
        return self.notes[note_id]

    def add_custom_undo_entry(self, _name: str) -> int:
        return 42

    def update_note(self, note: FakeNote) -> object:
        self.updated.append(int(note.id))
        return object()

    def merge_undo_entries(self, entry: int) -> object:
        self.merged.append(entry)
        return object()
