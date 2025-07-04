#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime
from typing import Optional, List, Dict

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
        print(f"Message sent to {to}: {subject}")
    
    def read_messages_for_me(self) -> List[Dict]:
        messages = self.read_all_messages()
        my_messages = [msg for msg in messages if msg["to"] == self.worker_name and not msg.get("read", True)]
        
        # Mark messages as read
        for msg in messages:
            if msg["to"] == self.worker_name:
                msg["read"] = True
        self.write_messages(messages)
        
        return my_messages
    
    def read_all_messages(self) -> List[Dict]:
        try:
            with open(self.messages_file, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def write_messages(self, messages: List[Dict]):
        with open(self.messages_file, 'w') as f:
            json.dump(messages, f, indent=2)
    
    def log_activity(self, activity: str, progress: Optional[int] = None):
        log_file = f"{self.worker_name}/{self.worker_name}_log.txt"
        os.makedirs(self.worker_name, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {activity}"
        if progress is not None:
            log_entry += f" (Progress: {progress}%)"
        
        with open(log_file, 'a') as f:
            f.write(log_entry + "\n")
        
        print(log_entry)

# Command line interface
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python worker_communication.py <worker_name> <command> [args...]")
        print("Commands:")
        print("  send <to> <subject> <message> [priority]")
        print("  read")
        print("  log <activity> [progress]")
        sys.exit(1)
    
    worker_name = sys.argv[1]
    comm = WorkerCommunication(worker_name)
    
    if len(sys.argv) < 3:
        print("Error: No command specified")
        sys.exit(1)
    
    command = sys.argv[2]
    
    if command == "send":
        if len(sys.argv) < 6:
            print("Error: send command requires: <to> <subject> <message> [priority]")
            sys.exit(1)
        to = sys.argv[3]
        subject = sys.argv[4]
        message = sys.argv[5]
        priority = sys.argv[6] if len(sys.argv) > 6 else "medium"
        comm.send_message(to, subject, message, priority)
    
    elif command == "read":
        messages = comm.read_messages_for_me()
        if not messages:
            print("No new messages")
        else:
            for msg in messages:
                print(f"\n--- Message from {msg['from']} ---")
                print(f"Time: {msg['timestamp']}")
                print(f"Subject: {msg['subject']}")
                print(f"Priority: {msg['priority']}")
                print(f"Message: {msg['message']}")
                print("---")
    
    elif command == "log":
        if len(sys.argv) < 4:
            print("Error: log command requires: <activity> [progress]")
            sys.exit(1)
        activity = sys.argv[3]
        progress = int(sys.argv[4]) if len(sys.argv) > 4 else None
        comm.log_activity(activity, progress)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)