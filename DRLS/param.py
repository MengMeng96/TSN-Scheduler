#!/usr/bin/python
# -*- coding: UTF-8 -*-

import argparse

parser = argparse.ArgumentParser(description='DAG_ML')

# -- Basic --
parser.add_argument('--seed', type=int, default=42,
                    help='random seed (default: 42)')
parser.add_argument('--eps', type=float, default=1e-6,
                    help='epsilon (default: 1e-6)')

# -- Learning --
parser.add_argument('--policy_input_dim', type=int, default=8,
                    help='policy input dimensions to graph embedding (default: 5)')
parser.add_argument('--output_dim', type=int, default=8,
                    help='output dimensions throughout graph embedding (default: 8)')
parser.add_argument('--lr', type=float, default=0.001,
                    help='learning rate (default: 0.001)')
parser.add_argument('--gamma', type=float, default=1,
                    help='discount factor (default: 1)')
parser.add_argument('--num_agents', type=int, default=1,
                    help='Number of parallel agents (default: 16)')
parser.add_argument('--num_ep', type=int, default=10000000,
                    help='Number of training epochs (default: 10000000)')
parser.add_argument('--max_depth', type=int, default=8,
                    help='Maximum depth of root-leaf message passing (default: 8)')
parser.add_argument('--hid_dims', type=int, default=[16, 8], nargs='+',
                    help='hidden dimensions throughout graph embedding (default: [16, 8])')

parser.add_argument('--data_path', type=str, default='../resource/PCL_NetWork/test/1/',
                    help='path of test data')
parser.add_argument('--output_directory', type=str, default=".",#4096,#8196,#32768,
                    help='output directory')
# 默认单位：ms
parser.add_argument('--tt_flow_cycles', type=int, default=[10],
#parser.add_argument('--tt_flow_cycles', type=str, default=[512, 1024, 2048, 4096],
#parser.add_argument('--tt_flow_cycles', type=str, default=[256, 512, 1024, 2048],
                    help='tt cycles(ms)')
# 默认单位：ms
parser.add_argument('--global_cycle', type=int, default=1,#4096,#8196,#32768,
                    help='global cycle(ms)')
parser.add_argument('--link_failure_pos', type=int, default=300,#8196,#32768,
                    help='path of test data')

# 每毫秒50个时隙，即一个时隙的长度为20微秒
parser.add_argument('--slot_per_millisecond', type=int, default=50,#4096,#8196,#32768,
                    help='number of slots in 1024 millisecond')
parser.add_argument('--link_rate', type=int, default=10,#4096,#8196,#32768,
                    help='rate of the TT network(MBps)')
parser.add_argument('--network_width', type=int, default=5,
                    help='rate of the TT network(MBps)')
parser.add_argument('--all_queue_count', type=int, default=8,
                    help='number of queues, include BE queue, TS queue, RC queue')
parser.add_argument('--per_node_port_count', type=int, default=5,
                    help='number of ports of a node')


args = parser.parse_args()

def gcd(a, b):
    if a < b:
        temp = b
        b = a
        a = temp
    remainder = a % b
    if remainder == 0:
        return b
    else:
        return gcd(remainder, b)


def lcm(a, b):
    remainder = gcd(a, b)
    return int(a * b / remainder)


for cycle in args.tt_flow_cycles:
    args.global_cycle = lcm(args.global_cycle, cycle)
