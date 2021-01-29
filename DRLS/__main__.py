# -*- coding: utf-8
import sys
import time

# 系统路径进入到上层目录，可以引用上层目录的库
sys.path.append("..")
sys.path.append(".")
from DRLS.Environment import *
from DRLS.Graph import *
from DRLS.utils import *
from DRLS.TSN_schedule import *
# from Data.RingSpecific import *
from DRLS.param import *

class Main:
    def __init__(self):
        self.env = None
        self.path = None
        self.start = -1
        self.end = -1
        self.cycle = -1
        self.length = -1
        self.deadline = -1
        self.delay = -1
        self.schedule = None

    def action(self, dfs=0):
        self.start, self.end, self.cycle, edge_mat, self.length, self.deadline = \
            self.env.translate_data_to_heuristic_inputs()
        self.path = None

        # dfs找到所有可用路由，bfs找到最短路由
        edge_path = self.find_path_bfs(edge_mat)
        # 找到路由并分配时隙
        delay, self.path = self.env.graph.select_time_slot_no_waiting(edge_path, self.cycle)
        assert self.path is not None
        if len(self.path) == 0:
            return False
        # 将调度表格转化为GCL表项
        self.schedule.update(self.env.cur_tt_flow_id, self.path)

        # 维护网络资源
        # print(self.env.cur_tt_flow_id, self.start, self.end, self.cycle)
        for [edge, queueID, receive_time_slot, send_time_slot] in self.path:
            # print("  ", edge.id, queueID, receive_time_slot, send_time_slot)
            edge.occupy_queue_and_time_slot(queueID, receive_time_slot, send_time_slot, self.cycle)
        return True

    def find_path_bfs(self, edge_mat):
        tree = {}
        cur_layer = []
        visited = set()
        edge_num = len(self.env.graph.edges)
        for edge in self.env.graph.edges.values():
            if edge.is_source_edge:
                cur_layer.append(edge.id)
                visited.add(edge.id)
        des = -1
        print()
        while des == -1:
            assert len(cur_layer) > 0
            next_layer = []
            for i in cur_layer:
                if self.env.graph.edges[i].is_destination_edge:
                    des = i
                    break
                for j in range(edge_num):
                    if edge_mat[i][j] == 1 and j not in visited and \
                            (self.env.graph.edges[j].is_destination_edge or self.env.graph.edges[j].start_node.type > 0):
                        tree[j] = i
                        next_layer.append(j)
                        visited.add(j)
            cur_layer = next_layer
        edge_path = [self.env.graph.edges[des]]
        while des in tree:
            edge_path.insert(0, self.env.graph.edges[tree[des]])
            des = tree[des]
        return edge_path

    def find_time_slot_fastest(self, edge, cycle):
        time_slot = -1
        for pos in range(cycle):
            flag = True
            while pos < 1024 and flag:
                if edge.time_slot_available[pos] == 0:
                    flag = False
                pos += cycle
            if flag:
                time_slot = pos % cycle
                break
        return time_slot

    def find_time_slot_smart(self, edge):
        return edge.find_time_slot_heuristic(-1, self.cycle, self.length, self.deadline)[0]


def main():
    input_file = args.data_path
    output_directory = args.output_directory
    # print(input_file, output_directory)
    actor_agent = Main()
    tsn_info = json.load(open(input_file, encoding='utf-8'))
    actor_agent.env = Environment(tsn_info)  # DataGenerater(node_num))
    actor_agent.schedule = TSN_Schedule(actor_agent.env.graph, args.all_queue_count)
    actor_agent.schedule.init_from_info_node(actor_agent.env.graph.node_info)
    start_time = time.time()
    flow_number = 1
    info_record = {}
    while actor_agent.action():
        end_time = time.time()
        #print("flow_number", flow_number, "cycle", actor_agent.cycle, "time", end_time - start_time,
        #      "hop", len(actor_agent.path), "delay", actor_agent.delay, "usage", actor_agent.env.edge_usage())
        info_record[flow_number] = [flow_number, actor_agent.cycle, end_time - start_time, len(actor_agent.path), actor_agent.delay]
        if not actor_agent.env.enforce_next_query():
            break
        flow_number += 1
    # actor_agent.schedule.show()
    actor_agent.schedule.write_result(output_directory)

    # data_genes = RingSpecificGenerater()
    # if not os.path.exists(f'../resource/PCL_NetWork/test'):
    #     os.mkdir(f'../resource/PCL_NetWork/test')
    # for i in range(1, 2):
    #     node_num = 10
    #     data_genes.gene_all(node_num=node_num, eps=0.35, rand_min=5, rand_max=10, tt_num=8,
    #                        delay_min=64, delay_max=512, pkt_min=72, pkt_max=1526, hop=1, dynamic=True)
    #     data_genes.transform_schedule_to_node_info(actor_agent.schedule.result)
    #     data_genes.write_to_file(filename=f"PCL_NetWork/test/{i}")
    # return len(info_record) == len(actor_agent.env.tt_queries), actor_agent.env.edge_usage(), time.time() - start_time
    return 0, "success"


if __name__ == '__main__':
    main()

