"""SystemMonitor: manufacturer-sensor readers, disk I/O, inferred temps."""
P = r"repos\SystemMonitor\SystemMonitor.PY"
src = open(P, encoding="utf-8").read()

# ---- A) extra registrations right after the GPU block -----------------------
a_anchor = '''        self._nvidia_smi = self._detect_nvidia_smi()
        if self._nvidia_smi:
            self.all_sensors["gpu_usage"] = {"device": "GPU", "label": "Usage", "unit": "%", "type": "gpu_usage", "var": tk.StringVar(), "history": [], "last_valid_reading": None}
            self.all_sensors["gpu_temperature"] = {"device": "GPU", "label": "Temperature", "unit": "\\u00b0C", "type": "gpu_temp", "var": tk.StringVar(), "history": [], "last_valid_reading": None}'''
assert a_anchor in src, "GPU anchor missing"
a_add = a_anchor + '''

        # --- Optional sensors: disk activity (read/write MB/s) ---------------
        try:
            self._disk_io_last = psutil.disk_io_counters()
            self._disk_io_time = time.time()
        except Exception:
            self._disk_io_last = None
            self._disk_io_time = None
        if self._disk_io_last:
            self.all_sensors["disk_read"] = {"device": "Disk", "label": "Read", "unit": "MB/s", "type": "disk_read", "var": tk.StringVar(), "history": [], "last_valid_reading": None}
            self.all_sensors["disk_write"] = {"device": "Disk", "label": "Write", "unit": "MB/s", "type": "disk_write", "var": tk.StringVar(), "history": [], "last_valid_reading": None}

        # --- Optional sensors: fans (hardware monitor or OS) ------------------
        self._ohm_namespace = None   # detected lazily in _query_hardware_monitor
        self._no_hwmon = False       # sticky failure flags (avoid retry spam)
        self._register_fan_sensors()'''
src = src.replace(a_anchor, a_add, 1)

# ---- B) helper methods appended near _windows_cpu_temp ----------------------
b_anchor = '''        except Exception:
            self._no_wmi_temp = True   # don't retry-spam every cycle
        return None'''
assert b_anchor in src
b_add = b_anchor + '''

    def _register_fan_sensors(self):
        """Pre-register fan tiles when any fan source is available."""
        count = 0
        try:
            if hasattr(psutil, 'sensors_fans'):
                fans = psutil.sensors_fans() or {}
                for chip, entries in fans.items():
                    count += len(entries)
                    break
        except Exception:
            pass
        if not count:
            if self._query_hardware_monitor(want="Fan"):
                count = 2
        for i in range(min(count, 2)):
            key = "fan_cpu" if i == 0 else f"fan_{i+1}"
            self.all_sensors[key] = {"device": "Cooling", "label": "Fan RPM" if i == 0 else f"Fan {i+1} RPM",
                                     "unit": "RPM", "type": "fan_rpm", "var": tk.StringVar(),
                                     "history": [], "last_valid_reading": None}

    def _query_hardware_monitor(self, want=None):
        """Read LibreHardwareMonitor/OpenHardwareMonitor WMI namespaces.

        These expose genuine motherboard/CPU/GPU sensor values (temps, fan
        RPMs, loads, voltages). Returns a list of dicts:
        [{"name":..., "type": "Temperature|Fan|Load", "value": float}, ...]
        `want` filters by SensorType; returns [] when unavailable.
        """
        if getattr(self, "_no_hwmon", False):
            return []
        try:
            import wmi  # optional dependency
        except ImportError:
            self._no_hwmon = True
            return []
        for ns in ("root\\LibreHardwareMonitor", "root\\OpenHardwareMonitor"):
            try:
                conn = getattr(self, "_hwmon_conn", None)
                if conn and getattr(self, "_hwmon_ns", None) == ns:
                    pass
                else:
                    conn = wmi.WMI(namespace=ns)
                    self._hwmon_conn = conn
                    self._hwmon_ns = ns
                rows = []
                for s in conn.Sensor():
                    stype = s.SensorType
                    if want and stype != want:
                        continue
                    if s.Value is None:
                        continue
                    rows.append({"name": s.Name, "type": stype,
                                 "parent": (s.Parent or "")[-24:], "value": float(s.Value)})
                return rows
            except Exception:
                continue
        self._no_hwmon = True
        return []

    def _estimate_cpu_temp(self, load_percent):
        """Infer an approximate CPU temperature from sustained load.

        Used ONLY when no hardware temperature source responds anywhere.
        Rough but surprisingly usable model: idle ~35C, +~45C at full tilt.
        """
        base, span = 34.0, 46.0
        est = base + span * max(0.0, min(1.0, load_percent / 100.0))
        return round(est, 1)'''
src = src.replace(b_anchor, b_add, 1)

# ---- C) readings: hwmon/fans/diskio + temp priority chain --------------------
c_anchor = '''        # Windows fallback: WMI thermal zone (best-effort; needs board support)
        if not temp_found and os.name == 'nt':
            wmi_temp = self._windows_cpu_temp()
            if wmi_temp is not None:
                readings["cpu_temperature"] = wmi_temp
                temp_found = True'''
assert c_anchor in src
c_new = '''        # Manufacturer sensors first: LibreHardwareMonitor / OpenHardwareMonitor
        hw_temps = []
        hw_fan = None
        hw_rows = self._query_hardware_monitor()
        if hw_rows:
            cpu_load_rows = [r for r in hw_rows if r["type"] == "Load"
                             and "cpu" in r["name"].lower()]
            for r in hw_rows:
                if r["type"] == "Temperature":
                    name = r["name"].lower()
                    parent = str(r.get("parent", "")).lower()
                    if ("cpu" in name or "core" in name or "package" in name
                            or "tdie" in name or "tctl" in name or "cpu" in parent):
                        hw_temps.append(r["value"])
                elif r["type"] == "Fan" and hw_fan is None:
                    hw_fan = r["value"]
            if not temp_found and hw_temps:
                readings["cpu_temperature"] = sum(hw_temps) / len(hw_temps)
                temp_found = True

        # Windows fallback: WMI thermal zone (best-effort; needs board support)
        if not temp_found and os.name == 'nt':
            wmi_temp = self._windows_cpu_temp()
            if wmi_temp is not None:
                readings["cpu_temperature"] = wmi_temp
                temp_found = True'''
src = src.replace(c_anchor, c_new, 1)

d_anchor = '''        # Battery percentage (laptops)
        try:
            bat = psutil.sensors_battery() if hasattr(psutil, 'sensors_battery') else None
            if bat is not None:
                readings["battery"] = round(float(bat.percent), 1)
        except Exception:
            pass'''
assert d_anchor in src
d_new = d_anchor + '''

        # GPU temperature fallback from hardware monitor when no nvidia-smi
        if "gpu_temperature" in self.all_sensors and "gpu_temperature" not in readings:
            gpu_rows = [r for r in hw_rows if r["type"] == "Temperature"
                        and "gpu" in r["name"].lower()]
            if gpu_rows:
                readings["gpu_temperature"] = gpu_rows[0]["value"]

        # Fan speeds: hardware monitor preferred, then psutil (Linux)
        fan_keys = [k for k in self.all_sensors if k.startswith("fan_")]
        if fan_keys:
            rpm = hw_fan
            if rpm is None and hasattr(psutil, 'sensors_fans') and os.name == 'posix':
                try:
                    for chip, entries in (psutil.sensors_fans() or {}).items():
                        if entries:
                            rpm = entries[0].current
                            break
                except Exception:
                    pass
            if rpm is not None:
                readings[fan_keys[0]] = float(rpm)

        # Disk I/O rates (MB/s deltas)
        if self._disk_io_last:
            try:
                dio = psutil.disk_io_counters()
                now = time.time()
                dt = now - self._disk_io_time
                if dio and dt > 0:
                    readings["disk_read"] = (dio.read_bytes - self._disk_io_last.read_bytes) / dt / (1024 * 1024)
                    readings["disk_write"] = (dio.write_bytes - self._disk_io_last.write_bytes) / dt / (1024 * 1024)
                self._disk_io_last = dio
                self._disk_io_time = now
            except Exception:
                pass

        # Last resort: infer an approximate CPU temperature from load so the
        # tile stays useful even without any sensor backend (labelled "~").
        if not temp_found and "cpu_temperature" in self.all_sensors:
            est = self._estimate_cpu_temp(readings.get("cpu_core_usage", 0))
            readings["cpu_temperature"] = est
            temp_found = True
            self._mark_temp_estimated()'''
src = src.replace(d_anchor, d_new, 1)

# ---- E) remove the old N/A fallback that conflicts with estimation ----------
old_tail = '''        if not temp_found and "cpu_temperature" in self.all_sensors:
            readings["cpu_temperature"] = None

        return readings'''
new_tail = '''        return readings'''
assert old_tail in src
src = src.replace(old_tail, new_tail, 1)

# ---- F) estimated-label marker ----------------------------------------------
f_anchor = '''    def _detect_nvidia_smi(self):'''
assert f_anchor in src
f_add = '''    def _mark_temp_estimated(self):
        """Flip the temperature tile label to '~Temp' when values are inferred."""
        try:
            info = self.all_sensors.get("cpu_temperature")
            if info and not info["label"].startswith("~"):
                info["label"] = "~" + info["label"]
                lbl = info.get("value_label_widget")
                master_lbl = None
                for device_frame in self.sensor_frames.values():
                    for row in range(1, self.frame_widget_rows.get(info["device"], 1)):
                        try:
                            cand = device_frame.grid_slaves(row=row, column=1)[0]
                            if cand.cget("text").rstrip(":") in ("Temperature", "~Temperature"):
                                master_lbl = cand
                                break
                        except IndexError:
                            continue
                    if master_lbl:
                        master_lbl.config(text="~Temperature:")
                        break
        except Exception:
            pass

    def _detect_nvidia_smi(self):'''
src = src.replace(f_anchor, f_add, 1)

open(P, "w", encoding="utf-8", newline="").write(src)

import ast
ast.parse(open(P, encoding="utf-8").read())
print("sensor expansion integrated; syntax OK")
