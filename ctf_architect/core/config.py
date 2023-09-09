import os
from yaml import safe_load, safe_dump

from ctf_architect.core.models import Config


def load_config() -> Config:
  files = os.listdir("./")
  if "ctf_config.yaml" not in files:
    raise FileNotFoundError("ctf_config.yaml not found")
  
  with open("ctf_config.yaml", "r") as f:
    data = safe_load(f)

  config = data.get("config")
  if config is None:
    raise ValueError("ctf_config.yaml does not specify config")

  return Config(**config)


def save_config(config: Config):
  with open("ctf_config.yaml", "w") as f:
    data = {
      "config": config.to_dict()
    }
    
    safe_dump(data, f)