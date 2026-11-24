# KWENCH / Ask Now

The slides are down and Field Notes starts at 2:00 p.m. This terminal desk card gives Morgan a person to ask, where to find them, and the handoff that supports the recommendation.

## Opening notes

Run from the repository root with Python 3.10 or newer. There are no packages to install.

```sh
python3 desk.py
```

At the fictional desk time of 1:55 p.m., ask **Sam in Novelty**. Priya confirms Sam handles screen setup (04). Casey says Sam has finished setup and can help immediately (07). Kai knows the screens and is still with a member in Connection (06).

## Take a new handoff

Copy [`data/note-template.json`](data/note-template.json) to a new file. Enter the note ID, fictional shift time (`HH:MM` in 24-hour time), title, and note text. In `facts`, add one object per person with a shift update. Set `person` and the fields the note confirms. Use `location` for a current location (or `null` if unknown), `availability` for `"free"`, `"busy"`, or `"unknown"`, and `skills` for `["screen"]` when the note explicitly establishes screen skills.

```sh
python3 desk.py --add data/new-note.json --at 13:55
```

Use the fictional time of Morgan’s second question for `--at`. Run the opening command again to replay the starting state. Add `--json` to get the recommendation and the note ID for each fact as structured output.

The card keeps the latest explicit fact for each person’s skills, location, and availability. An assignment supplies context. A handoff supplies evidence of where someone is and whether they can leave. If several qualified people are available, the person already in the workshop room comes first. If nobody qualifies, the card prompts Morgan to get a fresh handoff.

## Test

```sh
python3 -m unittest discover -s tests -v
```
