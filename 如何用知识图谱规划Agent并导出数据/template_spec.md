# Knowledge Graph Excel Template Specification

## Column Structure
1. **节点类型* (Node Type)**: Required. Values: `分类` (Category) or `知识点` (Knowledge Point).
2. **节点名称 (Node Name) - Levels 1 to 7**: Columns B to H. Each row supports only one node name at one level.
3. **前置节点 (Pre-requisite Nodes)**: Columns I. Use semicolon `;` to separate multiple nodes.
4. **后置节点 (Post-requisite Nodes)**: Columns J. Use semicolon `;` to separate multiple nodes.
5. **关联节点 (Related Nodes)**: Columns K. Use semicolon `;` to separate multiple nodes.
6. **标签 (Tags)**: Fixed tags include `重点` (Key), `难点` (Difficult), `考点` (Exam point), `课程思政` (Curriculum Ideology). Custom tags allowed, separated by `;`.
7. **知识点分类 (Knowledge Point Classification)**: For `知识点` type only. Values: `事实性` (Factual), `概念性` (Conceptual), `程序性` (Procedural), `元认知` (Metacognitive).
8. **节点说明 (Node Description)**: Text only. Max 256 characters.

## Rules & Constraints
- **Exclusivity**: Only one relationship (Pre, Post, or Related) between any two nodes. New imports override old ones.
- **Node Hierarchy**: Knowledge points cannot have child nodes.
- **Capacity**: Max 5000 nodes, 2000 relationships, 1000 tags.
- **Formatting**: Do not delete any rows or columns from the template.
- **Hierarchy Representation**: The level columns (B-H) represent the tree structure. A node in level N is a child of the most recent node in level N-1.
