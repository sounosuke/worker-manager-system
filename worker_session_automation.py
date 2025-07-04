#!/usr/bin/env python3
import json
import os
import sys
import time
import shutil
from datetime import datetime
from pathlib import Path
import subprocess

class WorkerSessionAutomation:
    def __init__(self, worker_name):
        self.worker_name = worker_name
        self.comm = WorkerCommunication(self.worker_name)
        self.running = True
        self.instructions_file = "worker_session_instructions.md"
        self.pending_tasks_dir = f"pending_tasks/{worker_name}"
        self.completed_tasks_dir = f"completed_tasks/{worker_name}"
        self.worker_dir = worker_name
        
        # ディレクトリ作成
        self.ensure_directories()
        
        # 初期ログ
        self.comm.log_activity(f"Worker {worker_name} session automation started")
        self.read_instructions()
    
    def ensure_directories(self):
        """必要なディレクトリを確保"""
        os.makedirs(self.pending_tasks_dir, exist_ok=True)
        os.makedirs(self.completed_tasks_dir, exist_ok=True)
        os.makedirs(self.worker_dir, exist_ok=True)
        os.makedirs("communication", exist_ok=True)
    
    def read_instructions(self):
        """指示書を読み込む"""
        try:
            with open(self.instructions_file, 'r') as f:
                instructions = f.read()
                self.comm.log_activity(f"Worker {self.worker_name} instructions loaded successfully")
                print(f"\n=== Worker {self.worker_name} Instructions ===")
                print(instructions[:500] + "..." if len(instructions) > 500 else instructions)
                print("=" * 40 + "\n")
        except Exception as e:
            self.comm.log_activity(f"Error reading instructions: {str(e)}")
    
    def check_pending_tasks(self):
        """保留中のタスクをチェック"""
        try:
            task_files = list(Path(self.pending_tasks_dir).glob("*.json"))
            if task_files:
                self.comm.log_activity(f"Found {len(task_files)} pending tasks")
                for task_file in task_files:
                    self.process_task(task_file)
        except Exception as e:
            self.comm.log_activity(f"Error checking pending tasks: {str(e)}")
    
    def process_task(self, task_file):
        """タスクを処理"""
        try:
            with open(task_file, 'r') as f:
                task_data = json.load(f)
            
            task_name = task_data.get('name', 'unknown_task')
            self.comm.log_activity(f"Starting task: {task_name}", progress=0)
            
            # Managerに開始報告
            self.comm.send_message("manager", f"タスク開始: {task_name}", 
                                 f"Task '{task_name}' has been started by {self.worker_name}")
            
            # タスクの種類に応じて実行
            if 'command' in task_data:
                self.execute_command_task(task_data)
            elif 'script' in task_data:
                self.execute_script_task(task_data)
            else:
                self.execute_generic_task(task_data)
            
            # 完了処理
            self.complete_task(task_file, task_data)
            
        except Exception as e:
            self.comm.log_activity(f"Error processing task {task_file}: {str(e)}")
            self.comm.send_message("manager", f"タスクエラー: {task_file.name}", 
                                 f"Error occurred while processing task: {str(e)}", "high")
    
    def execute_command_task(self, task_data):
        """コマンドタスクを実行"""
        command = task_data['command']
        task_name = task_data.get('name', 'command_task')
        
        self.comm.log_activity(f"Executing command: {command}", progress=25)
        
        try:
            # 作業ディレクトリを変更
            original_dir = os.getcwd()
            os.chdir(self.worker_dir)
            
            # コマンド実行
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            # 結果をファイルに保存
            output_file = f"task_{task_name}_output.txt"
            with open(output_file, 'w') as f:
                f.write(f"Task: {task_name}\n")
                f.write(f"Command: {command}\n")
                f.write(f"Exit Code: {result.returncode}\n")
                f.write(f"STDOUT:\n{result.stdout}\n")
                f.write(f"STDERR:\n{result.stderr}\n")
            
            self.comm.log_activity(f"Command executed successfully. Output saved to {output_file}", progress=75)
            
            # 元のディレクトリに戻る
            os.chdir(original_dir)
            
        except Exception as e:
            self.comm.log_activity(f"Error executing command: {str(e)}")
            os.chdir(original_dir)
            raise
    
    def execute_script_task(self, task_data):
        """スクリプトタスクを実行"""
        script = task_data['script']
        task_name = task_data.get('name', 'script_task')
        
        self.comm.log_activity(f"Executing script for task: {task_name}", progress=25)
        
        try:
            # 作業ディレクトリを変更
            original_dir = os.getcwd()
            os.chdir(self.worker_dir)
            
            # スクリプトを一時ファイルに保存
            script_file = f"temp_script_{task_name}.py"
            with open(script_file, 'w') as f:
                f.write(script)
            
            # スクリプト実行
            result = subprocess.run([sys.executable, script_file], 
                                  capture_output=True, text=True)
            
            # 結果をファイルに保存
            output_file = f"task_{task_name}_output.txt"
            with open(output_file, 'w') as f:
                f.write(f"Task: {task_name}\n")
                f.write(f"Script executed: {script_file}\n")
                f.write(f"Exit Code: {result.returncode}\n")
                f.write(f"STDOUT:\n{result.stdout}\n")
                f.write(f"STDERR:\n{result.stderr}\n")
            
            # 一時ファイルを削除
            os.remove(script_file)
            
            self.comm.log_activity(f"Script executed successfully. Output saved to {output_file}", progress=75)
            
            # 元のディレクトリに戻る
            os.chdir(original_dir)
            
        except Exception as e:
            self.comm.log_activity(f"Error executing script: {str(e)}")
            os.chdir(original_dir)
            raise
    
    def execute_generic_task(self, task_data):
        """一般的なタスクを実行"""
        task_name = task_data.get('name', 'generic_task')
        description = task_data.get('description', 'No description')
        
        self.comm.log_activity(f"Processing generic task: {task_name}", progress=25)
        
        # 作業ディレクトリを変更
        original_dir = os.getcwd()
        os.chdir(self.worker_dir)
        
        # タスク情報をファイルに保存
        output_file = f"task_{task_name}_output.txt"
        with open(output_file, 'w') as f:
            f.write(f"Task: {task_name}\n")
            f.write(f"Description: {description}\n")
            f.write(f"Worker: {self.worker_name}\n")
            f.write(f"Processed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Status: Task acknowledged and processed\n")
        
        self.comm.log_activity(f"Generic task processed. Output saved to {output_file}", progress=75)
        
        # 元のディレクトリに戻る
        os.chdir(original_dir)
    
    def complete_task(self, task_file, task_data):
        """タスクを完了"""
        task_name = task_data.get('name', 'unknown_task')
        
        try:
            # タスクファイルを完了フォルダに移動
            completed_file = Path(self.completed_tasks_dir) / task_file.name
            shutil.move(str(task_file), str(completed_file))
            
            self.comm.log_activity(f"Task completed: {task_name}", progress=100)
            
            # Managerに完了報告
            self.comm.send_message("manager", f"タスク完了: {task_name}", 
                                 f"Task '{task_name}' has been completed by {self.worker_name}")
            
        except Exception as e:
            self.comm.log_activity(f"Error completing task: {str(e)}")
    
    def check_messages(self):
        """メッセージをチェック"""
        messages = self.comm.read_messages_for_me()
        for msg in messages:
            self.comm.log_activity(f"Received message from {msg['from']}: {msg['subject']}")
            
            # 特定のメッセージタイプに応じた処理
            if "停止" in msg['subject'] or "stop" in msg['subject'].lower():
                self.comm.log_activity("Received stop command from manager")
                self.running = False
            elif "リトライ" in msg['subject']:
                self.comm.log_activity("Received retry command from manager")
                # 失敗したタスクを再処理
                self.check_pending_tasks()
    
    def run(self):
        """メインループ"""
        task_check_interval = 30    # 30秒ごとにタスクチェック
        message_check_interval = 20  # 20秒ごとにメッセージチェック
        
        last_task_check = 0
        last_message_check = 0
        
        self.comm.log_activity(f"Worker {self.worker_name} is now running autonomously")
        
        while self.running:
            current_time = time.time()
            
            # タスクチェック
            if current_time - last_task_check >= task_check_interval:
                self.check_pending_tasks()
                last_task_check = current_time
            
            # メッセージチェック
            if current_time - last_message_check >= message_check_interval:
                self.check_messages()
                last_message_check = current_time
            
            time.sleep(1)
    
    def stop(self):
        """自動化を停止"""
        self.running = False
        self.comm.log_activity(f"Worker {self.worker_name} automation stopped")

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
        log_file = f"{self.worker_name}/{self.worker_name}_log.txt"
        
        # ログファイルのディレクトリを確保
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {activity}"
        if progress is not None:
            log_entry += f" (Progress: {progress}%)"
        
        with open(log_file, 'a') as f:
            f.write(log_entry + "\n")
        
        print(f"[{self.worker_name.upper()}] {log_entry}")

# メイン実行
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python worker_session_automation.py <worker_name>")
        print("Example: python worker_session_automation.py worker1")
        sys.exit(1)
    
    worker_name = sys.argv[1]
    
    try:
        worker = WorkerSessionAutomation(worker_name)
        worker.run()
    except KeyboardInterrupt:
        print(f"\n{worker_name} automation stopped by user")
        worker.stop()