# -*- coding: utf-8 -*-
"""
鸣潮DPS计算器 v2.0 - 专业版

核心特性：
1. 特殊层数系统 - 每个动作独立的可配置层数
2. 高自由度界面 - 类似Excel的表格编辑
3. 现代化UI - 专业美观的界面设计
4. 实时计算 - 修改即更新
5. Sheet选择导入 - 支持多Sheet文件

使用方法:
    python main_pro.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from typing import List, Dict, Optional
import pandas as pd
from dataclasses import dataclass, field
from pathlib import Path
import copy


# ==================== 数据模型 ====================

@dataclass
class Skill:
    """动作数据 - 每个动作都有独立的特殊层数"""
    # 基础信息
    name: str = "新动作"
    skill_type: str = "a"
    count: int = 1
    
    # 输入值
    multiplier: float = 0  # 倍率(%)
    panel_atk: float = 0   # 面板攻击
    
    # 乘区
    atk_zone: float = 1.0
    bonus_zone: float = 1.0
    crit_zone: float = 1.0
    amplify_zone: float = 0
    defense_zone: float = 0.5
    resistance_zone: float = 0.8
    
    # 特殊乘区
    multiplier_boost: float = 0
    vulnerable_zone: float = 0
    independent_zone: float = 1.0
    
    # 特殊层数 - 每个动作独立！
    special_layer: int = 0  # 特殊层数，用户自由定义用途
    
    # 计算结果
    damage: float = 0
    total_damage: float = 0
    
    def calculate(self) -> float:
        """计算伤害"""
        self.damage = (
            self.panel_atk *
            (self.multiplier / 100) *
            self.atk_zone *
            self.bonus_zone *
            self.crit_zone *
            (1 + self.amplify_zone) *
            self.defense_zone *
            self.resistance_zone *
            (1 + self.multiplier_boost) *
            (1 + self.vulnerable_zone) *
            self.independent_zone
        )
        self.total_damage = self.damage * self.count
        return self.damage


@dataclass
class Character:
    """角色"""
    name: str = "新角色"
    skills: List[Skill] = field(default_factory=list)
    
    def add_skill(self, skill: Skill = None) -> Skill:
        if skill is None:
            skill = Skill(name=f"动作{len(self.skills)+1}")
        self.skills.append(skill)
        return skill
    
    def remove_skills(self, indices: List[int]):
        for idx in sorted(indices, reverse=True):
            if 0 <= idx < len(self.skills):
                del self.skills[idx]
    
    def get_total_damage(self) -> float:
        return sum(s.total_damage for s in self.skills)


@dataclass
class Team:
    """队伍"""
    name: str = ""
    characters: List[Character] = field(default_factory=list)
    time_seconds: float = 25.0
    
    def add_character(self, char: Character = None) -> Character:
        if char is None:
            char = Character(name=f"角色{len(self.characters)+1}")
        self.characters.append(char)
        return char
    
    def get_team_damage(self) -> float:
        return sum(c.get_total_damage() for c in self.characters)
    
    def get_team_dps(self) -> float:
        return self.get_team_damage() / self.time_seconds if self.time_seconds > 0 else 0


# ==================== Excel处理器 ====================

class ExcelHandler:
    """Excel处理器 - 支持Sheet选择"""
    
    def load(self, file_path: str, sheet_name: str = None) -> Team:
        """加载Excel文件"""
        xlsx = pd.ExcelFile(file_path)
        
        # 如果没有指定sheet，使用第一个
        if sheet_name is None:
            sheet_name = xlsx.sheet_names[0]
        
        df = pd.read_excel(xlsx, sheet_name=sheet_name, header=None)
        
        team = Team(name=Path(file_path).stem)
        
        # 查找角色分块
        char_starts = []
        for i in range(len(df)):
            row = df.iloc[i]
            for j, val in enumerate(row):
                if pd.notna(val) and str(val).strip() == "角色主类型":
                    char_starts.append(i)
                    break
        
        # 解析每个角色
        for start_row in char_starts:
            char = self._parse_character(df, start_row)
            if char and char.skills:
                team.characters.append(char)
        
        return team
    
    def _parse_character(self, df: pd.DataFrame, start_row: int) -> Optional[Character]:
        """解析角色"""
        try:
            # 获取角色名
            char_name = ""
            if start_row + 1 < len(df):
                name_val = df.iloc[start_row + 1, 1]
                if pd.notna(name_val):
                    char_name = str(name_val).strip()
            
            if not char_name:
                return None
            
            char = Character(name=char_name)
            
            # 查找技能起始行
            skill_start = None
            for i in range(start_row + 1, min(start_row + 15, len(df))):
                row = df.iloc[i]
                for j, val in enumerate(row):
                    if pd.notna(val) and str(val).strip() == "次数":
                        skill_start = i + 1
                        break
                if skill_start:
                    break
            
            if not skill_start:
                return char
            
            # 解析技能
            for i in range(skill_start, min(skill_start + 100, len(df))):
                row = df.iloc[i]
                
                if len(row) <= 14:
                    continue
                
                count_val = row.iloc[14] if len(row) > 14 else None
                if pd.isna(count_val):
                    # 检查是否新角色
                    if len(row) > 1 and pd.notna(row.iloc[1]):
                        if str(row.iloc[1]).strip() == "角色主类型":
                            break
                    continue
                
                try:
                    skill = Skill()
                    skill.count = int(float(count_val))
                    
                    # 动作名
                    if len(row) > 15 and pd.notna(row.iloc[15]):
                        skill.name = str(row.iloc[15]).strip()
                    
                    # 倍率
                    if len(row) > 16 and pd.notna(row.iloc[16]):
                        val = str(row.iloc[16]).strip().replace('%', '')
                        val = float(val)
                        if val < 10:  # Excel百分比格式
                            val = val * 100
                        skill.multiplier = val
                    
                    # 类型
                    if len(row) > 17 and pd.notna(row.iloc[17]):
                        skill.skill_type = str(row.iloc[17]).strip()
                    
                    # 面板攻击
                    if len(row) > 18 and pd.notna(row.iloc[18]):
                        skill.panel_atk = float(row.iloc[18])
                    
                    # 攻击区
                    if len(row) > 19 and pd.notna(row.iloc[19]):
                        val = str(row.iloc[19]).strip().replace('%', '')
                        skill.atk_zone = 1 + float(val) / 100 if float(val) > 10 else float(val)
                    
                    # 加成区
                    if len(row) > 20 and pd.notna(row.iloc[20]):
                        val = str(row.iloc[20]).strip().replace('%', '')
                        skill.bonus_zone = 1 + float(val) / 100 if float(val) > 10 else float(val)
                    
                    # 双爆区
                    if len(row) > 21 and pd.notna(row.iloc[21]):
                        skill.crit_zone = float(row.iloc[21])
                    
                    # 加深区
                    if len(row) > 22 and pd.notna(row.iloc[22]):
                        skill.amplify_zone = float(row.iloc[22])
                    
                    # 防御区
                    if len(row) > 23 and pd.notna(row.iloc[23]):
                        skill.defense_zone = float(row.iloc[23])
                    
                    # 抗性区
                    if len(row) > 24 and pd.notna(row.iloc[24]):
                        skill.resistance_zone = float(row.iloc[24])
                    
                    # 特殊层数（如果存在）
                    if len(row) > 31 and pd.notna(row.iloc[31]):
                        skill.special_layer = int(float(row.iloc[31]))
                    
                    skill.calculate()
                    char.skills.append(skill)
                    
                except Exception as e:
                    continue
            
            return char
            
        except Exception as e:
            print(f"解析角色失败: {e}")
            return None
    
    def get_sheet_names(self, file_path: str) -> List[str]:
        """获取所有Sheet名称"""
        xlsx = pd.ExcelFile(file_path)
        return xlsx.sheet_names


# ==================== GUI ====================

class ModernSkillTable(ttk.Frame):
    """现代化技能表格"""
    
    COLUMNS = [
        ('count', '次数', 50),
        ('name', '动作', 120),
        ('multiplier', '倍率(%)', 80),
        ('skill_type', '类型', 50),
        ('panel_atk', '面板攻击', 80),
        ('atk_zone', '攻击区', 70),
        ('bonus_zone', '加成区', 70),
        ('crit_zone', '双爆区', 70),
        ('amplify_zone', '加深区', 70),
        ('defense_zone', '防御区', 70),
        ('resistance_zone', '抗性区', 70),
        ('multiplier_boost', '倍率提升', 70),
        ('vulnerable_zone', '易伤区', 70),
        ('independent_zone', '独立乘区', 70),
        ('special_layer', '特殊层数', 70),  # 新增！
        ('damage', '伤害', 90),
        ('total_damage', '总伤害', 90),
    ]
    
    def __init__(self, parent, character: Character, on_change=None):
        super().__init__(parent)
        self.character = character
        self.on_change = on_change
        
        self._create_ui()
    
    def _create_ui(self):
        """创建界面"""
        # 工具栏
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=2)
        
        ttk.Button(toolbar, text="➕ 添加", command=self._add_skill).pack(side="left", padx=2)
        ttk.Button(toolbar, text="🗑️ 删除", command=self._delete_selected).pack(side="left", padx=2)
        ttk.Button(toolbar, text="📋 复制", command=self._copy).pack(side="left", padx=2)
        ttk.Button(toolbar, text="📄 粘贴", command=self._paste).pack(side="left", padx=2)
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=5)
        ttk.Button(toolbar, text="⚡ 计算", command=self._calculate).pack(side="left", padx=2)
        
        # 表格
        columns = [c[0] for c in self.COLUMNS]
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=25)
        
        for col_id, col_name, col_width in self.COLUMNS:
            self.tree.heading(col_id, text=col_name)
            self.tree.column(col_id, width=col_width, anchor="center")
        
        # 滚动条
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        # 绑定事件
        self.tree.bind("<Double-1>", self._on_double_click)
        self.clipboard = []
        
        self.refresh()
    
    def refresh(self):
        """刷新"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for i, skill in enumerate(self.character.skills):
            values = (
                skill.count,
                skill.name,
                f"{skill.multiplier:.2f}",
                skill.skill_type,
                int(skill.panel_atk) if skill.panel_atk else "",
                f"{skill.atk_zone:.4f}",
                f"{skill.bonus_zone:.4f}",
                f"{skill.crit_zone:.4f}",
                skill.amplify_zone,
                f"{skill.defense_zone:.4f}",
                skill.resistance_zone,
                f"{skill.multiplier_boost*100:.0f}%",
                f"{skill.vulnerable_zone*100:.0f}%",
                f"{(skill.independent_zone-1)*100:.0f}%",
                skill.special_layer,  # 特殊层数
                int(skill.damage) if skill.damage else "",
                int(skill.total_damage) if skill.total_damage else "",
            )
            self.tree.insert("", "end", iid=str(i), values=values)
    
    def _on_double_click(self, event):
        """双击编辑"""
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        
        if not item or not column:
            return
        
        col_idx = int(column[1:]) - 1
        if col_idx < 0 or col_idx >= len(self.COLUMNS):
            return
        
        col_id = self.COLUMNS[col_idx][0]
        if col_id in ('damage', 'total_damage'):
            return  # 计算结果不可编辑
        
        skill_idx = int(item)
        if skill_idx >= len(self.character.skills):
            return
        
        x, y, width, height = self.tree.bbox(item, column)
        
        entry = ttk.Entry(self.tree, width=width//8)
        entry.place(x=x, y=y, width=width, height=height)
        
        current = self.tree.item(item, "values")[col_idx]
        entry.insert(0, str(current).replace("%", ""))
        entry.select_range(0, tk.END)
        entry.focus()
        
        def save(event=None):
            try:
                val = entry.get().strip().replace("%", "")
                skill = self.character.skills[skill_idx]
                
                if col_id == 'count':
                    skill.count = int(float(val))
                elif col_id == 'name':
                    skill.name = val
                elif col_id == 'multiplier':
                    skill.multiplier = float(val)
                elif col_id == 'skill_type':
                    skill.skill_type = val
                elif col_id == 'panel_atk':
                    skill.panel_atk = float(val)
                elif col_id == 'atk_zone':
                    skill.atk_zone = float(val)
                elif col_id == 'bonus_zone':
                    skill.bonus_zone = float(val)
                elif col_id == 'crit_zone':
                    skill.crit_zone = float(val)
                elif col_id == 'amplify_zone':
                    skill.amplify_zone = float(val)
                elif col_id == 'defense_zone':
                    skill.defense_zone = float(val)
                elif col_id == 'resistance_zone':
                    skill.resistance_zone = float(val)
                elif col_id == 'multiplier_boost':
                    skill.multiplier_boost = float(val) / 100
                elif col_id == 'vulnerable_zone':
                    skill.vulnerable_zone = float(val) / 100
                elif col_id == 'independent_zone':
                    skill.independent_zone = 1 + float(val) / 100
                elif col_id == 'special_layer':
                    skill.special_layer = int(float(val))
                
                skill.calculate()
                self.refresh()
                if self.on_change:
                    self.on_change()
            except:
                pass
            entry.destroy()
        
        entry.bind("<Return>", save)
        entry.bind("<FocusOut>", save)
    
    def _add_skill(self):
        """添加动作"""
        count = simpledialog.askinteger("批量添加", "添加数量:", initialvalue=1, minvalue=1, maxvalue=100)
        if count:
            for _ in range(count):
                self.character.add_skill()
            self.refresh()
            if self.on_change:
                self.on_change()
    
    def _delete_selected(self):
        """删除选中"""
        selected = [int(i) for i in self.tree.selection()]
        if selected:
            self.character.remove_skills(selected)
            self.refresh()
            if self.on_change:
                self.on_change()
    
    def _copy(self):
        """复制"""
        selected = [int(i) for i in self.tree.selection()]
        self.clipboard = [copy.deepcopy(self.character.skills[i]) for i in selected]
        messagebox.showinfo("复制", f"已复制 {len(self.clipboard)} 个动作")
    
    def _paste(self):
        """粘贴"""
        if self.clipboard:
            for skill in self.clipboard:
                self.character.skills.append(copy.deepcopy(skill))
            self.refresh()
            if self.on_change:
                self.on_change()
            messagebox.showinfo("粘贴", f"已粘贴 {len(self.clipboard)} 个动作")
    
    def _calculate(self):
        """计算"""
        for skill in self.character.skills:
            skill.calculate()
        self.refresh()
        if self.on_change:
            self.on_change()


class DPSPanel(ttk.LabelFrame):
    """DPS面板"""
    
    def __init__(self, parent, team: Team):
        super().__init__(parent, text="DPS统计", padding=10)
        self.team = team
        
        self.labels = {}
        self._create_ui()
    
    def _create_ui(self):
        """创建界面"""
        # 表头
        headers = ["角色", "总伤害", "DPS", "占比"]
        for col, header in enumerate(headers):
            lbl = ttk.Label(self, text=header, font=("Arial", 10, "bold"))
            lbl.grid(row=0, column=col, padx=10, pady=5)
        
        # 数据行
        for i in range(6):
            row_labels = {}
            for col in range(4):
                lbl = ttk.Label(self, text="-", font=("Arial", 9))
                lbl.grid(row=i+1, column=col, padx=10, pady=2)
                row_labels[col] = lbl
            self.labels[i] = row_labels
    
    def update(self):
        """更新显示"""
        total = self.team.get_team_damage()
        
        for i, char in enumerate(self.team.characters):
            if i >= 6:
                break
            
            char_total = char.get_total_damage()
            char_dps = char_total / self.team.time_seconds if self.team.time_seconds > 0 else 0
            pct = (char_total / total * 100) if total > 0 else 0
            
            self.labels[i][0].config(text=char.name)
            self.labels[i][1].config(text=f"{char_total:,.0f}")
            self.labels[i][2].config(text=f"{char_dps:,.0f}")
            self.labels[i][3].config(text=f"{pct:.1f}%")
        
        for i in range(len(self.team.characters), 6):
            for col in range(4):
                self.labels[i][col].config(text="-")


class MainWindow:
    """主窗口 v2.0"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("鸣潮DPS计算器 v2.0 - 专业版")
        self.root.geometry("1920x1080")
        
        # 设置主题
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 初始化数据
        self.excel_handler = ExcelHandler()
        self.team = Team(name="新队伍")
        char = Character(name="角色1")
        self.team.characters.append(char)
        self.current_char_idx = 0
        
        self._create_ui()
    
    def _create_ui(self):
        """创建界面"""
        # 顶部工具栏
        toolbar = ttk.Frame(self.root, padding=10)
        toolbar.pack(fill="x")
        
        # 文件操作
        file_frame = ttk.LabelFrame(toolbar, text="文件", padding=5)
        file_frame.pack(side="left", padx=5)
        ttk.Button(file_frame, text="📂 打开", command=self._open_file).pack(side="left", padx=2)
        ttk.Button(file_frame, text="💾 保存", command=self._save_file).pack(side="left", padx=2)
        ttk.Button(file_frame, text="📝 新建", command=self._new_file).pack(side="left", padx=2)
        
        # 环境设置
        env_frame = ttk.LabelFrame(toolbar, text="环境", padding=5)
        env_frame.pack(side="left", padx=10)
        
        ttk.Label(env_frame, text="秒数:").pack(side="left", padx=2)
        self.time_var = tk.DoubleVar(value=25.0)
        ttk.Spinbox(env_frame, from_=1, to=300, increment=0.5, textvariable=self.time_var,
                   width=8, command=self._update).pack(side="left", padx=2)
        
        # 角色选择
        char_frame = ttk.LabelFrame(toolbar, text="角色", padding=5)
        char_frame.pack(side="left", padx=10)
        
        self.char_name_var = tk.StringVar(value=self.current_char.name)
        ttk.Entry(char_frame, textvariable=self.char_name_var, width=15).pack(side="left", padx=2)
        ttk.Button(char_frame, text="✓", width=3, command=self._rename_char).pack(side="left", padx=2)
        
        self.char_combo = ttk.Combobox(char_frame, state="readonly", width=12)
        self.char_combo.pack(side="left", padx=2)
        self.char_combo.bind("<<ComboboxSelected>>", self._switch_char)
        
        ttk.Button(char_frame, text="+", width=3, command=self._add_char).pack(side="left", padx=2)
        ttk.Button(char_frame, text="-", width=3, command=self._remove_char).pack(side="left", padx=2)
        
        # DPS面板
        self.dps_panel = DPSPanel(toolbar, self.team)
        self.dps_panel.pack(side="right", padx=10)
        
        # 主内容区
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 技能表格
        self.skill_table = ModernSkillTable(main_frame, self.current_char, self._update)
        self.skill_table.pack(fill="both", expand=True)
        
        # 更新角色列表
        self._update_char_list()
    
    @property
    def current_char(self) -> Character:
        """当前角色"""
        if 0 <= self.current_char_idx < len(self.team.characters):
            return self.team.characters[self.current_char_idx]
        return self.team.characters[0] if self.team.characters else Character()
    
    def _update_char_list(self):
        """更新角色列表"""
        names = [c.name for c in self.team.characters]
        self.char_combo['values'] = names
        if names:
            self.char_combo.set(names[self.current_char_idx])
            self.char_name_var.set(names[self.current_char_idx])
    
    def _rename_char(self):
        """重命名角色"""
        new_name = self.char_name_var.get().strip()
        if new_name:
            self.current_char.name = new_name
            self._update_char_list()
    
    def _switch_char(self, event=None):
        """切换角色"""
        idx = self.char_combo.current()
        if idx >= 0:
            self.current_char_idx = idx
            self.skill_table.character = self.current_char
            self.char_name_var.set(self.current_char.name)
            self.skill_table.refresh()
    
    def _add_char(self):
        """添加角色"""
        char = Character(name=f"角色{len(self.team.characters)+1}")
        self.team.characters.append(char)
        self.current_char_idx = len(self.team.characters) - 1
        self._update_char_list()
        self._switch_char()
    
    def _remove_char(self):
        """删除角色"""
        if len(self.team.characters) > 1:
            del self.team.characters[self.current_char_idx]
            self.current_char_idx = max(0, self.current_char_idx - 1)
            self._update_char_list()
            self._switch_char()
    
    def _update(self):
        """更新"""
        self.team.time_seconds = self.time_var.get()
        self.dps_panel.update()
    
    def _new_file(self):
        """新建"""
        self.team = Team(name="新队伍")
        char = Character(name="角色1")
        self.team.characters.append(char)
        self.current_char_idx = 0
        self._update_char_list()
        self._switch_char()
    
    def _open_file(self):
        """打开文件 - 支持Sheet选择"""
        file_path = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel文件", "*.xlsx *.xls")]
        )
        if not file_path:
            return
        
        try:
            # 获取所有Sheet名称
            sheet_names = self.excel_handler.get_sheet_names(file_path)
            
            if len(sheet_names) > 1:
                # 多Sheet，让用户选择
                sheet_window = tk.Toplevel(self.root)
                sheet_window.title("选择Sheet")
                sheet_window.geometry("300x200")
                sheet_window.transient(self.root)
                sheet_window.grab_set()
                
                ttk.Label(sheet_window, text="选择要导入的Sheet:").pack(pady=10)
                
                sheet_var = tk.StringVar(value=sheet_names[0])
                sheet_combo = ttk.Combobox(sheet_window, values=sheet_names, state="readonly", width=25)
                sheet_combo.set(sheet_names[0])
                sheet_combo.pack(pady=10)
                
                def do_load():
                    selected_sheet = sheet_combo.get()
                    sheet_window.destroy()
                    self._load_sheet(file_path, selected_sheet)
                
                ttk.Button(sheet_window, text="确定", command=do_load).pack(pady=20)
            else:
                # 单Sheet直接加载
                self._load_sheet(file_path, sheet_names[0])
                
        except Exception as e:
            messagebox.showerror("错误", f"加载失败:\n{str(e)}")
    
    def _load_sheet(self, file_path: str, sheet_name: str):
        """加载指定Sheet"""
        self.team = self.excel_handler.load(file_path, sheet_name)
        self.current_char_idx = 0
        self._update_char_list()
        self._switch_char()
        messagebox.showinfo("成功", f"已加载 [{sheet_name}]\n共 {len(self.team.characters)} 个角色")
    
    def _save_file(self):
        """保存文件"""
        messagebox.showinfo("提示", "保存功能开发中...")
    
    def run(self):
        """运行"""
        self.root.mainloop()


def main():
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
