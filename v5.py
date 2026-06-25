import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTableWidget, QTableWidgetItem, QGroupBox,
                             QHeaderView, QComboBox, QScrollArea, QMessageBox, QSpinBox, QAbstractItemView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class Process:
    def __init__(self, pid, arrival_time, burst_time, priority):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.priority = priority

        self.start_time = -1
        self.completion_time = 0
        self.waiting_time = 0
        self.turnaround_time = 0
        self.algo_used = ""


class QueueWidget(QWidget):
    def __init__(self, priority_val=1, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)

        # استایل‌دهی داخلی برای المان‌های صف
        lbl_style = "font-size: 14px; font-weight: bold; color: #cdd6f4;"

        lbl_pri = QLabel("اولویت صف (۱=بالاترین):")
        lbl_pri.setStyleSheet(lbl_style)
        self.layout.addWidget(lbl_pri)

        self.pri_spin = QSpinBox()
        self.pri_spin.setRange(1, 10)
        self.pri_spin.setValue(priority_val)
        self.layout.addWidget(self.pri_spin)

        lbl_algo = QLabel("الگوریتم:")
        lbl_algo.setStyleSheet(lbl_style)
        self.layout.addWidget(lbl_algo)

        self.algo_combo = QComboBox()
        self.algo_combo.addItems(["FCFS", "RR", "SJF", "SRTF", "HRRN"])
        self.layout.addWidget(self.algo_combo)

        # تنظیمات مخصوص Round Robin
        self.rr_widget = QWidget()
        rr_layout = QHBoxLayout(self.rr_widget)
        rr_layout.setContentsMargins(0, 0, 0, 0)

        lbl_quantum = QLabel("کوانتوم:")
        lbl_quantum.setStyleSheet(lbl_style)
        rr_layout.addWidget(lbl_quantum)

        self.quantum_spin = QSpinBox()
        self.quantum_spin.setRange(1, 20)
        self.quantum_spin.setValue(2)
        rr_layout.addWidget(self.quantum_spin)

        lbl_policy = QLabel("Policy:")
        lbl_policy.setStyleSheet(lbl_style)
        rr_layout.addWidget(lbl_policy)

        self.policy_combo = QComboBox()
        self.policy_combo.addItems(["اولویت با قدیمی‌ها", "اولویت با تازه‌واردها"])
        rr_layout.addWidget(self.policy_combo)

        self.layout.addWidget(self.rr_widget)

        self.del_btn = QPushButton("❌ حذف")
        self.del_btn.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; font-size: 14px;")
        self.layout.addWidget(self.del_btn)

        self.setLayout(self.layout)
        self.algo_combo.currentTextChanged.connect(self.toggle_rr_settings)
        self.toggle_rr_settings(self.algo_combo.currentText())

    def toggle_rr_settings(self, text):
        is_rr = (text == "RR")
        self.rr_widget.setVisible(is_rr)


class MLQSimulatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MLQ OS Scheduler - Dynamic Builder")
        self.resize(1600, 900)

        # استایل شیت جامع با فونت‌های بزرگتر و پدینگ مناسب
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e2e; }
            QLabel { color: #cdd6f4; font-size: 14px; font-weight: bold; }
            QGroupBox { 
                color: #89b4fa; 
                border: 2px solid #313244; 
                border-radius: 10px; 
                margin-top: 15px; 
                font-size: 15px; 
                font-weight: bold; 
                padding-top: 20px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 8px; }
            QPushButton { 
                background-color: #89b4fa; 
                color: #11111b; 
                border-radius: 6px; 
                padding: 10px 15px; 
                font-weight: bold; 
                font-size: 14px; 
            }
            QPushButton:hover { background-color: #b4befe; }
            QTableWidget { 
                background-color: #181825; 
                color: #cdd6f4; 
                gridline-color: #313244; 
                border: 1px solid #313244; 
                font-size: 15px; 
            }
            QHeaderView::section { 
                background-color: #313244; 
                color: #cdd6f4; 
                padding: 8px; 
                font-weight: bold; 
                font-size: 14px;
                border: 1px solid #181825;
            }
            QLineEdit, QComboBox, QSpinBox { 
                background-color: #313244; 
                color: #cdd6f4; 
                border: 1px solid #585b70; 
                border-radius: 6px; 
                padding: 8px; 
                font-size: 14px; 
            }
            QComboBox::drop-down { border: none; }
            /* استایل دهی اسکرول بار برای ظاهر بهتر */
            QScrollBar:vertical { background: #1e1e2e; width: 14px; margin: 0px 0px 0px 0px;}
            QScrollBar::handle:vertical { background: #585b70; min-height: 20px; border-radius: 7px;}
            QScrollBar:horizontal { background: #1e1e2e; height: 14px; margin: 0px 0px 0px 0px;}
            QScrollBar::handle:horizontal { background: #585b70; min-width: 20px; border-radius: 7px;}
        """)

        self.processes = []
        self.gantt_data = []
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(15)

        # ۱. بخش تنظیمات پویا صف‌ها
        queue_group = QGroupBox("تنظیمات ساختاری صف‌ها (MLQ)")
        queue_main_layout = QVBoxLayout()
        queue_main_layout.setSpacing(10)

        self.queues_layout = QVBoxLayout()
        queue_main_layout.addLayout(self.queues_layout)

        add_queue_btn = QPushButton("➕ افزودن صف جدید")
        add_queue_btn.setStyleSheet("background-color: #a6e3a1; color: #11111b; font-size: 15px;")
        add_queue_btn.clicked.connect(lambda: self.add_queue_widget())
        queue_main_layout.addWidget(add_queue_btn)
        queue_main_layout.addStretch()

        queue_group.setLayout(queue_main_layout)

        # اضافه کردن صف‌های پیش فرض
        self.add_queue_widget(priority=1, algo="RR")
        self.add_queue_widget(priority=2, algo="FCFS")

        # ۲. جدول فرآیندها
        process_group = QGroupBox("مدیریت فرآیندها")
        process_layout = QVBoxLayout()
        process_layout.setSpacing(15)

        p_inputs = QHBoxLayout()
        self.pid_input = QLineEdit()
        self.pid_input.setPlaceholderText("نام (مثل P1)")

        self.at_input = QLineEdit()
        self.at_input.setPlaceholderText("ورود (AT)")

        self.bt_input = QLineEdit()
        self.bt_input.setPlaceholderText("سرویس (BT)")

        self.pr_input = QLineEdit()
        self.pr_input.setPlaceholderText("اولویت صف")

        add_proc_btn = QPushButton("افزودن دستی")
        add_proc_btn.clicked.connect(self.add_process)

        test_data_btn = QPushButton("🧪 بارگذاری داده‌های تست")
        test_data_btn.setStyleSheet("background-color: #fab387; color: #11111b;")
        test_data_btn.clicked.connect(self.load_test_data)

        p_inputs.addWidget(self.pid_input)
        p_inputs.addWidget(self.at_input)
        p_inputs.addWidget(self.bt_input)
        p_inputs.addWidget(self.pr_input)
        p_inputs.addWidget(add_proc_btn)
        p_inputs.addWidget(test_data_btn)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["نام فرآیند", "زمان ورود", "زمان سرویس", "اولویت صف"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(40)  # ارتفاع بیشتر برای ردیف‌های جدول

        process_layout.addLayout(p_inputs)
        process_layout.addWidget(self.table)
        process_group.setLayout(process_layout)

        top_layout.addWidget(queue_group, 5)
        top_layout.addWidget(process_group, 5)
        main_layout.addLayout(top_layout)

        run_btn = QPushButton("🚀 اجرای شبیه‌ساز و رسم گراف")
        run_btn.setStyleSheet("""
            background-color: #cba6f7; 
            color: #11111b; 
            font-size: 18px; 
            font-weight: bold;
            padding: 15px;
            border-radius: 8px;
        """)
        run_btn.clicked.connect(self.run_simulation)
        main_layout.addWidget(run_btn)

        # ۳. بخش خروجی‌ها و نمودار
        output_group = QGroupBox("نتایج ارزیابی و نمودار گانت")
        self.output_layout = QVBoxLayout()
        self.output_layout.setSpacing(15)

        # بهبود بصری لیبل نتایج (AWT و ATT)
        self.stats_label = QLabel("منتظر اجرای شبیه‌ساز...")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_label.setStyleSheet("""
            background-color: #f38ba8; 
            color: #11111b; 
            font-size: 18px; 
            font-weight: bold; 
            padding: 15px; 
            border-radius: 8px;
        """)
        self.output_layout.addWidget(self.stats_label)

        self.gantt_scroll = QScrollArea()
        self.gantt_scroll.setWidgetResizable(True)
        self.gantt_scroll.setStyleSheet("border: none; background-color: transparent;")

        self.gantt_container = QWidget()
        self.gantt_container.setStyleSheet("background-color: #181825; border-radius: 8px;")

        self.gantt_layout = QHBoxLayout(self.gantt_container)
        self.gantt_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.gantt_layout.setSpacing(10)
        self.gantt_layout.setContentsMargins(15, 15, 15, 15)

        self.gantt_scroll.setWidget(self.gantt_container)

        self.output_layout.addWidget(self.gantt_scroll)
        output_group.setLayout(self.output_layout)
        main_layout.addWidget(output_group)

    def add_queue_widget(self, priority=1, algo="FCFS"):
        qw = QueueWidget(priority_val=priority)
        qw.algo_combo.setCurrentText(algo)
        qw.del_btn.clicked.connect(lambda: self.remove_queue_widget(qw))
        self.queues_layout.addWidget(qw)

    def remove_queue_widget(self, widget):
        if self.queues_layout.count() > 1:
            self.queues_layout.removeWidget(widget)
            widget.deleteLater()
        else:
            QMessageBox.warning(self, "اخطار", "سیستم حداقل به یک صف نیاز دارد!")

    def load_test_data(self):
        self.table.setRowCount(0)
        test_scenarios = [
            ("P1", "0", "5", "1"),
            ("P2", "1", "3", "1"),
            ("P3", "2", "6", "2"),
            ("P4", "4", "2", "2"),
            ("P5", "10", "4", "1")
        ]
        for pid, at, bt, pr in test_scenarios:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(pid))
            self.table.setItem(row, 1, QTableWidgetItem(at))
            self.table.setItem(row, 2, QTableWidgetItem(bt))
            self.table.setItem(row, 3, QTableWidgetItem(pr))

            # مرکز چین کردن متن جدول
            for col in range(4):
                self.table.item(row, col).setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    def add_process(self):
        pid = self.pid_input.text().strip()
        at = self.at_input.text().strip()
        bt = self.bt_input.text().strip()
        pr = self.pr_input.text().strip()

        if not (pid and at.isdigit() and bt.isdigit() and pr.isdigit()):
            QMessageBox.warning(self, "خطا", "لطفاً مقادیر معتبر وارد کنید.")
            return

        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(pid))
        self.table.setItem(row, 1, QTableWidgetItem(at))
        self.table.setItem(row, 2, QTableWidgetItem(bt))
        self.table.setItem(row, 3, QTableWidgetItem(pr))

        for col in range(4):
            self.table.item(row, col).setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        self.pid_input.clear()
        self.at_input.clear()
        self.bt_input.clear()
        self.pr_input.clear()

    def clear_gantt(self):
        for i in reversed(range(self.gantt_layout.count())):
            widget = self.gantt_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

    def run_simulation(self):
        self.processes.clear()
        self.gantt_data.clear()
        self.clear_gantt()

        if self.table.rowCount() == 0:
            QMessageBox.information(self, "داده ای نیست", "لطفاً ابتدا فرآیندها را وارد کنید.")
            return

        self.queues_config = {}
        for i in range(self.queues_layout.count()):
            qw = self.queues_layout.itemAt(i).widget()
            if qw:
                pri = qw.pri_spin.value()
                if pri not in self.queues_config:
                    self.queues_config[pri] = {
                        'algo': qw.algo_combo.currentText(),
                        'quantum': qw.quantum_spin.value(),
                        'policy': qw.policy_combo.currentText()
                    }

        ready_queues = {pri: [] for pri in self.queues_config}

        for r in range(self.table.rowCount()):
            pid = self.table.item(r, 0).text()
            at = int(self.table.item(r, 1).text())
            bt = int(self.table.item(r, 2).text())
            pr = int(self.table.item(r, 3).text())

            if pr not in self.queues_config:
                QMessageBox.critical(self, "خطای اولویت",
                                     f"فرآیند {pid} به صف {pr} اشاره می‌کند اما این صف تعریف نشده است!")
                return
            self.processes.append(Process(pid, at, bt, pr))

        current_time = 0
        completed = 0
        n = len(self.processes)

        running_p = None
        current_quantum_left = 0

        while completed != n:
            for p in self.processes:
                if p.arrival_time == current_time:
                    conf = self.queues_config[p.priority]
                    if conf['algo'] == "RR" and conf['policy'] == "اولویت با تازه‌واردها":
                        ready_queues[p.priority].insert(0, p)
                    else:
                        ready_queues[p.priority].append(p)

            if running_p is not None:
                if running_p.remaining_time == 0:
                    running_p.completion_time = current_time
                    completed += 1
                    running_p = None
                else:
                    higher_priority_exists = False
                    for q_pri in sorted(self.queues_config.keys()):
                        if q_pri < running_p.priority and len(ready_queues[q_pri]) > 0:
                            higher_priority_exists = True
                            break

                    rr_expired = (running_p.algo_used == "RR" and current_quantum_left <= 0)

                    if higher_priority_exists or rr_expired:
                        if higher_priority_exists and running_p.algo_used in ["FCFS", "SJF", "SRTF", "HRRN"]:
                            ready_queues[running_p.priority].insert(0, running_p)
                        else:
                            ready_queues[running_p.priority].append(running_p)
                        running_p = None

                    elif running_p.algo_used == "SRTF":
                        ready_queues[running_p.priority].insert(0, running_p)
                        running_p = None

            if running_p is None:
                for q_pri in sorted(self.queues_config.keys()):
                    if len(ready_queues[q_pri]) > 0:
                        conf = self.queues_config[q_pri]
                        algo = conf['algo']

                        if algo in ["FCFS", "RR"]:
                            running_p = ready_queues[q_pri].pop(0)
                        elif algo == "SJF":
                            running_p = min(ready_queues[q_pri], key=lambda x: x.burst_time)
                            ready_queues[q_pri].remove(running_p)
                        elif algo == "SRTF":
                            running_p = min(ready_queues[q_pri], key=lambda x: x.remaining_time)
                            ready_queues[q_pri].remove(running_p)
                        elif algo == "HRRN":
                            best_p = ready_queues[q_pri][0]
                            best_ratio = -1
                            for p in ready_queues[q_pri]:
                                w = current_time - p.arrival_time
                                ratio = (w + p.burst_time) / p.burst_time
                                if ratio > best_ratio:
                                    best_ratio = ratio
                                    best_p = p
                            running_p = best_p
                            ready_queues[q_pri].remove(running_p)

                        if running_p.algo_used != "RR" or current_quantum_left <= 0:
                            current_quantum_left = conf['quantum']

                        running_p.algo_used = algo
                        break

            if running_p is not None:
                if running_p.start_time == -1:
                    running_p.start_time = current_time

                self.gantt_data.append((running_p.pid, current_time, current_time + 1))
                running_p.remaining_time -= 1
                if running_p.algo_used == "RR":
                    current_quantum_left -= 1

            current_time += 1

        self.calculate_metrics()
        self.draw_gantt()

    def calculate_metrics(self):
        total_wt = 0
        total_tat = 0
        n = len(self.processes)

        if n == 0:
            return

        for p in self.processes:
            p.turnaround_time = p.completion_time - p.arrival_time
            p.waiting_time = p.turnaround_time - p.burst_time
            total_tat += p.turnaround_time
            total_wt += p.waiting_time

        avg_wt = total_wt / n
        avg_tat = total_tat / n

        # آپدیت متن لیبل با استایل جدید
        self.stats_label.setText(
            f" میانگین زمان انتظار (AWT): {avg_wt:.2f}   |   میانگین زمان بازگشت (ATT): {avg_tat:.2f} ")
        self.stats_label.setStyleSheet("""
            background-color: #a6e3a1; 
            color: #11111b; 
            font-size: 18px; 
            font-weight: bold; 
            padding: 15px; 
            border-radius: 8px;
        """)

    def draw_gantt(self):
        colors = ["#f5e0dc", "#f2cdcd", "#f5c2e7", "#cba6f7", "#f38ba8", "#eba0ac", "#fab387", "#f9e2af", "#a6e3a1",
                  "#94e2d5"]

        merged_gantt = []
        for item in self.gantt_data:
            if merged_gantt and merged_gantt[-1][0] == item[0] and merged_gantt[-1][2] == item[1]:
                merged_gantt[-1] = (merged_gantt[-1][0], merged_gantt[-1][1], item[2])
            else:
                merged_gantt.append(item)

        for idx, (pid, start, end) in enumerate(merged_gantt):
            block = QWidget()
            block_layout = QVBoxLayout(block)
            block_layout.setContentsMargins(0, 0, 0, 0)
            block_layout.setSpacing(5)

            name_lbl = QLabel(pid)
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            bg_color = colors[idx % len(colors)]

            # بزرگ‌تر شدن بلاک‌های گانت
            name_lbl.setStyleSheet(f"""
                background-color: {bg_color}; 
                color: #11111b; 
                border-radius: 8px; 
                padding: 20px 30px; 
                font-weight: bold; 
                font-size: 20px;
            """)

            time_lbl = QLabel(f"{start} ➔ {end}")
            time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            time_lbl.setStyleSheet("color: #a6adc8; font-size: 14px; font-weight: bold;")

            block_layout.addWidget(name_lbl)
            block_layout.addWidget(time_lbl)
            self.gantt_layout.addWidget(block)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # تنظیم یک فونت استاندارد با سایز پایه بزرگتر
    font = QFont("Ubuntu", 11)
    app.setFont(font)

    window = MLQSimulatorApp()
    window.show()
    sys.exit(app.exec())