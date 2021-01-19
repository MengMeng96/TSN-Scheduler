# coding=utf-8
import json
import numpy as np
import os
from DRLS.param import *

import sys
# sys.path.append("../jhy")

SCHE_FILE = '../resource/data-2-hop/schedule.json'


class TSN_Schedule:
    def __init__(self, graph, queue_count):
        self.row_result = {}
        self.result = None
        self.paths = []
        self.time_table = {}

        # init result
        time_slot_length = 1000 / args.slot_per_millisecond  # us
        for (node_id, node_info) in graph.nodes.items():
            cur_node = {"nodeId": node_id,
                        "ports": {}}
            self.time_table[node_id] = {}
            for (port_id, port_info) in node_info.ports.items():
                cur_port = {"portId": port_id,
                            "adminBaseTime": 0,
                            "adminCycleTimeExt": 0,
                            "gcls": [{"gclId": 0,
                                      "timeDuration": args.global_cycle * time_slot_length,
                                      "holdPMac": False,
                                      "gateStates": [0 for _ in range(args.all_queue_count)]
                                      }]}
                cur_node["ports"][port_id] = cur_port
                # 初始化time_table
                self.time_table[node_id][port_id] = {}
            self.row_result[node_id] = cur_node

    def init_from_info_node(self, node_infos):
        for node_info in node_infos:
            node_id = node_info["id"]
            for port_info in node_info["ports"]:
                port_id = port_info["id"]
                if "queues" in port_info:
                    for queue_info in port_info["queues"]:
                        queue_id = queue_info["id"]
                        time_slot_length = 1000 / args.slot_per_millisecond  # us
                        for interval in queue_info["occupiedTimeIntervals"]:
                            start_time = interval["startTime"]
                            end_time = interval["endTime"]
                            send_time_slot = int((end_time + time_slot_length - 1) / time_slot_length) - 1
                            if send_time_slot not in self.time_table[node_id][port_id]:
                                self.time_table[node_id][port_id][send_time_slot] = []
                            self.time_table[node_id][port_id][send_time_slot].append(queue_id)
                            self.row_result[node_id]["ports"][port_id]["gcls"] = \
                                self.time_table_to_GCLs(self.time_table[node_id][port_id])

    def update(self, tt_flow_id, path):
        # 维护路径信息，即self.path
        pre_node_id = -1
        pre_link_id = -1
        # TODO 要按照API的要求写输出，但是API现在有点问题
        cur_paths = {"flowId": tt_flow_id,
                     "path": []}
        cur_path = {"nodes": [],
                    "links": []}
        for [edge, _, _, _] in path:
            # 维护paths，这个保存了路由信息
            cur_path["nodes"].append({"id": edge.start_node.id,
                                      "pre": pre_node_id})
            cur_path["links"].append({"id": edge.id,
                                      "pre": pre_link_id})
            pre_node_id = edge.start_node.id
            pre_link_id = edge.id
        cur_path["nodes"].append({"id": edge.end_node.id,
                                  "pre": pre_node_id})
        # cur_paths是当前流的组播调度结果，cur_path是组播中的一条路由的信息
        cur_paths["path"].append(cur_path)
        # self.path是所有流的调度结果
        self.paths.append(cur_paths)

        # 维护GCL信息，即self.result
        for [edge, queueID, receive_time_slot, send_time_slot] in path:
            # 维护GCLs，这个保存了门控信息
            start_node = edge.start_node
            start_port = edge.start_port
        # 维护调度信息
            # 先维护时间表
            if send_time_slot not in self.time_table[start_node.id][start_port.id]:
                self.time_table[start_node.id][start_port.id][send_time_slot] = []
            self.time_table[start_node.id][start_port.id][send_time_slot].append(queueID)
            # 再用时间表转化GCL表项
            self.row_result[start_node.id]["ports"][start_port.id]["gcls"] = \
                self.time_table_to_GCLs(self.time_table[start_node.id][start_port.id])

    # 将时间表转化为GCL表项
    def time_table_to_GCLs(self, time_table):
        # print(time_table)
        time_slot_length = 1000 / args.slot_per_millisecond # us
        GCLs = []
        pre_time = 0
        GCL_index = 0
        for (cur_time, queueIDs) in sorted(time_table.items()):
            # print(cur_time, time_table[cur_time])
            # 将两个时隙时间的空隙填一下
            if cur_time - pre_time > 0:
                pre_gcl = {"gclId": GCL_index,
                           "timeDuration": (cur_time - pre_time) * time_slot_length,
                           "holdPMac": False,
                           "gateStates": [0 for _ in range(args.all_queue_count)]}
                GCLs.append(pre_gcl)
                GCL_index += 1
            # 打开队列，维持一个时隙（20us）
            cur_gcl = {"gclId": GCL_index,
                       "timeDuration": 1 * time_slot_length,
                       "holdPMac": True,
                       "gateStates": [0 for _ in range(args.all_queue_count)]}
            for open_queue_id in queueIDs:
                cur_gcl["gateStates"][open_queue_id] = 1
            GCLs.append(cur_gcl)
            pre_time = cur_time + 1
            GCL_index += 1

        cur_time = args.global_cycle
        if cur_time - pre_time > 0:
            pre_gcl = {"gclId": GCL_index,
                       "timeDuration": (cur_time - pre_time) * time_slot_length,
                       "holdPMac": False,
                       "gateStates": [0 for _ in range(args.all_queue_count)]}
            GCLs.append(pre_gcl)

        return GCLs

    def row_result_to_result(self):
        self.result = []
        for (node_id, node_info) in self.row_result.items():
            cur_node = {"nodeId": node_id,
                        "ports": []}
            for (port_id, port_info) in node_info["ports"].items():
                print(port_info)
                cur_port = {"portId": port_id,
                            "adminBaseTime": 0,
                            "adminCycleTimeExt": 0,
                            "gcls": port_info["gcls"]}
                cur_node["ports"].append(cur_port)
            self.result.append(cur_node)
        return self.result

    def show(self, file_path):
        self.row_result_to_result()
        for node_info in self.result:
            node_id = node_info["nodeId"]
            print("node id :", node_id)
            for port_info in node_info["ports"]:
                port_id = port_info["portId"]
                print("    ", "port id :", port_id, "adminBaseTime", port_info["adminBaseTime"])
                for gcl_info in port_info["gcls"]:
                    gcl_id = gcl_info["gclId"]
                    print("        ", "gclID:", gcl_id,
                          "timeDuration:", gcl_info["timeDuration"],
                          "gates:", gcl_info["gateStates"])
        for flow_info in self.paths:
            flow_id = flow_info["flowId"]
            print("flow id:", flow_id)
            for path in flow_info["path"]:
                print("nodes")
                for node in path["nodes"]:
                    print("    ", "pre node:", node["pre"], "cur node:", node["id"])
                print("links")
                for link in path["links"]:
                    print("    ", "pre link:", link["pre"], "cur link:", link["id"])

        output = {"result": self.result,
                  "paths": self.paths}
        if not os.path.exists(file_path):
            os.mkdir(file_path)
        json.dump(output, open(f'{file_path}/output.json', "w"), indent=4)


if __name__ == '__main__':
    ss = TSN_Schedule(10)

    ss.write_json()
