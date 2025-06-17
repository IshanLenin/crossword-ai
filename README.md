# 📘 Crossword Generator (CS50 AI)

This is a **Crossword Puzzle Generator** built as part of [Harvard's CS50 AI course](https://cs50.harvard.edu/ai/2020/), specifically the **Constraint Satisfaction Problems (CSP)** module.

It uses AI techniques like:
- **Backtracking Search**
- **Arc Consistency (AC-3)**
- **Minimum Remaining Values (MRV)**
- **Degree Heuristic**
- **Least Constraining Value (LCV)**

The program reads a crossword structure and a list of words, then uses CSP algorithms to fill the crossword correctly — finally rendering the puzzle as a `.png` image using Pillow.

---

## 🧠 What I Learned

- How to model problems using CSPs
- Implementing **node and arc consistency**
- Applying **heuristics to optimize backtracking**
- Visualizing crossword solutions programmatically

---

## 🛠️ How to Run

### Prerequisites

- Python 3
- [Pillow](https://pypi.org/project/Pillow/) (`pip install Pillow` if not already installed)
- A Linux-like environment (WSL/macOS/Linux preferred for running `check50`)

### Usage

```bash
python generate.py structure.txt words.txt output.png
