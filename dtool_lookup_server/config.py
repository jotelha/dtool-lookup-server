import json
import os

import dtool_lookup_server

_HERE = os.path.abspath(os.path.dirname(__file__))


def _get_file_content(key, default=""):
    file_path = os.environ.get(key, "")
    if os.path.isfile(file_path):
        content = open(file_path).read()
    else:
        content = ""
    return content


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY', 'you-will-never-guess')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'SQLALCHEMY_DATABASE_URI',
        'sqlite:///{}'.format(os.path.join(_HERE, "..", 'app.db'))
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MONGO_URI = os.environ.get(
        'MONGO_URI',
        'mongodb://localhost:27017/dtool_info'
    )
    JWT_ALGORITHM = "RS256"
    JWT_TOKEN_LOCATION = "headers"
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # Logic to give "JWT_PUBLIC_KEY" priority over "JWT_PUBLIC_KEY_FILE".
    # This is used when making use of JWT tokens generated by another service.
    # Hence there is no need for the JWT_PRIVATE_KEY_FILE.
    if os.environ.get("JWT_PUBLIC_KEY"):
        JWT_PUBLIC_KEY = os.environ.get("JWT_PUBLIC_KEY")
    else:
        JWT_PRIVATE_KEY = _get_file_content("JWT_PRIVATE_KEY_FILE")
        JWT_PUBLIC_KEY = _get_file_content("JWT_PUBLIC_KEY_FILE")

    JSONIFY_PRETTYPRINT_REGULAR = True

    # Above all enters the flask app, below does not.
    # Would those settings belong here or should they be somewhere else, i.e.
    # a specific dtool lookup server configuration file?

    MONGO_COLLECTION = os.environ.get('DTOOL_LOOKUP_SERVER_MONGO_COLLECTION', 'datasets')
    MONGO_DEPENDENCY_VIEW = os.environ.get('DTOOL_LOOKUP_SERVER_MONGO_DEPENDENCY_VIEW', 'dependencies')

    # This option allows a client to submit direct mongo-syntaxed aggregations
    # to the underlying mongo database. As above, externally managed privileges
    # will still apply to the initial '$match' stage of the aggregation
    # pipeline (see utils._dict_to_mongo_aggregation()), but can be easiliy
    # circumvented in subsequent aggregation stages. Further notice that
    # aggregation stages allow write access to the database, thus this option
    # should only be enabled if some privileges are configured a the MongoDB
    # level as well.
    ALLOW_DIRECT_AGGREGATION = os.environ.get('DTOOL_LOOKUP_SERVER_ALLOW_DIRECT_AGGREGATION',
                                              'False').lower() in ['true', '1', 'y', 'yes', 'on']

    # Appending the 'query' key to the list of valid query dict keys
    # allows a client to submit direct mongo-syntaxed queries
    # to the underlying mongo database. Externally managed privileges will
    # be enforced as usual by embedding such queries in accompanying logical
    # '$and' clauses, see utils._preprocess_privileges() and
    #  utils._dict_to_mongo_query().
    QUERY_DICT_VALID_KEYS = json.loads(
        os.environ.get('DTOOL_LOOKUP_SERVER_QUERY_DICT_VALID_KEYS',
                       '["free_text", "creator_usernames", "base_uris", "uuids", "tags"]'))
    if not isinstance(QUERY_DICT_VALID_KEYS, list):
        raise ValueError("DTOOL_LOOKUP_SERVER_QUERY_DICT_VALID_KEYS must be json-parsable list.")

    QUERY_DICT_LIST_KEYS = json.loads(
        os.environ.get('DTOOL_LOOKUP_SERVER_QUERY_DICT_LIST_KEYS',
                       '["creator_usernames", "base_uris", "tags"]'))
    if not isinstance(QUERY_DICT_LIST_KEYS, list):
        raise ValueError("DTOOL_LOOKUP_SERVER_QUERY_DICT_LIST_KEYS must be json-parsable list.")

    # If enabled, the underlying database will offer a 'view' named
    # 'dependencies' on the default collection 'datasets'. 'dependencies'
    # offers an on-the-fly-generated collection of undirected per-dataset
    # adjacency lists in order to facilitate searching dataset dependeny graphs
    # in both directions.
    # See https://docs.mongodb.com/manual/core/views/.
    ENABLE_DEPENDENCY_VIEW = os.environ.get('DTOOL_LOOKUP_SERVER_ENABLE_DEPENDENCY_VIEW',
                                            'False').lower() in ['true', '1', 'y', 'yes', 'on']

    FORCE_REBUILD_DEPENDENCY_VIEW = os.environ.get('DTOOL_LOOKUP_SERVER_FORCE_REBUILD_DEPENDENCY_VIEW',
                                                   'False').lower() in ['true', '1', 'y', 'yes', 'on']

    # Specify a key or multiple possible keys that hold unidirectional
    # dependency information in form of parents' UUIDs. The syntax must be
    # a single key or a JSON-formatted list of keys.
    # Nested fields are separated by a dot (.)
    DEPENDENCY_KEYS = [
        'readme.derived_from.uuid',
        'annotations.source_dataset_uuid'
    ]
    dep_key = os.environ.get('DTOOL_LOOKUP_SERVER_DEPENDENCY_KEYS', '')
    if len(dep_key) > 0:
        try:
            DEPENDENCY_KEYS = json.loads(dep_key)
        except json.JSONDecodeError:  # assume only one key, plain string
            DEPENDENCY_KEYS = [dep_key]

    @classmethod
    def to_dict(cls):
        """Convert server configuration into dict."""
        exclusions = [
            'JWT_PRIVATE_KEY',
            'MONGO_URI',
            'SECRET_KEY',
            'SQLALCHEMY_DATABASE_URI',
        ]  # config keys to exclude
        d = {'version': dtool_lookup_server.__version__}
        for k, v in cls.__dict__.items():
            # select only capitalized fields
            if k.upper() == k and k not in exclusions:
                d[k.lower()] = v
        return d
