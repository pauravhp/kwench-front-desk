# KWENCH / Ask Now

The slides are down and Field Notes starts at 2:00 p.m. This desk card gives Morgan a person to ask, where to find them, and the handoff that supports the recommendation.

## Open the desk card

Run `python3 serve.py` from the repository root and open [the local desk card](http://127.0.0.1:8731). The browser and terminal versions require Python 3.10 or newer and have no packages to install.

1. The opening card recommends **Sam in Novelty**. Note 07 confirms Sam has finished setup and can help with the screen right away.
2. Choose **Apply minute-40 note**, or choose **Load JSON note** and select [`data/minute-40.json`](data/minute-40.json). Both controls apply the same note through the same workflow. The card now recommends **Kai in Connection**. Note 09 confirms Kai has finished the welcome and can help now, while Sam is tied up past the workshop start. Note 04 establishes Kai’s screen skills.
3. Choose **Reset to opening** to return to the first eight notes. Open **All shift notes** to read the notes used in the current state.

The browser and terminal use the same decision logic. [GSAP](https://gsap.com/docs/v3/) animates the updated recommendation and respects the browser’s reduced motion setting.

[View the desk card after Priya’s handoff](evidence/desk-card.png).

## Replay both states in a terminal

```sh
python3 desk.py
python3 desk.py --add data/minute-40.json
```

Both commands answer Morgan’s question at the same fictional desk time of 1:55 p.m. The first reads the eight starting notes and returns Sam. The second includes Priya’s handoff and returns Kai. Each result includes the supporting notes and the action Morgan can take before 2:00 p.m.

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

The tests cover both rehearsal states, the winning note for each decision, and why a future note or a planned assignment cannot establish availability now. To check the browser, perform the three steps above and confirm the names, rooms, and evidence change as described.
