#!/usr/bin/env python3
import json
import os
import sys
import time
import threading
from datetime import datetime
from pathlib import Path

class WorkerAutomation:
    def __init__(self, worker_name: str):
        self.worker_name = worker_name
        self.comm = WorkerCommunication(worker_name)
        self.running = True
        self.pending_tasks_dir = f"pending_tasks/{worker_name}"
        self.completed_tasks_dir = f"completed_tasks/{worker_name}"
        self.instructions_file = f"{worker_name}/{worker_name}_instructions.md"
        
        # ディレクトリの確保
        os.makedirs(self.pending_tasks_dir, exist_ok=True)
        os.makedirs(self.completed_tasks_dir, exist_ok=True)
        
        # 初期ログ
        self.comm.log_activity(f"{worker_name} automation started")
        self.read_instructions()
    
    def read_instructions(self):
        """指示書を読み込む"""
        try:
            with open(self.instructions_file, 'r') as f:
                instructions = f.read()
                self.comm.log_activity("Instructions loaded successfully")
                print(f"\n=== {self.worker_name} Instructions ===")
                print(instructions[:500] + "..." if len(instructions) > 500 else instructions)
                print("=" * 40 + "\n")
        except Exception as e:
            self.comm.log_activity(f"Error reading instructions: {str(e)}")
    
    def check_messages(self):
        """メッセージをチェックして処理"""
        messages = self.comm.read_messages_for_me()
        for msg in messages:
            self.comm.log_activity(f"Received message from {msg['from']}: {msg['subject']}")
            
            # 高優先度メッセージの処理
            if msg['priority'] == 'high':
                self.process_high_priority_message(msg)
            else:
                self.process_normal_message(msg)
    
    def process_high_priority_message(self, msg):
        """高優先度メッセージの処理"""
        self.comm.log_activity(f"Processing high priority message: {msg['subject']}")
        
        # Worker1がデータ準備完了を通知した場合（Worker2用）
        if self.worker_name == "worker2" and msg['from'] == "worker1" and "データ準備完了" in msg['subject']:
            self.comm.log_activity("Starting data processing based on worker1's data")
            self.process_data_from_worker1()
        
        # Worker2が処理完了を通知した場合（Worker3用）
        elif self.worker_name == "worker3" and msg['from'] == "worker2" and "処理完了" in msg['subject']:
            self.comm.log_activity("Starting report generation based on worker2's results")
            self.generate_report_from_worker2()
    
    def process_normal_message(self, msg):
        """通常メッセージの処理"""
        self.comm.log_activity(f"Processing message: {msg['message']}")
    
    def check_pending_tasks(self):
        """保留中のタスクをチェックして実行"""
        try:
            task_files = list(Path(self.pending_tasks_dir).glob("*.json"))
            for task_file in task_files:
                self.comm.log_activity(f"Found pending task: {task_file.name}")
                self.execute_task(task_file)
        except Exception as e:
            self.comm.log_activity(f"Error checking tasks: {str(e)}")
    
    def execute_task(self, task_file):
        """タスクを実行"""
        try:
            with open(task_file, 'r') as f:
                task = json.load(f)
            
            self.comm.log_activity(f"Executing task: {task.get('name', 'unnamed')}", 0)
            
            # タスクにコマンドが含まれている場合は実行
            if 'command' in task:
                self.comm.log_activity(f"Executing command: {task['command']}")
                import subprocess
                try:
                    result = subprocess.run(
                        task['command'], 
                        shell=True, 
                        capture_output=True, 
                        text=True,
                        cwd=self.worker_name
                    )
                    self.comm.log_activity(f"Command output: {result.stdout}")
                    if result.stderr:
                        self.comm.log_activity(f"Command error: {result.stderr}")
                    
                    # 結果をファイルに保存
                    output_file = f"{self.worker_name}/task_{task.get('name', 'unnamed')}_output.txt"
                    with open(output_file, 'w') as f:
                        f.write(f"Task: {task.get('name', 'unnamed')}\n")
                        f.write(f"Command: {task['command']}\n")
                        f.write(f"Output:\n{result.stdout}\n")
                        if result.stderr:
                            f.write(f"Error:\n{result.stderr}\n")
                except Exception as cmd_error:
                    self.comm.log_activity(f"Command execution error: {str(cmd_error)}")
            
            # スクリプトが含まれている場合は実行
            elif 'script' in task:
                script_file = f"{self.worker_name}/temp_script.py"
                with open(script_file, 'w') as f:
                    f.write(task['script'])
                
                import subprocess
                result = subprocess.run(
                    [sys.executable, script_file],
                    capture_output=True,
                    text=True,
                    cwd=self.worker_name
                )
                self.comm.log_activity(f"Script output: {result.stdout}")
                if result.stderr:
                    self.comm.log_activity(f"Script error: {result.stderr}")
                
                os.remove(script_file)
            
            # それ以外の場合はシミュレーション
            else:
                for i in range(0, 101, 20):
                    time.sleep(1)
                    self.comm.log_activity(f"Task progress: {task.get('name', 'unnamed')}", i)
            
            # タスクを完了済みフォルダに移動
            completed_file = Path(self.completed_tasks_dir) / task_file.name
            task_file.rename(completed_file)
            
            self.comm.log_activity(f"Task completed: {task.get('name', 'unnamed')}", 100)
            
            # 次のワーカーに通知（必要に応じて）
            self.notify_next_worker(task)
            
        except Exception as e:
            self.comm.log_activity(f"Error executing task: {str(e)}")
    
    def notify_next_worker(self, task):
        """次のワーカーに完了を通知"""
        if self.worker_name == "worker1":
            self.comm.send_message("worker2", "データ準備完了", 
                                 f"Task '{task.get('name')}' completed. Data ready for processing.", "high")
        elif self.worker_name == "worker2":
            self.comm.send_message("worker3", "処理完了", 
                                 f"Task '{task.get('name')}' completed. Results ready for reporting.", "high")
        elif self.worker_name == "worker3":
            self.comm.send_message("manager", "レポート生成完了", 
                                 f"Task '{task.get('name')}' completed. Report saved to output folder.", "high")
            # outputフォルダにレポートをコピー
            self.save_to_output()
    
    def save_to_output(self):
        """成果物をoutputフォルダに保存"""
        try:
            output_file = f"output/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(output_file, 'w') as f:
                f.write(f"Report generated by {self.worker_name} at {datetime.now()}\n")
                f.write("=" * 50 + "\n")
                f.write("Final report content here...\n")
            self.comm.log_activity(f"Report saved to {output_file}")
        except Exception as e:
            self.comm.log_activity(f"Error saving to output: {str(e)}")
    
    def process_data_from_worker1(self):
        """Worker1からのデータを処理（Worker2用）"""
        self.comm.log_activity("Processing data from worker1", 0)
        for i in range(0, 101, 25):
            time.sleep(1)
            self.comm.log_activity("Data processing progress", i)
        self.comm.log_activity("Data processing completed", 100)
        self.comm.send_message("worker3", "処理完了", "Data processing completed. Ready for report generation.", "high")
    
    def generate_report_from_worker2(self):
        """Worker2からの結果をレポート化（Worker3用）"""
        self.comm.log_activity("Generating report from worker2 results", 0)
        for i in range(0, 101, 33):
            time.sleep(1)
            self.comm.log_activity("Report generation progress", i)
        self.comm.log_activity("Report generation completed", 100)
        self.save_to_output()
        self.comm.send_message("manager", "レポート生成完了", "Final report has been generated and saved to output folder.", "high")
    
    def run(self):
        """メインループ"""
        message_check_interval = 30  # 30秒ごとにメッセージチェック
        task_check_interval = 10     # 10秒ごとにタスクチェック
        progress_report_interval = 60  # 60秒ごとに進捗報告
        
        last_message_check = 0
        last_task_check = 0
        last_progress_report = 0
        
        self.comm.log_activity(f"{self.worker_name} is now running autonomously")
        
        while self.running:
            current_time = time.time()
            
            # メッセージチェック
            if current_time - last_message_check >= message_check_interval:
                self.check_messages()
                last_message_check = current_time
            
            # タスクチェック
            if current_time - last_task_check >= task_check_interval:
                self.check_pending_tasks()
                last_task_check = current_time
            
            # 進捗報告
            if current_time - last_progress_report >= progress_report_interval:
                self.comm.log_activity(f"{self.worker_name} is alive and monitoring")
                last_progress_report = current_time
            
            time.sleep(1)  # CPU使用率を抑える
    
    def stop(self):
        """自動化を停止"""
        self.running = False
        self.comm.log_activity(f"{self.worker_name} automation stopped")

# WorkerCommunicationクラスをインポート
class WorkerCommunication:
    def __init__(self, worker_name: str):
        self.worker_name = worker_name
        self.messages_file = "communication/messages.json"
        self.ensure_communication_dir()
    
    def ensure_communication_dir(self):
        os.makedirs("communication", exist_ok=True)
        if not os.path.exists(self.messages_file):
            with open(self.messages_file, 'w') as f:
                json.dump([], f)
    
    def send_message(self, to: str, subject: str, message: str, priority: str = "medium"):
        msg = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "from": self.worker_name,
            "to": to,
            "subject": subject,
            "message": message,
            "priority": priority,
            "read": False
        }
        
        messages = self.read_all_messages()
        messages.append(msg)
        self.write_messages(messages)
        print(f"[{self.worker_name}] Message sent to {to}: {subject}")
    
    def read_messages_for_me(self):
        messages = self.read_all_messages()
        my_messages = [msg for msg in messages if msg["to"] == self.worker_name and not msg.get("read", True)]
        
        # Mark messages as read
        for msg in messages:
            if msg["to"] == self.worker_name:
                msg["read"] = True
        self.write_messages(messages)
        
        return my_messages
    
    def read_all_messages(self):
        try:
            with open(self.messages_file, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def write_messages(self, messages):
        with open(self.messages_file, 'w') as f:
            json.dump(messages, f, indent=2)
    
    def log_activity(self, activity: str, progress=None):
        log_file = f"{self.worker_name}/{self.worker_name}_log.txt"
        os.makedirs(self.worker_name, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {activity}"
        if progress is not None:
            log_entry += f" (Progress: {progress}%)"
        
        with open(log_file, 'a') as f:
            f.write(log_entry + "\n")
        
        print(f"[{self.worker_name}] {log_entry}")

# メイン実行
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python worker_automation.py <worker_name>")
        sys.exit(1)
    
    worker_name = sys.argv[1]
    
    try:
        automation = WorkerAutomation(worker_name)
        automation.run()
    except KeyboardInterrupt:
        print(f"\n{worker_name} automation stopped by user")
        automation.stop()