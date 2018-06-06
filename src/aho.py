# -*- coding: utf-8 -*-


class Vertex(object):
    def __init__(self):
        self.char = None
        self.parent = -1
        self.children = {}
        self.word_id = -1
        self.leaf = None

        self.suffix_link = -1
        # 加速查找 word 使用
        self.end_word_link = -1


class Aho(object):
    def __init__(self):
        self._root = 0
        self._trie = [Vertex()]
        self._word_id_2_info = {}    # {word_id: (length, value)}
        self._cur_word_id = -1
        self._added_word = set()     # 只需要在 make_automation 之前存在，之后可以删除
        self._has_made_automation = False   # 如果在调用了 make_automation 之后，禁止调用 add_word

    def _gen_word_id(self):
        self._cur_word_id += 1
        return self._cur_word_id

    def add_word(self, word, value):

        assert not self._has_made_automation, u"调用了 make_automation 之后，禁止调用 add_word"

        if not isinstance(word, unicode):
            word = word.decode("utf8")

        if word in self._added_word:
            return False

        cur_vertex_idx = self._root
        for _char in word:
            if _char not in self._trie[cur_vertex_idx].children:
                self._trie.append(Vertex())
                # node is the vertex created above
                node = self._trie[-1]
                node.char = _char
                node.parent = cur_vertex_idx
                self._trie[cur_vertex_idx].children[_char] = len(self._trie) - 1
            cur_vertex_idx = self._trie[cur_vertex_idx].children[_char]

        self._added_word.add(word)
        word_id = self._gen_word_id()
        self._trie[cur_vertex_idx].leaf = True
        self._trie[cur_vertex_idx].word_id = word_id
        self._word_id_2_info[word_id] = (len(word), value)
        return True

    def make_automation(self):
        assert not self._has_made_automation, u"不可重复调用make_automation"
        self._has_made_automation = True
        # 至此可以删除_added_word
        del self._added_word

        queue = [self._root]
        while queue:
            vertex_idx = queue.pop(0)
            self._calculate_suffix(vertex_idx)
            vertex = self._trie[vertex_idx]
            for _, v in vertex.children.iteritems():
                queue.append(v)

    def _calculate_suffix(self, vertex_idx):
        if vertex_idx == self._root:
            self._trie[vertex_idx].suffix_link= self._root
            self._trie[vertex_idx].end_word_link = self._root
            return

        if self._trie[vertex_idx].parent == self._root:
            self._trie[vertex_idx].suffix_link = self._root
            if self._trie[vertex_idx].leaf:
                self._trie[vertex_idx].end_word_link = vertex_idx
            else:
                self._trie[vertex_idx].end_word_link = self._root
            return

        cur_better_vertex = self._trie[self._trie[vertex_idx].parent].suffix_link
        ch_vertex = self._trie[vertex_idx].char

        while True:
            if ch_vertex in self._trie[cur_better_vertex].children:
                self._trie[vertex_idx].suffix_link = self._trie[cur_better_vertex].children[ch_vertex]
                break

            if cur_better_vertex == self._root:
                self._trie[vertex_idx].suffix_link = self._root
                break

            cur_better_vertex = self._trie[cur_better_vertex].suffix_link

        if self._trie[vertex_idx].leaf:
            self._trie[vertex_idx].end_word_link = vertex_idx
        else:
            self._trie[vertex_idx].end_word_link = self._trie[self._trie[vertex_idx].suffix_link].end_word_link

    def iter(self, text):
        current_state = self._root
        for j in range(len(text)):
            while True:
                if text[j] in self._trie[current_state].children:
                    current_state = self._trie[current_state].children[text[j]]
                    break

                if current_state == self._root:
                    break
                current_state = self._trie[current_state].suffix_link

            check_state = current_state

            while True:
                check_state = self._trie[check_state].end_word_link

                if check_state == self._root:
                    break

                yield (j + 1 - self._word_id_2_info[self._trie[check_state].word_id][0],  j + 1), self._word_id_2_info[self._trie[check_state].word_id][1]

                check_state = self._trie[check_state].suffix_link


if __name__ == '__main__':
    aho = Aho()
    aho.add_word("b", "b")
    aho.add_word("ab", "ab")
    aho.add_word("bab", "bab")
    aho.make_automation()
    print list(aho.iter("ababdegh"))

    from graphviz import Digraph
    from collections import deque
    graph = Digraph(comment='Visualization of aho-corasick', node_attr={"style": "filled", "color": "grey", "fontcolor": "white", "fontsize": "20"})

    graph.node("root", "ROOT")
    q = deque([0])

    while q:
        node_index = q.popleft()
        node = aho._trie[node_index]
        p_name = "%s_%s" % (node_index, node.char) if node_index != 0 else "root"
        for char, index in sorted([(k, v) for k, v in node.children.iteritems()], key=lambda x: x[1]):
            child_node = aho._trie[index]
            name = "%s_%s" % (index, char)
            graph.node(name, char, shape="doublecircle" if child_node.word_id != -1 else "circle")

            graph.edge(p_name, name)

            q.append(index)

        suffix_name = ("%s_%s" % (node.suffix_link, aho._trie[node.suffix_link].char)) if node.suffix_link != 0 else "root"
        graph.edge(p_name, suffix_name, color="red", constraint="false")

    graph.render('./ac_visual.gv', view=True)

