# AI Agent Design: Growth-oriented Knowledge Graph Assistant

## Architecture
The system is built as a Gradio application that manages a stateful "Knowledge Graph" (KG). The growth is achieved by iterative interaction where the AI suggests structures and the user refines them.

### 1. Data Model
- **Node**: ID, Type (Category/Knowledge Point), Name, Level, Parent, Tags, Classification, Description.
- **Relationship**: Source, Target, Type (Pre/Post/Related).
- **History**: Store previous states to allow "growth" and undo.

### 2. Workflow
1.  **Phase 1: Blueprint Generation (Overall Blueprint)**
    - User provides course name/description.
    - AI generates high-level categories (Chapters/Modules).
    - User reviews and adjusts.
2.  **Phase 2: Progressive Growth (Full Course System)**
    - For each category, user can ask AI to "Expand" or "Detail".
    - AI extracts sub-categories and specific knowledge points.
    - AI identifies relationships (Pre/Post) based on logical teaching sequence.
3.  **Phase 3: Refinement & Tagging**
    - AI suggests tags (Key, Difficult, Exam point) and classifications.
    - User provides descriptions or asks AI to generate them.
4.  **Phase 4: Export & Visualization**
    - Convert internal state to the Excel template format.
    - Render a visual graph (e.g., using NetworkX + Matplotlib or a simple interactive diagram).

### 3. Key Components
- **Extractor**: LLM-powered engine to parse natural language into structured KG nodes.
- **State Manager**: Handles the growing tree structure and relationship map.
- **Excel Formatter**: Maps the internal tree to the specific 7-level column format.
- **Gradio UI**:
    - Chatbot for interaction.
    - Dynamic table view for current KG.
    - Download buttons for Excel.
    - Visualization panel.
