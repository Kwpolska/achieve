import pytest


@pytest.mark.django_db
def test_achieveprofile(admin_user):
    assert admin_user.achieveprofile.timezone == "UTC"
