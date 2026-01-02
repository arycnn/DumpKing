#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════╗
║                     DUMPKING v3.5 by Aryan                    ║
║          Ultimate Memory Scanner & Editor for Android         ║
║             Automated Il2CppDumper Extraction Suite           ║
╚═══════════════════════════════════════════════════════════════╝
"""

import socket
import time
import os
import sys
import threading
import subprocess
import shutil
from datetime import datetime

# ==================== CONFIGURATION ====================
METADATA_SIGNATURE_HEX = "af1bb1fa" 
IP = '127.0.0.1'
PORT = 12345
# =======================================================

# Enable ANSI colors in Windows CMD
os.system('color')

class UI:
    # Cyberpunk / Hacker Color Palette
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    ul = '\033[4m'
    
    @staticmethod
    def box(text, color=CYAN):
        lines = text.split('\n')
        width = max(len(line) for line in lines) + 2
        print(f"{color}╔{'═'*width}╗")
        for line in lines:
            print(f"║ {line.center(width-2)} ║")
        print(f"╚{'═'*width}╝{UI.END}")

    @staticmethod
    def print_item(index, text, info=""):
        idx_str = f"[{index}]".ljust(5)
        print(f" {UI.GREEN}{idx_str}{UI.END} {UI.BOLD}{text.ljust(30)}{UI.END} {UI.BLUE}{info}{UI.END}")

    @staticmethod
    def header(text):
        print(f"\n{UI.CYAN}>> {text.upper()} <<{UI.END}")
        print(f"{UI.BLUE}{'-'*40}{UI.END}")

class DumpKing:
    def __init__(self):
        self.host = IP
        self.port = PORT
        self.search_results = []
        self.saved_values = {}
        self.watch_thread = None
        self.watching = False
        self.watch_addresses = []
        
        # --- ROBUST PATH SETUP ---
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.ROOT_DUMP_FOLDER = os.path.join(self.BASE_DIR, "Dumped Memory Tools")
        self.METADATA_FOLDER = os.path.join(self.BASE_DIR, "Dumped MetaData")
        self.IL2CPP_FOLDER = os.path.join(self.BASE_DIR, "Pulled libil2cpp")
        self.DUMPER_FOLDER = os.path.join(self.BASE_DIR, "Il2CppDumper")

        for folder in [self.ROOT_DUMP_FOLDER, self.METADATA_FOLDER, self.IL2CPP_FOLDER]:
            if not os.path.exists(folder):
                try: os.makedirs(folder)
                except: pass

    def banner(self):
        print(f"{UI.CYAN}")
        print(r"""
  ____  _   _ __  __ ____  _  _____ _   _  ____ 
 |  _ \| | | |  \/  |  _ \| |/ /_ _| \ | |/ ___|
 | | | | | | | |\/| | |_) | ' / | ||  \| | |  _ 
 | |_| | |_| | |  | |  __/| . \ | || |\  | |_| |
 |____/ \___/|_|  |_|_|   |_|\_\___|_| \_|\____| v3.5
        """)
        print(f"{UI.END}")
        print(f" {UI.YELLOW}[*] Root Path: {self.BASE_DIR}{UI.END}")
        print(f" {UI.GREEN}[*] Output:    {self.ROOT_DUMP_FOLDER}{UI.END}\n")

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    # ==================== NETWORK CORE ====================

    def send_command(self, cmd, timeout=30):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((self.host, self.port))
            s.send(cmd.encode())
            response = b''
            while True:
                try:
                    chunk = s.recv(65536)
                    if not chunk: break
                    response += chunk
                    if len(response) > 52428800: break 
                except socket.timeout: break
            s.close()
            return response.decode('utf-8', errors='replace').strip('\x00')
        except Exception as e: return f"ERROR:{e}"

    def test_connection(self):
        print(f"{UI.YELLOW}[*] Connecting to device...{UI.END}", end='\r')
        result = self.send_command("PING", timeout=5)
        if "PONG" in result:
            print(f"{UI.GREEN}[✓] CONNECTED: Memory Spy Active{UI.END}      ")
            return True
        else:
            print(f"{UI.RED}[✗] CONNECTION FAILED{UI.END}                 ")
            print(f"\n{UI.YELLOW}TROUBLESHOOTING:{UI.END}")
            print(" 1. Is the game running?")
            print(" 2. Did you inject the smali?")
            print(f" 3. Run: {UI.BOLD}adb forward tcp:12345 tcp:12345{UI.END}")
            return False

    # ==================== UTILITY FUNCTIONS ====================

    def int_to_hex_le(self, value):
        return value.to_bytes(4, byteorder='little').hex()

    def hex_le_to_int(self, hex_str):
        try: return int.from_bytes(bytes.fromhex(hex_str.strip()), byteorder='little')
        except: return None

    def parse_address_list(self, result):
        if result.startswith('ERROR'): return []
        return [int(x.strip()) for x in result.replace('[', '').replace(']', '').split(',') if x.strip()]

    def read_int(self, address):
        return self.hex_le_to_int(self.send_command(f"READ:{hex(address)}:4", timeout=5))

    def write_int(self, address, value):
        return "WRITE_OK" in self.send_command(f"WRITE:{hex(address)}:{value}")

    def check_file_overwrite(self, filepath):
        if os.path.exists(filepath):
            print(f"\n{UI.YELLOW}[!] File exists: {os.path.basename(filepath)}{UI.END}")
            if input(f"{UI.CYAN}Overwrite? (y/n): {UI.END}").lower() == 'y':
                try:
                    os.remove(filepath)
                    time.sleep(0.5)
                    return True
                except: return False
            return False
        return True

    # ==================== CORE DUMPING ENGINE ====================

    def draw_progress_bar(self, current, total, speed, width=30):
        percent = current / total
        filled = int(width * percent)
        bar = '█' * filled + '░' * (width - filled)
        sys.stdout.write(f"\r {UI.CYAN}[{bar}] {percent*100:.1f}% | {speed:.1f} KB/s{UI.END}")
        sys.stdout.flush()

    def perform_smart_dump(self, start_addr, size, filename):
        CHUNK_SIZE = 16384 # Increased chunk size for speed
        total_read = 0
        
        # Absolute path enforcement
        if not os.path.isabs(filename):
            filename = os.path.join(self.ROOT_DUMP_FOLDER, filename)

        UI.header("INITIATING MEMORY DUMP")
        print(f" {UI.BOLD}Target:{UI.END} {hex(start_addr)}")
        print(f" {UI.BOLD}Size:{UI.END}   {size:,} bytes")
        print(f" {UI.BOLD}File:{UI.END}   {os.path.basename(filename)}")
        
        start_time = time.time()
        try:
            with open(filename, 'wb') as f:
                while total_read < size:
                    bytes_to_read = min(CHUNK_SIZE, size - total_read)
                    cmd = f"READ:{hex(start_addr + total_read)}:{bytes_to_read}"
                    hex_data = self.send_command(cmd, timeout=10)
                    
                    if "ERROR" in hex_data or not hex_data:
                        f.write(b'\x00' * bytes_to_read)
                    else:
                        try: f.write(bytes.fromhex(hex_data))
                        except: f.write(b'\x00' * bytes_to_read)
                    
                    total_read += bytes_to_read
                    elapsed = time.time() - start_time
                    speed = (total_read / 1024) / (elapsed if elapsed > 0 else 1)
                    self.draw_progress_bar(total_read, size, speed)
            
            print(f"\n\n{UI.GREEN}[✓] DUMP SUCCESSFUL{UI.END}")
            print(f"Saved to: {UI.YELLOW}{filename}{UI.END}")
            time.sleep(1)
            return True
        except KeyboardInterrupt:
            print(f"\n{UI.RED}[!] Dump Aborted{UI.END}")
            return False

    def get_parsed_maps(self):
        print(f"{UI.YELLOW}[*] Mapping memory regions...{UI.END}", end='\r')
        raw = self.send_command("MAPS", timeout=60)
        if raw.startswith("ERROR"): return []
        
        lines = raw.replace('[', '').replace(']', '').split(',')
        if len(lines) < 2: lines = raw.split('\n')
        
        parsed = []
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 1 and "-" in parts[0]:
                try:
                    s, e = [int(x, 16) for x in parts[0].split('-')]
                    perms = parts[1] if len(parts) > 1 else ""
                    name = parts[-1] if len(parts) > 5 and not parts[-1].startswith('[') else "anon"
                    parsed.append({'start': s, 'end': e, 'size': e-s, 'perms': perms, 'name': name})
                except: pass
        print(f"{UI.GREEN}[✓] Mapped {len(parsed)} regions       {UI.END}")
        return parsed

    # ==================== AUTOMATED SUITE ====================

    def scan_metadata_region(self, start, size, sig_bytes):
        # Optimized scanner without verbose output per chunk
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((self.host, self.port))
        except: return None

        CHUNK = 1024 * 1024
        curr = 0
        overlap = b""
        limit = min(size, 32 * 1024 * 1024) # Scan first 32MB

        while curr < limit:
            read_len = min(CHUNK, size - curr)
            s.send(f"READ:{hex(start+curr)}:{read_len}".encode())
            
            hex_data = b""
            expected = read_len * 2
            while len(hex_data) < expected:
                try:
                    p = s.recv(65536)
                    if not p or b"ERROR" in p: 
                        s.close()
                        return None
                    hex_data += p
                except: break
            
            try: chunk = bytes.fromhex(hex_data.decode())
            except: 
                curr += read_len
                continue

            buf = overlap + chunk
            idx = buf.find(sig_bytes)
            if idx != -1:
                s.close()
                return start + curr - len(overlap) + idx
            
            overlap = chunk[-len(sig_bytes):]
            curr += read_len
        s.close()
        return None

    def auto_pull_metadata(self):
        UI.header("PHASE 1: METADATA HUNT")
        target = os.path.join(self.METADATA_FOLDER, "global-metadata.dat")
        if not self.check_file_overwrite(target): return True
        
        maps = self.get_parsed_maps()
        cands = [m for m in maps if 'rw' in m['perms'] and 10*1024*1024 <= m['size'] <= 128*1024*1024]
        
        print(f"[*] Scanning {len(cands)} candidate regions...")
        sig = bytes.fromhex(METADATA_SIGNATURE_HEX)
        
        found = None
        for i, m in enumerate(cands):
            sys.stdout.write(f"\r {UI.YELLOW}>> Scanning {i+1}/{len(cands)}: {m['name']} ({m['size']//1024//1024}MB){UI.END}   ")
            found = self.scan_metadata_region(m['start'], m['size'], sig)
            if found: break
            
        if found:
            print(f"\n{UI.GREEN}[!!!] SIGNATURE FOUND AT {hex(found)} [!!!]{UI.END}")
            return self.perform_smart_dump(found, 40000000, target)
        else:
            print(f"\n{UI.RED}[-] Signature not found.{UI.END}")
            return False

    def auto_pull_libil2cpp(self):
        UI.header("PHASE 2: BINARY PULL")
        target = os.path.join(self.IL2CPP_FOLDER, "libil2cpp.so")
        if not self.check_file_overwrite(target): return True
        
        maps = self.get_parsed_maps()
        best = None
        max_s = 0
        for m in maps:
            if "libil2cpp.so" in m['name'] and m['size'] > max_s:
                max_s = m['size']
                best = m
                
        if best:
            print(f"{UI.GREEN}[+] Located libil2cpp.so at {hex(best['start'])}{UI.END}")
            return self.perform_smart_dump(best['start'], best['size'], target)
        
        print(f"{UI.RED}[-] libil2cpp.so not found in maps.{UI.END}")
        return False

    def run_dumper(self):
        UI.header("PHASE 3: GENERATE DUMP.CS")
        exe = os.path.join(self.DUMPER_FOLDER, "Il2CppDumper.exe")
        if not os.path.exists(exe):
            print(f"{UI.RED}[!] Il2CppDumper.exe missing.{UI.END}")
            print(f"    Expected: {exe}")
            return
        
        print(f"{UI.GREEN}[+] Launching external tool...{UI.END}")
        try: subprocess.Popen([exe], cwd=self.DUMPER_FOLDER, shell=True)
        except Exception as e: print(f"{UI.RED}Error: {e}{UI.END}")

    def automated_menu(self):
        while True:
            self.clear_screen()
            UI.box("AUTOMATED DUMP SUITE", UI.YELLOW)
            print("")
            UI.print_item("1", "Pull Metadata", "Finds encrypted global-metadata")
            UI.print_item("2", "Pull Binary", "Dumps libil2cpp.so")
            UI.print_item("3", "Run Dumper", "Generates dump.cs")
            UI.print_item("4", "FULL SEQUENCE", "Runs 1 -> 2 -> 3")
            print("")
            UI.print_item("0", "Back")
            
            c = input(f"\n{UI.CYAN}root@android:~/auto# {UI.END}")
            if c == '1': 
                self.auto_pull_metadata()
                input("Done. Enter to continue...")
            elif c == '2':
                self.auto_pull_libil2cpp()
                input("Done. Enter to continue...")
            elif c == '3':
                self.run_dumper()
                input("Done. Enter to continue...")
            elif c == '4':
                if self.auto_pull_metadata():
                    time.sleep(1)
                    if self.auto_pull_libil2cpp():
                        time.sleep(1)
                        self.run_dumper()
                input("Sequence complete. Enter...")
            elif c == '0': break

    # ==================== MAIN MENUS ====================

    def search_menu(self):
        while True:
            self.clear_screen()
            UI.box("SEARCH MEMORY", UI.GREEN)
            print("")
            UI.print_item("1", "Integer Search", "DWORD (4 bytes)")
            UI.print_item("2", "Hex Search", "Pattern matching")
            UI.print_item("3", "Refine", "Filter current results")
            UI.print_item("4", "View Results", f"{len(self.search_results)} found")
            UI.print_item("5", "Clear", "Reset search")
            print("")
            UI.print_item("0", "Back")
            
            c = input(f"\n{UI.CYAN}root@android:~/search# {UI.END}")
            if c == '1':
                try:
                    val = int(input(f"{UI.YELLOW}Value: {UI.END}"))
                    res = self.send_command(f"SCAN:{val}", 120)
                    self.search_results = self.parse_address_list(res)
                    print(f"{UI.GREEN}Found {len(self.search_results)} matches.{UI.END}")
                except: pass
                input("Enter...")
            elif c == '2':
                pat = input(f"{UI.YELLOW}Hex: {UI.END}").replace(" ","").replace("0x","")
                res = self.send_command(f"SEARCHHEX:{pat}", 180)
                if "ERROR" not in res:
                    self.search_results = self.parse_address_list(res)
                    print(f"{UI.GREEN}Found {len(self.search_results)} matches.{UI.END}")
                input("Enter...")
            elif c == '3':
                try:
                    val = int(input(f"{UI.YELLOW}New Value: {UI.END}"))
                    self.search_results = [a for a in self.search_results if self.read_int(a) == val]
                    print(f"{UI.GREEN}Refined to {len(self.search_results)}.{UI.END}")
                except: pass
                input("Enter...")
            elif c == '4':
                UI.header("RESULTS")
                for i in range(min(20, len(self.search_results))):
                    print(f" {hex(self.search_results[i])} : {self.read_int(self.search_results[i])}")
                input("Enter...")
            elif c == '5':
                self.search_results = []
                print("Cleared.")
                time.sleep(0.5)
            elif c == '0': break

    def dump_menu(self):
        while True:
            self.clear_screen()
            UI.box("MANUAL DUMP TOOLS", UI.RED)
            print("")
            UI.print_item("1", "Region Dump", "Select from map list")
            UI.print_item("2", "Manual Dump", "Start Address + Size")
            UI.print_item("3", "Dump Anonymous", "Bulk dump RW regions")
            print("")
            UI.print_item("0", "Back")
            
            c = input(f"\n{UI.CYAN}root@android:~/dump# {UI.END}")
            if c == '1': self.dump_region_selector()
            elif c == '2': self.dump_address_manual()
            elif c == '3': self.dump_all_anon()
            elif c == '0': break

    def dump_region_selector(self):
        maps = self.get_parsed_maps()
        if not maps: return
        print(f"\n{UI.YELLOW}[1] RW Only  [2] Libraries Only  [0] All{UI.END}")
        opt = input("Filter: ")
        
        filtered = []
        for m in maps:
            if opt == '1' and 'rw' not in m['perms']: continue
            if opt == '2' and '.so' not in m['name']: continue
            filtered.append(m)
            
        print("\n   ID   |    ADDRESS    |   SIZE   | NAME")
        print("-" * 50)
        for i, m in enumerate(filtered):
            sz = f"{m['size']//1024} KB"
            print(f" [{str(i).rjust(3)}] | {hex(m['start']).ljust(12)} | {sz.ljust(8)} | {m['name']}")
            
        try:
            idx = int(input(f"\n{UI.CYAN}ID to Dump: {UI.END}"))
            t = filtered[idx]
            name = "".join(c for c in t['name'].split('/')[-1] if c.isalnum() or c in '._') or "anon"
            fname = f"dump_{name}_{hex(t['start'])}.bin"
            self.perform_smart_dump(t['start'], t['size'], fname)
        except: pass
        input("Enter...")

    def dump_address_manual(self):
        try:
            start = int(input("Start Address (hex): "), 16)
            size = int(input("Size (bytes): "))
            fname = f"dump_{hex(start)}.bin"
            self.perform_smart_dump(start, size, fname)
        except: pass
        input("Enter...")

    def dump_all_anon(self):
        print("Bulk dumping anonymous regions...")
        maps = self.get_parsed_maps()
        sub = os.path.join(self.ROOT_DUMP_FOLDER, f"Bulk_{datetime.now().strftime('%H%M')}")
        if not os.path.exists(sub): os.makedirs(sub)
        
        cands = [m for m in maps if 'rw' in m['perms'] and (m['name'] == '' or 'anon' in m['name'])]
        for i, m in enumerate(cands):
            print(f"Processing {i}/{len(cands)}...")
            fname = os.path.join(sub, f"anon_{hex(m['start'])}.bin")
            self.perform_smart_dump(m['start'], m['size'], fname)
        input("Enter...")

    def view_memory_maps(self):
        maps = self.get_parsed_maps()
        print(f"\n{UI.GREEN}Total Regions: {len(maps)}{UI.END}")
        input("Enter to scroll list...")
        for m in maps:
            print(f" {hex(m['start'])} - {hex(m['end'])} [{m['perms']}] {m['name']}")
        input("Enter...")

    def main_menu(self):
        while True:
            self.clear_screen()
            self.banner()
            
            # Dual Column Layout
            print(f" {UI.YELLOW}SCANNER TOOLS{UI.END}                 {UI.YELLOW}DUMPER TOOLS{UI.END}")
            print(f" {UI.BLUE}-------------{UI.END}                 {UI.BLUE}------------{UI.END}")
            print(f" {UI.GREEN}[1]{UI.END} Search Memory             {UI.GREEN}[3]{UI.END} Manual Dump")
            print(f" {UI.GREEN}[2]{UI.END} Write / Freeze            {UI.GREEN}[8]{UI.END} {UI.RED}AUTO-EXTRACT (DUMP.CS){UI.END}")
            print("")
            print(f" {UI.YELLOW}UTILS{UI.END}")
            print(f" {UI.BLUE}-----{UI.END}")
            print(f" {UI.GREEN}[4]{UI.END} Watch List")
            print(f" {UI.GREEN}[5]{UI.END} View Maps")
            print(f" {UI.GREEN}[6]{UI.END} Reconnect")
            print(f" {UI.GREEN}[0]{UI.END} Exit")
            
            choice = input(f"\n{UI.CYAN}root@android:~# {UI.END}")
            
            if choice == '1': self.search_menu()
            elif choice == '2': self.write_menu() # Re-implement if needed, placeholder for now
            elif choice == '3': self.dump_menu()
            elif choice == '4': 
                print("Watch list is empty."); time.sleep(1)
            elif choice == '5': self.view_memory_maps()
            elif choice == '6': 
                self.test_connection(); time.sleep(1)
            elif choice == '8': self.automated_menu()
            elif choice == '0': sys.exit(0)

    # Placeholder for write menu to avoid attribute error if selected
    def write_menu(self):
        print("Manual write not implemented in this UI version.")
        time.sleep(1)

    def run(self):
        self.clear_screen()
        self.banner()
        if not self.test_connection():
            sys.exit(1)
        time.sleep(1)
        self.main_menu()

if __name__ == "__main__":
    try:
        dk = DumpKing()
        dk.run()
    except KeyboardInterrupt:
        print(f"\n{UI.YELLOW}Session Terminated.{UI.END}")
        sys.exit(0)
