
import json

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet
from ryu.lib import hub


class Controller1(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(Controller1, self).__init__(*args, **kwargs)

        self.mac_to_port = {}

        self.tcp_server = hub.StreamServer(
            ('127.0.0.1', 9000),
            self.handle_sync_connection
        )

        self.tcp_server_thread = hub.spawn(
            self.tcp_server.serve_forever
        )

        self.logger.info("Controller 1 started")
        self.logger.info("TCP synchronization server listening on port 9000")

    def handle_sync_connection(self, sock, address):

        self.logger.info("TCP connection established from %s", address)

        buffer = b''

        try:
            while True:
                data = sock.recv(4096)

                if not data:
                    break

                buffer += data

                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)

                    if not line.strip():
                        continue

                    try:
                        state = json.loads(line.decode('utf-8'))

                        self.logger.info(
                            "SYNC RX from Controller2: %s",
                            json.dumps(state)
                        )

                    except (ValueError, UnicodeDecodeError):
                        self.logger.warning(
                            "Received invalid sync message"
                        )

        except Exception as error:
            self.logger.warning(
                "TCP connection error: %s", error
            )

        finally:
            sock.close()
            self.logger.info("TCP synchronization connection closed")

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):

        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        self.logger.info(
            "Controller 1 connected to switch %s",
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
