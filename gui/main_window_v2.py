# -*- coding: utf-8 -*-
"""
鸣潮DPS计算器 v1.1 - 增强版主窗口

新增功能：
1. 角色属性面板（攻击/加成/暴击/爆伤/加深/副词条）
2. 可编辑角色名
3. 现代化UI风格
4. 多角色DPS对比
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import Skill, Character, Team, Environment, CharacterStats
from core.calculator import DamageCalculator
from core.events import EventBus, EventType
from core.layers import LayerSystem
from dataio.excel_handler import ExcelHandler


class CharacterStatsPanel(ttk.LabelFrame):
    """角色属性面板 - 类似Excel的表格形式"""
    
    def __init__(self, parent, character: Character, on_change=None):
        super().__init__(parent, text="角色属性面板", padding=5)
        self.character = character
        self.on_change = on_change
        
        # 创建属性表格
        self._create_stats_table()
    
    def _create_stats_table(self):
        """创建属性表格"""
        stats = self.character.stats
        
        # 使用网格布局创建类似Excel的表格
        # 第0行：标题
        headers = ["", "攻击", "", "加成区", "", "暴击", "", "暴击伤害", "", "加深区", "", "副词条"]
        for col, header in enumerate(headers):
            ttk.Label(self, text=header, font=("Arial", 9, "bold"), 
                     background="#4472C4", foreground="white").grid(
                row=0, column=col, sticky="nsew", padx=1, pady=1)
        
        # 属性数据
        data_rows = [
            # (行标签, 属性名, 值, 行标签, 属性名, 值, ...)
            ("白值", "base_atk", stats.base_atk, "3C声骸", "echo_3c_bonus", stats.echo_3c_bonus,
             "基础与固有", "base_crit_rate", stats.base_crit_rate, "基础与固有", "base_crit_dmg", stats.base_crit_dmg,
             "全加深", "universal_amplify", stats.universal_amplify, "大攻击", "atk_substat", stats.atk_substat),
            
            ("固有武器", "weapon_atk_percent", stats.weapon_atk_percent, "套装首位", "set_first_bonus", stats.set_first_bonus,
             "武器", "weapon_crit_rate", stats.weapon_crit_rate, "武器", "weapon_crit_dmg", stats.weapon_crit_dmg,
             "e加深", "e_amplify", stats.e_amplify, "共技伤害", "skill_dmg_substat", stats.skill_dmg_substat),
            
            ("主副词条", "echo_atk_percent", stats.echo_atk_percent, "自拐属伤", "self_element_buff", stats.self_element_buff,
             "套装", "set_crit_rate", stats.set_crit_rate, "套装", "set_crit_dmg", stats.set_crit_dmg,
             "q加深", "q_amplify", stats.q_amplify, "暴击", "crit_rate_substat", stats.crit_rate_substat),
            
            ("自拐攻击", "self_atk_buff", stats.self_atk_buff, "被拐属伤", "received_element_buff", stats.received_element_buff,
             "主副词条", "echo_crit_rate", stats.echo_crit_rate, "主副词条", "echo_crit_dmg", stats.echo_crit_dmg,
             "", "", "", "爆伤", "crit_dmg_substat", stats.crit_dmg_substat),
            
            ("被拐攻击", "received_atk_buff", stats.received_atk_buff, "其他属伤", "other_element_buff", stats.other_element_buff,
             "共鸣链", "chain_crit_rate", stats.chain_crit_rate, "共鸣链", "chain_crit_dmg", stats.chain_crit_dmg,
             "", "", "", "", "", ""),
            
            ("声骸固定攻击", "fixed_atk", stats.fixed_atk, "e加成", "e_bonus", stats.e_bonus,
             "队友", "teammate_crit_rate", stats.teammate_crit_rate, "队友", "teammate_crit_dmg", stats.teammate_crit_dmg,
             "", "", "", "", "", ""),
            
            ("额外固定攻击", "extra_fixed_atk", stats.extra_fixed_atk, "q加成", "q_bonus", stats.q_bonus,
             "面板暴击率", "", f"{stats.get_crit_rate()*100:.2f}%", "面板暴击伤害", "", f"{stats.get_crit_dmg()*100:.2f}%",
             "", "", "", "", "", ""),
        ]
        
        # 创建表格行
        for row_idx, row_data in enumerate(data_rows, 1):
            for col_idx in range(0, 18, 3):  # 每3列一组
                if col_idx // 3 < 6:  # 6组数据
                    label = row_data[col_idx]
                    attr = row_data[col_idx + 1] if col_idx + 1 < len(row_data) else ""
                    value = row_data[col_idx + 2] if col_idx + 2 < len(row_data) else ""
                    
                    # 标签列
                    ttk.Label(self, text=label, font=("Arial", 8), 
                             background="#E7E6E6" if row_idx % 2 == 0 else "white").grid(
                        row=row_idx, column=col_idx, sticky="nsew", padx=1, pady=1)
                    
                    # 值列（可编辑）
                    if attr:
                        var = tk.StringVar(value=str(value))
                        entry = ttk.Entry(self, textvariable=var, width=8, font=("Arial", 8))
                        entry.grid(row=row_idx, column=col_idx + 1, sticky="nsew", padx=1, pady=1)
                        entry.bind("<FocusOut>", lambda e, a=attr, v=var: self._on_value_change(a, v))
                        entry.bind("<Return>", lambda e, a=attr, v=var: self._on_value_change(a, v))
                    else:
                        ttk.Label(self, text=str(value), font=("Arial", 8),
                                 background="#FFF2CC").grid(
                            row=row_idx, column=col_idx + 1, sticky="nsew", padx=1, pady=1)
                    
                    # 空列
                    ttk.Label(self, text="", width=2).grid(
                        row=row_idx, column=col_idx + 2, sticky="nsew", padx=1, pady=1)
    
    def _on_value_change(self, attr: str, var: tk.StringVar):
        """属性值变更"""
        try:
            value = var.get().replace('%', '')
            float_value = float(value)
            setattr(self.character.stats, attr, float_value)
            if self.on_change:
                self.on_change()
        except ValueError:
            pass
    
    def refresh(self):
        """刷新显示"""
        # 清除并重建
        for widget in self.winfo_children():
            widget.destroy()
        self._create_stats_table()


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
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=20)
        
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
        
        # 刷新
        self.refresh()
    
    def refresh(self):
        """刷新表格"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for i, skill in enumerate(self.character.skills):
            values = self._skill_to_values(skill)
            self.tree.insert("", "end", iid=str(i), values=values)
    
    def _skill_to_values(self, skill: Skill) -> tuple:
        """技能转表格值"""
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
            f"{skill.defense_zone:.4f}" if skill.defense_zone else "",
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
        
        if not self.COLUMN_CONFIG[col_key]['editable']:
            return
        
        skill_idx = int(item)
        if skill_idx >= len(self.character.skills):
            return
        
        x, y, width, height = self.tree.bbox(item, column)
        
        entry = ttk.Entry(self.tree, width=width // 8)
        entry.place(x=x, y=y, width=width, height=height)
        
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
        """更新技能"""
        try:
            skill = self.character.skills[skill_idx]
            value = value.strip()
            
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
            
            skill.calculate()
            self.refresh()
            
            if self.on_change:
                self.on_change()
        except Exception as e:
            messagebox.showerror("输入错误", f"无效的值: {value}")
    
    def _on_select(self, event):
        """选择变更"""
        self.selected_indices = [int(i) for i in self.tree.selection()]
    
    def add_skills(self, count: int = 1):
        """批量添加"""
        for i in range(count):
            self.character.add_skill()
        self.refresh()
        if self.on_change:
            self.on_change()
    
    def delete_selected(self):
        """删除选中"""
        if self.selected_indices:
            self.character.remove_skills(self.selected_indices)
            self.selected_indices = []
            self.refresh()
            if self.on_change:
                self.on_change()
    
    def calculate_all(self):
        """计算所有"""
        self.character.calculate_all()
        self.refresh()


class DPSDashboard(ttk.LabelFrame):
    """DPS仪表盘 - 显示多角色DPS对比"""
    
    def __init__(self, parent, team: Team):
        super().__init__(parent, text="DPS对比", padding=5)
        self.team = team
        
        self.labels = {}
        self._create_dashboard()
    
    def _create_dashboard(self):
        """创建仪表盘"""
        # 表头
        headers = ["角色", "总伤害", "DPS", "占比"]
        for col, header in enumerate(headers):
            ttk.Label(self, text=header, font=("Arial", 9, "bold"),
                     background="#4472C4", foreground="white").grid(
                row=0, column=col, sticky="nsew", padx=1, pady=1)
        
        # 为每个角色创建行
        for i in range(6):  # 最多6个角色
            row_widgets = {}
            for col in range(4):
                lbl = ttk.Label(self, text="", font=("Arial", 9))
                lbl.grid(row=i+1, column=col, sticky="nsew", padx=1, pady=1)
                row_widgets[col] = lbl
            self.labels[i] = row_widgets
    
    def update(self):
        """更新显示"""
        total_damage = self.team.get_team_damage()
        
        for i, char in enumerate(self.team.characters):
            if i >= 6:
                break
            
            char_damage = char.get_total_damage()
            char_dps = char_damage / self.team.time_seconds if self.team.time_seconds > 0 else 0
            percentage = (char_damage / total_damage * 100) if total_damage > 0 else 0
            
            self.labels[i][0].config(text=char.name)
            self.labels[i][1].config(text=f"{char_damage:,.0f}")
            self.labels[i][2].config(text=f"{char_dps:,.0f}")
            self.labels[i][3].config(text=f"{percentage:.1f}%")
        
        # 清空剩余行
        for i in range(len(self.team.characters), 6):
            for col in range(4):
                self.labels[i][col].config(text="")


class MainWindow:
    """主窗口 v1.1"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("鸣潮DPS计算器 v1.1")
        self.root.geometry("1920x1080")
        
        # 初始化
        self.event_bus = EventBus()
        self.calculator = DamageCalculator(self.event_bus)
        self.excel_handler = ExcelHandler()
        
        self.team = Team(name="新队伍")
        char = Character(name="弗洛洛")
        self.team.characters.append(char)
        self.current_char_index = 0
        
        self.clipboard_skills: List[Skill] = []
        
        self._create_menu()
        self._create_ui()
        
        # 订阅事件
        self.event_bus.subscribe(EventType.CALCULATION_NEEDED, self._on_calculation_needed)
    
    def _create_menu(self):
        """创建菜单"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="新建", command=self._new_file)
        file_menu.add_command(label="打开...", command=self._open_file)
        file_menu.add_command(label="保存...", command=self._save_file)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="添加动作", command=self._add_skill)
        edit_menu.add_command(label="删除选中", command=self._delete_skill)
        edit_menu.add_separator()
        edit_menu.add_command(label="复制", command=self._copy_skills)
        edit_menu.add_command(label="粘贴", command=self._paste_skills)
    
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
        
        # 角色选择和编辑
        char_frame = ttk.LabelFrame(toolbar, text="角色", padding=5)
        char_frame.pack(side="left", fill="x", padx=10)
        
        # 角色名下拉框（可编辑）
        self.char_name_var = tk.StringVar(value=self.current_character.name)
        self.char_name_entry = ttk.Entry(char_frame, textvariable=self.char_name_var, width=15)
        self.char_name_entry.pack(side="left", padx=2)
        self.char_name_entry.bind("<FocusOut>", self._on_char_name_change)
        self.char_name_entry.bind("<Return>", self._on_char_name_change)
        
        self.char_selector = ttk.Combobox(char_frame, state="readonly", width=10)
        self.char_selector.pack(side="left", padx=2)
        self.char_selector.bind("<<ComboboxSelected>>", self._on_char_change)
        
        ttk.Button(char_frame, text="+", width=3, command=self._add_character).pack(side="left", padx=2)
        ttk.Button(char_frame, text="-", width=3, command=self._remove_character).pack(side="left", padx=2)
        
        # DPS仪表盘
        self.dps_dashboard = DPSDashboard(toolbar, self.team)
        self.dps_dashboard.pack(side="right", fill="y", padx=5)
        
        # 主内容区
        content = ttk.PanedWindow(self.root, orient="horizontal")
        content.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 左侧面板
        left_panel = ttk.Notebook(content)
        content.add(left_panel, weight=2)
        
        # 动作表格页
        skills_frame = ttk.Frame(left_panel)
        left_panel.add(skills_frame, text="动作列表")
        
        # 表格工具栏
        table_toolbar = ttk.Frame(skills_frame)
        table_toolbar.pack(fill="x", pady=2)
        
        ttk.Button(table_toolbar, text="添加", command=self._add_skill).pack(side="left", padx=2)
        ttk.Button(table_toolbar, text="删除", command=self._delete_skill).pack(side="left", padx=2)
        ttk.Button(table_toolbar, text="复制", command=self._copy_skills).pack(side="left", padx=2)
        ttk.Button(table_toolbar, text="粘贴", command=self._paste_skills).pack(side="left", padx=2)
        ttk.Button(table_toolbar, text="批量添加", command=self._batch_add).pack(side="left", padx=2)
        ttk.Button(table_toolbar, text="计算", command=self._calculate_all).pack(side="left", padx=2)
        
        # 技能表格
        self.skill_table = SkillTable(skills_frame, self.current_character, self._on_data_change)
        self.skill_table.pack(fill="both", expand=True)
        
        # 属性面板页
        stats_frame = ttk.Frame(left_panel)
        left_panel.add(stats_frame, text="属性面板")
        
        self.stats_panel = CharacterStatsPanel(stats_frame, self.current_character, self._on_data_change)
        self.stats_panel.pack(fill="both", expand=True)
        
        # 右侧面板
        right_panel = ttk.Frame(content, width=300)
        content.add(right_panel, weight=1)
        
        # 叠层控制
        layer_frame = ttk.LabelFrame(right_panel, text="特殊叠层", padding=10)
        layer_frame.pack(fill="x", pady=5)
        
        ttk.Button(layer_frame, text="添加奥古斯塔叠层", 
                  command=lambda: self._add_layer('augusta')).pack(fill="x", pady=2)
        ttk.Button(layer_frame, text="添加弗洛洛叠层", 
                  command=lambda: self._add_layer('flolo')).pack(fill="x", pady=2)
        ttk.Button(layer_frame, text="添加西格莉卡叠层", 
                  command=lambda: self._add_layer('sigilica')).pack(fill="x", pady=2)
        
        # 更新角色选择器
        self._update_char_selector()
    
    @property
    def current_character(self) -> Character:
        """获取当前角色"""
        if 0 <= self.current_char_index < len(self.team.characters):
            return self.team.characters[self.current_char_index]
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
            self.char_name_var.set(char_names[self.current_char_index])
    
    def _on_char_name_change(self, event=None):
        """角色名变更"""
        new_name = self.char_name_var.get().strip()
        if new_name:
            self.current_character.name = new_name
            self._update_char_selector()
    
    def _on_char_change(self, event=None):
        """角色切换"""
        selected = self.char_selector.current()
        if selected >= 0:
            self.current_char_index = selected
            self.skill_table.character = self.current_character
            self.stats_panel.character = self.current_character
            self.char_name_var.set(self.current_character.name)
            self.skill_table.refresh()
            self.stats_panel.refresh()
    
    def _on_data_change(self):
        """数据变更"""
        self._calculate_all()
    
    def _on_calculation_needed(self, data=None):
        """需要计算"""
        self._calculate_all()
    
    def _calculate_all(self):
        """计算所有"""
        self.skill_table.calculate_all()
        self.dps_dashboard.update()
    
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
        dialog.title("批量添加")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        
        ttk.Label(dialog, text="数量:").pack(pady=10)
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
        """复制"""
        self.clipboard_skills = self.skill_table.copy_selected()
        messagebox.showinfo("复制", f"已复制 {len(self.clipboard_skills)} 个动作")
    
    def _paste_skills(self):
        """粘贴"""
        if self.clipboard_skills:
            self.skill_table.paste_skills(self.clipboard_skills)
            messagebox.showinfo("粘贴", f"已粘贴 {len(self.clipboard_skills)} 个动作")
    
    def _add_layer(self, template_name: str):
        """添加叠层"""
        layer = LayerSystem.create_layer(template_name, self.current_character.name)
        if layer:
            self.current_character.special_layers.append(layer)
            messagebox.showinfo("叠层", f"已添加 {layer.name}")
    
    def _new_file(self):
        """新建"""
        self.team = Team(name="新队伍")
        char = Character(name="角色1")
        self.team.characters.append(char)
        self.current_char_index = 0
        self._update_char_selector()
        self._on_char_change()
    
    def _open_file(self):
        """打开"""
        file_path = filedialog.askopenfilename(
            title="选择文件",
            filetypes=[("Excel", "*.xlsx *.xls"), ("所有文件", "*.*")]
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
        """保存"""
        file_path = filedialog.asksaveasfilename(
            title="保存",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx"), ("所有文件", "*.*")]
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
