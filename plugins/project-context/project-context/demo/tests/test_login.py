from login import tokenlogin


def test_tokenlogin():
    assert tokenlogin("synthetic-demo")["offline_days"] == 7
