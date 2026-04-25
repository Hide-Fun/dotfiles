# Confirmation Prompts

Use these templates when Word review metadata or citation fields are at risk.

## Principles
- Ask only when the change crosses a real safety boundary.
- State the exact risk, not a generic warning.
- State the default action. For this skill, the default is usually to stop rather than silently downgrade to a plain edit.
- Keep the prompt short enough that the user can answer with a direct yes or no.

## Citation field edits

### Touching Zotero or other field-coded citations
`This change would require editing a Zotero or other citation field. Default is to leave citation fields untouched. Do you want me to edit the citation field as well?`

### Leaving the citation field untouched and using placeholders
`This sentence appears to need a citation, but adding it safely would require touching a citation field. Default is to leave the field untouched and use a placeholder such as (ref) or XXXX et al. Do you want me to proceed that way?`

## Revision-history risk

### Crossing a field boundary or complex review markup
`This edit crosses an existing citation field or complex review markup boundary, so tracked changes may stop being visible in Word even if the file still opens. Default is to stop here. Do you want me to continue anyway?`

### Model name unavailable for the author label
`This edit would add tracked changes, but this session does not expose a concrete model name for the required author label format Codex (model name). Default is to stop here. Do you want to provide the model label to use?`

### Falling back to an unverified path
`I can make this edit, but I cannot verify in Word that tracked changes remain visible afterward. Default is to stop and leave the file unchanged. Do you want me to proceed with that limitation?`

### Review markup appears to have disappeared
`The file opens, but the tracked changes are no longer visibly reviewable in Word. I am treating this as a failure and keeping the original unchanged. Do you want me to attempt a lower-level OOXML repair, or should I stop here?`

## Word-side verification

### Ask the user to verify All Markup
`Please open the revised DOCX in Word and confirm that Review -> All Markup shows the expected tracked changes. I am not treating this edit as complete until that is confirmed.`

### Ask the user to verify comments and revision pane
`Please check the revised DOCX in Word with All Markup and the Reviewing Pane enabled, and confirm that both tracked changes and comments are still visible.`

## Scope guardrails

### Refusing a plain edit downgrade
`This request cannot currently be completed while keeping tracked changes visibly reviewable in Word. The skill's default is to stop rather than silently switch to a plain edit. Do you want to keep that restriction, or do you want a separate non-tracked edit workflow instead?`

### Confirming markdown snapshot only
`I can generate the Markdown diff sidecar without touching the source DOCX. Do you want only the snapshot and git-diff artifact, with no Word edit yet?`
