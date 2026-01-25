import json
import pandas as pd
from typing import List, Dict, Optional
from openai import OpenAI
from config import OPEN_API_KEY, OPEN_API_BASE, OPEN_API_MODEL

# Initialize OpenAI client with configuration
client = OpenAI(
    api_key=OPEN_API_KEY,
    base_url=OPEN_API_BASE
)

class KGNode:
    def __init__(self, name: str, node_type: str, level: int, parent=None):
        self.name = name
        self.node_type = node_type  # '分类' or '知识点'
        self.level = level
        self.parent = parent
        self.pre_nodes = []
        self.post_nodes = []
        self.related_nodes = []
        self.tags = []
        self.classification = "" # 事实性, 概念性, 程序性, 元认知
        self.description = ""

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.node_type,
            "level": self.level,
            "parent": self.parent.name if self.parent else None,
            "pre": ";".join(self.pre_nodes),
            "post": ";".join(self.post_nodes),
            "related": ";".join(self.related_nodes),
            "tags": ";".join(self.tags),
            "class": self.classification,
            "desc": self.description
        }

class KGEngine:
    def __init__(self):
        self.nodes: List[KGNode] = []

    def add_node(self, node: KGNode):
        self.nodes.append(node)

    def generate_blueprint(self, course_info: str):
        prompt = f"""
        Act as an educational expert. Based on the course info: "{course_info}", 
        generate a high-level course blueprint (Chapter/Module level).
        Return a JSON list of objects with: "name", "type" (always '分类'), "level" (1 or 2).
        Keep it concise (max 8 nodes).
        """
        response = client.chat.completions.create(
            model=OPEN_API_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        # Process and update internal state
        return data

    def expand_node(self, parent_name: str, context: str):
        prompt = f"""
        Expand the node "{parent_name}" within the context of "{context}".
        Provide sub-categories ('分类') or knowledge points ('知识点').
        For knowledge points, include:
        - "classification": '事实性', '概念性', '程序性', or '元认知'
        - "tags": list from ['重点', '难点', '考点', '课程思政']
        - "pre_nodes": list of logical prerequisites
        Return JSON list.
        """
        response = client.chat.completions.create(
            model=OPEN_API_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    def export_to_excel(self, filename: str):
        rows = []
        for node in self.nodes:
            row = {
                "节点类型*": node.node_type,
                "节点名称1": node.name if node.level == 1 else "",
                "节点名称2": node.name if node.level == 2 else "",
                "节点名称3": node.name if node.level == 3 else "",
                "节点名称4": node.name if node.level == 4 else "",
                "节点名称5": node.name if node.level == 5 else "",
                "节点名称6": node.name if node.level == 6 else "",
                "节点名称7": node.name if node.level == 7 else "",
                "前置节点": ";".join(node.pre_nodes),
                "后置节点": ";".join(node.post_nodes),
                "关联节点": ";".join(node.related_nodes),
                "标签": ";".join(node.tags),
                "知识点分类": node.classification,
                "节点说明": node.description
            }
            rows.append(row)
        
        # Add instruction row as per template (Row 1 is usually instructions)
        # But here we just follow the column structure
        df = pd.DataFrame(rows)
        cols = ["节点类型*", "节点名称1", "节点名称2", "节点名称3", "节点名称4", "节点名称5", "节点名称6", "节点名称7", 
                "前置节点", "后置节点", "关联节点", "标签", "知识点分类", "节点说明"]
        
        # Ensure all columns exist
        for col in cols:
            if col not in df.columns:
                df[col] = ""
        
        df = df[cols]
        # Rename columns to match the image precisely if needed (B-H are all '节点名称')
        # In the image, B-H columns are all titled "节点名称"
        # We will use the titles from the image for the final export
        display_cols = ["节点类型*", "节点名称", "节点名称", "节点名称", "节点名称", "节点名称", "节点名称", "节点名称", 
                        "前置节点", "后置节点", "关联节点", "标签", "知识点分类", "节点说明"]
        
        df.columns = display_cols
        df.to_excel(filename, index=False)
        return filename

    def visualize(self):
        import networkx as nx
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg') # Non-interactive backend
        
        G = nx.DiGraph()
        for node in self.nodes:
            G.add_node(node.name, type=node.node_type)
            if node.parent:
                G.add_edge(node.parent.name, node.name, rel='child')
            for pre in node.pre_nodes:
                G.add_edge(pre, node.name, rel='pre')
        
        plt.figure(figsize=(10, 8))
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True, node_size=2000, node_color="skyblue", font_size=10, font_weight="bold", arrows=True)
        plt.title("Course Knowledge Graph Visualization")
        
        img_path = "kg_viz.png"
        plt.savefig(img_path)
        plt.close()
        return img_path
