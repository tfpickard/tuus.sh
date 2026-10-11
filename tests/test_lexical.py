from tuus.lexical import known_violations


def test_supplied_and_input_markers_allowed_but_other_known_markers_rejected(make_entry):
    entries = [make_entry("rockstar"), make_entry("cyberspace")]
    records = [{"id": "rockstar", "surface": "rockstar", "variants": []}]
    assert not known_violations("Thanks, rockstar.", "Thank a colleague", records, entries)
    assert known_violations("Thanks from cyberspace, rockstar.", "Thank a colleague", records, entries) == ["cyberspace"]
    assert not known_violations("Thanks from cyberspace, rockstar.", "Thank someone in cyberspace", records, entries)


def test_polysemous_connectives_are_distinct_from_dated_fragments(make_entry):
    reaction = make_entry("tumblr_cant_even")
    reaction.surface = "I can't even"
    reaction.variants = ["I can't", "I can’t", "I just can't"]
    refusal = make_entry("as_if_formula")
    refusal.surface = "as if"
    opening = make_entry("cb_break")
    opening.surface = "break"
    entries = [reaction, refusal, opening]
    for output in ("I can't attend Monday's event.", "I can’t even attend Monday’s event.",
                   "It seems as if the room changed.", "We will take a break."):
        assert not known_violations(output, "Decline an invitation.", [], entries)
    for output in ("I can't even.", "I can’t…", "I can't even with this.", "As if!", "Break: may I speak?"):
        assert known_violations(output, "Decline an invitation.", [], entries)
