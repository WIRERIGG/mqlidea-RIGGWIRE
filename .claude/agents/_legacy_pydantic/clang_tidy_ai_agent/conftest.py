import pytest

def pytest_sessionfinish(session):
    """Enforce ≥95% coverage requirement per AI Agent Validator.md."""
    if hasattr(session.config, 'pluginmanager'):
        cov_plugin = session.config.pluginmanager.get_plugin('pytest_cov')
        if cov_plugin and hasattr(cov_plugin, 'cov_total'):
            if cov_plugin.cov_total < 95.0:
                raise Exception(f"Coverage {cov_plugin.cov_total}% < required 95%")
