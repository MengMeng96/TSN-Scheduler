# coding=utf-8
from DRLS.param import *


class Port:
    def __init__(self, port_info, queue_count=args.all_queue_count):
        self.queues = {}
        self.id = port_info["id"]
        self.port_status = [1 for _ in range(args.global_cycle * args.slot_per_millisecond)]
        for queue_id in range(queue_count):
            self.queues[queue_id] = Queue(queue_id)

    # TODO 写一个函数，将初始化和读取已有信息分开
        if "queues" in port_info:
            for queue_info in port_info["queues"]:
                print(queue_info)
                queue_id = queue_info["id"]
                time_slot_length = 1000 / args.slot_per_millisecond  # us
                for interval in queue_info["occupiedTimeIntervals"]:
                    start_time = interval["startTime"]
                    end_time = interval["endTime"]
                    for time_slot in range(int(start_time / time_slot_length),
                                           int((end_time + time_slot_length - 1) / time_slot_length)):
                        self.queues[queue_id].queue_status[time_slot] = 0
                        self.port_status[time_slot] = 0


class Queue:
    def __init__(self, queue_id, queue_capacity=1):
        self.id = queue_id
        self.queue_status = [queue_capacity for _ in range(args.global_cycle * args.slot_per_millisecond)]


class Node:
    def __init__(self, index, ports_info, tsQueueIDs, type, capacity=1):
        self.id = index
        self.buffer_capacity = capacity
        self.type = type
        self.tsQueueIDs = tsQueueIDs
        self.is_source_node = 0
        self.is_destination_node = 0

        # 创建port，并且把singleCalculate里面含有的队列信息存储起来
        self.ports = {}
        self.init_ports(ports_info)

    # 链路与端口一一对应，queueIDs是链路起始端口的TS专用队列的编号，每个队列都可以存储报文
    # 在不排队策略下，每个队列同一时间最多只能存储一个报文，这个性质体现在self.queue_capacity=1中
    def init_ports(self, port_infos):
        self.ports = {}
        for port_info in port_infos:
            port_id = port_info["id"]
            self.ports[port_id] = Port(port_info)

    def set_source_node(self):
        self.is_source_node = 1

    def set_destination_node(self):
        self.is_destination_node = 1

    def unset_source_node(self):
        self.is_source_node = 0

    def unset_destination_node(self):
        self.is_destination_node = 0

    def check_buffer(self, start, cycle):
        for pos in range(args.global_cycle):
            if pos % cycle == start:
                if self.buffer_avaiable[pos] - 1 < 0:
                    return False
        return True

    def occupy_buffer(self, start, cycle):
        for pos in range(args.global_cycle):
            if pos % cycle == start:
                self.buffer_avaiable[pos] -= 1

    def check_buffers(self, start, end, cycle):
        for pos in range(args.global_cycle):
            offset = pos % cycle
            if (start < end and start < offset <= end) or \
                    (start > end and (offset <= end or start < offset)):
                if self.buffer_avaiable[pos] - 1 < 0:
                    return False
        return True

    def occupy_buffers(self, start, end, cycle):
        # 不占用开始时隙的缓存，因为开始时隙的缓存是在确定上一条边的时候占用的
        for pos in range(args.global_cycle):
            offset = pos % cycle
            if (start < end and start < offset <= end) or \
                    (start > end and (offset <= end or start < offset)):
                self.buffer_avaiable[pos] -= 1

    def reset(self):
        self.is_source_node = 0
        self.is_destination_node = 0
        self.buffer_avaiable = [self.buffer_capacity for _ in range(args.global_cycle)]

    def show(self, cycle):
        for i in range(args.global_cycle):
            print(self.buffer_avaiable[i], end=' ')
            if i % cycle == cycle - 1:
                print()

def main():
    node = Node(0, 1)
    node.check_buffers(61, 3, 64)
    node.occupy_buffers(3, 61, 64)
    for i in range(args.global_cycle):
        print(node.buffer_avaiable[i], end=' ')
        if i % 64 == 63:
            print()


if __name__ == '__main__':
    main()