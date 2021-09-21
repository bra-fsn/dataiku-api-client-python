from enum import Enum
import json
from dataikuapi.fm.future import FMFuture


class FMInstanceSettingsTemplateCreator(object):
    def __init__(self, client, label):
        """
        A builder class to create an Instance Settings Template

        :param str label: The label of the Virtual Network
        """

        self.data = {}
        self.data["label"] = label
        self.client = client

    def create(self):
        """
        Create the Instance Settings Template

        :return: Created InstanceSettingsTemplate
        :rtype: :class:`dataikuapi.fm.instancesettingstemplates.FMInstanceSettingsTemplate`
        """

        template = self.client._perform_tenant_json(
            "POST", "/instance-settings-templates", body=self.data
        )
        return FMInstanceSettingsTemplate(self, template)

    def with_setup_actions(self, setup_actions):
        """
        Add setup actions

        :param list setup_actions: List of :class:`dataikuapi.fm.instancesettingstemplates.FMSetupAction` to be played on an instance
        :rtype: :class:`dataikuapi.fm.instancesettingstemplates.FMInstanceSettingsTemplateCreator`
        """
        self.data["setupActions"] = setup_actions
        return self

    def with_license(self, license):
        self.data["license"] = license
        return self


class FMAWSInstanceSettingsTemplateCreator(FMInstanceSettingsTemplateCreator):
    def with_aws_keypair(self, aws_keypair_name):
        """
        Add an AWS Keypair to the DSS instance.
        Needed to get SSH access to the DSS instance, using the centos user.

        :param str aws_keypair_name: Name of an AWS key pair to add to the instance.
        """
        self.data["awsKeyPairName"] = aws_keypair_name
        return self

    def with_startup_instance_profile(self, startup_instance_profile_arn):
        """
        Add a Instance Profile to be assign to the DSS instance on startup

        :param str startup_instance_profile_arn: ARN of the Instance profile assigned to the DSS instance at startup time
        """
        self.data["startupInstanceProfileArn"] = startup_instance_profile_arn
        return self

    def with_runtime_instance_profile(self, runtime_instance_profile_arn):
        """
        Add a Instance Profile to be assign to the DSS instance when running

        :param str runtime_instance_profile_arn: ARN of the Instance profile assigned to the DSS instance during runtime
        """
        self.data["runtimeInstanceProfileArn"] = runtime_instance_profile_arn
        return self

    def with_restrict_aws_metadata_server_access(
        self, restrict_aws_metadata_server_access=True
    ):
        """
        Restrict AWS metadata server access on the DSS instance.

        :param boolean restrict_aws_metadata_server_access: Optional, If true, restrict the access to the metadata server access. Defaults to true
        """
        self.data[
            "restrictAwsMetadataServerAccess"
        ] = restrict_aws_metadata_server_access
        return self

    def with_default_aws_api_access_mode(self):
        """
        The DSS Instance will use the Runtime Instance Profile to access AWS API.
        """
        self.data["dataikuAwsAPIAccessMode"] = "NONE"
        return self

    def with_keypair_aws_api_access_mode(
        self,
        aws_access_key_id,
        aws_keypair_storage_mode="NONE",
        aws_secret_access_key=None,
        aws_secret_access_key_aws_secret_name=None,
        aws_secrets_manager_region=None,
    ):
        """
        DSS Instance will use an Access Key to authenticate against the AWS API.

        :param str aws_access_key_id: AWS Access Key ID.
        :param str aws_keypair_storage_mode: Optional, the storage mode of the AWS api key. Accepts "NONE", "INLINE_ENCRYPTED" or "AWS_SECRETS_MANAGER". Defaults to "NONE"
        :param str aws_secret_access_key: Optional, AWS Access Key Secret. Only needed if keypair_storage_mode is "INLINE_ENCRYPTED"
        :param str aws_secret_access_key_aws_secret_name: Optional, ASM secret name. Only needed if aws_keypair_storage_mode is "AWS_SECRET_MANAGER"
        :param str aws_secrets_manager_region: Optional, Secret Manager region to use. Only needed if aws_keypair_storage_mode is "AWS_SECRET_MANAGER"
        """
        if aws_keypair_storage_mode not in [
            "NONE",
            "INLINE_ENCRYPTED",
            "AWS_SECRETS_MANAGER",
        ]:
            raise ValueError(
                'aws_keypair_storage_mode should be either "NONE", "INLINE_ENCRYPTED" or "AWS_SECRET_MANAGER"'
            )

        self.data["dataikuAwsAPIAccessMode"] = "KEYPAIR"
        self.data["dataikuAwsKeypairStorageMode"] = aws_keypair_storage_mode

        if aws_keypair_storage_mode == "NONE":
            return self

        self.data["dataikuAwsAccessKeyId"] = aws_access_key_id

        if aws_keypair_storage_mode == "INLINE_ENCRYPTED":
            if aws_secret_access_key == None:
                raise ValueError(
                    'When aws_keypair_storage_mode is "INLINE_ENCRYPTED", aws_secret_access_key should be provided'
                )
            self.data["dataikuAwsSecretAccessKey"] = aws_secret_access_key
        elif aws_keypair_storage_mode == "AWS_SECRETS_MANAGER":
            if aws_secret_access_key_aws_secret_name == None:
                raise ValueError(
                    'When aws_keypair_storage_mode is "AWS_SECRETS_MANAGER", aws_secret_access_key_aws_secret_name should be provided'
                )
            self.data[
                "dataikuAwsSecretAccessKeyAwsSecretName"
            ] = aws_secret_access_key_aws_secret_name
            self.data["awsSecretsManagerRegion"] = aws_secrets_manager_region

        return self


class FMAzureInstanceSettingsTemplateCreator(FMInstanceSettingsTemplateCreator):
    def with_ssh_key(self, ssh_public_key):
        """
        Add an SSH public key to the DSS Instance.
        Needed to access it through SSH, using the centos user.

        :param str ssh_public_key: The content of the public key to add to the instance.
        """
        self.data["azureSshKey"] = ssh_public_key
        return self

    def with_startup_managed_identity(self, startup_managed_identity):
        """
        Add a managed identity to be assign to the DSS instance on startup

        :param str startup_managed_identity: Managed Identity ID
        """
        self.data["startupManagedIdentity"] = startup_managed_identity
        return self

    def with_runtime_managed_identity(self, runtime_managed_identity):
        """
        Add a managed identity to be assign to the DSS instance when running

        :param str runtime_managed_identity: Managed Identity ID
        """
        self.data["runtimeManagedIdentity"] = runtime_managed_identity
        return self


class FMInstanceSettingsTemplate(object):
    def __init__(self, client, ist_data):
        self.client = client
        self.id = ist_data["id"]
        self.ist_data = ist_data

    def save(self):
        """
        Update the Instance Settings Template.
        """
        self.client._perform_tenant_empty(
            "PUT", "/instance-settings-templates/%s" % self.id, body=self.ist_data
        )
        self.ist_data = self.client._perform_tenant_json(
            "GET", "/instance-settings-templates/%s" % self.id
        )

    def delete(self):
        """
        Delete the DSS Instance Settings Template.

        :return: A :class:`~dataikuapi.fm.future.FMFuture` representing the deletion process
        :rtype: :class:`~dataikuapi.fm.future.FMFuture`
        """
        future = self.client._perform_tenant_json(
            "DELETE", "/instance-settings-templates/%s" % self.id
        )
        return FMFuture.from_resp(self.client, future)

    def add_setup_action(self, setup_action):
        """
        Add a setup_action

        :param object setup_action: a :class:`dataikuapi.fm.instancesettingstemplates.FMSetupAction`
        """
        self.ist_data["setupActions"].append(setup_action)
        self.save()


class FMSetupAction(dict):
    def __init__(self, setupActionType, params=None):
        """
        A class representing a SetupAction

        Do not create this directly, use:
            - :meth:`dataikuapi.fm.instancesettingstemplates.FMSetupAction.add_authorized_key`

        """
        data = {
            "type": setupActionType.value,
        }
        if params:
            data["params"] = params

        super(FMSetupAction, self).__init__(data)

    @staticmethod
    def add_authorized_key(ssh_key):
        """
        Return a ADD_AUTHORIZED_KEY FMSetupAction
        """
        return FMSetupAction(FMSetupActionType.ADD_AUTHORIZED_KEY, {"sshKey": ssh_key})

    @staticmethod
    def run_ansible_task(stage, yaml_string):
        """
        Return a RUN_ANSIBLE_TASK FMSetupAction

        :param object stage: a :class:`dataikuapi.fm.instancesettingstemplates.FMSetupActionStage`
        :param str yaml_string: a yaml encoded string defining the ansibles tasks to run
        """
        return FMSetupAction(
            FMSetupActionType.RUN_ANSIBLE_TASKS,
            {"stage": stage.value, "ansibleTasks": yaml_string},
        )

    @staticmethod
    def install_system_packages(packages):
        """
        Return an INSTALL_SYSTEM_PACKAGES FMSetupAction

        :param list packages: List of packages to install
        """
        return FMSetupAction(
            FMSetupActionType.INSTALL_SYSTEM_PACKAGES, {"packages": packages}
        )

    @staticmethod
    def setup_advanced_security(basic_headers=True, hsts=False):
        """
        Return an SETUP_ADVANCED_SECURITY FMSetupAction

        :param boolean basic_headers: Optional, Prevent browsers to render Web content served by DSS to be embedded into a frame, iframe, embed or object tag. Defaults to True
        :param boolean hsts: Optional,  Enforce HTTP Strict Transport Security. Defaults to False
        """
        return FMSetupAction(
            FMSetupActionType.SETUP_ADVANCED_SECURITY,
            {"basic_headers": basic_headers, "hsts": hsts},
        )

    @staticmethod
    def install_jdbc_driver(
        database_type,
        url,
        paths_in_archive=None,
        http_headers=None,
        http_username=None,
        http_password=None,
        datadir_subdirectory=None,
    ):
        """
        Return a INSTALL_JDBC_DRIVER FMSetupAction

        :param object database_type: a :class:`dataikuapi.fm.instancesettingstemplates.FMSetupActionAddJDBCDriverDatabaseType`
        :param str url: The full address to the driver. Supports http(s)://, s3://, abs:// or file:// endpoints
        :param list paths_in_archive: Optional, must be used when the driver is shipped as a tarball or a ZIP file. Add here all the paths to find the JAR files in the driver archive. Paths are relative to the top of the archive. Wildcards are supported.
        :param dict http_headers: Optional, If you download the driver from a HTTP(S) endpoint, add here the headers you want to add to the query. This setting is ignored for any other type of download.
        :param str http_username: Optional, If the HTTP(S) endpoint expect a Basic Authentication, add here the username. To explicitely specify which Assigned Identity use if the machine have several, set the client_id here. To authenticate with a SAS Token on Azure Blob Storage (not recommended), use "token" as the value here.
        :param str http_password: Optional, If the HTTP(S) endpoint expect a Basic Authentication, add here the password. To authenticate with a SAS Token on Azure Blob Storage (not recommended), store the token in this field.
        :param str datadir_subdirectory: Optional, Some drivers are shipped with a high number of JAR files along with them. In that case, you might want to install them under an additional level in the DSS data directory. Set the name of this subdirectory here. Not required for most drivers.
        """
        return FMSetupAction(
            FMSetupActionType.INSTALL_JDBC_DRIVER,
            {
                "url": url,
                "dbType": database_type.value,
                "pathsInArchive": paths_in_archive,
                "headers": http_headers,
                "username": http_username,
                "password": http_password,
                "subpathInDatadir": datadir_subdirectory,
            },
        )

    @staticmethod
    def setup_k8s_and_spark():
        """
        Return a SETUP_K8S_AND_SPARK FMSetupAction
        """
        return FMSetupAction(FMSetupActionType.SETUP_K8S_AND_SPARK)


class FMSetupActionType(Enum):
    RUN_ANSIBLE_TASKS = "RUN_ANSIBLE_TASKS"
    INSTALL_SYSTEM_PACKAGES = "INSTALL_SYSTEM_PACKAGES"
    INSTALL_DSS_PLUGINS_FROM_STORE = "INSTALL_DSS_PLUGINS_FROM_STORE"
    SETUP_K8S_AND_SPARK = "SETUP_K8S_AND_SPARK"
    SETUP_RUNTIME_DATABASE = "SETUP_RUNTIME_DATABASE"
    SETUP_MUS_AUTOCREATE = "SETUP_MUS_AUTOCREATE"
    SETUP_UI_CUSTOMIZATION = "SETUP_UI_CUSTOMIZATION"
    SETUP_MEMORY_SETTINGS = "SETUP_MEMORY_SETTINGS"
    SETUP_GRAPHICS_EXPORT = "SETUP_GRAPHICS_EXPORT"
    ADD_AUTHORIZED_KEY = "ADD_AUTHORIZED_KEY"
    INSTALL_JDBC_DRIVER = "INSTALL_JDBC_DRIVER"
    SETUP_ADVANCED_SECURITY = "SETUP_ADVANCED_SECURITY"


class FMSetupActionStage(Enum):
    after_dss_startup = "after_dss_startup"
    after_install = "after_install"
    before_install = "before_install"


class FMSetupActionAddJDBCDriverDatabaseType(Enum):
    mysql = "mysql"
    mssql = "mssql"
    oracle = "oracle"
    mariadb = "mariadb"
    snowflake = "snowflake"
    athena = "athena"
    bigquery = "bigquery"