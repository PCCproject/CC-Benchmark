#!/usr/bin/python
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.topo import Topo

def runMultiLink():
    "Create and run multiple link network"
    topo = simpleMPTCP()
    net = Mininet( topo=topo )
    net.start()
    CLI( net )
    net.stop()

class simpleMPTCP(Topo):
    def build(self):
        h1, h2 = self.addHost('h1'), self.addHost('h2')
        s1, s2 = self.addSwitch('s1'), self.addSwitch('s2')

        self.addLink(h1, s1)
        self.addLink(h2, s1)

        self.addLink(h1, s2)
        self.addLink(h2, s2)
if __name__ == '__main__':
    setLogLevel( 'info' )
    runMultiLink()
