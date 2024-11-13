# DESCRIPTION: Example verification code for "easy to verify" observations.

FSP_RAW = [
    {
        "observation": "**Expansion of Dimensions**: Each transformation results in an output grid with larger dimensions, 3 times wider and taller, indicating spatial expansion.",
        "verification_code": """To verify if the output grid dimensions are exactly 3 times larger than the input grid, we'll:
1. Convert both grids to numpy arrays for easy shape comparison
2. Check if output height = 3 * input height
3. Check if output width = 3 * input width
4. Return True only if both dimensions match the 3x scaling

Here's a function that implements this verification:

```python
def verify(input_grid, output_grid):
    import numpy as np
    input_arr = np.array(input_grid)
    output_arr = np.array(output_grid)
    return (output_arr.shape[0] == 3 * input_arr.shape[0] and 
            output_arr.shape[1] == 3 * input_arr.shape[1])
```"""
    },
    {
        "observation": "**Change of Color in Enclosed Regions**: In the input grid, any contiguous region of blank cells (represented by 0) that is completely surrounded by a border of green cells (represented by 3) is changed to yellow cells (represented by 4) in the output grid.",
        "verification_code": """To verify if blank regions (0) that are completely surrounded by green cells (3) are changed to yellow cells (4) in the output grid, we'll:
1. Use BFS to find connected components of blank cells
2. For each component, check if it's completely surrounded by green cells
3. If a component is enclosed, verify all its cells are yellow in the output
4. If a component is not enclosed, verify its cells remain unchanged
5. Also verify non-blank cells remain unchanged

Here's a function that implements this verification:

```python
def verify(input_grid, output_grid):
    from collections import deque
    rows, cols = len(input_grid), len(input_grid[0])
    
    def bfs(x, y):
        queue = deque([(x, y)])
        component = set()
        while queue:
            cx, cy = queue.popleft()
            if (cx, cy) not in component:
                component.add((cx, cy))
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < rows and 0 <= ny < cols and input_grid[nx][ny] == 0:
                        queue.append((nx, ny))
        return component

    def is_enclosed(component):
        for x, y in component:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if not (0 <= nx < rows and 0 <= ny < cols) or input_grid[nx][ny] != 3:
                    if (nx, ny) not in component:
                        return False
        return True

    visited = set()
    for x in range(rows):
        for y in range(cols):
            if input_grid[x][y] == 0 and (x, y) not in visited:
                component = bfs(x, y)
                visited.update(component)
                if is_enclosed(component):
                    if any(output_grid[cx][cy] != 4 for cx, cy in component):
                        return False
                else:
                    if any(output_grid[cx][cy] != input_grid[cx][cy] for cx, cy in component):
                        return False
            elif input_grid[x][y] != 0 and output_grid[x][y] != input_grid[x][y]:
                return False

    return True
```"""
    }
] 