"""知识图谱生成和分析"""
import networkx as nx
from typing import Dict, List, Tuple, Optional
from collections import Counter, defaultdict
import json

from filemap.core.models import File, Tag
from filemap.storage.datastore import DataStore


class KnowledgeGraph:
    """知识图谱类"""

    def __init__(self, datastore: DataStore):
        """
        初始化知识图谱

        Args:
            datastore: 数据存储实例
        """
        self.datastore = datastore
        self.graph = nx.Graph()

    def generate(self, mode: str = "tags") -> None:
        """
        生成知识图谱

        Args:
            mode: 生成模式 - 'tags'（标签关系）, 'files'（文件关系）, 'full'（完整图谱）
        """
        self.graph.clear()

        if mode in ["tags", "full"]:
            self._build_tag_graph()

        if mode in ["files", "full"]:
            self._build_file_graph()

        if mode == "full":
            self._link_tags_and_files()

    def _build_tag_graph(self) -> None:
        """构建标签关系图谱"""
        # 添加标签节点
        for tag in self.datastore.tags.values():
            self.graph.add_node(
                tag.tag_id,
                type="tag",
                name=tag.name,
                category=tag.category,
                usage_count=tag.usage_count,
            )

        # 分析标签共现关系
        tag_cooccurrence = defaultdict(int)

        for file in self.datastore.files.values():
            # 文件的标签之间两两建立关系
            for i, tag1_id in enumerate(file.tags):
                for tag2_id in file.tags[i + 1:]:
                    pair = tuple(sorted([tag1_id, tag2_id]))
                    tag_cooccurrence[pair] += 1

        # 添加边（只保留共现次数 >= 2 的关系）
        for (tag1_id, tag2_id), count in tag_cooccurrence.items():
            if count >= 2:
                # 计算关联强度（归一化）
                tag1 = self.datastore.get_tag(tag1_id)
                tag2 = self.datastore.get_tag(tag2_id)
                if tag1 and tag2:
                    max_usage = max(tag1.usage_count, tag2.usage_count)
                    strength = count / max_usage if max_usage > 0 else 0

                    self.graph.add_edge(
                        tag1_id,
                        tag2_id,
                        weight=count,
                        strength=strength,
                        type="cooccurrence",
                    )

    def _build_file_graph(self) -> None:
        """构建文件关系图谱"""
        # 添加文件节点
        for file in self.datastore.files.values():
            self.graph.add_node(
                file.file_id,
                type="file",
                name=file.name,
                size=file.size,
                tag_count=len(file.tags),
            )

        # 基于标签相似度建立文件关系
        files = list(self.datastore.files.values())
        for i, file1 in enumerate(files):
            for file2 in files[i + 1:]:
                similarity = self._calculate_tag_similarity(file1, file2)
                if similarity > 0.3:  # 只保留相似度 > 0.3 的关系
                    self.graph.add_edge(
                        file1.file_id,
                        file2.file_id,
                        weight=similarity,
                        type="similarity",
                    )

    def _link_tags_and_files(self) -> None:
        """连接标签和文件"""
        for file in self.datastore.files.values():
            for tag_id in file.tags:
                if tag_id in self.graph and file.file_id in self.graph:
                    self.graph.add_edge(
                        file.file_id,
                        tag_id,
                        type="tagged",
                    )

    def _calculate_tag_similarity(self, file1: File, file2: File) -> float:
        """
        计算两个文件的标签相似度（Jaccard相似度）

        Args:
            file1: 文件1
            file2: 文件2

        Returns:
            相似度 (0-1)
        """
        if not file1.tags or not file2.tags:
            return 0.0

        tags1 = set(file1.tags)
        tags2 = set(file2.tags)

        intersection = len(tags1 & tags2)
        union = len(tags1 | tags2)

        return intersection / union if union > 0 else 0.0

    def find_hubs(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """
        识别核心节点（度中心性最高的节点）

        Args:
            top_n: 返回前N个核心节点

        Returns:
            (节点ID, 度数) 列表
        """
        degrees = dict(self.graph.degree())
        sorted_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:top_n]

    def find_orphans(self, node_type: Optional[str] = None) -> List[str]:
        """
        找出孤立节点（度为0或1的节点）

        Args:
            node_type: 节点类型过滤 ('tag', 'file', None)

        Returns:
            孤立节点ID列表
        """
        orphans = []
        for node in self.graph.nodes():
            if self.graph.degree(node) <= 1:
                if node_type is None:
                    orphans.append(node)
                else:
                    node_data = self.graph.nodes[node]
                    if node_data.get("type") == node_type:
                        orphans.append(node)
        return orphans

    def find_communities(self) -> Dict[int, List[str]]:
        """
        发现社区（聚类）

        Returns:
            {社区ID: [节点ID列表]}
        """
        if len(self.graph) == 0:
            return {}

        # 使用Louvain算法进行社区发现
        try:
            import community as community_louvain
            partition = community_louvain.best_partition(self.graph)
        except ImportError:
            # 如果没有python-louvain库，使用NetworkX的贪心模块化社区
            from networkx.algorithms import community
            communities = community.greedy_modularity_communities(self.graph)
            partition = {}
            for idx, comm in enumerate(communities):
                for node in comm:
                    partition[node] = idx

        # 重组为 {社区ID: [节点列表]}
        result = defaultdict(list)
        for node, comm_id in partition.items():
            result[comm_id].append(node)

        return dict(result)

    def recommend_tags(self, file_id: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """
        为文件推荐标签

        Args:
            file_id: 文件ID
            top_n: 返回前N个推荐

        Returns:
            [(标签ID, 推荐分数)] 列表
        """
        file = self.datastore.get_file(file_id)
        if not file:
            return []

        # 基于文件现有标签，找出经常与之共现的其他标签
        tag_scores = Counter()

        for tag_id in file.tags:
            # 找出与当前标签相关的其他标签
            if tag_id in self.graph:
                for neighbor in self.graph.neighbors(tag_id):
                    neighbor_data = self.graph.nodes[neighbor]
                    if neighbor_data.get("type") == "tag" and neighbor not in file.tags:
                        edge_data = self.graph.get_edge_data(tag_id, neighbor)
                        weight = edge_data.get("weight", 1) if edge_data else 1
                        tag_scores[neighbor] += weight

        # 返回得分最高的标签
        return tag_scores.most_common(top_n)

    def get_stats(self) -> Dict:
        """
        获取图谱统计信息

        Returns:
            统计信息字典
        """
        if len(self.graph) == 0:
            return {
                "total_nodes": 0,
                "total_edges": 0,
                "tag_nodes": 0,
                "file_nodes": 0,
                "avg_degree": 0,
                "density": 0,
            }

        tag_nodes = sum(1 for n in self.graph.nodes() if self.graph.nodes[n].get("type") == "tag")
        file_nodes = sum(1 for n in self.graph.nodes() if self.graph.nodes[n].get("type") == "file")

        return {
            "total_nodes": len(self.graph.nodes()),
            "total_edges": len(self.graph.edges()),
            "tag_nodes": tag_nodes,
            "file_nodes": file_nodes,
            "avg_degree": sum(dict(self.graph.degree()).values()) / len(self.graph.nodes()),
            "density": nx.density(self.graph),
            "connected_components": nx.number_connected_components(self.graph),
        }

    def export_json(self) -> Dict:
        """
        导出图谱为JSON格式

        Returns:
            图谱数据字典
        """
        nodes = []
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id].copy()
            node_data["id"] = node_id
            nodes.append(node_data)

        edges = []
        for u, v, data in self.graph.edges(data=True):
            edge_data = data.copy()
            edge_data["source"] = u
            edge_data["target"] = v
            edges.append(edge_data)

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": self.get_stats(),
        }

    def save(self, file_path: str) -> None:
        """
        保存图谱到文件

        Args:
            file_path: 保存路径
        """
        data = self.export_json()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def visualize_text(self, max_nodes: int = 50) -> str:
        """
        生成文本形式的可视化

        Args:
            max_nodes: 最大显示节点数

        Returns:
            文本可视化字符串
        """
        if len(self.graph) == 0:
            return "图谱为空"

        lines = []
        lines.append(f"=== 知识图谱 (节点: {len(self.graph.nodes())}, 边: {len(self.graph.edges())}) ===\n")

        # 显示核心节点
        hubs = self.find_hubs(min(10, max_nodes))
        lines.append("核心节点 (度中心性最高):")
        for node_id, degree in hubs:
            node_data = self.graph.nodes[node_id]
            node_type = node_data.get("type", "unknown")
            name = node_data.get("name", "未知")
            lines.append(f"  • [{node_type}] {name} (连接数: {degree})")

        lines.append("")

        # 显示标签共现关系（权重最高的）
        tag_edges = [
            (u, v, data) for u, v, data in self.graph.edges(data=True)
            if self.graph.nodes[u].get("type") == "tag" and self.graph.nodes[v].get("type") == "tag"
        ]

        if tag_edges:
            tag_edges.sort(key=lambda x: x[2].get("weight", 0), reverse=True)
            lines.append("标签关联关系 (共现次数最多):")
            for u, v, data in tag_edges[:10]:
                tag1_name = self.graph.nodes[u].get("name")
                tag2_name = self.graph.nodes[v].get("name")
                weight = data.get("weight", 0)
                lines.append(f"  • {tag1_name} <--({weight})-->  {tag2_name}")

        return "\n".join(lines)
