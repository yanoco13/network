import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import uuid #uuidモジュールをインポート

class NetworkGraph:
    def __init__(self):
        self.graph = nx.Graph()

    def add_node(self, node_id, label):
        self.graph.add_node(node_id, label=label)

    def add_link(self, node1_id, node2_id, label, bandwidth, delay):
        self.graph.add_edge(node1_id, node2_id, bandwidth=bandwidth, delay=delay, label = label)

    def draw(self):
        "リンクの帯域幅に基づいて線の太さを決定する関数"
        def get_edge_width(bandwidth):
            return np.log10(bandwidth) + 1 #bps単位での対数スケール
        
        # リンクの遅延に基づいて線の色を決定する関数
        def get_edge_color(delay):
            if delay <= 0.001: #1ms以下
                return 'green'
            elif delay <= 0.01: #10ms以下
                return 'yellow'
            else: #10ms以上
                return 'red'
        pos = nx.spring_layout(self.graph)
        edge_widths = [get_edge_width(self.graph[u][v]['bandwidth']) for u, v in self.graph.edges()]
        edge_colors = [get_edge_color(self.graph[u][v]['delay']) for u, v in self.graph.edges()]

        nx.draw(self.graph, pos, with_labels=False, node_size=700, node_color='lightblue', font_size=2000, edge_color=edge_colors, width=edge_widths)
        nx.draw_networkx_labels(self.graph, pos, labels=nx.get_node_attributes(self.graph, 'label'))
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=nx.get_edge_attributes(self.graph, 'label'))
        plt.show()

"""
ネットワーク内のノードを定義するクラス
:param node_id: ノードの一意な識別子
:param address: ノードのアドレス
:param links: ノードが接続されているリンク
"""
class Node:
    def __init__(self, node_id, address,network_graph):
        self.node_id = node_id
        self.address = address
        self.links = []
        self.network_graph = network_graph

        #グラフにノードを追加
        label = f'Node{node_id} \n {address}'
        self.network_graph.add_node(node_id, label)

    #リンクを接続するメソッド
    def add_link(self, link):
        if link not in self.links:
            self.links.append(link)

    #パケットを送信するメソッド
    def send_packet(self, packet):
        if packet.destination == self.address:
            self.receive_packet(packet)
        else:
            for link in self.links:
                next_node = link.node_x if self != link.node_x else link.node_y
                print(f"ノード{self.node_id}がパケットを受信: {packet.payload}")
                link.transfer_packet(packet, self)
                break

    #パケットを受信するメソッド
    def receive_packet(self, packet):
        print(f"ノード{self.node_id}がパケットを受信: {packet.payload}")

    #ノードの文字列表現を返すメソッド
    def __str__(self):
        connected_nodes = [link.node_x.node_id if self != link.node_x else link.node_y.node_id for link in self.links]
        connected_node_str = ', '.join(map(str, connected_nodes))
        return f"ノード(ノードID:{self.node_id}, アドレス:{self.address}, 接続: {connected_node_str})"

"""
ネットワーク内の2つのノード間のリンクを表すLinkクラス
:param node_x: リンクの一方のノード
:param node_y: リンクのもう一方のノード
:param bandwidth: リンクの帯域幅（デフォルトは1）
"""
class Link:
    def __init__(self, node_x, node_y, network_graph,bandwidth=10000, delay=0.001, packet_loss=0.0):
        self.node_x = node_x
        self.node_y = node_y
        self.bandwidth = bandwidth
        self.network_graph = network_graph
        self.delay = delay
        self.packet_loss = packet_loss

        #ノードに対して、リンクを接続
        node_x.add_link(self)
        node_y.add_link(self)

        #グラフにリンクを追加
        label = f'{bandwidth/100000}Mbps, {delay}s'
        self.network_graph.add_link(node_x.node_id, node_y.node_id,label, bandwidth, self.delay)
    
    #次のノードへパケットを渡すメソッド
    def transfer_packet(self, packet, from_node):
        next_node = self.node_x if from_node != self.node_x else self.node_y
        next_node.receive_packet(packet)
        
        print(f"リンク({self.node_x.node_id} ↔︎ {self.node_y.node_id})を介してパケットを転送: {packet.payload}")
        next_node.receive_packet(packet)

    def __str__(self):
        return f"リンク({self.node_x.node_id} ↔︎ {self.node_y.node_id}, 帯域幅: {self.bandwidth}, 遅延] {self.delay})"

"""
ネットワーク内で送信されるパケットを表すPacketクラス

:param source: パケットの送信元ノードのアドレス
:param destination: パケットの宛先ノードのアドレス
:param payload: パケットに含まれるデータ(ペイロード)
"""
class Packet:
    #Packetクラスのコンストラクタ
    def __init__(self, source, destination, header_size, payload_size, network_event_scheduler):
        self.network_event_scheduler = network_event_scheduler
        self.id = str(uuid.uuid4()) #パケットに一意のID(UUID)を割り当てる

        #パケットのヘッダ情報を辞書で定義
        self.header = {
            "source" : source, #送信元アドレス
            "destination" : destination,  #宛先アドレス
        }
        self.payload = 'X' * payload_size #パケットのペイロード（実際に送信するデータ）
        self.size = header_size + payload_size #パケット全体のサイズ
        self.creation_time = self.network_event_scheduler.current_time #パケット生成時刻記録
        self.arrival_time = None #パケット到着時刻(初期値はNone)
    
    #到着時刻を設定するメソッド
    def set_arrived(self, arrival_time):
        self.arrival_time = arrival_time #到着時刻を設定

    #heapqモジュールでの比較のための特殊メソッド
    #この実装では比較を行わないため、常にFalseを返す
    def __lt__(self, other):
        return False
        
    def __str__(self):
        return f"パケット(送信元: {self.header["source"]}, 宛先: {self.header["destination"]}, ペイロード: {self.payload})"