
from hypothesis import settings
import hypothesis.strategies as st
from hypothesis.stateful import Bundle, RuleBasedStateMachine, rule

import bigger

@settings(max_examples=100)
class UnionFindRules(RuleBasedStateMachine):
    Unions = Bundle("unions")

    @rule(target=Unions, items=st.lists(elements=st.integers(), min_size=1, unique=True))
    def initialize(self, items):
        return bigger.UnionFind(items)

    @rule(data=st.data(), union=Unions)
    def find(self, data, union):
        a = data.draw(st.sampled_from(union.items))
        union(a)

    @rule(union=Unions)
    def iterate(self, union):
        assert set(sum(union, [])) == set(union.items)

    @rule(union=Unions, data=st.data())
    def union2(self, data, union):
        a = data.draw(st.sampled_from(union.items))
        b = data.draw(st.sampled_from(union.items))
        orig_len = len(union)
        union.union2(a, b)
        assert union(a) == union(b)
        assert len(union) in (orig_len, orig_len - 1)

    @rule(data=st.data(), union=Unions)
    def union(self, data, union):
        items = data.draw(st.lists(elements=st.sampled_from(union.items)))
        union.union(*items)
        for item in items:
            assert union(item) == union(items[0])

TestUnionFind = UnionFindRules.TestCase
