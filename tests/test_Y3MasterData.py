from sentinel.classes.Y3MasterDatabase import Y3MasterDatabase
from sentinel.helpers import PathHelper

# pylint: disable=maybe-no-member

def test_add():
    test = Y3MasterDatabase(platform=PathHelper.Platform.android, previous_version='test', is_english=False)
    test.make_changelog("test")
    assert True