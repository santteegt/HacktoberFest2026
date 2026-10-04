---
name: devrelay-mlh-submissions
description: Create or update an MLH project, submit it to an MLH event the user is registered for, and enter it into the event's challenges through the DevRelay MCP gateway (search_mlh_events, register_for_mlh_event, list_my_projects, create_project, update_project, submit_project_to_event, enter_challenge, withdraw_challenge_entry, reactivate_challenge_entry). Use when the user wants to submit a hackathon project, enter a prize category or sponsor challenge, fix a project after MLH rejected it, or when a build is finished and the event's submission window is still open.
---

# DevRelay MLH Submissions

Project submission is a chain of MLH writes, each acting as the MLH account
connected to DevRelay, and MLH enforces the order and the rules. Your job is to
call the steps in order, pass MLH's answers through faithfully, and never claim a
result MLH did not return.

## The chain

1. `list_my_mlh_events` — find the event and confirm the participation is
   `registered` or `checked_in`. When the user has no such participation for the
   event, find the event with `search_mlh_events` (or take the id, slug, or
   mlh.com URL they give), confirm it with them, and call
   `register_for_mlh_event`; then continue.
2. `get_mlh_event` with the event id — the challenges (prize categories), each with
   an `id`, name, prize description, and a `description` that is the sponsor's own
   statement of what they want built and judged. Read those descriptions; the names
   ("Best Use of Vultr") say nothing about the criteria, and a track claimed against
   the name alone is a track the judges will score against the text. Note which are
   `active`.
3. **Check the event takes submissions through MLH at all, before creating
   anything.** An event whose `submission_url` points at Devpost or another
   third-party platform does not: MLH will refuse step 5, and a project created in
   step 4 will exist attached to no event. When you see that, say so, give the user
   that URL, and stop here. Do not create the MLH project to "have it ready".
4. `list_my_projects` — reuse an existing project if the user has one for this
   work. Otherwise `create_project` with the repository `source_url` and
   `built_with`, plus name, description, and demo URLs when known. Always send
   `built_with`: many events reject a submission with no technologies ("Select at
   least one technology."). When the stack is unknown, infer it from the
   repository (manifests, imports) or ask the user. When reusing a project whose
   `built_with` is empty, fill it with `update_project` before submitting.
5. `submit_project_to_event` with the project id and event id, in the same turn as
   `create_project` — nothing goes between them. One project per participant per
   event, while the event's submission window is open.
6. `enter_challenge` with the project id, event id, and each chosen challenge id.
   The event submission must exist first; MLH refuses otherwise.

`update_project` changes only the fields passed. Use it to fix a project after a
422 or when the user adds a demo link. Never clear `built_with` on a submitted
project: the technology requirement applies to edits too. MLH refuses edits once a
submitted event's window has closed, or once one of the project's entries has been
approved or won.

`withdraw_challenge_entry` and `reactivate_challenge_entry` act on an entry id from
`enter_challenge`, while the window is open. Approved or winning entries are locked.

## Reading MLH's answers

- **`already_existed: true`** on a submission or entry means it was already there
  and nothing changed. Say so; do not report a new submission.
- **A 422 is a requirements failure**, and the message names what failed (a
  required demo URL, an empty `built_with`, an empty project, a program rule). Fix
  the project with `update_project`, then retry the same call.
- **A refusal ("MLH denied", "MLH refused") is final for this turn.** The user is
  not registered, the window is closed, the project is not theirs, or another
  project is already submitted. Relay the reason. Do not retry and do not try a
  different id to get around it.
- **A refusal on `submit_project_to_event` leaves the project attached to nothing.**
  The project is real and it is the user's; it is just not part of any event. Say
  that plainly rather than reporting only the refusal, and do not create a second
  project. Offer the two ways out: submit this same project to a different event, or
  leave it and follow the event's own submission link.
- **A rate-limit message names the wait.** Respect it; never loop on writes.
- **"Not connected to MLH" or "DevRelay needs new MLH permissions"** means tell the
  user a browser window is about to open for MLH sign-in and that they must finish
  it there, then call `connect_mlh_account`, then retry the step.

## Before you write

Submissions and entries are visible to organizers and judges. Confirm the event
with the user before calling `register_for_mlh_event`, the project and event before
`submit_project_to_event`, and the project, event, and challenges before
`enter_challenge`, and show MLH's response after. Never send fields MLH owns (`submitter`,
`submitted_at`, `status`); the tools do not expose them.

The rules judges apply (all work during the event, public repo kept public,
secrets out of the repo, AI use disclosed, stop at the deadline) are in the
`mlh-policies` and `mlh-hackers` knowledge guides (see [[devrelay-knowledge]]).
Check the project against them before submitting, and tell the user about any
gap rather than submitting over it.

## Before the user asks

The user installed DevRelay so the submission happens while the window is open. When
`list_my_mlh_events` shows a `registered` or `checked_in` participation whose event is
current and the work in this session is plausibly the project, raise it once: name the
event, the submission deadline, and offer to run the chain. Do not wait for "submit my
project".

## After submitting

Offer, once, to draft the write-up as a DEV post with `create_article` (see
[[devrelay-publishing]]): a draft, `published: false`, with the default `some_ai`
disclosure. Hand over the `edit_url` the tool returns, not `url` — a draft's `url`
carries a `-temp-slug-<id>` suffix that reads as broken. The user publishes from DEV. Do not claim a post was
published unless `create_article` or `update_article` returned it with `published:
true`.
