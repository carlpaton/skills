---
name: blobs
description: Find and read files in an Azure Storage account (blob containers) using only the Azure CLI, such as app debug traces, exports or logs. Works out the account, container and folder, then lists them and either pulls the files to local disk or reads them into context as a structure summary or capped excerpt. Read-only. Use when the user points at a storage account, container or folder and wants to see, download or analyse what is in it.
argument-hint: [tenant-id] [account] [container] [prefix] [pull | show]
---

# Read Azure blobs

Lists and fetches blobs from a storage account from the outside with `az`. It works the same in every tenant. Follow [../_shared/azure-debug.md](../_shared/azure-debug.md) for sign-in, safety and facts versus guesses. All steps use the helper [../_shared/blobs.py](../_shared/blobs.py), run as `python3 -I ../_shared/blobs.py` from this skill's folder or with the full path.

## Inputs

| Input | Notes |
|-------|-------|
| tenant | Optional. If the signed-in tenant is not the one wanted, the user runs `az login --tenant <id>`. |
| account | Storage account name. If unknown, find it (step 2). |
| container | Container name. If unknown, list them (step 2). |
| prefix | Folder inside the container, such as `ChatDebugTracing/`. Optional. |
| mode | `pull` to local disk, or `show` to read into context. If the user did not say, ask. |

## Steps

1. **Context.** Follow the shared doc: `az account show`, state the tenant and subscription and confirm they are right. Never log in or switch subscription unasked.
2. **Find the place.** Skip what the user already gave.
   - Account: `az storage account list --query "[].{name:name, rg:resourceGroup, loc:location}" -o table`. Several and no hint: ask.
   - Container: `az storage container list --account-name <account> --auth-mode login --query "[].name" -o tsv`.
   - Folder: run `list` with a short prefix and read the first path segments. Blob names are paths, so the layout is visible in the names, for example `<folder>/<id>/<yyyy>/<mm>/<dd>/<file>`.
3. **Pick the auth.** Start with `login`. If it fails with a permissions error the helper says so. Then ask the user to choose between granting `Storage Blob Data Reader` on the account, a SAS token they supply, or `--auth-mode key`. `key` makes `az` fetch the account key through management permissions: it is broader than the task needs, so only use it when the user agrees, and say which account it is, especially for production. Never print a key.
4. **List.**

   ```
   python3 -I blobs.py list --account <account> --container <container> --prefix <prefix> [--auth-mode key]
   ```

   Report the count, total size and date range, and group by the first folder levels. Name files by their blob path. The file extension may not match what the user expected, for example `.json` rather than `.jsonl`, so say what is actually there.
5. **Pull to disk** (mode `pull`).

   ```
   python3 -I blobs.py pull --account <account> --container <container> --prefix <prefix> --dest <dir> [--auth-mode key]
   ```

   - Put it in a new folder. If the user gave no destination, ask, or use the scratchpad and say so.
   - Check whether the destination is inside a git repo with `git check-ignore`. Blobs from production often hold personal data and prompts, so warn before they could be committed and offer a folder outside the repo or a `.gitignore` entry.
   - The helper never overwrites, so a re-run only adds new files. Report downloaded and skipped counts.
6. **Read into context** (mode `show`). Go from the least to the most revealing form:
   1. `--shape` prints keys, types and string lengths with no values, plus plain numbers. Use it first to learn the file structure and to find fields such as status, duration or error.
   2. Pull the files (step 5), then summarise across them with a short script, for example counts by status code or the slowest durations. This keeps bodies out of context.
   3. Print raw content only when the user asks for it, one blob at a time: `python3 -I blobs.py show ... --blob <name> [--max-bytes 20000]`. Output is capped.

   Never paste prompt, response, email or token values into the answer. Describe them ("a 4 KB user message") instead. Refer to people by role.
7. **Report.** Say which account, container and prefix were read, how many blobs, the auth mode used, where files were saved and what was not looked at. Answer the user's actual question from the data, and label guesses as guesses.

## Notes

- Everything is read-only. The helper only runs `az storage blob list` and `download`.
- Timestamps in blob metadata and names are UTC.
- Large containers: always use a prefix. A `list` over millions of blobs is slow.
- Add `--auth-mode key` to every helper call once chosen. The helper defaults to `login`.
