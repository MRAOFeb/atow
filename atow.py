import socket
import sounddevice as sd
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal


def get_local_ip():
    addrs = set()
    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if ip and not ip.startswith("127."):
                addrs.add(ip)
    except Exception:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127."):
            addrs.add(ip)
    except Exception:
        pass
    if not addrs:
        return ["127.0.0.1"]
    return sorted(addrs)


settings = {}
for i in open('settings.txt'):
    key, value = i.strip().split('=')
    settings[key] = float(value)

class AudioServer(QObject):
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.running = False
        self.volume_value = settings.get('volume', 0.3)
        self.sock = None
        self.stream = None

    def set_volume(self, value):
        self.volume_value = value

    def start(self):
        if not self.running:
            self.running = True
            self.listen()

    def stop(self):
        self.running = False

    def listen(self):
        UDP_IP = "0.0.0.0"
        UDP_PORT = 5006
        LOCAL_IPS = get_local_ip()
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((UDP_IP, UDP_PORT))
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
            self.sock.settimeout(0.5)

            self.log_signal.emit("=" * 50)
            self.log_signal.emit(f"Your PC IPs: {', '.join(LOCAL_IPS)}")
            self.log_signal.emit("Введите один из этих IP в Android приложении")
            self.log_signal.emit("=" * 50)
            self.log_signal.emit(f"Listening on port {UDP_PORT}...")
            self.log_signal.emit("Waiting for data...")

            samplerate = 44100
            channels = 1
            self.stream = sd.OutputStream(
                samplerate=samplerate,
                channels=channels,
                dtype='float32'
            )
            self.stream.start()

            packet_count = 0
            while self.running:
                try:
                    data, addr = self.sock.recvfrom(8192)
                except socket.timeout:
                    continue
                except Exception as e:
                    self.log_signal.emit(f"Socket error: {e}")
                    break
                packet_count += 1
                audio_chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                audio_chunk = np.clip(audio_chunk * self.volume_value, -1.0, 1.0)
                if packet_count % 100 == 0:
                    volume = np.max(np.abs(audio_chunk))
                    self.log_signal.emit(
                        f"[{packet_count}] Recv: {len(data)} bytes from {addr} | Level: {volume:.2f}"
                    )
                    if volume < 0.01:
                        self.log_signal.emit("   Внимание: получена тишина!")
                try:
                    self.stream.write(audio_chunk)
                except Exception as e:
                    self.log_signal.emit(f"Ошибка записи в поток: {e}")
        except Exception as e:
            self.log_signal.emit(f"Ошибка: {e}")
        finally:
            try:
                if self.stream:
                    self.stream.stop()
                    self.stream.close()
            except:
                pass
            if self.sock:
                self.sock.close()
            self.running = False
            self.log_signal.emit("Остановлено")