from mininet.topo import Topo


class SDNTopo(Topo):
    def build(self):

        # Three OpenFlow 1.3 switches
        s1 = self.addSwitch('s1', protocols='OpenFlow13')
        s2 = self.addSwitch('s2', protocols='OpenFlow13')
        s3 = self.addSwitch('s3', protocols='OpenFlow13')

        # Six hosts
        for i in range(1, 7):
            host = self.addHost(
                f'h{i}',
                ip=f'10.0.0.{i}/24'
            )

            if i <= 2:
                self.addLink(host, s1)
            elif i <= 4:
                self.addLink(host, s2)
            else:
                self.addLink(host, s3)

        # Inter-switch links
        self.addLink(s1, s2)
        self.addLink(s2, s3)


topos = {
    'sdntopo': (lambda: SDNTopo())
}
