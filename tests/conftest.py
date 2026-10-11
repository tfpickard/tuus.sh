import pytest

from tuus.schema import Entry, Example, Kairolexicon, Signature, Source, Window


@pytest.fixture
def make_entry():
    def make(identifier="marker", group="small", onset=2009, peak=2012, fade=2015):
        return Entry(id=identifier, surface=identifier.replace("_", " "), variants=[],
                     kairolexica=[group], signature=Signature(onset=onset, peak=peak, fade=fade,
                                                             fade_status="estimated", confidence="medium"),
                     gloss="A curated expression of encouragement.", functions=["praising", "requesting"],
                     examples=[Example(text="Please proceed with this expression.", kind="constructed")],
                     rationale="Temporal parameters are estimated for a bounded test moment.",
                     source_ids=["source"], review_status="accepted")
    return make


@pytest.fixture
def make_group():
    def make(identifier, entries):
        return Kairolexicon(id=identifier, name=identifier, window=Window(start=1970, end=2030),
                           description="A bounded cultural vocabulary for statistical verification.",
                           cause_of_death=None,
                           sources=[Source(id="source", title="Test evidence", url="https://example.org/evidence",
                                           published="2012", accessed="2026-10-11", note="Synthetic statistical fixture, not corpus evidence.")],
                           entries=entries)
    return make
