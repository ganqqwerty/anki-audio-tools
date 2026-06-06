# Persistent Undo/Redo Design

## Purpose

Audio edits should remain undoable after the editor session ends, Anki restarts, or the user returns to a note later. The current session undo stack is useful for immediate interactions, but it is not durable and cannot protect media files that become unreferenced after an edit.

The design introduces a persistent SQLite operation journal plus an add-on-owned media archive. SQLite records what changed. The archive preserves the audio payloads needed to undo or redo even after Anki media cleanup removes unreferenced files.

## User Guarantee

For every successfully committed audio operation, the user can return later and undo the last action for that note field, provided the add-on history retention policy has not expired the required archive entry.

If undo cannot be completed because the note field changed externally or the archived media has been removed, the add-on reports that clearly instead of silently changing the wrong content.

## Storage Model

Use a separate add-on-owned SQLite database for persistent history. Do not store audio bytes in SQLite.

SQLite operation records store:

- collection identity,
- note id,
- field index,
- operation type,
- old field HTML,
- new field HTML,
- old audio filename,
- new audio filename,
- old and new `AudioEditState` JSON where available,
- old and new media hashes and sizes,
- archive keys or relative archive paths,
- user-facing status summary,
- creation timestamp,
- undo/redo state.

The media archive stores copies of audio files outside Anki's collection media folder. This keeps the archive out of Anki's unused-media cleanup path.

## Commit Timing

Archive immediately as part of the successful operation commit.

Recommended order:

1. Render the new audio into a temporary output path.
2. Read and archive the currently referenced audio before replacing the field.
3. Archive the newly rendered audio from the temp output.
4. Write the new audio into Anki media through Anki's media manager.
5. Replace the sound reference in the note field.
6. Append the committed operation row to SQLite.
7. Refresh undo/redo availability in the editor UI.

The old audio must not become unreferenced in Anki media before the add-on has archived it. That avoids the cleanup race where a file becomes eligible for deletion before persistent undo can restore it.

If archiving fails, the operation should fail before replacing the field. This keeps the persistent undo guarantee simple: a successful audio edit has a durable undo record and the media needed to execute it.

## Undo Flow

Undo resolves the latest undoable operation for the current collection, note id, and field index.

Before changing the note, the add-on validates that the operation still applies:

- Prefer an exact match against the current field HTML and the operation's `new_field_html`.
- If the full field HTML changed, allow a narrower match when the current field still contains the operation's `new_audio_filename`.
- If neither match succeeds, refuse undo because the field changed after the audio edit.

Then the add-on restores the previous audio reference:

1. Check whether `old_audio_filename` already exists in Anki media with the expected hash.
2. If it is missing, restore it from the archive through Anki's media manager.
3. Replace the current sound reference with `old_audio_filename`, or restore `old_field_html` when exact field matching is valid.
4. Mark the operation undone in SQLite.
5. Update the in-memory session state and toolbar availability.
6. Reload the editor field and refresh playback/graph state.

Redo performs the same checks in reverse, restoring `new_audio_filename` from Anki media or the archive as needed.

## Cleanup Mitigation

Anki media cleanup can delete files that are no longer referenced by cards. Persistent undo cannot depend on those files staying in collection media.

Mitigation:

- archive the pre-edit file before it becomes unreferenced,
- archive every produced file before or while it is written into Anki media,
- store hashes and sizes to detect stale or replaced media files,
- rehydrate missing files from the archive before undo/redo,
- compute undo availability from both SQLite state and archive/media availability.

The add-on should not create hidden notes or dummy references to keep media alive. That would pollute the user's collection and make cleanup behavior surprising.

## Retention Policy

The archive needs bounded growth.

Initial policy:

- keep history for a configurable number of days,
- cap archive size with oldest-entry pruning,
- keep SQLite rows for pruned operations but mark them expired,
- never advertise undo/redo for expired operations,
- provide a settings action to clear persistent audio undo history.

The retention policy should expire operation records only when both directions that depend on an archived file can no longer be honored.

## User-Facing Settings

Provide two archive retention settings:

- `Archive size`: maximum total size for archived undo/redo media.
- `Remove older than`: maximum age for archived undo/redo entries.

Both settings affect archive pruning, not immediate undo behavior. A newly committed operation should remain undoable even if the archive is near the configured size limit; pruning runs after the commit and expires the oldest eligible records first.

When either setting causes an entry to be pruned, keep the SQLite operation row for diagnostics but mark it expired. Expired entries should not enable undo/redo buttons.

## Release Phases

Each phase should be independently releasable and should deliver visible user value. The first release intentionally starts without a media archive so users get persistent undo sooner, with clear cleanup limitations.

### Phase 1: SQLite-Only Persistent Undo

User value: users can return to a note later and undo the last standard editor audio edit as long as the previous media file still exists in Anki media.

Scope:

- Add the SQLite operation journal.
- Record standard editor render operations that replace a note field audio reference.
- Persist old/new field HTML, old/new filenames, edit state JSON, media hash/size, status summary, and timestamp.
- Compute undo availability from SQLite on editor load when session history is empty.
- Undo from SQLite when the in-memory undo stack is empty.
- Refuse undo safely when the old media file is missing, hash validation fails, or the field changed after the edit.

Release tests:

- Perform a standard editor edit, clear the editor session, reopen the note, and undo successfully.
- Perform a standard editor edit, remove the old media file, reopen the note, and verify undo is unavailable or refuses without changing the note.
- Manually edit the field after a recorded operation and verify undo refuses without changing the note.

Out of scope for this phase:

- Media archive and rehydration.
- Persistent redo.
- Special transforms and region delete.
- Retention settings.

### Phase 2: Persistent Undo For All Editor Audio Operations

User value: every editor operation that replaces audio gets the same best-effort persistent undo behavior.

Scope:

- Extend persistent operation recording to denoise, reduce size, voice-only, pitch hum, region delete, and delete rest.
- Keep the Phase 1 cleanup limitation: undo requires the old media file to still exist in Anki media.
- Standardize enough commit-path behavior that all operation types record old/new references consistently.

Release tests:

- Each editor operation type records a persistent undo row.
- Each editor operation type can be undone after clearing the editor session when the old media file still exists.
- Missing old media disables or refuses undo without changing the note.

### Phase 3: Media Archive And Rehydration

User value: persistent undo survives Anki media cleanup.

Scope:

- Add an add-on-owned media archive outside the Anki media folder.
- Archive the old referenced audio before replacing the field.
- Archive produced audio from the temp output for future redo support.
- Rehydrate missing old media from the archive during undo.
- Validate restored media with recorded hash and size.

Release tests:

- Perform an edit, delete the now-unreferenced old media from Anki media, reopen the note, and undo successfully via archive rehydration.
- Archive write failure prevents the note field from being replaced.
- Missing or corrupted archive payload refuses undo without changing the note.

### Phase 4: Persistent Redo

User value: users can redo a previously undone audio edit after returning later.

Scope:

- Mark persistent operations undone/redone in SQLite.
- Compute redo availability from SQLite and media/archive availability.
- Redo from SQLite when session redo history is empty.
- Rehydrate missing new media from the archive when needed.
- Invalidate redo when a new operation is committed for the same note field.

Release tests:

- Edit, clear session, undo, clear session again, and redo successfully.
- Delete the new media after undo and verify redo rehydrates it from the archive.
- Commit a new edit after undo and verify redo is no longer available.

### Phase 5: User-Controlled Retention

User value: users can control disk usage created by persistent undo/redo.

Scope:

- Add the `Archive size` setting.
- Add the `Remove older than` setting.
- Add a settings action to clear persistent audio undo history.
- Prune archive payloads and mark corresponding SQLite rows expired.
- Hide expired entries from undo/redo availability.

Release tests:

- Lowering `Archive size` expires the oldest eligible archive entries.
- Lowering `Remove older than` expires old entries.
- Expired entries do not enable undo or redo.
- Clearing persistent audio undo history removes archive payloads and disables undo/redo availability.

### Phase 6: Conflict Safety And Diagnostics

User value: failures are understandable and undo avoids corrupting manually edited notes.

Scope:

- Strengthen field-change detection and user-facing refusal messages.
- Report specific reasons for unavailable undo/redo, including changed field, missing media, archive hash mismatch, and restore failure.
- Add diagnostics for archive size, active rows, expired rows, and missing archive payloads.

Release tests:

- Manual field edits after an audio operation produce a clear refusal and leave the field unchanged.
- Missing media, missing archive, and hash mismatch produce distinct status messages.
- Diagnostics report archive and history health accurately.

### Phase 7: Batch Operation Decision

User value: batch behavior is either explicitly supported or explicitly documented as editor-only.

Scope:

- Decide whether persistent undo applies to browser batch operations.
- If supported, implement batch undo as a separate batch-job history model rather than mixing many-note operations into the editor note-field stack.
- If excluded, document the editor-only boundary in user-facing help and internal docs.

Release tests:

- If supported, a batch job can be undone safely at job granularity with conflict detection per note.
- If excluded, batch operations do not create misleading editor undo availability.

## Integration Points

The existing mutation boundary is the right place to add persistent history. Standard render, special transforms, and region delete already converge on this sequence:

- write generated media,
- replace the sound reference in the note field,
- update `EditorSession`,
- sync undo/redo availability.

Persistent history should be inserted into those commit paths, while the existing in-memory undo/redo stack remains a fast mirror for the active editor session.

Editor injection should compute initial undo/redo availability from persistent history when no session history is available. This lets the toolbar reflect undo capability when the user opens a note later.

## Failure Behavior

Expected refusals:

- no matching undoable operation exists,
- current field no longer matches the recorded operation,
- archive entry is missing or hash validation fails,
- Anki media write fails while rehydrating a file.

These should produce user-facing status messages and leave the note unchanged.

## Testing

Unit tests should cover:

- SQLite migration and operation append,
- latest undoable/redoable lookup,
- redo invalidation after a new operation,
- media archive write and hash validation,
- rehydrating a missing media file from the archive,
- expired history entries being hidden from availability.

Editor integration tests should cover:

- undo after the in-memory `EditorSession` is gone,
- redo after a persistent undo,
- refusing undo after external field edits,
- toolbar availability on editor reload from persistent history,
- operation commit failure when archiving fails.

End-to-end tests should cover:

- perform an edit,
- simulate editor/session restart,
- remove the now-unreferenced old media from Anki media,
- undo successfully via archive rehydration,
- redo successfully after undo.

## Out Of Scope

- Storing audio bytes directly in SQLite.
- Replacing Anki's own undo system.
- Persisting every transient slider or preview state before an operation is committed.
- Creating hidden notes or dummy card references to prevent Anki media cleanup.
- Offering unlimited history without a retention cap.
