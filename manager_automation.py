#!/usr/bin/env python3
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
import subprocess

class ManagerAutomation:
    def __init__(self):
        self.worker_name = "manager"
        self.comm = WorkerCommunication(self.worker_name)
        self.running = True
        self.workers = ["worker1", "worker2", "worker3"]
        self.instructions_file = "manager_instructions.md"
        
        # 初期ログ
        self.comm.log_activity("Manager automation started")
        self.read_instructions()
        self.ensure_directories()
    
    def ensure_directories(self):
        """必要なディレクトリを確保"""
        for worker in self.workers:
            os.makedirs(f"pending_tasks/{worker}", exist_ok=True)
            os.makedirs(f"completed_tasks/{worker}", exist_ok=True)
    
    def read_instructions(self):
        """指示書を読み込む"""
        try:
            with open(self.instructions_file, 'r') as f:
                instructions = f.read()
                self.comm.log_activity("Manager instructions loaded successfully")
                print("\n=== Manager Instructions ===")
                print(instructions[:500] + "..." if len(instructions) > 500 else instructions)
                print("=" * 40 + "\n")
        except Exception as e:
            self.comm.log_activity(f"Error reading instructions: {str(e)}")
    
    def check_messages(self):
        """メッセージをチェックして処理"""
        messages = self.comm.read_messages_for_me()
        for msg in messages:
            self.comm.log_activity(f"Received message from {msg['from']}: {msg['subject']}")
            
            # 完了報告の処理
            if "完了" in msg['subject']:
                self.handle_completion_report(msg)
            
            # エラー報告の処理
            elif "エラー" in msg['subject'] or "error" in msg['subject'].lower():
                self.handle_error_report(msg)
    
    def handle_completion_report(self, msg):
        """完了報告を処理"""
        self.comm.log_activity(f"Processing completion report from {msg['from']}")
        
        # Worker3からの最終レポート完了通知
        if msg['from'] == "worker3" and "レポート生成完了" in msg['subject']:
            self.comm.log_activity("Final report received. Checking output folder...")
            self.check_output_folder()
    
    def handle_error_report(self, msg):
        """エラー報告を処理"""
        self.comm.log_activity(f"ERROR reported by {msg['from']}: {msg['message']}")
        # エラー内容を分析して適切な対処を決定
        self.analyze_and_respond_to_error(msg)
    
    def analyze_and_respond_to_error(self, error_msg):
        """エラーを分析して対処"""
        # リトライ可能なエラーの場合
        if "timeout" in error_msg['message'].lower() or "connection" in error_msg['message'].lower():
            self.comm.log_activity(f"Suggesting retry for {error_msg['from']}")
            self.comm.send_message(error_msg['from'], "リトライ指示", 
                                 "エラーを検知しました。タスクを再実行してください。", "high")
    
    def check_worker_status(self):
        """各ワーカーの状態をチェック"""
        for worker in self.workers:
            log_file = f"{worker}/{worker}_log.txt"
            if os.path.exists(log_file):
                # 最終更新時刻をチェック
                last_modified = os.path.getmtime(log_file)
                time_since_update = time.time() - last_modified
                
                # 5分以上更新がない場合は警告
                if time_since_update > 300:
                    self.comm.log_activity(f"WARNING: {worker} has not updated for {int(time_since_update/60)} minutes")
    
    def check_output_folder(self):
        """outputフォルダの内容を確認"""
        output_files = list(Path("output").glob("*"))
        if output_files:
            self.comm.log_activity(f"Found {len(output_files)} files in output folder:")
            for file in output_files:
                self.comm.log_activity(f"  - {file.name}")
    
    def distribute_task(self, task_data, target_worker):
        """タスクをワーカーに配布"""
        task_file = f"pending_tasks/{target_worker}/task_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(task_file, 'w') as f:
            json.dump(task_data, f, indent=2)
        
        self.comm.log_activity(f"Task '{task_data.get('name')}' distributed to {target_worker}")
        self.comm.send_message(target_worker, "新規タスク", 
                             f"New task available: {task_data.get('name')}", "high")
    
    def create_sample_tasks(self):
        """サンプルタスクを作成して配布"""
        tasks = [
            {
                "name": "data_collection",
                "description": "収集データの準備",
                "command": "echo 'Collecting data...' && ls -la",
                "worker": "worker1"
            },
            {
                "name": "data_processing",
                "description": "データの処理",
                "script": "print('Processing data...')\nfor i in range(5):\n    print(f'Step {i+1}/5')",
                "worker": "worker2"
            },
            {
                "name": "report_generation",
                "description": "レポートの生成",
                "command": "echo 'Generating report...'",
                "worker": "worker3"
            }
        ]
        
        for task in tasks:
            worker = task.pop('worker')
            self.distribute_task(task, worker)
    
    def generate_status_report(self):
        """全体のステータスレポートを生成"""
        report = []
        report.append("=== Manager Status Report ===")
        report.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 各ワーカーのステータス
        for worker in self.workers:
            pending = len(list(Path(f"pending_tasks/{worker}").glob("*.json")))
            completed = len(list(Path(f"completed_tasks/{worker}").glob("*.json")))
            report.append(f"{worker}: Pending={pending}, Completed={completed}")
        
        report_text = "\n".join(report)
        self.comm.log_activity(f"Status Report:\n{report_text}")
        
        # レポートをoutputフォルダに保存
        with open(f"output/status_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", 'w') as f:
            f.write(report_text)
    
    def run(self):
        """メインループ"""
        message_check_interval = 20  # 20秒ごとにメッセージチェック
        status_check_interval = 60   # 60秒ごとにステータスチェック
        report_interval = 180        # 3分ごとにレポート生成
        
        last_message_check = 0
        last_status_check = 0
        last_report = 0
        initial_tasks_created = False
        
        self.comm.log_activity("Manager is now running autonomously")
        
        while self.running:
            current_time = time.time()
            
            # 初回のみサンプルタスクを作成
            if not initial_tasks_created and current_time > 5:
                self.create_sample_tasks()
                initial_tasks_created = True
            
            # メッセージチェック
            if current_time - last_message_check >= message_check_interval:
                self.check_messages()
                last_message_check = current_time
            
            # ステータスチェック
            if current_time - last_status_check >= status_check_interval:
                self.check_worker_status()
                last_status_check = current_time
            
            # レポート生成
            if current_time - last_report >= report_interval:
                self.generate_status_report()
                last_report = current_time
            
            time.sleep(1)
    
    def stop(self):
        """自動化を停止"""
        self.running = False
        self.comm.log_activity("Manager automation stopped")

# WorkerCommunicationクラス
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
        log_file = "manager_log.txt"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {activity}"
        if progress is not None:
            log_entry += f" (Progress: {progress}%)"
        
        with open(log_file, 'a') as f:
            f.write(log_entry + "\n")
        
        print(f"[MANAGER] {log_entry}")

# メイン実行
if __name__ == "__main__":
    try:
        manager = ManagerAutomation()
        manager.run()
    except KeyboardInterrupt:
        print("\nManager automation stopped by user")
        manager.stop()