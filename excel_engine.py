# -*- coding: utf-8 -*-
"""
类Excel计算引擎
支持A1,B2单元格引用和公式解析
"""

import re
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field


class CellRef:
    """单元格引用"""
    
    def __init__(self, col: int, row: int):
        self.col = col  # 0-based列索引
        self.row = row  # 0-based行索引
    
    @classmethod
    def from_string(cls, ref: str) -> 'CellRef':
        """从字符串解析，如'A1' -> CellRef(0, 0)"""
        ref = ref.upper().strip()
        match = re.match(r'([A-Z]+)(\d+)', ref)
        if not match:
            raise ValueError(f"无效的单元格引用: {ref}")
        
        col_str, row_str = match.groups()
        
        # 转换列字母到数字 (A=0, B=1, ..., Z=25, AA=26, ...)
        col = 0
        for char in col_str:
            col = col * 26 + (ord(char) - ord('A') + 1)
        col -= 1  # 转为0-based
        
        row = int(row_str) - 1  # 转为0-based
        
        return cls(col, row)
    
    def to_string(self) -> str:
        """转换为字符串"""
        # 转换数字到列字母
        col = self.col
        col_str = ""
        while col >= 0:
            col_str = chr(col % 26 + ord('A')) + col_str
            col = col // 26 - 1
        
        return f"{col_str}{self.row + 1}"
    
    def __repr__(self):
        return f"CellRef({self.to_string()})"


class CellRange:
    """单元格范围"""
    
    def __init__(self, start: CellRef, end: CellRef):
        self.start = start
        self.end = end
    
    @classmethod
    def from_string(cls, range_str: str) -> 'CellRange':
        """从字符串解析，如'A1:B10'"""
        parts = range_str.upper().strip().split(':')
        if len(parts) != 2:
            raise ValueError(f"无效的范围: {range_str}")
        
        start = CellRef.from_string(parts[0])
        end = CellRef.from_string(parts[1])
        
        return cls(start, end)
    
    def get_cells(self) -> List[CellRef]:
        """获取范围内所有单元格"""
        cells = []
        for row in range(self.start.row, self.end.row + 1):
            for col in range(self.start.col, self.end.col + 1):
                cells.append(CellRef(col, row))
        return cells


@dataclass
class Cell:
    """单元格"""
    ref: CellRef
    value: Any = None
    formula: str = ""  # 公式，如"=A1+B2"
    
    def is_formula(self) -> bool:
        """是否是公式单元格"""
        return isinstance(self.formula, str) and self.formula.startswith('=')


class Spreadsheet:
    """电子表格"""
    
    def __init__(self):
        self.cells: Dict[str, Cell] = {}
        self.functions: Dict[str, Callable] = {
            'SUM': self._func_sum,
            'AVERAGE': self._func_average,
            'MAX': self._func_max,
            'MIN': self._func_min,
            'IF': self._func_if,
        }
    
    def get_cell(self, ref: str) -> Optional[Cell]:
        """获取单元格"""
        return self.cells.get(ref.upper())
    
    def set_cell(self, ref: str, value: Any = None, formula: str = ""):
        """设置单元格"""
        cell_ref = CellRef.from_string(ref)
        cell = Cell(ref=cell_ref, value=value, formula=formula)
        self.cells[ref.upper()] = cell
    
    def get_value(self, ref: str) -> Any:
        """获取单元格值（如果是公式则计算）"""
        cell = self.get_cell(ref)
        if cell is None:
            return None
        
        if cell.is_formula():
            return self.evaluate_formula(cell.formula)
        
        return cell.value
    
    def evaluate_formula(self, formula: str) -> Any:
        """计算公式"""
        if not formula.startswith('='):
            return formula
        
        formula = formula[1:]  # 去掉开头的'='
        
        # 替换单元格引用为实际值
        formula = self._replace_cell_refs(formula)
        
        # 处理函数调用
        formula = self._evaluate_functions(formula)
        
        # 计算表达式
        try:
            return eval(formula)
        except Exception as e:
            return f"#ERROR: {e}"
    
    def _replace_cell_refs(self, formula: str) -> str:
        """替换单元格引用为实际值"""
        # 匹配单元格引用，如A1, B2, $C$3等
        pattern = r'\$?([A-Z]+)\$?(\d+)'
        
        def replace(match):
            ref_str = match.group(1) + match.group(2)
            value = self.get_value(ref_str)
            if value is None:
                return "0"
            return str(value)
        
        return re.sub(pattern, replace, formula)
    
    def _evaluate_functions(self, formula: str) -> str:
        """评估函数调用"""
        # 匹配函数调用，如SUM(A1:A10), IF(A1>0,1,0)等
        pattern = r'(\w+)\s*\(([^)]*)\)'
        
        def replace(match):
            func_name = match.group(1).upper()
            args_str = match.group(2)
            
            if func_name not in self.functions:
                return match.group(0)  # 不处理未知函数
            
            # 解析参数
            args = [arg.strip() for arg in args_str.split(',')]
            
            # 执行函数
            try:
                result = self.functions[func_name](*args)
                return str(result)
            except Exception as e:
                return f"#ERROR"
        
        # 递归处理嵌套函数
        prev_formula = ""
        while prev_formula != formula:
            prev_formula = formula
            formula = re.sub(pattern, replace, formula)
        
        return formula
    
    # 内置函数
    def _func_sum(self, *args) -> float:
        """SUM函数"""
        total = 0.0
        for arg in args:
            if ':' in arg:  # 范围，如A1:A10
                try:
                    range_obj = CellRange.from_string(arg)
                    for cell_ref in range_obj.get_cells():
                        val = self.get_value(cell_ref.to_string())
                        if val is not None and isinstance(val, (int, float)):
                            total += val
                except:
                    pass
            else:  # 单个单元格
                try:
                    val = self.get_value(arg)
                    if val is not None and isinstance(val, (int, float)):
                        total += val
                except:
                    pass
        return total
    
    def _func_average(self, *args) -> float:
        """AVERAGE函数"""
        values = []
        for arg in args:
            if ':' in arg:
                try:
                    range_obj = CellRange.from_string(arg)
                    for cell_ref in range_obj.get_cells():
                        val = self.get_value(cell_ref.to_string())
                        if val is not None and isinstance(val, (int, float)):
                            values.append(val)
                except:
                    pass
            else:
                try:
                    val = self.get_value(arg)
                    if val is not None and isinstance(val, (int, float)):
                        values.append(val)
                except:
                    pass
        
        return sum(values) / len(values) if values else 0
    
    def _func_max(self, *args) -> float:
        """MAX函数"""
        values = []
        for arg in args:
            if ':' in arg:
                try:
                    range_obj = CellRange.from_string(arg)
                    for cell_ref in range_obj.get_cells():
                        val = self.get_value(cell_ref.to_string())
                        if val is not None and isinstance(val, (int, float)):
                            values.append(val)
                except:
                    pass
            else:
                try:
                    val = self.get_value(arg)
                    if val is not None and isinstance(val, (int, float)):
                        values.append(val)
                except:
                    pass
        
        return max(values) if values else 0
    
    def _func_min(self, *args) -> float:
        """MIN函数"""
        values = []
        for arg in args:
            if ':' in arg:
                try:
                    range_obj = CellRange.from_string(arg)
                    for cell_ref in range_obj.get_cells():
                        val = self.get_value(cell_ref.to_string())
                        if val is not None and isinstance(val, (int, float)):
                            values.append(val)
                except:
                    pass
            else:
                try:
                    val = self.get_value(arg)
                    if val is not None and isinstance(val, (int, float)):
                        values.append(val)
                except:
                    pass
        
        return min(values) if values else 0
    
    def _func_if(self, condition: str, true_val: str, false_val: str) -> Any:
        """IF函数"""
        try:
            # 评估条件
            condition = self._replace_cell_refs(condition)
            if eval(condition):
                # 评估真值
                true_val = self._replace_cell_refs(true_val)
                return eval(true_val)
            else:
                # 评估假值
                false_val = self._replace_cell_refs(false_val)
                return eval(false_val)
        except:
            return 0


# 测试
if __name__ == "__main__":
    print("=" * 60)
    print("类Excel计算引擎测试")
    print("=" * 60)
    
    sheet = Spreadsheet()
    
    # 设置基础数据
    sheet.set_cell("A1", 10)
    sheet.set_cell("A2", 20)
    sheet.set_cell("A3", 30)
    sheet.set_cell("B1", 100)
    sheet.set_cell("B2", 200)
    
    print("\n基础数据:")
    print(f"A1 = {sheet.get_value('A1')}")
    print(f"A2 = {sheet.get_value('A2')}")
    print(f"B1 = {sheet.get_value('B1')}")
    
    # 测试公式
    sheet.set_cell("C1", formula="=A1+A2")
    sheet.set_cell("C2", formula="=A1*B1")
    sheet.set_cell("C3", formula="=SUM(A1:A3)")
    sheet.set_cell("C4", formula="=IF(A1>5,100,0)")
    
    print("\n公式计算:")
    print(f"C1 (=A1+A2) = {sheet.get_value('C1')}")
    print(f"C2 (=A1*B1) = {sheet.get_value('C2')}")
    print(f"C3 (=SUM(A1:A3)) = {sheet.get_value('C3')}")
    print(f"C4 (=IF(A1>5,100,0)) = {sheet.get_value('C4')}")
    
    # 测试单元格引用解析
    print("\n单元格引用解析:")
    print(f"A1 -> {CellRef.from_string('A1')}")
    print(f"B2 -> {CellRef.from_string('B2')}")
    print(f"AA10 -> {CellRef.from_string('AA10')}")
    print(f"ABC123 -> {CellRef.from_string('ABC123')}")
