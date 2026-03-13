# -*- coding: utf-8 -*-
"""
鸣潮DPS计算器 v1.0 - 主窗口

专业级GUI，支持：
- 表格形式编辑大量动作
- 批量添加/删除/复制/粘贴
- 实时计算
- 叠层系统
- 多角色切换
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import Skill, Character, Team, Environment, SpecialLayer
from core.calculator import DamageCalculator
from core.events import EventBus, EventType
from core.layers import LayerSystem
from dataio.excel_handler import ExcelHandler


class SkillTable(ttk.Frame):
    """技能表格 - 专业级可编辑表格"""
    
    COLUMN_CONFIG = {
        'count': {'name': '次数', 'width': 50, 'editable': True},
        'name': {'name': '动作', 'width': 120, 'editable': True},
        'multiplier_input': {'name': '倍率(%)', 'width': 80, 'editable': True},
        'skill_type': {'name': '类型', 'width': 50, 'editable': True},
        'panel_atk_input': {'name': '面板攻击', 'width': 80, 'editable': True},
        'atk_zone': {'name': '攻击区', 'width': 80, 'editable': True},
        'bonus_zone': {'name': '加成区', 'width': 80, 'editable': True},
        'crit_zone': {'name': '双爆区', 'width': 80, 'editable': True},
        'amplify_zone': {'name': '加深区', 'width': 80, 'editable': True},
        'defense_zone': {'name': '防御区', 'width': 80, 'editable': True},
        'resistance_zone': {'name': '抗性区', 'width': 80, 'editable': True},
        'multiplier_boost': {'name': '倍率提升', 'width': 80, 'editable': True},
        'vulnerable_zone': {'name': '易伤区', 'width': 80, 'editable': True},
        'independent_zone': {'name': '独立乘区', 'width': 80, 'editable': True},
        'damage': {'name': '伤害', 'width': 100, 'editable': False},
        'total_damage': {'name': '总伤害', 'width': 100, 'editable': False},
    }
    
    def __init__(self, parent, character: Character, on_change=None):
        super().__init__(parent)
        self.character = character
        self.on_change = on_change
        self.selected_indices: List[int] = []
        
        # 创建表格
        columns = list(self.COLUMN_CONFIG.keys())
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=25)
        
        # 设置列
        for col, config in self.COLUMN_CONFIG.items():
            self.tree.heading(col, text=config['name'])
            self.tree.column(col, width=config['width'], anchor="center")
        
        # 滚动条
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # 布局
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # 绑定事件
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Delete>", self._on_delete_key)
        
        # 刷新
        self.refresh()
    
    def refresh(self):
        """刷新表格"""
        # 清空
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 填充数据
        for i, skill in enumerate(self.character.skills):
            values = self._skill_to_values(skill)
            self.tree.insert("", "end", iid=str(i), values=values)
    
    def _skill_to_values(self, skill: Skill) -> tuple:
        """将技能转换为表格值"""
        return (
            skill.count,
            skill.name,
            f"{skill.multiplier_input:.2f}",
            skill.skill_type,
            int(skill.panel_atk_input) if skill.panel_atk_input else "",
            f"{skill.atk_zone:.4f}" if skill.atk_zone != 1 else "1.0",
            f"{skill.bonus_zone:.4f}" if skill.bonus_zone != 1 else "1.0",
            f"{skill.crit_zone:.4f}",
            skill.amplify_zone,
            f"{skill.defense_zone:.4f}",
            skill.resistance_zone,
            f"{skill.multiplier_boost * 100:.0f}%",
            f"{skill.vulnerable_zone * 100:.0f}%",
            f"{(skill.independent_zone - 1) * 100:.0f}%",
            int(skill.damage) if skill.damage else "",
            int(skill.total_damage) if skill.total_damage else ""
        )
    
    def _on_double_click(self, event):
        """双击编辑"""
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        
        if not item or not column:
            return
        
        col_idx = int(column[1:]) - 1
        col_keys = list(self.COLUMN_CONFIG.keys())
        
        if col_idx < 0 or col_idx >= len(col_keys):
            return
        
        col_key = col_keys[col_idx]
        
        # 检查是否可编辑
        if not self.COLUMN_CONFIG[col_key]['editable']:
            return
        
        skill_idx = int(item)
        if skill_idx >= len(self.character.skills):
            return
        
        # 获取单元格位置
        x, y, width, height = self.tree.bbox(item, column)
        
        # 创建编辑框
        entry = ttk.Entry(self.tree, width=width // 8)
        entry.place(x=x, y=y, width=width, height=height)
        
        # 设置当前值
        current_value = self.tree.item(item, "values")[col_idx]
        entry.insert(0, str(current_value).replace("%", ""))
        entry.select_range(0, tk.END)
        entry.focus()
        
        def _save_edit(event=None):
            new_value = entry.get()
            entry.destroy()
            self._update_skill(skill_idx, col_key, new_value)
        
        entry.bind("<Return>", _save_edit)
        entry.bind("<FocusOut>", _save_edit)
    
    def _update_skill(self, skill_idx: int, col_key: str, value: str):
        """更新技能数据"""
        try:
            skill = self.character.skills[skill_idx]
            value = value.strip()
            
            # 根据字段更新
            if col_key == 'count':
                skill.count = int(float(value))
            elif col_key == 'name':
                skill.name = value
            elif col_key == 'multiplier_input':
                skill.multiplier_input = float(value)
            elif col_key == 'skill_type':
                skill.skill_type = value
            elif col_key == 'panel_atk_input':
                skill.panel_atk_input = float(value)
            elif col_key == 'atk_zone':
                skill.atk_zone = float(value)
            elif col_key == 'bonus_zone':
                skill.bonus_zone = float(value)
            elif col_key == 'crit_zone':
                skill.crit_zone = float(value)
            elif col_key == 'amplify_zone':
                skill.amplify_zone = float(value)
            elif col_key == 'defense_zone':
                skill.defense_zone = float(value)
            elif col_key == 'resistance_zone':
                skill.resistance_zone = float(value)
            elif col_key == 'multiplier_boost':
                skill.multiplier_boost = float(value) / 100
            elif col_key == 'vulnerable_zone':
                skill.vulnerable_zone = float(value) / 100
            elif col_key == 'independent_zone':
                skill.independent_zone = 1 + float(value) / 100
            
            # 实时计算
            skill.calculate()
            
            # 刷新显示
            self.refresh()
            
            # 通知变更
            if self.on_change:
                self.on_change()
                
        except Exception as e:
            messagebox.showerror("输入错误", f"无效的值: {value}\n{str(e)}")
    
    def _on_select(self, event):
        """选择变更"""
        self.selected_indices = [int(i) for i in self.tree.selection()]
    
    def _on_delete_key(self, event):
        """Delete键删除"""
        self.delete_selected()
    
    def add_skills(self, count: int = 1):
        """批量添加动作"""
        for i in range(count):
            self.character.add_skill()
        self.refresh()
        if self.on_change:
            self.on_change()
    
    def delete_selected(self):
        """删除选中动作"""
        if self.selected_indices:
            self.character.remove_skills(self.selected_indices)
            self.selected_indices = []
            self.refresh()
            if self.on_change:
                self.on_change()
    
    def copy_selected(self) -> List[Skill]:
        """复制选中动作"""
        return self.character.clone_skills(self.selected_indices)
    
    def paste_skills(self, skills: List[Skill]):
        """粘贴动作"""
        if skills:
            index = max(self.selected_indices) + 1 if self.selected_indices else None
            self.character.paste_skills(skills, index)
            self.refresh()
            if self.on_change:
                self.on_change()
    
    def calculate_all(self):
        """计算所有动作"""
        self.character.calculate_all()
        self.refresh()


class LayerPanel(ttk.LabelFrame):
    """叠层面板"""
    
    def __init__(self, parent, character: Character, on_change=None):
        super().__init__(parent, text="特殊叠层", padding=10)
        self.character = character
        self.on_change = on_change
        
        # 叠层列表
        self.layer_vars = []
        self._refresh_layers()
        
        # 添加叠层按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(btn_frame, text="添加奥古斯塔叠层", 
                  command=lambda: self._add_layer('augusta')).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="添加弗洛洛叠层", 
                  command=lambda: self._add_layer('flolo')).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="添加西格莉卡叠层", 
                  command=lambda: self._add_layer('sigilica')).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="添加自定义叠层", 
                  command=lambda: self._add_layer('custom')).pack(side="left", padx=2)
    
    def _refresh_layers(self):
        """刷新叠层显示"""
        # 清除旧控件
        for widget in self.winfo_children():
            if isinstance(widget, ttk.Frame) and widget != self.winfo_children()[-1]:
                widget.destroy()
        
        self.layer_vars = []
        
        # 创建叠层控件
        for i, layer in enumerate(self.character.special_layers):
            frame = ttk.Frame(self)
            frame.pack(fill="x", pady=2)
            
            ttk.Label(frame, text=layer.name, width=15).pack(side="left", padx=5)
            
            var = tk.IntVar(value=layer.current)
            self.layer_vars.append((layer, var))
            
            spin = ttk.Spinbox(frame, from_=0, to=layer.max_layers, 
                             textvariable=var, width=8)
            spin.pack(side="left", padx=5)
            
            ttk.Label(frame, text=f"/ {layer.max_layers}").pack(side="left")
            
            # 绑定变更
            var.trace_add("write", lambda *args, l=layer, v=var: self._on_layer_change(l, v))
    
    def _add_layer(self, template_name: str):
        """添加叠层"""
        layer = LayerSystem.create_layer(template_name, self.character.name)
        if layer:
            layer.on_changed = self._on_any_layer_change
            self.character.special_layers.append(layer)
            self._refresh_layers()
            if self.on_change:
                self.on_change()
    
    def _on_layer_change(self, layer: SpecialLayer, var: tk.IntVar):
        """叠层数值变更"""
        try:
            layer.set_layers(var.get())
            if self.on_change:
                self.on_change()
        except:
            pass
    
    def _on_any_layer_change(self):
        """任意叠层变更"""
        if self.on_change:
            self.on_change()


class MainWindow:
    """主窗口"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("鸣潮DPS计算器 v1.0")
        self.root.geometry("1920x1080")
        
        # 初始化核心组件
        self.event_bus = EventBus()
        self.calculator = DamageCalculator(self.event_bus)
        self.excel_handler = ExcelHandler()
        
        # 创建默认队伍
        self.team = Team(name="新队伍")
        char = Character(name="弗洛洛")
        self.team.characters.append(char)
        self.current_char_index = 0
        
        # 剪贴板
        self.clipboard_skills: List[Skill] = []
        
        self._create_menu()
        self._create_ui()
        
        # 订阅事件
        self.event_bus.subscribe(EventType.SKILL_CHANGED, self._on_skill_changed)
        self.event_bus.subscribe(EventType.CALCULATION_NEEDED, self._on_calculation_needed)
    
    def _create_menu(self):
        """创建菜单"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="新建", command=self._new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="打开...", command=self._open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="保存...", command=self._save_file, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="添加动作", command=self._add_skill, accelerator="Insert")
        edit_menu.add_command(label="删除选中", command=self._delete_skill, accelerator="Delete")
        edit_menu.add_separator()
        edit_menu.add_command(label="复制", command=self._copy_skills, accelerator="Ctrl+C")
        edit_menu.add_command(label="粘贴", command=self._paste_skills, accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="批量添加...", command=self._batch_add)
        
        # 计算菜单
        calc_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="计算", menu=calc_menu)
        calc_menu.add_command(label="重新计算", command=self._calculate_all, accelerator="F5")
        
        # 绑定快捷键
        self.root.bind("<Control-n>", lambda e: self._new_file())
        self.root.bind("<Control-o>", lambda e: self._open_file())
        self.root.bind("<Control-s>", lambda e: self._save_file())
        self.root.bind("<Control-c>", lambda e: self._copy_skills())
        self.root.bind("<Control-v>", lambda e: self._paste_skills())
        self.root.bind("<Insert>", lambda e: self._add_skill())
        self.root.bind("<F5>", lambda e: self._calculate_all())
    
    def _create_ui(self):
        """创建界面"""
        # 顶部工具栏
        toolbar = ttk.Frame(self.root, padding=5)
        toolbar.pack(fill="x")
        
        # 环境设置
        env_frame = ttk.LabelFrame(toolbar, text="环境", padding=5)
        env_frame.pack(side="left", fill="x", padx=5)
        
        ttk.Label(env_frame, text="怪物等级:").pack(side="left", padx=2)
        self.enemy_level_var = tk.IntVar(value=100)
        ttk.Spinbox(env_frame, from_=1, to=200, textvariable=self.enemy_level_var, 
                   width=8).pack(side="left", padx=2)
        
        ttk.Label(env_frame, text="抗性区:").pack(side="left", padx=2)
        self.resistance_var = tk.DoubleVar(value=0.8)
        ttk.Spinbox(env_frame, from_=0, to=2, increment=0.01, textvariable=self.resistance_var,
                   width=8).pack(side="left", padx=2)
        
        ttk.Label(env_frame, text="秒数:").pack(side="left", padx=2)
        self.time_var = tk.DoubleVar(value=25.0)
        ttk.Spinbox(env_frame, from_=1, to=300, increment=0.5, textvariable=self.time_var,
                   width=8).pack(side="left", padx=2)
        
        # 角色切换
        char_frame = ttk.LabelFrame(toolbar, text="角色", padding=5)
        char_frame.pack(side="left", fill="x", padx=10)
        
        self.char_selector = ttk.Combobox(char_frame, state="readonly", width=15)
        self.char_selector.pack(side="left", padx=2)
        self.char_selector.bind("<<ComboboxSelected>>", self._on_char_change)
        
        ttk.Button(char_frame, text="+", width=3, command=self._add_character).pack(side="left", padx=2)
        ttk.Button(char_frame, text="-", width=3, command=self._remove_character).pack(side="left", padx=2)
        
        # 统计信息
        stats_frame = ttk.LabelFrame(toolbar, text="统计", padding=5)
        stats_frame.pack(side="right", fill="x", padx=5)
        
        self.total_damage_var = tk.StringVar(value="总伤害: 0")
        ttk.Label(stats_frame, textvariable=self.total_damage_var, 
                 font=("Arial", 11, "bold"), foreground="blue").pack(side="left", padx=10)
        
        self.dps_var = tk.StringVar(value="DPS: 0")
        ttk.Label(stats_frame, textvariable=self.dps_var, 
                 font=("Arial", 11, "bold"), foreground="red").pack(side="left", padx=10)
        
        # 主内容区
        content = ttk.PanedWindow(self.root, orient="horizontal")
        content.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 左侧：技能表格
        left_frame = ttk.Frame(content)
        content.add(left_frame, weight=3)
        
        # 表格工具栏
        table_toolbar = ttk.Frame(left_frame)
        table_toolbar.pack(fill="x", pady=2)
        
        ttk.Button(table_toolbar, text="添加", command=self._add_skill).pack(side="left", padx=2)
        ttk.Button(table_toolbar, text="删除", command=self._delete_skill).pack(side="left", padx=2)
        ttk.Button(table_toolbar, text="复制", command=self._copy_skills).pack(side="left", padx=2)
        ttk.Button(table_toolbar, text="粘贴", command=self._paste_skills).pack(side="left", padx=2)
        ttk.Separator(table_toolbar, orient="vertical").pack(side="left", fill="y", padx=5)
        ttk.Button(table_toolbar, text="批量添加", command=self._batch_add).pack(side="left", padx=2)
        ttk.Button(table_toolbar, text="计算", command=self._calculate_all).pack(side="left", padx=2)
        
        # 技能表格
        self.skill_table = SkillTable(left_frame, self.current_character, self._on_data_change)
        self.skill_table.pack(fill="both", expand=True)
        
        # 右侧：叠层面板
        right_frame = ttk.Frame(content, width=300)
        content.add(right_frame, weight=1)
        
        self.layer_panel = LayerPanel(right_frame, self.current_character, self._on_data_change)
        self.layer_panel.pack(fill="both", expand=True)
        
        # 更新角色选择器
        self._update_char_selector()
    
    @property
    def current_character(self) -> Character:
        """获取当前角色"""
        if 0 <= self.current_char_index < len(self.team.characters):
            return self.team.characters[self.current_char_index]
        # 创建默认角色
        char = Character(name="新角色")
        self.team.characters.append(char)
        self.current_char_index = 0
        return char
    
    def _update_char_selector(self):
        """更新角色选择器"""
        char_names = [c.name for c in self.team.characters]
        self.char_selector['values'] = char_names
        if char_names:
            self.char_selector.set(char_names[self.current_char_index])
    
    def _on_char_change(self, event=None):
        """角色切换"""
        selected = self.char_selector.current()
        if selected >= 0:
            self.current_char_index = selected
            self.skill_table.character = self.current_character
            self.layer_panel.character = self.current_character
            self.skill_table.refresh()
            self.layer_panel._refresh_layers()
            self._update_stats()
    
    def _on_data_change(self):
        """数据变更"""
        self._calculate_all()
    
    def _on_skill_changed(self, data=None):
        """技能变更事件"""
        self._update_stats()
    
    def _on_calculation_needed(self, data=None):
        """需要计算事件"""
        self._calculate_all()
    
    def _update_stats(self):
        """更新统计"""
        total = self.team.get_team_damage()
        dps = total / self.time_var.get() if self.time_var.get() > 0 else 0
        
        self.total_damage_var.set(f"总伤害: {total:,.0f}")
        self.dps_var.set(f"DPS: {dps:,.0f}")
    
    def _add_character(self):
        """添加角色"""
        char = Character(name=f"角色{len(self.team.characters) + 1}")
        self.team.characters.append(char)
        self._update_char_selector()
        self.char_selector.set(char.name)
        self._on_char_change()
    
    def _remove_character(self):
        """删除角色"""
        if len(self.team.characters) > 1:
            self.team.remove_character(self.current_char_index)
            self.current_char_index = max(0, self.current_char_index - 1)
            self._update_char_selector()
            self._on_char_change()
    
    def _add_skill(self):
        """添加动作"""
        self.skill_table.add_skills(1)
    
    def _batch_add(self):
        """批量添加"""
        dialog = tk.Toplevel(self.root)
        dialog.title("批量添加动作")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="添加数量:").pack(pady=10)
        
        count_var = tk.IntVar(value=5)
        ttk.Spinbox(dialog, from_=1, to=100, textvariable=count_var, width=10).pack()
        
        def confirm():
            self.skill_table.add_skills(count_var.get())
            dialog.destroy()
        
        ttk.Button(dialog, text="确定", command=confirm).pack(pady=20)
    
    def _delete_skill(self):
        """删除动作"""
        self.skill_table.delete_selected()
    
    def _copy_skills(self):
        """复制动作"""
        self.clipboard_skills = self.skill_table.copy_selected()
        messagebox.showinfo("复制", f"已复制 {len(self.clipboard_skills)} 个动作")
    
    def _paste_skills(self):
        """粘贴动作"""
        if self.clipboard_skills:
            self.skill_table.paste_skills(self.clipboard_skills)
            messagebox.showinfo("粘贴", f"已粘贴 {len(self.clipboard_skills)} 个动作")
    
    def _calculate_all(self):
        """计算所有"""
        self.skill_table.calculate_all()
        self._update_stats()
    
    def _new_file(self):
        """新建文件"""
        self.team = Team(name="新队伍")
        char = Character(name="角色1")
        self.team.characters.append(char)
        self.current_char_index = 0
        self._update_char_selector()
        self._on_char_change()
    
    def _open_file(self):
        """打开文件"""
        file_path = filedialog.askopenfilename(
            title="选择拉表文件",
            filetypes=[("Excel文件", "*.xlsx *.xls"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                self.team = self.excel_handler.load(file_path)
                self.current_char_index = 0
                self._update_char_selector()
                self._on_char_change()
                messagebox.showinfo("成功", f"已加载: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"加载失败:\n{str(e)}")
    
    def _save_file(self):
        """保存文件"""
        file_path = filedialog.asksaveasfilename(
            title="保存拉表文件",
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                self.excel_handler.save(self.team, file_path)
                messagebox.showinfo("成功", f"已保存: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败:\n{str(e)}")
    
    def run(self):
        """运行"""
        self.root.mainloop()


def main():
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
