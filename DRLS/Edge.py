# -*- coding: utf-8
import numpy as np
from DRLS.param import *


class Edge:
    def __init__(self, index, start_node, start_port, end_node, end_port, edge_speed, src_port_queues_info={}, queue_capacity=1):
        self.id = index
        self.start_node = start_node
        self.start_port = start_port
        self.end_node = end_node
        self.end_port = end_port
        self.is_source_edge = self.start_node.is_source_node
        self.is_destination_edge = self.end_node.is_destination_node
        self.global_cycle = args.global_cycle
        self.edge_speed = edge_speed
        # self.time_slot_available = np.ones([self.global_cycle * args.slot_per_millisecond])
        # self.time_slot_status = {}
        # self.max_cycle = max(args.tt_flow_cycles)
        # self.queue_status = [0 for i in range(8)]
        # TODO
        # for cycle in [i * args.slot_per_millisecond for i in args.tt_flow_cycles]:
        #     self.time_slot_status[cycle] = {i for i in range(cycle)}


    def occupy_single_time_slot(self, time_slot, cycle):
        for key in self.time_slot_status:
            pos = time_slot % key
            if pos in self.time_slot_status[key]:
                self.time_slot_status[key].remove(pos)
        pos = time_slot
        while pos < self.global_cycle:
            assert self.time_slot_available[pos] == 1
            for key in self.time_slot_status:
                if pos in self.time_slot_status[key]:
                    self.time_slot_status[key].remove(pos)
            self.time_slot_available[pos] = 0
            pos += cycle

    def occupy_time_slot(self, time_slot, cycle, length):
        # print("occupy", time_slot, cycle, length)
        for k in range(length):
            self.occupy_single_time_slot(time_slot + k, cycle)

    def occupy_queue_and_time_slot(self, queueID, receive_time_slot, send_time_slot, flow_cycle):
        total_time_slot_num = args.global_cycle * args.slot_per_millisecond
        cur_receive_time = receive_time_slot
        cur_send_time = send_time_slot
        while cur_send_time < total_time_slot_num:
            # 占用端口时隙，只需要一个时隙即可，用来发送报文
            assert self.start_port.port_status[cur_send_time] == 1
            self.start_port.port_status[cur_send_time] = 0
            for i in range(cur_receive_time, cur_send_time + 1):
                # 占用队列时隙，可能会占用多个时隙，用来存储报文
                assert self.start_port.queues[queueID].queue_status[i] == 1
                self.start_port.queues[queueID].queue_status[i] = 0
                cur_receive_time += flow_cycle
                cur_send_time += flow_cycle

    def check_time_slot(self, receive_time_slot, send_time_slot, queueID, flow_cycle):
        if queueID not in self.start_node.tsQueueIDs:
            return False
        if send_time_slot >= flow_cycle:
            return False
        total_time_slot_num = args.global_cycle * args.slot_per_millisecond
        cur_receive_time = receive_time_slot
        cur_send_time = send_time_slot
        # 端口在发送的那个时隙是空闲的
        flag = True
        while cur_send_time < total_time_slot_num:
            # 端口在发送的那个时隙是空闲的
            if self.start_port.port_status[cur_send_time] == 0:
                flag = False
            # 队列在转发前的所有时隙都是空闲的
            for i in range(cur_receive_time, cur_send_time + 1):
                if self.start_port.queues[queueID].queue_status[i] == 0:
                    flag = False
            if not flag:
                break
            cur_receive_time += flow_cycle
            cur_send_time += flow_cycle
        return flag

    # start_time表示目前已经使用的时间，offser表示目前所在的时隙
    def find_time_slot(self, start_time, offset, cycle, length, deadline):
        max_score = -120
        time_solt = -2
        # print(self.time_slot_status, cycle)
        for i in range(cycle):
            flag = True
            for k in range(length):
                if i + k not in self.time_slot_status[cycle]:
                    flag = False
            if not flag:
                continue
            if i > offset:
                delay = start_time + i - offset
            else:
                delay = start_time + i - offset + args.global_cycle
            if start_time == -1:
                delay = 0
            if delay > deadline:
                if time_solt < 0:
                    time_solt = -3
                continue
            score = 0
            for k in range(length):
                for key in self.time_slot_status:
                    pos = (i + k) % key
                    if pos in self.time_slot_status[key] and key != cycle:
                        score -= args.global_cycle / key
            score -= args.global_cycle * 2 / (deadline - delay + 1)
            # print(i, start_time, deadline - delay, score)
            if time_solt < 0 or max_score < score:
                time_solt = i
                max_score = score
        return time_solt, max_score

    # 找最快的时隙
    def find_time_slot_fast(self, start_time, offset, cycle, length, max_delay):
        min_delay = -120
        time_solt = -2
        delay = -1
        # print(self.time_slot_status, cycle)
        for i in range(cycle):
            flag = True
            for k in range(length):
                if i + k not in self.time_slot_status[cycle]:
                    flag = False
            if not flag:
                continue
            if i > offset:
                delay = start_time + i - offset
            else:
                delay = start_time + i - offset + args.global_cycle
            if start_time == -1:
                delay = 0
            if delay > max_delay:
                continue
            if time_solt == -2 or delay < min_delay:
                time_solt = i
                min_delay = delay
        return time_solt, -delay

    def find_time_slot_LD_old(self, start_time, cycle, length, max_delay):
        max_score = -120
        time_solt = -2
        # print(self.time_slot_status, cycle)
        for i in range(cycle):
            flag = True
            for k in range(length):
                if i + k not in self.time_slot_status[cycle]:
                    flag = False
            if not flag:
                continue
            delay = (i - start_time + args.global_cycle) % args.global_cycle
            if delay == 0:
                delay = args.global_cycle
            if start_time == -1:
                delay = 0
            if delay > max_delay:
                continue
            score = 0
            for k in range(length):
                for key in self.time_slot_status:
                    pos = (i + k) % key
                    if pos in self.time_slot_status[key] and key != cycle:
                        score -= args.global_cycle * 4 / key
            score -= delay
            if time_solt == -2 or max_score < score:
                time_solt = i
                max_score = score
        # print(max_time_slot_score)
        if time_solt == -3:
            print(start_time, cycle)
        return time_solt, max_score

    def reset_time_slot(self, time_slot, cycle=args.global_cycle):
        # print("reset", time_slot, cycle)
        for key in self.time_slot_status:
            if key >= cycle:
                pos = time_slot
                while pos < key:
                    self.time_slot_status[key].add(pos)
                    pos += cycle
            else:
                pos = time_slot % key
                if self.judge(pos, key):
                    self.time_slot_status[key].add(pos)
        pos = time_slot
        while pos < self.global_cycle:
            assert self.time_slot_available[pos] == 0
            self.time_slot_available[pos] = 1
            pos += cycle

    def judge(self, time_slot, cycle):
        pos = time_slot
        while pos < self.global_cycle:
            if self.time_slot_available[pos] == 0:
                return False
            pos += cycle
        return True

    def refresh(self):
        self.is_source_edge = self.start_node.is_source_node
        self.is_destination_edge = self.end_node.is_destination_node

    def reset(self):
        self.time_slot_available = [1 for _ in range(self.global_cycle)]
        self.refresh()
