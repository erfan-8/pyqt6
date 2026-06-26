import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTableWidget, QTableWidgetItem, QGroupBox,
                             QHeaderView, QComboBox, QScrollArea, QMessageBox,
                             QSpinBox, QAbstractItemView, QFrame,
                             QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class TaskDef:
    def __init__(self, p_id, arrival, burst, q_level):
        self.p_id = str(p_id).strip()
        self.arrival = int(arrival)
        self.burst = int(burst)
        self.q_level = int(q_level)
        self.rem_time = self.burst
        self.end_time = 0
        self.wait_time = 0
        self.ta_time = 0
        self.start_tick = -1
        self.active_algo = ""


class MLQ_Academic_Simulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("زمان‌بند MLQ - الناز هدایت")
        self.resize(1800, 850)

        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #fafafa;
            }
            QLabel {
                color: #2c3e50;
                font-family: 'Segoe UI', 'Tahoma';
                font-size: 13px;
            }
            QGroupBox {
                background-color: #ffffff;
                color: #1a5276;
                border: 1px solid #d5dbdb;
                border-radius: 12px;
                margin-top: 18px;
                font-size: 15px;
                font-weight: bold;
                padding: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                background-color: #ffffff;
                border: 1px solid #d5dbdb;
                border-radius: 6px;
            }
            QPushButton {
                background-color: #2980b9;
                color: #ffffff;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1f6ea1;
            }
            QPushButton#ActionBtn {
                background-color: #27ae60;
                font-size: 16px;
                padding: 14px 24px;
                border-radius: 10px;
            }
            QPushButton#ActionBtn:hover {
                background-color: #1e8449;
            }
            QPushButton#TestBtn {
                background-color: #f39c12;
                color: #000000;
            }
            QPushButton#TestBtn:hover {
                background-color: #d68910;
            }
            QTableWidget {
                background-color: #ffffff;
                color: #2c3e50;
                gridline-color: #d5dbdb;
                border: 1px solid #d5dbdb;
                border-radius: 8px;
                font-size: 13px;
                alternate-background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #eaf2f8;
                color: #1a5276;
                padding: 8px;
                font-weight: bold;
                border: 1px solid #d5dbdb;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #ffffff;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 7px;
                font-size: 13px;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        self.queue_configs = []
        self.task_list = []
        self.timeline = []

        self.init_interface()

    def init_interface(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # --- هدر (فقط عنوان) ---
        header = QHBoxLayout()
        title_lbl = QLabel("🔬 سیستم شبیه‌سازی صف‌های چندسطحی (MLQ)")
        title_lbl.setStyleSheet("font-size: 20px; color: #1a5276; font-weight: bold;")
        header.addWidget(title_lbl)
        header.addStretch()
        main_layout.addLayout(header)

        # خط جداکننده
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #d5dbdb;")
        main_layout.addWidget(sep)

        # بخش میانی
        mid_layout = QHBoxLayout()

        # --- کارت فرآیندها ---
        p_card = QGroupBox("📌 تعریف فرآیندها")
        p_card_layout = QVBoxLayout(p_card)

        # ردیف ورودی
        input_row = QHBoxLayout()
        self.inp_name = QLineEdit(); self.inp_name.setPlaceholderText("نام فرآیند")
        self.inp_at = QLineEdit(); self.inp_at.setPlaceholderText("زمان ورود")
        self.inp_bt = QLineEdit(); self.inp_bt.setPlaceholderText("زمان سرویس")
        self.inp_prio = QLineEdit(); self.inp_prio.setPlaceholderText("اولویت صف")
        btn_add = QPushButton("➕ افزودن")
        btn_add.clicked.connect(self.insert_task)
        input_row.addWidget(self.inp_name)
        input_row.addWidget(self.inp_at)
        input_row.addWidget(self.inp_bt)
        input_row.addWidget(self.inp_prio)
        input_row.addWidget(btn_add)
        p_card_layout.addLayout(input_row)

        # دکمه بارگذاری داده‌های نمونه (زیر ورودی‌ها و بالای جدول)
        btn_test = QPushButton("📋 بارگذاری داده‌های نمونه")
        btn_test.setObjectName("TestBtn")
        btn_test.clicked.connect(self.inject_test_data)
        p_card_layout.addWidget(btn_test, alignment=Qt.AlignmentFlag.AlignLeft)
        p_card_layout.addSpacing(5)

        # جدول فرآیندها
        self.task_table = QTableWidget(0, 4)
        self.task_table.setHorizontalHeaderLabels(["نام فرآیند", "زمان ورود", "زمان سرویس", "سطح اولویت"])
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.task_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.task_table.setAlternatingRowColors(True)
        p_card_layout.addWidget(self.task_table)

        mid_layout.addWidget(p_card, 3)

        # --- کارت صف‌ها ---
        q_card = QGroupBox("⚙️ پیکربندی صف‌های MLQ")
        q_card.setMinimumWidth(450)
        q_card_layout = QVBoxLayout(q_card)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        q_container = QWidget()
        self.q_container_layout = QVBoxLayout(q_container)
        self.q_container_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(q_container)
        q_card_layout.addWidget(scroll, 1)

        btn_new_q = QPushButton("➕ ایجاد سطح جدید")
        btn_new_q.setStyleSheet("background-color: #7f8c8d; color: white;")
        btn_new_q.clicked.connect(lambda: self.build_queue_row())
        q_card_layout.addWidget(btn_new_q)

        mid_layout.addWidget(q_card, 4)
        main_layout.addLayout(mid_layout)

        # پیش‌فرض دو صف
        self.build_queue_row(1, "RR")
        self.build_queue_row(2, "FCFS")

        # دکمه اجرا
        btn_exec = QPushButton("🚀 اجرای شبیه‌سازی و نمایش نمودار گانت")
        btn_exec.setObjectName("ActionBtn")
        btn_exec.clicked.connect(self.start_simulation)
        main_layout.addWidget(btn_exec)

        # برچسب نتایج
        self.lbl_results = QLabel("⏳ در انتظار اجرا...")
        self.lbl_results.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_results.setStyleSheet("""
            background-color: #ebf5fb;
            color: #154360;
            padding: 14px;
            border-radius: 8px;
            font-size: 14px;
            border: 1px solid #aed6f1;
        """)
        main_layout.addWidget(self.lbl_results)

        # نمودار گانت
        self.gantt_scroll = QScrollArea()
        self.gantt_scroll.setWidgetResizable(True)
        self.gantt_scroll.setStyleSheet("background-color: transparent; border: none;")
        self.gantt_widget = QWidget()
        self.gantt_widget.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.gantt_layout = QHBoxLayout(self.gantt_widget)
        self.gantt_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.gantt_layout.setSpacing(6)
        self.gantt_scroll.setWidget(self.gantt_widget)
        main_layout.addWidget(self.gantt_scroll)

    # ----------------------------------------------------------------------
    # توابع منطقی (بدون تغییر)
    # ----------------------------------------------------------------------
    def build_queue_row(self, default_prio=1, default_algo="FCFS"):
        frame = QFrame()
        frame.setStyleSheet("""
            background-color: #f4f6f7;
            border: 1px solid #d5dbdb;
            border-radius: 8px;
            padding: 5px;
        """)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)

        lbl1 = QLabel("سطح:")
        layout.addWidget(lbl1)
        spin_lvl = QSpinBox(); spin_lvl.setRange(1, 10); spin_lvl.setValue(default_prio)
        layout.addWidget(spin_lvl)

        lbl2 = QLabel("الگوریتم:")
        layout.addWidget(lbl2)
        combo_algo = QComboBox(); combo_algo.addItems(["FCFS", "SJF", "SRTF", "HRRN", "RR"])
        combo_algo.setCurrentText(default_algo)
        layout.addWidget(combo_algo)

        rr_frame = QFrame()
        rr_frame.setStyleSheet("border: none;")
        rr_layout = QHBoxLayout(rr_frame)
        rr_layout.setContentsMargins(0, 0, 0, 0)

        lbl3 = QLabel("کوانتوم:")
        rr_layout.addWidget(lbl3)
        spin_q = QSpinBox(); spin_q.setRange(1, 20); spin_q.setValue(2)
        rr_layout.addWidget(spin_q)

        lbl4 = QLabel("سیاست:")
        rr_layout.addWidget(lbl4)
        combo_pol = QComboBox(); combo_pol.addItems(["اولویت با قدیمی", "اولویت با جدید"])
        rr_layout.addWidget(combo_pol)
        layout.addWidget(rr_frame)

        btn_del = QPushButton("حذف")
        btn_del.setStyleSheet("background-color: #e74c3c; color: white; border-radius: 4px;")
        btn_del.clicked.connect(lambda: self.remove_q_row(frame, obj_dict))
        layout.addWidget(btn_del)

        def on_algo_change(text):
            rr_frame.setVisible(text == "RR")
        combo_algo.currentTextChanged.connect(on_algo_change)
        on_algo_change(default_algo)

        obj_dict = {'frame': frame, 'prio': spin_lvl, 'algo': combo_algo,
                    'quant': spin_q, 'pol': combo_pol}
        self.queue_configs.append(obj_dict)
        self.q_container_layout.addWidget(frame)

    def remove_q_row(self, frame, obj_dict):
        if len(self.queue_configs) > 1:
            frame.deleteLater()
            self.queue_configs.remove(obj_dict)
        else:
            QMessageBox.warning(self, "خطا", "حذف تمامی صف‌ها امکان‌پذیر نیست.")

    def insert_task(self):
        n = self.inp_name.text().strip()
        a = self.inp_at.text().strip()
        b = self.inp_bt.text().strip()
        p = self.inp_prio.text().strip()
        if n and a.isdigit() and b.isdigit() and p.isdigit():
            if int(b) <= 0:
                QMessageBox.warning(self, "خطا", "زمان اجرا باید بزرگتر از صفر باشد.")
                return
            row = self.task_table.rowCount()
            self.task_table.insertRow(row)
            self.task_table.setItem(row, 0, QTableWidgetItem(n))
            self.task_table.setItem(row, 1, QTableWidgetItem(a))
            self.task_table.setItem(row, 2, QTableWidgetItem(b))
            self.task_table.setItem(row, 3, QTableWidgetItem(p))
            self.inp_name.clear(); self.inp_at.clear(); self.inp_bt.clear(); self.inp_prio.clear()
        else:
            QMessageBox.warning(self, "خطا", "لطفاً مقادیر عددی صحیح وارد کنید.")

    def inject_test_data(self):
        self.task_table.setRowCount(0)
        sample = [("P1", "0", "4", "1"), ("P2", "1", "3", "1"),
                  ("P3", "3", "5", "2"), ("P4", "12", "2", "1")]
        for n, a, b, p in sample:
            row = self.task_table.rowCount()
            self.task_table.insertRow(row)
            self.task_table.setItem(row, 0, QTableWidgetItem(n))
            self.task_table.setItem(row, 1, QTableWidgetItem(a))
            self.task_table.setItem(row, 2, QTableWidgetItem(b))
            self.task_table.setItem(row, 3, QTableWidgetItem(p))

    def clear_gantt_view(self):
        for i in reversed(range(self.gantt_layout.count())):
            w = self.gantt_layout.itemAt(i).widget()
            if w: w.deleteLater()

    def start_simulation(self):
        self.task_list.clear()
        self.timeline.clear()
        self.clear_gantt_view()
        if self.task_table.rowCount() == 0:
            QMessageBox.information(self, "اخطار", "جدول فرآیندها خالی است.")
            return

        sys_qs = {}
        for q in self.queue_configs:
            lvl = q['prio'].value()
            sys_qs[lvl] = {
                'algo': q['algo'].currentText(),
                'quant': q['quant'].value(),
                'pol': q['pol'].currentText()
            }
        active_lines = {lvl: [] for lvl in sys_qs}

        for r in range(self.task_table.rowCount()):
            pid = self.task_table.item(r, 0).text()
            at = self.task_table.item(r, 1).text()
            bt = self.task_table.item(r, 2).text()
            prio = self.task_table.item(r, 3).text()
            if int(prio) not in sys_qs:
                QMessageBox.critical(self, "خطا", f"صف {prio} پیکربندی نشده است!")
                return
            self.task_list.append(TaskDef(pid, at, bt, prio))

        tick = 0
        done_count = 0
        total_tasks = len(self.task_list)
        cpu_task = None
        q_time_left = 0

        while done_count < total_tasks:
            for t in self.task_list:
                if t.arrival == tick:
                    conf = sys_qs[t.q_level]
                    if conf['algo'] == 'RR' and conf['pol'] == 'اولویت با جدید':
                        active_lines[t.q_level].insert(0, t)
                    else:
                        active_lines[t.q_level].append(t)

            if cpu_task:
                if cpu_task.rem_time == 0:
                    cpu_task.end_time = tick
                    done_count += 1
                    cpu_task = None
                else:
                    interrupted = False
                    for lvl in sorted(sys_qs.keys()):
                        if lvl < cpu_task.q_level and len(active_lines[lvl]) > 0:
                            interrupted = True
                            break
                    rr_expire = (cpu_task.active_algo == "RR" and q_time_left <= 0)
                    if interrupted or rr_expire:
                        if interrupted and cpu_task.active_algo in ["FCFS", "SJF", "SRTF", "HRRN"]:
                            active_lines[cpu_task.q_level].insert(0, cpu_task)
                        else:
                            active_lines[cpu_task.q_level].append(cpu_task)
                        cpu_task = None
                    elif cpu_task.active_algo == "SRTF":
                        active_lines[cpu_task.q_level].insert(0, cpu_task)
                        cpu_task = None

            if not cpu_task:
                for lvl in sorted(sys_qs.keys()):
                    if len(active_lines[lvl]) > 0:
                        alg = sys_qs[lvl]['algo']
                        if alg in ["FCFS", "RR"]:
                            cpu_task = active_lines[lvl].pop(0)
                        elif alg == "SJF":
                            cpu_task = min(active_lines[lvl], key=lambda x: x.burst)
                            active_lines[lvl].remove(cpu_task)
                        elif alg == "SRTF":
                            cpu_task = min(active_lines[lvl], key=lambda x: x.rem_time)
                            active_lines[lvl].remove(cpu_task)
                        elif alg == "HRRN":
                            target = active_lines[lvl][0]
                            max_hrrn = -1
                            for p in active_lines[lvl]:
                                ratio = ((tick - p.arrival) + p.burst) / p.burst
                                if ratio > max_hrrn:
                                    max_hrrn = ratio; target = p
                            cpu_task = target
                            active_lines[lvl].remove(cpu_task)
                        if alg == "RR":
                            q_time_left = sys_qs[lvl]['quant']
                        cpu_task.active_algo = alg
                        break

            if cpu_task:
                if cpu_task.start_tick == -1:
                    cpu_task.start_tick = tick
                self.timeline.append((cpu_task.p_id, tick, tick + 1))
                cpu_task.rem_time -= 1
                if cpu_task.active_algo == "RR":
                    q_time_left -= 1
            tick += 1

        self.evaluate_performance()
        self.render_gantt()

    def evaluate_performance(self):
        t_wt = 0; t_tat = 0; n = len(self.task_list)
        for t in self.task_list:
            t.ta_time = t.end_time - t.arrival
            t.wait_time = t.ta_time - t.burst
            t_tat += t.ta_time; t_wt += t.wait_time
        awt = t_wt / n if n else 0
        att = t_tat / n if n else 0
        self.lbl_results.setText(f"✅ میانگین زمان انتظار (AWT) : {awt:.2f}    |    میانگین زمان بازگشت (ATT) : {att:.2f}")
        self.lbl_results.setStyleSheet("""
            background-color: #d5f5e3;
            color: #145a32;
            padding: 14px;
            border-radius: 8px;
            font-size: 15px;
            border: 1px solid #82e0aa;
        """)

    def render_gantt(self):
        pallete = ["#fadbd8", "#d4efdf", "#d6eaf8", "#fdebd0", "#e8daef", "#f9e79f", "#abebc6"]
        compressed = []
        for item in self.timeline:
            if compressed and compressed[-1][0] == item[0] and compressed[-1][2] == item[1]:
                compressed[-1] = (compressed[-1][0], compressed[-1][1], item[2])
            else:
                compressed.append(item)
        for i, (name, s, e) in enumerate(compressed):
            box = QWidget()
            box_ly = QVBoxLayout(box)
            box_ly.setContentsMargins(0, 0, 0, 0)
            lbl_n = QLabel(name)
            lbl_n.setAlignment(Qt.AlignmentFlag.AlignCenter)
            c = pallete[i % len(pallete)]
            lbl_n.setStyleSheet(f"background-color: {c}; border: 1px solid #99a3a4; border-radius: 6px; padding: 18px 30px; font-size: 18px; font-weight: bold;")
            lbl_t = QLabel(f"{s} ➔ {e}")
            lbl_t.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_t.setStyleSheet("color: #5d6d7e; font-size: 11px;")
            box_ly.addWidget(lbl_n)
            box_ly.addWidget(lbl_t)
            self.gantt_layout.addWidget(box)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    win = MLQ_Academic_Simulator()
    win.show()
    sys.exit(app.exec())