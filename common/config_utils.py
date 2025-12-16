#
#  Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
import asyncio
import os
import copy
import logging
import importlib
import socket
from filelock import FileLock
from api.constants import RAG_FLOW_SERVICE_NAME
from common.file_utils import get_project_base_directory
from common.constants import SERVICE_CONF, NACOS_DEFAULT_DATA_ID, NACOS_DEFAULT_GROUP
from ruamel.yaml import YAML

from v2.nacos import NacosNamingService, NacosConfigService, ClientConfigBuilder, GRPCConfig, \
    Instance, SubscribeServiceParam, RegisterInstanceParam, DeregisterInstanceParam, \
    BatchRegisterInstanceParam, GetServiceParam, ListServiceParam, ListInstanceParam, ConfigParam

nacos_config_client = (ClientConfigBuilder()
                .username(os.getenv('NACOS_USERNAME'))
                .password(os.getenv('NACOS_PASSWORD'))
                .server_address(os.getenv('NACOS_SERVER_ADDR', 'localhost:8848'))
                .namespace_id(os.getenv('NACOS_NAMESPACE_ID'))
                .log_level('DEBUG')
                .grpc_config(GRPCConfig(grpc_timeout=5000))
                .build())

async def _load_yaml_from_nacos_async(data_id: str = NACOS_DEFAULT_DATA_ID, group: str = NACOS_DEFAULT_GROUP) -> dict:
    """
    从 Nacos 读取 YAML 配置并使用 ruamel.yaml 解析
    """
    config_client = await NacosConfigService.create_config_service(nacos_config_client)
    content = await config_client.get_config(ConfigParam(
        data_id=data_id,
        group=group
    ))
    if not content:
        return {}
    try:
        yaml = YAML(typ="safe", pure=True)
        conf = yaml.load(content)
    except Exception as e:
        raise ValueError(f'Invalid YAML config in Nacos: "{data_id}", {e}')
    if conf is None:
        return {}
    if not isinstance(conf, dict):
        raise ValueError(f'Config "{data_id}" must be a YAML mapping')
    return conf

def load_yaml_from_nacos(
    data_id: str = NACOS_DEFAULT_DATA_ID,
    group: str = NACOS_DEFAULT_GROUP,
) -> dict:
    """
    同步接口（供 RAGFlow / 配置系统使用）
    """
    return asyncio.run(
        _load_yaml_from_nacos_async(data_id, group)
    )

def load_yaml_conf(conf_path):
    return load_yaml_from_nacos()

def rewrite_yaml_conf(conf_path, config):
    if not os.path.isabs(conf_path):
        conf_path = os.path.join(get_project_base_directory(), conf_path)
    try:
        with open(conf_path, "w") as f:
            yaml = YAML(typ="safe")
            yaml.dump(config, f)
    except Exception as e:
        raise EnvironmentError("rewrite yaml file config {} failed:".format(conf_path), e)


def conf_realpath(conf_name):
    conf_path = f"conf/{conf_name}"
    return os.path.join(get_project_base_directory(), conf_path)


def read_config(conf_name=SERVICE_CONF):
    local_config = {}
    local_path = conf_realpath(f'local.{conf_name}')

    # load local config file
    if os.path.exists(local_path):
        local_config = load_yaml_conf(local_path)
        if not isinstance(local_config, dict):
            raise ValueError(f'Invalid config file: "{local_path}".')

    global_config_path = conf_realpath(conf_name)
    global_config = load_yaml_conf(global_config_path)

    if not isinstance(global_config, dict):
        raise ValueError(f'Invalid config file: "{global_config_path}".')

    global_config.update(local_config)
    return global_config


CONFIGS = read_config()

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 尝试连接外部地址，但不发送数据
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
    except Exception:
        # 失败时回退到获取主机名 IP
        ip_address = socket.gethostbyname(socket.gethostname())
    finally:
        s.close()
    return ip_address

def show_configs():
    msg = f"Current configs, from {conf_realpath(SERVICE_CONF)}:"
    for k, v in CONFIGS.items():
        if isinstance(v, dict):
            if "password" in v:
                v = copy.deepcopy(v)
                v["password"] = "*" * 8
            if "access_key" in v:
                v = copy.deepcopy(v)
                v["access_key"] = "*" * 8
            if "secret_key" in v:
                v = copy.deepcopy(v)
                v["secret_key"] = "*" * 8
            if "secret" in v:
                v = copy.deepcopy(v)
                v["secret"] = "*" * 8
            if "sas_token" in v:
                v = copy.deepcopy(v)
                v["sas_token"] = "*" * 8
            if "oauth" in k:
                v = copy.deepcopy(v)
                for key, val in v.items():
                    if "client_secret" in val:
                        val["client_secret"] = "*" * 8
            if "authentication" in k:
                v = copy.deepcopy(v)
                for key, val in v.items():
                    if "http_secret_key" in val:
                        val["http_secret_key"] = "*" * 8
        msg += f"\n\t{k}: {v}"
    logging.info(msg)


def get_base_config(key, default=None):
    if key is None:
        return None
    if default is None:
        default = os.environ.get(key.upper())
    return CONFIGS.get(key, default)


def decrypt_database_password(password):
    encrypt_password = get_base_config("encrypt_password", False)
    encrypt_module = get_base_config("encrypt_module", False)
    private_key = get_base_config("private_key", None)

    if not password or not encrypt_password:
        return password

    if not private_key:
        raise ValueError("No private key")

    module_fun = encrypt_module.split("#")
    pwdecrypt_fun = getattr(
        importlib.import_module(
            module_fun[0]),
        module_fun[1])

    return pwdecrypt_fun(private_key, password)


def decrypt_database_config(database=None, passwd_key="password", name="database"):
    if not database:
        database = get_base_config(name, {})

    database[passwd_key] = decrypt_database_password(database[passwd_key])
    return database


def update_config(key, value, conf_name=SERVICE_CONF):
    conf_path = conf_realpath(conf_name=conf_name)
    if not os.path.isabs(conf_path):
        conf_path = os.path.join(get_project_base_directory(), conf_path)

    with FileLock(os.path.join(os.path.dirname(conf_path), ".lock")):
        config = load_yaml_conf(conf_path=conf_path) or {}
        config[key] = value
        rewrite_yaml_conf(conf_path=conf_path, config=config)


async def _register_to_server():
    local_ip = get_local_ip()
    server_http_port = CONFIGS.get(RAG_FLOW_SERVICE_NAME, {}).get("http_port")
    naming_service = await NacosNamingService.create_naming_service(nacos_config_client)

    response = await naming_service.register_instance(
        RegisterInstanceParam(
            service_name="xugurtp-ai-ragflow",
            group_name="DEFAULT_GROUP",
            ip=local_ip,
            port=server_http_port,
            weight=1.0,
            cluster_name="c1",
            metadata={"a": "b"},
            enabled=True,
            healthy=True,
            ephemeral=True,
        )
    )
    return response


def register_to_nacos():
    """
    注册服务到nacos
    """
    asyncio.run(_register_to_server())
    logging.info("register to nacos success")