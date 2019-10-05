import yaml
import os

__all__ = ["cfg"]

with open(os.path.join(os.getcwd(), "configs/local_config.yaml"), 'r') as yamlfile:
    cfg = yaml.safe_load(yamlfile)

