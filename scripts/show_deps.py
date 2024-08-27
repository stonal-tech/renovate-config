#!/usr/bin/env python3

import json
import logging
import re
from pathlib import Path
from typing import Dict, List

EXTEND_PATTERN: re.Pattern = re.compile(r".*\/([a-z0-9-]+)$")

logging.basicConfig(level=logging.INFO)


class Node:
    """A node in the dependency graph."""

    def __init__(self, name: str):
        self.name: str = name
        self.children: List[Node] = []
        self.depth = 0

    def add_child(self, child: "Node"):
        self.children.append(child)

    def __str__(self):
        return f"{self.name}"


nodes: Dict[str, Node] = {}


def get_node(name: str) -> Node:
    """Get a node by name, creating it if it doesn't exist."""
    if name not in nodes:
        nodes[name] = Node(name)
    return nodes[name]


for file in [f for f in Path(".").glob("*.json") if not f.name.startswith(".")]:
    logging.info("Parsing %s...", file)
    j = json.loads(file.read_text())
    dst_name = file.name.rsplit(".", 1)[0]
    dst_node = get_node(dst_name)

    extends: List[str] = j.get("extends", [])
    if not extends:
        logging.info("  No extends found")
        continue

    for e in extends:
        match = EXTEND_PATTERN.match(e)
        if match:
            src_name = match.group(1)
        else:
            src_name = e

        src_node = get_node(src_name)
        src_node.add_child(dst_node)


logging.info("Calculating depth")
should_continue = True
while should_continue:
    should_continue = False
    for node in nodes.values():
        for child in node.children:
            if child.depth < node.depth + 1:
                child.depth = node.depth + 1
                logging.info(
                    "  %s switches to depth %d because it is the a child of %s (%d)",
                    child.name,
                    child.depth,
                    node.name,
                    node.depth,
                )
                should_continue = True


sorted_nodes = sorted(nodes.values(), key=lambda n: n.depth)


output = """# Renovate dependencies
Documentation is [on notion](https://www.notion.so/Renovate-f455c421fc084ab38bf3145d243f7833).

```mermaid
graph TD;
"""

for node in sorted_nodes:
    for child in node.children:
        output += f'{node.name}("{node}") --> {child.name}("{child}")\n'

output += """```"""

Path("README.md").write_text(output, encoding="utf-8")
