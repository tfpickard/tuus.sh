import json
from pathlib import Path

import httpx
import pytest

from tuus.evaluation import validate_judgment
from tuus.generation import ModelUnavailable, SmallModel, detect_function
from tuus.lexical import address_recipient, contains, detail_violations, material_violations, protected_details, used_markers


def test_explicit_names_and_numeric_constraints_are_retained():
    assert protected_details("Ask Morgan to collect printouts before 15:00.") == ["Morgan", "15:00"]
    assert protected_details("Politely decline Monday's invitation.") == ["Monday"]
    assert detail_violations("Thank you for covering yesterday.", "Thank Sam for covering yesterday.", [])
    assert detail_violations("The workshop opens Thursday at 5 PM.", "Announce that the workshop opens Thursday.", [])
    assert not detail_violations("Sam, thank you for covering yesterday.", "Thank Sam for covering yesterday.", [])
    assert detect_function("Tell the team the room has changed.") == "informing"
    assert detail_violations("Morgan, inspect the printouts before 15:00.", "Ask Morgan to collect the printouts before 15:00.", [])
    assert detail_violations("Let us meet Priya at 10:00 on Friday.", "Ask Priya to meet at 10:00 on Friday.", [])


def test_sentence_punctuation_and_explicit_curated_action_equivalents():
    assert contains("Got your ears on, Morgan?", "got your ears on?")
    assert contains("Good truckin’, Alex.", "good truckin'")
    assert not contains("That is a moment.", "micro-moment")
    record = {"id": "cb_eyeball", "surface": "eyeball", "variants": [],
              "meaning": "Meet or inspect something in person."}
    assert not detail_violations("Let us have an eyeball at 10:00 on Friday, Priya.",
                                 "Ask Priya to meet at 10:00 on Friday.", [record])
    assert detail_violations("Morgan, have an eyeball at the printouts before 15:00.",
                             "Ask Morgan to collect the printouts before 15:00.", [record])
    assert not detail_violations("Morgan, could you help by collecting the printouts before 15:00?",
                                 "Ask Morgan to collect the printouts before 15:00.", [])


def test_omitted_recipient_can_be_restored_without_concealing_actor_inversions():
    intent = "Ask Morgan to collect printouts before 15:00."
    assert address_recipient("Please collect printouts before 15:00.", intent) == "Morgan, Please collect printouts before 15:00."
    inverted = "Please collect printouts from Morgan before 15:00."
    assert address_recipient(inverted, intent) == inverted
    assert detail_violations(inverted, intent, [])
    assert address_recipient("Room 4 is ready.", "Tell the team room 4 is ready.") == "Room 4 is ready."


def test_reason_inflection_preserves_the_actual_contribution():
    intent = "Apologize to Jordan for missing yesterday's deadline."
    assert not detail_violations("Jordan, I'm sorry I missed yesterday's deadline.", intent, [])
    assert detail_violations("Jordan, I'm sorry I missed today's deadline.", intent, [])
    assert detail_violations("Jordan, I'm sorry for finishing yesterday's deadline.", intent, [])
    assert not detail_violations("Sam, you covered my shift yesterday; thank you.",
                                 "Thank Sam for covering my shift yesterday.", [])


def test_contracted_negation_retains_the_requested_action():
    intent = "Ask Lee not to publish the draft before approval."
    assert not detail_violations("Lee, don't publish the draft before approval.", intent, [])
    assert not detail_violations("Lee, don’t publish the draft before approval.", intent, [])
    assert detail_violations("Lee, don't collect the draft before approval.", intent, [])
    assert detail_violations("Lee, publish the draft before approval.", intent, [])


def test_task_objects_refusal_scope_and_unrequested_deadlines_are_preserved():
    assert detail_violations("Morgan, collect all the things before 15:00.",
                             "Ask Morgan to collect the printouts before 15:00.", [])
    assert detail_violations("Casey, bring three copies of the agenda.",
                             "Ask Casey to bring exactly three copies of the agenda.", [])
    assert detail_violations("I can't attend Monday's event.",
                             "Politely decline the invitation to speak at Monday's event.", [])
    assert not detail_violations("Thank you, but I won't be speaking at Monday's event.",
                                 "Politely decline the invitation to speak at Monday's event.", [])
    assert detail_violations("Casey, bring exactly three copies of the agenda before the next meeting.",
                             "Ask Casey to bring exactly three copies of the agenda.", [])


def test_fragment_and_closing_roles_and_each_supplied_group_are_required():
    records = [{"id": "reaction", "surface": "I can't even", "variants": [],
                "kairolexicon": "reactions", "usage_role": "fragment"},
               {"id": "closing", "surface": "good truckin'", "variants": [],
                "kairolexicon": "farewells", "usage_role": "closing"}]
    assert not used_markers("I can't even apologize. Good truckin' on your report.", records)
    assert set(used_markers("I can't even. I'm sorry. Good truckin', Jordan.", records)) == {"reaction", "closing"}
    assert material_violations("I'm sorry. Good truckin'.", records)
    assert not material_violations("I can't even. I'm sorry. Good truckin'.", records)


def test_model_response_must_obey_the_intent_contract():
    model = SmallModel("http://localhost/v1", Path("prompts/generation_v3.txt"))
    model.client.close()
    model.client = httpx.Client(base_url="http://localhost/v1/", transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({
            "intent": "Changed intent", "utterance": "An unrelated sentence."})}}]})))
    with pytest.raises(ModelUnavailable):
        model.synthesize("Thank a colleague.", [], 7)
    model.close()


@pytest.mark.parametrize("value", [
    {"intent": "true", "fidelity": True, "jargon": [], "reason": "Evidence"},
    {"intent": True, "fidelity": True, "jargon": [None], "reason": "Evidence"},
    {"intent": True, "fidelity": True, "jargon": [], "reason": ""},
])
def test_malformed_reviews_cannot_inflate_the_baseline(value):
    with pytest.raises(ValueError):
        validate_judgment(value)
