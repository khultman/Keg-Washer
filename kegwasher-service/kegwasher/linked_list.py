# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Kyle Hultman <khultman@gmail.com>


class Node(object):
    def __init__(self, data):
        self.data = data
        self.next = None
        self.previous = None


class CircularDoublyLinkedList(object):
    def __init__(self):
        self.head = None

    @property
    def data(self):
        cur_node = self.head
        if cur_node is None:
            return None
        return cur_node.data

    def get_node(self, index):
        cur_node = self.head
        for i in range(index):
            cur_node = cur_node.next
            if cur_node == self.head:
                return None
            return cur_node

    def insert_after(self, ref_node, new_node):
        new_node.previous = ref_node
        new_node.next = ref_node.next
        new_node.next.previous = new_node
        ref_node.next = new_node

    def insert_before(self, ref_node, new_node):
        self.insert_after(ref_node.previous, new_node)

    def append(self, new_node=None):
        if self.head is None:
            new_node.next = new_node
            new_node.previous = new_node
            self.head = new_node
        else:
            self.insert_after(self.head.previous, new_node)

    def push(self, new_node=None):
        self.append(new_node)
        self.head = new_node

    def next(self):
        self.head = self.head.next

    def previous(self):
        self.head = self.head.previous
