#!/usr/bin/env python3
import socket
import serial
import time
import sys
from config import *
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

def print_status(service, status, details=""):
    if status:
        print(f"{Fore.GREEN}[✓] {service}: Connected {details}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}[✗] {service}: Failed {details}{Style.RESET_ALL}")

def check_tcp_connection(host, port, service_name):
    try:
        # Using the same connection method as TCPClient.py
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.settimeout(2)
            client_socket.connect((host, port))
            print_status(f"TCP {service_name} ({host}:{port})", True)
            return True
    except Exception as e:
        print_status(f"TCP {service_name} ({host}:{port})", False, f"- Error: {str(e)}")
        return False

def check_udp_connection(host, port):
    try:
        # Using similar setup as ImageBroker.py
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(2)
        
        # Try to bind to receive port (as server would)
        try:
            sock.bind(('0.0.0.0', port))
            sock.close()
            print_status(f"UDP Image Port ({host}:{port})", True, "- Port available")
            return True
        except Exception as e:
            if "Address already in use" in str(e):
                print_status(f"UDP Image Port ({host}:{port})", True, "- Port in use (likely by Image Server)")
                return True
            print_status(f"UDP Image Port ({host}:{port})", False, f"- Error: {str(e)}")
            return False
    except Exception as e:
        print_status(f"UDP Image Port ({host}:{port})", False, f"- Error: {str(e)}")
        return False

def check_serial_connection(port, baudrate, service_name, timeout=1):
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        time.sleep(0.2)  # Allow connection time (reduced from 2s in SerialBluetooth.py)
        is_open = ser.is_open
        ser.close()
        print_status(f"Serial {service_name} ({port})", is_open)
        return is_open
    except Exception as e:
        print_status(f"Serial {service_name} ({port})", False, f"- Error: {str(e)}")
        return False

def check_camera():
    try:
        import picamera
        camera = picamera.PiCamera()
        camera.close()
        print_status("Pi Camera", True)
        return True
    except ImportError:
        print_status("Pi Camera", False, "- picamera module not installed")
        return False
    except Exception as e:
        print_status("Pi Camera", False, f"- Error: {str(e)}")
        return False

def main():
    print(f"{Fore.CYAN}=== MDP Robot Health Check ==={Style.RESET_ALL}")
    
    # Check TCP Algo Server
    algo_status = check_tcp_connection(ALGO_TCP_IP, ALGO_TCP_PORT, "Algo Server")
    
    # Check TCP Image Server
    img_status = check_tcp_connection(IMG_TCP_IP, IMG_TCP_PORT, "Image Server")
    
    # Check UDP Image Port
    udp_status = check_udp_connection(UDP_IP, UDP_PORT)
    
    # Check STM UART Connection
    stm_status = check_serial_connection(STM_PORT, STM_BAUD_RATE, "STM")
    
    # Check Bluetooth Connection
    bluetooth_status = check_serial_connection(BLUETOOTH_PORT, 9600, "Bluetooth")
    
    # Check Pi Camera (if running on Raspberry Pi)
    camera_status = check_camera()
    
    # Summary
    print(f"\n{Fore.CYAN}=== Summary ==={Style.RESET_ALL}")
    total_services = 6
    working_services = sum([algo_status, img_status, udp_status, stm_status, bluetooth_status, camera_status])
    print(f"Working Services: {working_services}/{total_services}")
    
    # Exit with appropriate status code
    sys.exit(0 if working_services == total_services else 1)

if __name__ == "__main__":
    main()
