from cli.internal.utils.store import Store
from cli.version import __version__

LOG_PROTOCOL_TRACE = 4

AUTH = Store('auth', {
    'api_key': None,
    'id_token': None,
    'access_token': None
})

ENDPOINTS = Store('endpoints', {
    'client_id': 'QLWpUwYOOcLlAJsmyQhQMXyeWn6RZpoc',
    'auth_url': 'https://bymason.auth0.com/oauth/ro',
    'user_info_url': 'https://bymason.auth0.com/userinfo',
    'projects_url': 'https://platform.bymason.com/api/dashboard/projects',
    'registry_artifact_url': 'https://platform.bymason.com/api/registry/artifacts',
    'registry_signed_url': 'https://platform.bymason.com/api/registry/signedurl',
    'builder_url': 'https://platform.bymason.com/api/tracker/builder',
    'deploy_url': 'https://platform.bymason.com/api/deploy',
    'xray_url': 'wss://api.bymason.com/v1/global/xray',
    'analytics_url': None,
    'console_projects_url': 'https://platform.bymason.com/controller/projects',
    'latest_version_url': 'https://raw.githubusercontent.com/MasonAmerica/mason-cli/master/VERSION'
})

UPDATE_CHECKER_CACHE = Store('version-check-cache', {
    'last_update_check_timestamp': 0,
    'current_version': __version__,
    'latest_version': None,
    'last_nag_timestamp': 0,
    'first_update_found_timestamp': 0,
    'update_check_frequency_seconds': 86400  # 1 day
})
UPDATE_CHECKER_CACHE['current_version'] = None
