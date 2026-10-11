from tuus.lexical import known_violations


def test_supplied_and_input_markers_allowed_but_other_known_markers_rejected(make_entry):
    entries = [make_entry("rockstar"), make_entry("cyberspace")]
    records = [{"id": "rockstar", "surface": "rockstar", "variants": []}]
    assert not known_violations("Thanks, rockstar.", "Thank a colleague", records, entries)
    assert known_violations("Thanks from cyberspace, rockstar.", "Thank a colleague", records, entries) == ["cyberspace"]
    assert not known_violations("Thanks from cyberspace, rockstar.", "Thank someone in cyberspace", records, entries)
