from dot import reset_config


def pytest_runtest_teardown(item, nextitem):
    reset_config()
