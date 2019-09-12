import os
import yaml


def read_yaml_conf(p_file_name):
    script_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    path = os.path.join(script_dir, "conf/{}".format(p_file_name))
    return yaml.load(open(path))


def load():
    return read_yaml_conf("api-conf.yml")
