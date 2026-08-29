from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ToolDefination:
    name : str
    description: str
    function : Callable[..., Any]


class ToolRegistry:
    def __init__(self):
        self.__tools: dict[str, ToolDefination] = {}

    def register(
            self,
            name: str,
            description: str,
            function: Callable[..., Any]
    ) -> None:
        if name in self.__tools:
            raise ValueError(f"Tool already registeres: {name}")
        

        self.__tools[name]= ToolDefination(
            name=name,
            description=description,
            function=function
        )  

    def get(self, name:str) -> ToolDefination:
        tool = self.__tools.get(name)

        if tool is None:
            raise KeyError(f"Unknown tool: {name}")

        return tool

    def list_tools(self) -> list[ToolDefination]:
        return list(self.__tools.values())

    def has(self, name:str) -> bool:
        return name in self.__tools