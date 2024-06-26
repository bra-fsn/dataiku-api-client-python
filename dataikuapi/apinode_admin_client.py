import json

from .apinode_admin.service import APINodeService
from .apinode_admin.auth import APINodeAuth
from .utils import DataikuException
from .base_client import DSSBaseClient

class APINodeAdminClient(DSSBaseClient):
    """Entry point for the DSS APINode admin client"""

    def __init__(self, uri, api_key):
        """
        Instantiate a new DSS API client on the given base uri with the given API key.
        """
        DSSBaseClient.__init__(self, "%s/%s" % (uri, "admin/api"), api_key)

    ########################################################
    # Services generations
    ########################################################

    def create_service(self, service_id):
        """
        Creates a new API service

        :param service_id: id of the created API service
        """
        self._perform_empty("POST", "services/", body = {
            "serviceId" : service_id
        })

    def list_services(self):
        """
        Lists the currently declared services and their enabled/disabled state

        :return: a dict of services containing their id and state, as a JSON object
        :rtype: dict
        """
        return self._perform_json("GET", "services")

    def service(self, service_id):
        """
        Gets a handle to interact with a service

        :param service_id: id of requested service
        :rtype: :class: `dataikuapi.apinode_admin.service.APINodeService`
        """
        return APINodeService(self, service_id)

    def auth(self):
        """
        Returns a handle to interact with authentication

        :rtype: :class: `dataikuapi.apinode_admin.auth.APINodeAuth`
        """
        return APINodeAuth(self)

    def get_metrics(self):
        """
        Get the metrics for this API Node

        :return: the metrics, as a JSON object
        :rtype: dict
        """
        return self._perform_json("GET", "metrics")

    def import_code_env_in_cache(self, file_dir, language):
        """
        Import a code env in global cache from an exported code env base folder

        :param file_dir: path of an exported code env base folder
        :param language: language of the code env (`python` or `R`)
        """
        return self._perform_json("POST", "cached-code-envs", params={
            "fileDir": file_dir,
            "language": language
        })

    def register_code_env_in_cache(self, exported_env_dir, built_env_dir, language):
        """
        Import a code env in global cache from an exported code env base folder

        :param exported_env_dir: path of an exported code env base folder
        :param built_env_dir: path where the code env was built and is available
        :param language: language of the code env (`python` or `R`)
        """
        return self._perform_json("POST", "register-global-code-env", params={
            "exportedEnvDir": exported_env_dir,
            "builtEnvDir": built_env_dir,
            "language": language
        })

    def import_model_archive_in_cache(self, model_archive_path):
        """
        Import a model in model cache from an exported model archive

        :param model_archive_path: path of an exported model archive
        """
        return self._perform_json("POST", "model-cache", params={
            "modelArchivePath": model_archive_path
        })

    def clear_model_cache(self):
        """
        Clear the model cache
        """
        self._perform_empty("DELETE", "model-cache")

    def clean_unused_services_and_generations(self):
        """
        Deletes disabled services, unused generations and unused code environments
        """
        resp = self._perform_json("DELETE", "services-clean-unused")
        print(json.dumps(resp, indent=4))

    def clean_code_env_cache(self):
        """
        Deletes unused code envs from cache
        """
        resp = self._perform_json("DELETE", "cached-code-envs")
        print(json.dumps(resp, indent=4))
