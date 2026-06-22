from backend.state import JarvisState, JarvisStatus


def test_all_six_statuses_defined():
    """All 6 states required by the voice flow are present."""
    expected = {"STANDBY", "GREETING", "LISTENING", "PROCESSING", "RESPONDING", "ACTIVE_WINDOW"}
    assert {s.value for s in JarvisStatus} == expected


def test_status_values_are_strings():
    """JarvisStatus inherits from str so values can be serialised directly."""
    for status in JarvisStatus:
        assert isinstance(status.value, str)


def test_default_state():
    """JarvisState defaults to STANDBY with empty transcript and results."""
    s = JarvisState()
    assert s.status == JarvisStatus.STANDBY
    assert s.transcript == ""
    assert s.results == []
    assert s.preferences == {}


def test_status_transition_to_every_value():
    """Status field accepts every valid JarvisStatus value."""
    s = JarvisState()
    for status in JarvisStatus:
        s.status = status
        assert s.status == status


def test_transcript_update():
    """Transcript can be set and cleared."""
    s = JarvisState()
    s.transcript = "What time is it?"
    assert s.transcript == "What time is it?"
    s.transcript = ""
    assert s.transcript == ""


def test_results_accumulate():
    """Results list accepts arbitrary dicts."""
    s = JarvisState()
    s.results.append({"title": "BBC", "url": "https://bbc.com"})
    s.results.append({"title": "Reuters", "url": "https://reuters.com"})
    assert len(s.results) == 2
    assert s.results[0]["title"] == "BBC"


def test_preferences_dict():
    """Preferences can be updated like a regular dict."""
    s = JarvisState()
    s.preferences["name"] = "boss"
    assert s.preferences["name"] == "boss"
