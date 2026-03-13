# -*- coding: utf-8 -*-
"""
鸣潮DPS计算器 v1.0 - 图形化界面
表格形式，支持大量动作编辑
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, List
from calculator import WuWaCalculator, Team, Character, Skill, Environment


class SkillTable(ttk.Frame):
    """技能表格 - 可编辑的表格形式"""
    
    def __init__(self, parent, skills: List[Skill], on_change=None):
        super().__init__(parent)
        self.skills = skills
        self.on_change = on_change
        
        # 创建表格
        columns = ("次数", "动作", "倍率", "类型", "面板攻击", "攻击区", "加成区", 
                   "双爆区", "加深区", "防御区", "抗性区", "倍率提升", "易伤区", 
                   "独立乘区", "伤害", "余响", "溢出")
        
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=20)
        
        # 设置列标题
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80, anchor="center")
        
        # 特殊列宽
        self.tree.column("动作", width=120)
        self.tree.column("伤害", width=100)
        
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
        
        # 绑定双击编辑
        self.tree.bind("<Double-1>", self._on_double_click)
        
        # 刷新显示
        self._refresh()
    
    def _refresh(self):
        """刷新表格显示"""
        # 清空
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 填充数据
        for i, skill in enumerate(self.skills):
            values = (
                skill.count,
                skill.name,
                f"{skill.multiplier:.2f}%",
                skill.skill_type,
                int(skill.panel_atk) if skill.panel_atk else "",
                f"{(skill.atk_zone - 1) * 100:.2f}%" if skill.atk_zone != 1 else "",
                f"{(skill.bonus_zone - 1) * 100:.2f}%" if skill.bonus_zone != 1 else "",
                f"{skill.crit_zone:.4f}" if skill.crit_zone else "",
                skill.amplify_zone,
                f"{skill.defense_zone:.4f}" if skill.defense_zone else "",
                skill.resistance_zone,
                f"{skill.multiplier_boost * 100:.0f}%",
                f"{skill.vulnerable_zone * 100:.0f}%",
                f"{(skill.independent_zone - 1) * 100:.0f}%",
                int(skill.damage) if skill.damage else "",
                skill.echo,
                skill.overflow
            )
            self.tree.insert("", "end", iid=str(i), values=values)
    
    def _on_double_click(self, event):
        """双击编辑"""
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        
        if not item or not column:
            return
        
        col_idx = int(column[1:]) - 1  # 转换为0-based索引
        if col_idx < 0 or col_idx >= len(self.skills):
            return
        
        skill_idx = int(item)
        if skill_idx >= len(self.skills):
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
        
        # 绑定回车和失去焦点
        def _save_edit(event=None):
            new_value = entry.get()
            entry.destroy()
            self._update_skill(skill_idx, col_idx, new_value)
        
        entry.bind("<Return>", _save_edit)
        entry.bind("<FocusOut>", _save_edit)
    
    def _update_skill(self, skill_idx: int, col_idx: int, value: str):
        """更新技能数据"""
        try:
            skill = self.skills[skill_idx]
            value = value.strip()
            
            # 根据列索引更新对应字段
            if col_idx == 0:  # 次数
                skill.count = int(float(value))
            elif col_idx == 1:  # 动作
                skill.name = value
            elif col_idx == 2:  # 倍率
                skill.multiplier = float(value)
            elif col_idx == 3:  # 类型
                skill.skill_type = value
            elif col_idx == 4:  # 面板攻击
                skill.panel_atk = float(value)
            elif col_idx == 5:  # 攻击区
                skill.atk_zone = 1 + float(value) / 100
            elif col_idx == 6:  # 加成区
                skill.bonus_zone = 1 + float(value) / 100
            elif col_idx == 7:  # 双爆区
                skill.crit_zone = float(value)
            elif col_idx == 8:  # 加深区
                skill.amplify_zone = float(value)
            elif col_idx == 9:  # 防御区
                skill.defense_zone = float(value)
            elif col_idx == 10:  # 抗性区
                skill.resistance_zone = float(value)
            elif col_idx == 11:  # 倍率提升
                skill.multiplier_boost = float(value) / 100
            elif col_idx == 12:  # 易伤区
                skill.vulnerable_zone = float(value) / 100
            elif col_idx == 13:  # 独立乘区
                skill.independent_zone = 1 + float(value) / 100
            elif col_idx == 14:  # 伤害
                skill.damage = float(value)
            elif col_idx == 15:  # 余响
                skill.echo = int(float(value))
            elif col_idx == 16:  # 溢出
                skill.overflow = int(float(value))
            
            # 刷新显示
            self._refresh()
            
            # 通知父组件
            if self.on_change:
                self.on_change()
                
        except Exception as e:
            messagebox.showerror("输入错误", f"无效的值: {value}")
    
    def add_skill(self):
        """添加新技能"""
        skill = Skill(name=f"动作{len(self.skills) + 1}")
        self.skills.append(skill)
        self._refresh()
        if self.on_change:
            self.on_change()
    
    def delete_selected(self):
        """删除选中行"""
        selected = self.tree.selection()
        if selected:
            idx = int(selected[0])
            if 0 <= idx < len(self.skills):
                del self.skills[idx]
                self._refresh()
                if self.on_change:
                    self.on_change()
    
    def calculate_all(self):
        """计算所有技能伤害"""
        for skill in self.skills:
            skill.calculate()
        self._refresh()


class MainWindow:
    """主窗口 - 表格形式"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("鸣潮DPS计算器 v1.0")
        self.root.geometry("1920x1080")
        
        self.calculator = WuWaCalculator()
        self.team = Team()
        
        # 创建示例角色
        char = Character(name="新角色")
        self.team.characters.append(char)
        
        self._create_menu()
        self._create_ui()
    
    def _create_menu(self):
        """创建菜单栏"""
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
        edit_menu.add_command(label="删除选中动作", command=self._delete_skill)
        edit_menu.add_separator()
        edit_menu.add_command(label="计算所有伤害", command=self._calculate_all)
    
    def _create_ui(self):
        """创建主界面"""
        # 顶部：环境设置和统计
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill="x")
        
        # 环境设置
        env_frame = ttk.LabelFrame(top_frame, text="环境设置", padding=10)
        env_frame.pack(side="left", fill="x", expand=True)
        
        ttk.Label(env_frame, text="怪物等级:").grid(row=0, column=0, sticky="w", padx=5)
        self.enemy_level_var = tk.IntVar(value=100)
        ttk.Spinbox(env_frame, from_=1, to=200, textvariable=self.enemy_level_var, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Label(env_frame, text="抗性区:").grid(row=0, column=2, sticky="w", padx=5)
        self.resistance_var = tk.DoubleVar(value=0.8)
        ttk.Spinbox(env_frame, from_=0, to=2, increment=0.01, textvariable=self.resistance_var, width=10).grid(row=0, column=3, padx=5)
        
        ttk.Label(env_frame, text="秒数:").grid(row=0, column=4, sticky="w", padx=5)
        self.time_var = tk.DoubleVar(value=25.0)
        ttk.Spinbox(env_frame, from_=1, to=300, increment=0.5, textvariable=self.time_var, width=10).grid(row=0, column=5, padx=5)
        
        # 统计信息
        stats_frame = ttk.LabelFrame(top_frame, text="统计", padding=10)
        stats_frame.pack(side="right", fill="x", padx=10)
        
        self.total_damage_var = tk.StringVar(value="总伤害: 0")
        ttk.Label(stats_frame, textvariable=self.total_damage_var, font=("Arial", 12, "bold"), foreground="blue").pack(side="left", padx=10)
        
        self.dps_var = tk.StringVar(value="DPS: 0")
        ttk.Label(stats_frame, textvariable=self.dps_var, font=("Arial", 12, "bold"), foreground="red").pack(side="left", padx=10)
        
        # 角色选择
        char_frame = ttk.Frame(self.root, padding=10)
        char_frame.pack(fill="x")
        
        ttk.Label(char_frame, text="角色:").pack(side="left", padx=5)
        self.char_name_var = tk.StringVar(value="新角色")
        ttk.Entry(char_frame, textvariable=self.char_name_var, width=20).pack(side="left", padx=5)
        
        ttk.Button(char_frame, text="添加角色", command=self._add_character).pack(side="left", padx=5)
        ttk.Button(char_frame, text="添加动作", command=self._add_skill).pack(side="left", padx=5)
        ttk.Button(char_frame, text="删除动作", command=self._delete_skill).pack(side="left", padx=5)
        ttk.Button(char_frame, text="计算", command=self._calculate_all).pack(side="left", padx=5)
        
        # 技能表格
        table_frame = ttk.Frame(self.root, padding=10)
        table_frame.pack(fill="both", expand=True)
        
        if self.team.characters:
            self.skill_table = SkillTable(table_frame, self.team.characters[0].skills, self._on_data_change)
            self.skill_table.pack(fill="both", expand=True)
    
    def _on_data_change(self):
        """数据改变时更新统计"""
        self._update_stats()
    
    def _update_stats(self):
        """更新统计信息"""
        total_damage = self.team.get_team_damage()
        dps = total_damage / self.time_var.get() if self.time_var.get() > 0 else 0
        
        self.total_damage_var.set(f"总伤害: {total_damage:,.0f}")
        self.dps_var.set(f"DPS: {dps:,.0f}")
    
    def _add_skill(self):
        """添加动作"""
        if self.team.characters:
            self.skill_table.add_skill()
    
    def _delete_skill(self):
        """删除动作"""
        if self.team.characters:
            self.skill_table.delete_selected()
    
    def _calculate_all(self):
        """计算所有伤害"""
        if self.team.characters:
            self.skill_table.calculate_all()
            self._update_stats()
    
    def _add_character(self):
        """添加角色"""
        char = Character(name=self.char_name_var.get())
        self.team.characters.append(char)
        messagebox.showinfo("提示", f"已添加角色: {char.name}")
    
    def _new_file(self):
        """新建文件"""
        self.team = Team()
        char = Character(name="新角色")
        self.team.characters.append(char)
        self.skill_table.skills = char.skills
        self.skill_table._refresh()
        self._update_stats()
    
    def _open_file(self):
        """打开文件"""
        file_path = filedialog.askopenfilename(
            title="选择拉表文件",
            filetypes=[("Excel文件", "*.xlsx *.xls"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                self.team = self.calculator.load_from_excel(file_path)
                if self.team.characters:
                    self.skill_table.skills = self.team.characters[0].skills
                    self.skill_table._refresh()
                    self.char_name_var.set(self.team.characters[0].name)
                self._update_stats()
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
                self.calculator.save_to_excel(self.team, file_path)
                messagebox.showinfo("成功", f"已保存: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败:\n{str(e)}")
    
    def run(self):
        """运行应用"""
        self.root.mainloop()


def main():
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
