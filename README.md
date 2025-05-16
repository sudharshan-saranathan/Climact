# 🌀 Climact

**Climact** is a visual process modeling and optimization tool designed for simulating energy, emissions, and material flow systems. Built with **PyQt6**, it offers a fast, interactive way to construct schematics, assign parameters, and compute balances — all enhanced by AI-assisted modeling features.

---

## 🚀 Features

- Drag-and-drop schematic editor
- Mass, energy, and emissions balance tracking
- Editable tables with assign/erase actions
- Undo/redo, snapping, and alignment tools
- Gemini AI integration for flow generation
- JSON-based save/load of models
- Themeable UI with `.qss` stylesheets
- Parameter commit & validation system

---

## 🛠️ Installation

### Using Poetry

```bash
git clone https://github.com/<your-username>/climact.git
cd climact
poetry install
poetry run python main.py
