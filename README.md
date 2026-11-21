# SDN Two-Controller Network

## Overview
An SDN simulation using Mininet, Open vSwitch, and Ryu.
A network with two Ryu controllers managing three OpenFlow 1.3 switches,
including a TCP channel that exchanges status information between the controllers.

## Network Topology
- 6 hosts (h1-h6)
- 3 OpenFlow 1.3 switches (s1-s3)
- 2 Ryu controllers (controller1, controller2)

## Project Structure
```
.
├── topology.py              # Network topology definition
├── run_topology.py          # Entry point - starts the simulation
├── miniedit_topology.mn     # Topology exported from MiniEdit
├── controllers/
│   ├── controller1.py       # Ryu controller 1 (with TCP status server)
│   └── controller2.py       # Ryu controller 2 (with TCP status client)
└── screenshots/             # Evidence: terminal outputs & GUI states
```

## Tested Environment
- Debian GNU/Linux 13
- Python 3.11
- Ryu 4.34
- Mininet 2.3.0
- Open vSwitch 3.5.0
- OpenFlow 1.3

## Running
Start both Ryu controllers in separate terminals:
```bash
ryu-manager controllers/controller1.py
ryu-manager controllers/controller2.py
```
Then run:
```bash
sudo python3 run_topology.py
```

## Test Results
- Python syntax compilation: successful.
- Full pingall: 30 successful checks, 0% packet loss.
- Switch-controller connections: verified.
- Flow tables on s1, s2, and s3: inspected.
- TCP JSON status transmission and reception: verified.

See [`screenshots/`](screenshots/) for the full evidence.

## Limitation
The TCP channel exchanges status information only.
It does not implement shared MAC-learning state or automatic controller failover.
