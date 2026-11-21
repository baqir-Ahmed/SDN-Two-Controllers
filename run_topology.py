
#!/usr/bin/python3

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from topology import SDNTopo


def run():
    topo = SDNTopo()

    net = Mininet(
        topo=topo,
        controller=None,
        switch=OVSSwitch,
        autoSetMacs=True,
        build=False
    )

    info("*** Adding remote controllers\n")

    c1 = net.addController(
        'c1',
        controller=RemoteController,
        ip='127.0.0.1',
        port=6653
    )

    c2 = net.addController(
        'c2',
        controller=RemoteController,
        ip='127.0.0.1',
        port=6654
    )

    info("*** Building network\n")
    net.build()

    info("*** Starting network with controllers and switches\n")
    net.start()

    info("*** Starting network CLI\n")
    CLI(net)

    info("*** Stopping network\n")
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()
