# Worktree chat room

owner: user

Status: **agreed, not built**.  
UI repo: `agents-holding-mac-app`. Company data stays on the company OS.  
Refines the chat part of `agents-holding-mac-app/docs/plans/company-os-mission-control-ui.md`.

## Goal

Chat with a company happens in that company's room. One worktree of that company is one room. The user always talks to `ceo` in that room. Other staff who may speak to the user get their own thread in the same room, under the CEO thread. They are not merged into one transcript.

## Room

| Rule | Choice |
| --- | --- |
| Where | Inside the open company. Not a holding-wide chat. |
| Open | On company detail, Open chat shows that company's worktree list. Choosing one opens a separate window for that room. The chat flow can live in its own UI package. |
| Worktree list | Each company has its own list. Company A can have worktrees a, b, c. Company B can have c, d. Those lists are separate. Opening company B does not show company A's worktrees. |
| Room | One worktree on that company's list = one room. Another worktree of the same company is another room. |
| Worktree | The room branch is checked out as the CEO worktree. Another staff gets a worktree only when that staff is activated in this conversation, and that worktree is linked to the CEO worktree. Switching rooms switches the conversation branch only. The files in the checkout are always the live project, not the code stored on that branch. |
| Main thread | Always `ceo`. |
| Side threads | Each staff who must talk to the user gets their own box, stacked under `ceo`. `ba` and `cto` can both be open. Do not merge them into the CEO transcript or into each other. |
| Same room | Side threads stay in this room. Do not open another room. |
| Who may speak | Only staff allowed to address the user. Example: a technical decision for the user goes to BA, not to every developer. |
| Round | One user question starts one round. |

Hop when a side thread appears: `ceo` assigns the team (business, BA, or the matching team). That team's lead assigns the staff. That staff then opens the side thread with the user. Staff who only do the work stay out of the chat and show up in **Working**.

## While the round is running

**Working** sits at the top of the room.

Open it to see each staff who is in this round:

- what they will do
- what they are doing
- what they already finished

## When the round is finished

The user's question stays in the CEO thread. After that question, when every staff in the round is done, show a horizontal list named **Recap**.

Each item is one staff who worked in that round. Tap a staff to open a dialog of what that staff did in this round. The dialog is not the full chat history.

Do not show Recap while anyone is still working.

## Names

| Surface | Name |
| --- | --- |
| Live staff in this round | **Working** |
| Finished staff row after the user question | **Recap** |

## UI shape before this is built

The mac app is split into `Screens/` and `Views/`. A screen sends an enum action with a payload. Its view model observes that stream and does the work. View models use `@Observable` (`@State`), not `@StateObject`. macOS minimum is 14. Chat, when built, follows the same screen, action, and view model split, and its UI can be its own package.

## Out of scope for this plan

- Holding staff names stay fixed. This plan does not rename them.
- Do not write the transcript into the staff markdown.
- Do not build the chat until this plan is picked up.
