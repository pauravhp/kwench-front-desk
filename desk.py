#!/usr/bin/env python3
"""A small, evidence-backed shift sheet. Python 3.10+, standard library only."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QUESTION = "Who can help with the screen right now, where are they, and why?"
FIELDS = {"skills", "location", "availability"}


def minutes(value):
    hour, minute = map(int, value.split(":"))
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ValueError(f"Invalid 24-hour time: {value}")
    return hour * 60 + minute


def load_notes(path, additions=()):
    notes = json.loads(Path(path).read_text(encoding="utf-8"))
    for addition in additions:
        note = json.loads(Path(addition).read_text(encoding="utf-8"))
        notes.extend(note if isinstance(note, list) else [note])
    return order_notes(notes)


def order_notes(notes):
    ids = set()
    for note in notes:
        if not isinstance(note, dict) or type(note.get("id")) is not int or note["id"] < 1:
            raise ValueError("Every note needs a positive integer ID.")
        if note["id"] in ids:
            raise ValueError(f"Duplicate note ID: {note['id']}")
        ids.add(note["id"])
        minutes(note["at"])
        if any(not isinstance(note.get(key), str) or not note[key].strip() for key in ("title", "text")):
            raise ValueError("Every note needs a title and its original text.")
        for fact in note.get("facts", []):
            if not isinstance(fact, dict) or not isinstance(fact.get("person"), str) or not fact["person"].strip():
                raise ValueError("Every shift fact needs a person.")
            if "availability" in fact and fact["availability"] not in ("free", "busy", "unknown"):
                raise ValueError("Availability must be free, busy, or unknown.")
            if "skills" in fact and not isinstance(fact["skills"], list):
                raise ValueError("Skills must be a list.")
            if fact.get("location") is not None and not isinstance(fact["location"], str):
                raise ValueError("Location must be a room name or null.")
            if set(fact) - (FIELDS | {"person"}):
                raise ValueError("Use person, skills, location, and availability for shift facts.")
    return sorted(notes, key=lambda n: (minutes(n["at"]), n["id"]))


def recommend(notes, now="13:55"):
    """Use the latest explicit fact for each field at the desk time."""
    query_time = minutes(now)
    people = {}
    context = {}
    for note in notes:
        if minutes(note["at"]) > query_time:
            break
        context.update(note.get("context", {}))
        for fact in note.get("facts", []):
            state = people.setdefault(fact["person"], {})
            for field, value in fact.items():
                if field != "person":
                    state[field] = {"value": value, "note": note["id"], "at": note["at"]}
    eligible = []
    excluded = []
    for name, state in people.items():
        if "screen" not in state.get("skills", {}).get("value", []):
            continue
        availability = state.get("availability", {})
        location = state.get("location", {})
        if availability.get("value") != "free":
            reason = "busy" if availability.get("value") == "busy" else "availability unconfirmed"
            excluded.append({"person": name, "reason": reason, "evidence": availability})
        elif not location.get("value"):
            excluded.append({"person": name, "reason": "current location unconfirmed", "evidence": location})
        else:
            eligible.append({"person": name, "location": location["value"], "evidence": state})
    # If more than one is free, prefer somebody already in the workshop room.
    eligible.sort(key=lambda p: (p["location"] != context.get("room"), p["person"]))
    return {
        "as_of": now,
        "context": context,
        "question": QUESTION,
        "recommendation": eligible[0] if eligible else None,
        "other_available": eligible[1:],
        "excluded": excluded,
    }


def render(result, notes):
    by_id = {note["id"]: note for note in notes}
    context = result["context"]
    room = context.get("room")
    booking = " · ".join(context[key] for key in ("workshop", "room", "starts") if key in context)
    lines = ["KWENCH / ASK NOW", f"Desk time {result['as_of']}"]
    if booking:
        lines.append(booking)
    if context.get("problem"):
        lines.append(context["problem"])
    lines.append("")
    person = result["recommendation"]
    if person:
        lines += [f"WHO    {person['person']}", f"WHERE  {person['location']}", "WHY    Knows the screens and is explicitly available to help now."]
        if not room or person["location"] == room:
            lines += [f"DO     Ask {person['person']} in {person['location']} for screen help now."]
        else:
            lines += [f"DO     Find {person['person']} in {person['location']} and ask them to help in {room} now."]
        refs = sorted({evidence["note"] for evidence in person["evidence"].values()})
        lines += ["", "EVIDENCE"]
        for ref in refs:
            note = by_id[ref]
            lines += [f"  [{ref:02d}] {note['at']} · {note['title']}", f"       {note['text']}"]
    else:
        lines += ["No screen-capable colleague is confirmed free at a known location.", "Check for a fresh handoff before directing the member."]
    if result["excluded"]:
        lines += ["", "UNAVAILABLE OR UNCONFIRMED"]
        for excluded in result["excluded"]:
            evidence = excluded["evidence"]
            source = f" (note {evidence['note']:02d}, {evidence['at']})" if evidence else ""
            lines += [f"  {excluded['person']}: {excluded['reason']}{source}."]
    if result["other_available"]:
        lines += ["", "ALSO AVAILABLE"]
        lines += [f"  {p['person']} in {p['location']}." for p in result["other_available"]]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Tell Morgan who can help now, where, and why. Add a new handoff as a JSON file.")
    parser.add_argument("--notes", type=Path, default=ROOT / "data/starting.json", help="Starting notes JSON")
    parser.add_argument("--add", type=Path, action="append", default=[], help="Append a new note JSON; repeat for multiple handoffs")
    parser.add_argument("--at", default="13:55", help="Fictional desk time in HH:MM (default 13:55)")
    parser.add_argument("--json", action="store_true", help="Print structured recommendation and per-field evidence")
    args = parser.parse_args()
    try:
        notes = load_notes(args.notes, args.add)
        result = recommend(notes, args.at)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2) if args.json else render(result, notes))


if __name__ == "__main__":
    main()
