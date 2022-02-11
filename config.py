import yaml
import os

__all__ = [
    "cfg",
    "tusc_api_cfg",
    "general_cfg",
    "wallet_cfg"
]

with open(os.path.join(os.getcwd(), "configs/local_config.yaml"), 'r') as yamlfile:
    cfg = yaml.safe_load(yamlfile)

tusc_api_cfg = cfg["tusc_api"]
general_cfg = cfg["general"]
wallet_cfg = cfg["wallet"]