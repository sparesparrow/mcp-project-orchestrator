# Questions to ask the user (AskUserQuestion)

Ask these in plan mode, after read-only triage and research, before writing the plan. Max 4 questions per call; put the recommended option first and add "(Recommended)". The tool adds an "Other" free-text choice itself, so do not add one. Skip a question when triage already answers it or the user's request does. If there is no interactive user (headless run, subagent), do not guess: write each question with **all of its options verbatim from this file** (recommended one marked) and stop at the approval gate. Do not merge options into a new one (test finding: a run recommended "local disk and Google" instead of listing the four backup options); if a combination makes sense, say so as a note and ask it as a multiSelect. A question never replaces a per-command confirmation.

## 1. Select backup method (header: "Backup")
Required before any unlock/wipe. Question: "Select backup method before the bootloader unlock wipes the phone."
| Option | What you do |
|---|---|
| Back up now to local disk | Ask for a destination dir; `adb pull` /sdcard (DCIM, Download, Documents, Pictures), list `pm list packages -3`, `adb shell dumpsys backup` notes; record path + sizes + sha256 list. No unlock until the copy is verified. |
| Use backup from Google account | Old phone: Settings > Google > Backup > "Back up now"; user confirms the last-backup time and which account; plan Phase 5b restore in the setup wizard. Not covered: authenticators, WhatsApp chats, banking logins. |
| Backup already exists at ... | Ask for the path/account. Verify it exists and is non-empty (local) or that the user confirms the date (cloud). |
| No backup (device is new/empty) | Confirm the user understands that all data is erased and unrecoverable; continue only with explicit confirmation. |

Several can apply (local + Google): ask as multiSelect when the user may want both.

## 2. Select firmware source (header: "Firmware")
Options come from `references/firmware-sources.md` after browsing, filtered by `host.os` (recommended first). Include "I already have the firmware at ...". Never download before this is answered.

## 3. Select root method (header: "Method")
Magisk patched boot/init_boot (default) · KernelSU/APatch (only if the kernel supports it) · No root, just adb/Shizuku for what you need · Custom ROM (separate task). Offer only what research supports for this device.

## 4. Restore after the wipe (header: "Restore")
Restore apps/settings from Google account (name the account, which old phone) · Set up as new · I'll restore manually. If "Google account", confirm the old phone's backup question above was answered.

## 5. Unlock eligibility / carrier (header: "Carrier")
Only when `ro.carrier`/channel suggests a branded unit: "Bought unlocked/retail" · "Carrier-branded/financed" · "Not sure" (then stop and check the OEM portal eligibility first).

## 6. Portal / account steps (header: "Browser")
Ask before any website step (unlock portal, Motorola ID, Lenovo sign-in). Check what is connected first (ToolSearch for playwright/chrome/browser).
| Option | What happens |
|---|---|
| Drive a browser tool, I type secrets (Recommended if one is connected) | Claude navigates and fills non-secret fields in a headed browser; you type passwords, solve CAPTCHA/2FA, accept the legal notice. |
| Same, and read the verification email from Gmail | As above, plus read-only Gmail search for the one vendor email (code or reset link); nothing is sent, replied to or deleted. |
| Install Playwright MCP first | You run the `claude mcp add playwright ...` line from `browser-steps.md` and restart; then as the first option. |
| I'll do the website steps myself | Claude gives exact click paths and the string to submit; you paste back only non-secret results. |

## Not questions (always per-command gates)
`adb reboot bootloader`, `fastboot oem unlock`, every `fastboot flash`: show the exact command and consequence and wait for a yes in that moment.
