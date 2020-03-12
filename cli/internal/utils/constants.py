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

    'platform_url_base': 'https://platform.bymason.com',
    'api_url_base': 'https://platform.bymason.com/api',

    'projects_url_path': '/dashboard/projects',
    'registry_signed_url_path': '/registry/signedurl',
    'registry_artifact_url_path': '/registry/artifacts',
    'builder_url_path': '/tracker/builder',
    'deploy_url_path': '/deploy',

    'console_create_url_path': '/controller/create',
    'console_projects_url_path': '/controller/projects',

    'xray_url': 'wss://api.bymason.com/v1/global/xray',

    'analytics_url': None,
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
