
import json
import time

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet
from ryu.lib import hub


class Controller2(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(Controller2, self).__init__(*args, **kwargs)

        self.mac_to_port = {}
        self.tcp_client = None

        self.logger.info("Controller 2 started")

        self.sync_thread = hub.spawn(self.sync_loop)

    def sync_loop(self):

        while True:

            try:
                if self.tcp_client is None:

                    self.logger.info(
                        "Connecting to Controller1 TCP server..."
                    )

                    self.tcp_client = hub.connect(
                        ('127.0.0.1', 9000)
                    )

                    self.logger.info(
                        "Connected to Controller1 TCP server"
                    )

                state = {
                    "controller": "Controller2",
                    "timestamp": time.time(),
                    "switches": list(self.mac_to_port.keys()),
                    "learned_mac_count": sum(
                        len(table)
                        for table in self.mac_to_port.values()
                    )
                }

                message = json.dumps(state) + "\n"

                self.tcp_client.sendall(
                    message.encode('utf-8')
                )

                self.logger.info(
                    "SYNC TX to Controller1: %s",
                    message.strip()
                )

                hub.sleep(5)

            except Exception as error:

                self.logger.warning(
                    "TCP synchronization error: %s",
                    error
                )

                if self.tcp_client is not None:

                    try:
                        self.tcp_client.close()
                    except Exception:
                        pass

                    self.tcp_client = None

                hub.sleep(3)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):

        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        self.logger.info(
            "Controller 2 connected to switch %s",
            datapath.id
        )

        match = parser.OFPMatch()

        actions = [
            parser.OFPActionOutput(
                ofproto.OFPP_CONTROLLER,
                ofproto.OFPCML_NO_BUFFER
            )
        ]

        self.add_flow(datapath, 0, match, actions)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):

        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth is None or eth.ethertype == 0x88cc:
            return

        dst = eth.dst
        src = eth.src
        in_port = msg.match['in_port']

        self.mac_to_port.setdefault(dpid, {})

        self.mac_to_port[dpid][src] = in_port

        out_port = self.mac_to_port[dpid].get(
            dst,
            ofproto.OFPP_FLOOD
        )

        actions = [
            parser.OFPActionOutput(out_port)
        ]

        if out_port != ofproto.OFPP_FLOOD:

            match = parser.OFPMatch(
                in_port=in_port,
                eth_dst=dst
            )

            self.add_flow(
                datapath,
                1,
                match,
                actions
            )

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=msg.data if msg.buffer_id == ofproto.OFP_NO_BUFFER else None
        )

        datapath.send_msg(out)

    def add_flow(self, datapath, priority, match, actions):

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        instructions = [
            parser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS,
                actions
            )
        ]

        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=instructions
        )

        datapath.send_msg(mod)
