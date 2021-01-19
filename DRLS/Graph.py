# -*- coding: utf-8
from DRLS.Node import *
from DRLS.Edge import *
import json
import sys

import os
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"

from Edge import Edge

sys.path.append("../resource")
sys.path.append("../zcm")
from param import *
# from Data.Ladder import *


class Graph:
    def __init__(self, tsn_input=None):
        self.edge_info = None
        self.adjacent_edge_matrix = []
        self.reachable_edge_matrix = []
        self.distance_edge_matrix = []
        self.start_node = []
        self.end_node = []
        self.nodes = {}
        self.edges = {}
        self.node_to_edge = {}
        self.node_info = tsn_input["nodes"]
        self.edge_info = tsn_input["links"]
        self.depth = 8

        # self.data_generater = DataGenerater()
        # 需要先调用 load_adjacent_matrix 生成邻接矩阵，该函数包含了生成节点个数

        self.init()
        # print(len(self.edges))

    def init(self):
        self.load_nodes()
        self.load_edge_info()
        # 在此处更新 depth 会引起报错
        # self.update_graph_depth()
        self.get_reachable_edge_matrix()
        self.get_distance_edge_matrix()
        # self.update_graph_depth()

    def load_nodes(self):
        # 读取的 info 是一个字典，也可以改成下述方式
        for node in self.node_info:
            node_id = node["id"]
            tsQueueIDs = node["tsBusinessQueues"]
            ports = node["ports"]
            self.nodes[node_id] = Node(node_id, ports, tsQueueIDs)

    def load_edge_info(self):
        # print(self.edge_info)
        node_len = len(self.nodes)
        start_from_node = {}
        end_with_node = {}
        self.edges = {}
        self.node_to_edge = {}
        for node_id in self.nodes:
            start_from_node[node_id] = []
            end_with_node[node_id] = []
        for edge in self.edge_info:
            edge_id = edge["id"]
            src_node = self.nodes[edge["sourceNodeId"]]
            src_port = src_node.ports[edge["sourcePort"]]
            dst_node = self.nodes[edge["destNodeId"]]
            dst_port = dst_node.ports[edge["destPort"]]
            self.edges[edge_id] = Edge(edge_id, src_node, src_port, dst_node, dst_port)
            # TODO 需要修改，因为当前环境下两个网络节点之间可能会有重复链路
            self.node_to_edge[(src_node.id, dst_node.id)] = edge_id
            start_from_node[src_node.id].append(edge_id)
            end_with_node[dst_node.id].append(edge_id)
        print("edge number: ", len(self.edges))
        # 初始化边邻接矩阵
        edge_number = len(self.edges)
        self.adjacent_edge_matrix = np.zeros([edge_number, edge_number])
        for i in range(edge_number):
            for j in start_from_node[self.edges[i].end_node.id]:
                self.adjacent_edge_matrix[i][j] = 1
        # for edge in self.edges.values():
        #     print(edge.id, edge.start_node.id, edge.end_node.id)
        # print(self.adjacent_edge_matrix)

    # TODO 这个函数用来计算网络的宽度，但是写的有问题，用的地方也有问题，暂时搁置，等以后修改
    def update_graph_depth(self):
        one_step = np.array(self.adjacent_edge_matrix)
        pre_step = one_step
        depth = 1
        while depth < self.depth:
            cur_step = np.matmul(pre_step, one_step) + np.matmul(one_step, pre_step) + one_step + pre_step
            cur_step[cur_step >= 1] = 1
            if np.sum(cur_step) == np.sum(pre_step):
                break
            pre_step = cur_step
            depth += 1

        self.depth = depth
        args.max_depth = depth
        # print("graph maximum width", depth)
        return depth

    # self.reachable_edge_matrix[layer][start][cur_edge]表示start能否最短经过layer跳到哪cur_edge
    # TODO get_reachable_edge_matrix() 和get_distance_edge_matrix()都可以改成弗洛伊德算法
    def get_reachable_edge_matrix(self):
        edge_num = len(self.edges)
        self.reachable_edge_matrix = [np.zeros([edge_num, edge_num]) for _ in range(self.depth)]
        for start in range(edge_num):
            # print(start)
            visited_edge = {start}
            cur_list = [start]
            for layer in range(self.depth):
                next_list = []
                for cur_edge in cur_list:
                    self.reachable_edge_matrix[layer][start][cur_edge] = 1
                    for adjacent in range(edge_num):
                        if self.adjacent_edge_matrix[cur_edge][adjacent] == 1 and \
                                adjacent not in visited_edge:
                            visited_edge.add(adjacent)
                            next_list.append(adjacent)
                cur_list = next_list
        # for i in range(self.depth):
        #     print(i, self.reachable_edge_matrix[i])
        #     print(i, np.sum(self.reachable_edge_matrix[i]))

    # distance_edge_matrix的含义是每条边到每一个节点的距离
    def get_distance_edge_matrix(self):
        edge_num = len(self.edges)
        node_num = len(self.nodes)
        self.distance_edge_matrix = {}
        for edge_id in self.edges:
            self.distance_edge_matrix[edge_id] = {}
            for node_id in self.nodes:
                self.distance_edge_matrix[edge_id][node_id] = 9999
        for i in range(edge_num):
            visited_edge = {i}
            cur_list = [self.edges[i]]
            dis = 1
            self.distance_edge_matrix[i][self.edges[i].start_node.id] = 0
            while len(cur_list) > 0:
                next_list = []
                for cur_edge in cur_list:
                    self.distance_edge_matrix[i][cur_edge.end_node.id] = min(self.distance_edge_matrix[i][cur_edge.end_node.id], dis)
                    for adjacent in range(edge_num):
                        if self.adjacent_edge_matrix[cur_edge.id][adjacent] == 1 and adjacent not in visited_edge:
                            visited_edge.add(adjacent)
                            next_list.append(self.edges[adjacent])
                cur_list = next_list
                dis += 1

    def delete_edge(self, edge_id, tt_flow_to_edge):
        self.adjacent_node_matrix[edge_id[0]][edge_id[1]] = 0
        self.init()
        for tt_flow in tt_flow_to_edge.values():
            for info in tt_flow:
                edge_tuple = info[0]
                time_slot = info[1]
                cycle = info[2]
                length = info[3]
                edge_id = self.node_to_edge[edge_tuple]
                # 因为所有的数据都重置了，所以要把所有的流再导入一遍
                self.edges[edge_id].occupy_time_slot(time_slot, cycle, length)

    def reset(self):
        for edge in self.edges.values():
            edge.reset()
        for node in self.nodes.values():
            node.reset()

    def select_time_slot_no_waiting(self, edge_path, flow_cycle):
        route = []
        for queueID in range(0, args.all_queue_count):
            for time_slot in range(0, flow_cycle):
                offset = 0
                for edge in edge_path:
                    receive_time_slot = time_slot + offset
                    send_time_slot = receive_time_slot + 1
                    if not edge.check_time_slot(receive_time_slot, send_time_slot, queueID, flow_cycle):
                        route = []
                        break
                    route.append([edge, queueID, receive_time_slot, send_time_slot])
                    offset += 1
                if len(route) > 0:
                    break
            if len(route) > 0:
                break
        return len(route), route


def main():
    graph = Graph()
    print("node")
    for i in range(len(graph.nodes)):
        print(i, end=": ")
        print(graph.nodes[i].tsQueueIDs)
    print("edge")
    for edge in graph.edges.values():
        print(edge.id, edge.start_node.id, ":", edge.start_port, edge.end_node.id, ":", edge.end_port)
    graph.edges[0].occupy_time_slot(0, 256, 1)
    graph.edges[0].occupy_time_slot(1, 256, 1)
    graph.edges[0].find_time_slot(0, 0, 128, 1, 1)
    # for c in graph.edges[0].time_slot_status:
    #     print(graph.edges[0].time_slot_status[c])
    print(graph.node_to_edge)


if __name__ == '__main__':
    main()
