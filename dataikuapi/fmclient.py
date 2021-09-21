import json
from requests import Session
from requests import exceptions
from requests.auth import HTTPBasicAuth
import os.path as osp

from enum import Enum
from .utils import DataikuException

from .fm.tenant import FMCloudCredentials
from .fm.virtualnetworks import FMVirtualNetwork
from .fm.instances import FMInstance, FMInstanceEncryptionMode, FMAWSInstanceCreator, FMAzureInstanceCreator
from .fm.instancesettingstemplates import FMInstanceSettingsTemplate, FMAWSInstanceSettingsTemplateCreator, FMAzureInstanceSettingsTemplateCreator

class FMClient(object):
    """Entry point for the FM API client"""

    def __init__(self, host, api_key_id, api_key_secret, cloud, tenant_id="main", extra_headers=None):
        """
        Instantiate a new FM API client on the given host with the given API key.

        API keys can be managed in FM on the project page or in the global settings.

        The API key will define which operations are allowed for the client.

        :param str host: Full url of the FM

        """
        self.api_key_id = api_key_id
        self.api_key_secret = api_key_secret
        self.host = host
        if cloud not in ["AWS", "Azure"]:
            raise ValueError("cloud should be either \"AWS\" or \"Azure\"")
        self.cloud = cloud
        self.__tenant_id = tenant_id
        self._session = Session()

        if self.api_key_id is not None and self.api_key_secret is not None:
            self._session.auth = HTTPBasicAuth(self.api_key_id, self.api_key_secret)
        else:
            raise ValueError("API Key ID and API Key secret are required")

        if extra_headers is not None:
            self._session.headers.update(extra_headers)


    ########################################################
    # Tenant
    ########################################################

    def get_cloud_credentials(self):
        """
        Get Cloud Credentials

        :return: Cloud credentials
        :rtype: :class:`dataikuapi.fm.tenant.FMCloudCredentials`
        """
        creds = self._perform_tenant_json("GET", "/cloud-credentials")
        return FMCloudCredentials(self, creds)


    ########################################################
    # VirtualNetwork
    ########################################################

    def list_virtual_networks(self):
        """
        List all Virtual Networks

        :return: list of virtual networks
        :rtype: list of :class:`dataikuapi.fm.virtualnetworks.FMVirtualNetwork`
        """
        vns = self._perform_tenant_json("GET", "/virtual-networks")
        return [ FMVirtualNetwork(self, x) for x in vns]

    def get_virtual_network(self, virtual_network_id):
        """
        Get a Virtual Network

        :param str virtual_network_id

        :return: requested virtual network
        :rtype: :class:`dataikuapi.fm.virtualnetworks.FMVirtualNetwork`
        """
        vn = self._perform_tenant_json("GET", "/virtual-networks/%s" % virtual_network_id)
        return FMVirtualNetwork(self, vn)

    def create_virtual_network(self,
                               label,
                               awsVpcId=None,
                               awsSubnetId=None,
                               awsAutoCreateSecurityGroups=False,
                               awsSecurityGroups=None,
                               azureVnId=None,
                               azureSubnetId=None,
                               azureAutoUpdateSecurityGroups=None,
                               internetAccessMode = "YES"):
        """
        Create a Virtual Network

        :param str label: The label of the Virtual Network

        :param str awsVpcId: AWS Only, ID of the VPC to use
        :param str awsSubnetId: AWS Only, ID of the subnet to use
        :param boolean awsAutoCreateSecurityGroups: Optional, AWS Only, If false, do not create security groups automatically. Defaults to false
        :param list awsSecurityGroups: Optional, AWS Only, A list of up to 5 security group ids to assign to the instances created in this virtual network. Ignored if awsAutoCreateSecurityGroups is true

        :param str azureVnId: Azure Only, ID of the Azure Virtual Network to use
        :param str azureSubnetId: Azure Only, ID of the subnet to use
        :param boolean azureAutoUpdateSecurityGroups: Azure Only, Auto update the subnet security group

        :param str internetAccessMode: Optional, The internet access mode of the instances created in this virtual network. Accepts "YES", "NO", "EGRESS_ONLY". Defaults to "YES"

        :return: requested instance settings template
        :rtype: :class:`dataikuapi.fm.instancesettingstemplates.FMInstanceSettingsTemplate`
        """

        data = {
            "label": label,
            "awsVpcId": awsVpcId,
            "awsSubnetId": awsSubnetId,
            "awsAutoCreateSecurityGroups": awsAutoCreateSecurityGroups,
            "awsSecurityGroups": awsSecurityGroups,
            "azureVnId": azureVnId,
            "azureSubnetId": azureSubnetId,
            "azureAutoUpdateSecurityGroups": azureAutoUpdateSecurityGroups,
            "internetAccessMode": internetAccessMode,
            "mode": "EXISTING_MONOTENANT"
        }

        vn = self._perform_tenant_json("POST", "/virtual-networks", body=data)
        return FMVirtualNetwork(self, vn)


    ########################################################
    # Instance settings template
    ########################################################

    def list_instance_templates(self):
        """
        List all Instance Settings Templates

        :return: list of instance settings template
        :rtype: list of :class:`dataikuapi.fm.tenant.FMInstanceSettingsTemplate`
        """
        templates = self._perform_tenant_json("GET", "/instance-settings-templates")
        return [ FMInstanceSettingsTemplate(self, x) for x in templates]

    def get_instance_template(self, template_id):
        """
        Get an Instance Template

        :param str template_id

        :return: requested instance settings template
        :rtype: :class:`dataikuapi.fm.instancesettingstemplates.FMInstanceSettingsTemplate`
        """
        template = self._perform_tenant_json("GET", "/instance-settings-templates/%s" % template_id)
        return FMInstanceSettingsTemplate(self, template)

    def new_instance_template_creator(self, label):
        """
        Instantiate a new instance template creator

        :param str label: The label of the instance
        :rtype: :class:`dataikuapi.fm.instancesettingstemplates.FMInstanceSettingsTemplateCreator`
        """
        if self.cloud == "AWS":
            return FMAWSInstanceSettingsTemplateCreator(self, label)
        elif self.cloud == "Azure":
            return FMAzureInstanceSettingsTemplateCreator(self, label)


    ########################################################
    # Instance
    ########################################################

    def list_instances(self):
        """
        List all DSS Instances

        :return: list of instances
        :rtype: list of :class:`dataikuapi.fm.instances.FMInstance`
        """
        instances = self._perform_tenant_json("GET", "/instances")
        return [ FMInstance(self, **x) for x in instances]

    def get_instance(self, instance_id):
        """
        Get a DSS Instance

        :param str instance_id

        :return: Instance
        :rtype: :class:`dataikuapi.fm.instances.FMInstance`
        """
        instance = self._perform_tenant_json("GET", "/instances/%s" % instance_id)
        return FMInstance(self, instance)

    def new_instance_creator(self, label, instance_settings_template_id, virtual_network_id, image_id):
        """
        Instantiate a new instance creator

        :param str label: The label of the instance
        :param str instance_settings_template: The instance settings template id this instance should be based on
        :param str virtual_network: The virtual network where the instance should be spawned
        :param str image_id: The ID of the DSS runtime image (ex: dss-9.0.3-default)
        :rtype: :class:`dataikuapi.fm.instances.FMInstanceCreator`
        """
        if self.cloud == "AWS":
            return FMAWSInstanceCreator(self, label, instance_settings_template_id, virtual_network_id, image_id)
        elif self.cloud == "Azure":
            return FMAzureInstanceCreator(self, label, instance_settings_template_id, virtual_network_id, image_id)


    ########################################################
    # Internal Request handling
    ########################################################

    def _perform_http(self, method, path, params=None, body=None, stream=False, files=None, raw_body=None):
        if body is not None:
            body = json.dumps(body)
        if raw_body is not None:
            body = raw_body
        try:
            http_res = self._session.request(
                    method, "%s/api/public%s" % (self.host, path),
                    params=params, data=body,
                    files = files,
                    stream = stream)
            http_res.raise_for_status()
            return http_res
        except exceptions.HTTPError:
            try:
                ex = http_res.json()
            except ValueError:
                ex = {"message": http_res.text}
            raise DataikuException("%s: %s" % (ex.get("errorType", "Unknown error"), ex.get("message", "No message")))

    def _perform_empty(self, method, path, params=None, body=None, files = None, raw_body=None):
        self._perform_http(method, path, params=params, body=body, files=files, stream=False, raw_body=raw_body)

    def _perform_json(self, method, path, params=None, body=None,files=None, raw_body=None):
        return self._perform_http(method, path,  params=params, body=body, files=files, stream=False, raw_body=raw_body).json()

    def _perform_tenant_json(self, method, path, params=None, body=None,files=None, raw_body=None):
        return self._perform_json(method, "/tenants/%s%s" % ( self.__tenant_id, path ), params=params, body=body, files=files, raw_body=raw_body)

    def _perform_tenant_empty(self, method, path, params=None, body=None, files = None, raw_body=None):
        self._perform_empty(method, "/tenants/%s%s" % ( self.__tenant_id, path ), params=params, body=body, files=files, raw_body=raw_body)