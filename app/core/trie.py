from __future__ import annotations


class TrieNode:
    def __init__(self) -> None:
        self.children: dict[str, TrieNode] = {}
        self.is_word = False


class Trie:
    """A handwritten trie for prefix-based fuzzy search."""

    def __init__(self) -> None:
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word.lower():
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_word = True

    def starts_with(self, prefix: str, limit: int = 10) -> list[str]:
        node = self.root
        normalized = prefix.lower()

        for ch in normalized:
            if ch not in node.children:
                return []
            node = node.children[ch]

        result: list[str] = []
        self._collect(node, normalized, result, limit)
        return result

    def _collect(self, node: TrieNode, path: str, out: list[str], limit: int) -> None:
        if len(out) >= limit:
            return

        if node.is_word:
            out.append(path)

        for ch, child in node.children.items():
            if len(out) >= limit:
                return
            self._collect(child, path + ch, out, limit)
