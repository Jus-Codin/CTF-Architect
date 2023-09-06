from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Flag:
  flag: str
  regex: bool = False

  def to_dict(self) -> dict:
    return {
      "flag": self.flag,
      "regex": self.regex
    }


@dataclass
class Hint:
  description: str
  cost: int
  requirement: int | None = None

  def to_dict(self) -> dict:
    return {
      "description": self.description,
      "cost": self.cost,
      "requirement": self.requirement
    }


@dataclass
class Service:
  name: str
  path: str
  ports: list[str]
  protocol: str

  # This is for internal use only
  port_mappings: dict[str, str] | None = None

  def to_dict(self) -> dict:
    return {
      "name": self.name,
      "path": self.path,
      "ports": self.ports,
      "protocol": self.protocol,
      "port_mappings": self.port_mappings
    }


@dataclass
class ChallengeInfo:
  name: str
  description: str
  difficulty: str
  category: str
  author: str
  discord: str
  flags: list[Flag]

  hints: list[Hint] | None = None
  files: list[str] | None = None
  requirements: list[str] | None = None
  
  services: list[Service] | None = None

  @classmethod
  def from_dict(cls, d: dict, services: list[Service] | None = None) -> ChallengeInfo:
    flags = [Flag(**flag) for flag in d.pop("flags")]

    hints = d.pop("hints")
    if hints is not None:
      hints = [Hint(**hint) for hint in hints]

    return cls(
      flags=flags,
      hints=hints,
      services=services,
      **d
    )
  
  def to_dict(self) -> dict:
    return {
      "name": self.name,
      "description": self.description,
      "difficulty": self.difficulty,
      "category": self.category,
      "author": self.author,
      "discord": self.discord,
      "flags": [flag.to_dict() for flag in self.flags],
      "hints": [hint.to_dict() for hint in self.hints] if self.hints is not None else None,
      "files": self.files,
      "requirements": self.requirements,
      "services": [service.to_dict() for service in self.services] if self.services is not None else None
    }


@dataclass
class Config:
  categories: list[str]
  difficulties: list[dict[str, str | int]]
  port: int

  @property
  def diff_names(self) -> list[str]:
    return [d["name"] for d in self.difficulties]
  
  def to_dict(self) -> dict:
    return {
      "categories": self.categories,
      "difficulties": self.difficulties,
      "port": self.port
    }