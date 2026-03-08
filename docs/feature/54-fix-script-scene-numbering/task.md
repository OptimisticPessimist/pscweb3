# Task List

## Active Tasks
- [/] Fix script parsing issue where "登場人物" is treated as a scene
    - [x] Update `fountain_parser.py` to prevent "登場人物" from being matched by the "場" keyword
    - [x] Make sure "登場人物" explicitly bypasses scene creation even if it's a `##` Level 2 heading
    - [ ] Ensure tests cover `# 登場人物` and `## 登場人物` scenarios

## Completed Tasks
