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
  requirements: list[int] | None = None

  def to_dict(self) -> dict:
    return {
      "description": self.description,
      "cost": self.cost,
      "requirements": self.requirements
    }


@dataclass
class Service:
  name: str
  path: str
  port: str

  def to_dict(self) -> dict:
    return {
      "name": self.name,
      "path": self.path,
      "port": self.port
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
    flags = []
    for flag in d.pop("flags"):
      if isinstance(flag, str):
        flags.append(Flag(flag))
      else:
        flags.append(Flag(**flag))

    hints = d.pop("hints")
    if hints is not None:
      hints = [Hint(**hint) for hint in hints]

    return cls(
      flags=flags,
      hints=hints,
      services=services,
      **d
    )
  
  def to_dict(self) -> dict[str, dict | list[dict]]:
    return {
      "challenge": {
        "name": self.name,
        "description": self.description,
        "difficulty": self.difficulty,
        "category": self.category,
        "author": self.author,
        "discord": self.discord,
        "flags": [flag.to_dict() for flag in self.flags],
        "hints": [hint.to_dict() for hint in self.hints] if self.hints is not None else None,
        "files": self.files,
        "requirements": self.requirements
      },
      "services": {
        service.name: service.to_dict()
        for service in self.services
      } if self.services is not None else None
    }


@dataclass
class Config:
  categories: list[str]
  difficulties: list[dict[str, str | int]]
  port: int
  name: str | None = None

  @property
  def diff_names(self) -> list[str]:
    return [d["name"] for d in self.difficulties]
  
  def to_dict(self) -> dict:
    return {
      "categories": self.categories,
      "difficulties": self.difficulties,
      "port": self.port,
      "name": self.name
    }