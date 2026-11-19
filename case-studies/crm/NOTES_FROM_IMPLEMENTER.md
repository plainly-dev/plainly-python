# Notes from the implementer

- CONTRACT (edit form): "a missing `status` on edit is NOT specified". Decided: blank/missing status on edit keeps the contact's current status (on create it means `lead`). No test pins this.
- CONTRACT (email storage): stored trimmed but in the case typed; uniqueness is compared case-insensitively. Not pinned by a test which case is shown back.
- CONTRACT (ids): deleted ids are never reused (counter only goes up); spec says unspecified.
- CONTRACT (API 404): any unknown `/api/...` path answers JSON `{"error": "Contact not found"}`, even paths that are not contacts. The spec only defines it for contact ids; a more precise message for other API paths would be nicer but is untested.
- CONTRACT (refused note): the typed note text is shown again in the textarea. The textarea is the only named field, as required.
- No test was found contradictory or impossible; all 113 pass.
