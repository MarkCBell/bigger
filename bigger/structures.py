""" A module of data structures. """

from collections import defaultdict
from typing import Generic, TypeVar, Iterable, Iterator, List

X = TypeVar("X")


class UnionFind(Generic[X]):
    """ A fast union--find data structure. Given items must be hashable. """

    def __init__(self, items: Iterable[X]) -> None:
        self.items = items
        self.parent = dict((item, item) for item in items)
        self.rank = dict((item, 0) for item in items)

    def __iter__(self) -> Iterator[List[X]]:
        """ Iterate through the groups of self. """
        groups = defaultdict(list)
        for item in self.items:
            groups[self(item)].append(item)
        return iter(groups.values())

    def __len__(self) -> int:
        return sum(1 if self.parent[item] == item else 0 for item in self.parent)

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return ", ".join("{" + ", ".join(str(item) for item in g) + "}" for g in self)

    def __call__(self, x: X) -> X:
        """ Find the root of x. Two items are in the same group iff they have the same root. """
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:
            x, self.parent[x] = self.parent[x], root
        return root

    def union2(self, x: X, y: X) -> None:
        """ Combine the class containing x and the class containing y. """
        rx, ry = self(x), self(y)
        if self.rank[x] > self.rank[y]:
            self.parent[ry] = rx
        elif self.rank[x] < self.rank[y]:
            self.parent[rx] = ry
        elif rx != ry:
            self.parent[ry] = rx
            self.rank[rx] += 1

    def union(self, *args: X) -> None:
        """ Combine all of the classes containing the given items. """
        for item in args:
            self.union2(args[0], item)
