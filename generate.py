import copy
import itertools
import sys
from crossword import *


class CrosswordCreator():
    def __init__(self, crossword):
        # Initialize crossword CSP with domains for each variable (all possible words initially)
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        # Convert a variable-to-word assignment into a 2D letter grid
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        # Print the crossword assignment as a human-readable grid
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        # Save the crossword assignment to an image file
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create blank image canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        # Draw cells and letters
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                            bbox = draw.textbbox((0, 0), letters[i][j], font=font)
                            w = bbox[2] - bbox[0]
                            h = bbox[3] - bbox[1]


                            draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )
        img.save(filename)

    def solve(self):
        # Enforce consistency constraints and solve the puzzle using backtracking
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        # Remove values from domains that don't match variable length
        for variable in self.domains:
            remove_word = set()
            for word in self.domains[variable]:
                if len(word) != variable.length:
                    remove_word.add(word)
            for word in remove_word:
                self.domains[variable].remove(word)

    def revise(self, x, y):
        # Remove values from x's domain if they can't match any value in y's domain at the overlap
        revised = False
        overlap = self.crossword.overlaps[x, y]
        if overlap is not None:
            remove_word = set()
            for x_word in self.domains[x]:
                overlap_char = x_word[overlap[0]]
                corresponding_y_chars = {w[overlap[1]] for w in self.domains[y]}
                if overlap_char not in corresponding_y_chars:
                    remove_word.add(x_word)
                    revised = True
            for word in remove_word:
                self.domains[x].remove(word)
        return revised

    def ac3(self, arcs=None):
        # Apply the AC-3 algorithm to enforce arc consistency
        if arcs is None:
            # Start with all overlapping variable pairs
            queue = list(itertools.product(self.crossword.variables, self.crossword.variables))
            queue = [arc for arc in queue if arc[0] != arc[1] and self.crossword.overlaps[arc[0], arc[1]] is not None]
        else:
            queue = arcs
        while queue:
            x, y = queue.pop(0)
            if self.revise(x, y):
                if not self.domains[x]:
                    return False  # Domain empty → no solution
                for z in (self.crossword.neighbors(x) - {y}):
                    queue.append((z, x))  # Recheck neighbors of x
        return True

    def assignment_complete(self, assignment):
        # Check if assignment is complete (all variables assigned)
        return set(assignment.keys()) == self.crossword.variables and all(assignment.values())

    def consistent(self, assignment):
        # Check if assignment is consistent (lengths match, no conflicts, no repeats)
        if len(set(assignment.values())) != len(assignment):
            return False  # Duplicate word used
        if any(variable.length != len(word) for variable, word in assignment.items()):
            return False
        for var1, word1 in assignment.items():
            for var2 in self.crossword.neighbors(var1).intersection(assignment.keys()):
                i, j = self.crossword.overlaps[var1, var2]
                if word1[i] != assignment[var2][j]:
                    return False  # Overlap conflict
        return True

    def order_domain_values(self, var, assignment):
        # Order domain values by least-constraining-value heuristic
        num_choices_eliminated = {word: 0 for word in self.domains[var]}
        neighbors = self.crossword.neighbors(var)
        for word_var in self.domains[var]:
            for neighbor in (neighbors - assignment.keys()):
                overlap = self.crossword.overlaps[var, neighbor]
                for word_n in self.domains[neighbor]:
                    if word_var[overlap[0]] != word_n[overlap[1]]:
                        num_choices_eliminated[word_var] += 1
        # Sort by fewest eliminations first
        sorted_list = sorted(num_choices_eliminated.items(), key=lambda x: x[1])
        return [x[0] for x in sorted_list]

    def select_unassigned_variable(self, assignment):
        # Select unassigned variable using MRV, with degree as tiebreaker
        unassigned = self.crossword.variables - assignment.keys()
        num_remaining_values = {v: len(self.domains[v]) for v in unassigned}
        sorted_by_mrv = sorted(num_remaining_values.items(), key=lambda x: x[1])

        if len(sorted_by_mrv) == 1 or sorted_by_mrv[0][1] != sorted_by_mrv[1][1]:
            return sorted_by_mrv[0][0]  # No tie
        else:
            # Tiebreak by highest degree (most constraints on neighbors)
            num_degrees = {v: len(self.crossword.neighbors(v)) for v in unassigned}
            sorted_by_degree = sorted(num_degrees.items(), key=lambda x: x[1], reverse=True)
            return sorted_by_degree[0][0]

    def backtrack(self, assignment):
        # Solve CSP using backtracking search
        if self.assignment_complete(assignment):
            return assignment  # Base case

        var = self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(var, assignment):
            test_assignment = copy.deepcopy(assignment)
            test_assignment[var] = value
            if self.consistent(test_assignment):
                assignment[var] = value  # Choose value
                result = self.backtrack(assignment)
                if result is not None:
                    return result  # Solution found
            assignment.pop(var, None)  # Undo choice
        return None  # No valid assignment


def main():
    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword puzzle
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print or save result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
