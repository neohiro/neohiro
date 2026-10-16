import io

P = r"repos\SystemMonitor\SystemMonitor.PY"
src = open(P, encoding="utf-8").read()
lines = src.split("\n")

# locate anchors (0-based)
i_can = next(i for i, l in enumerate(lines) if l.strip() == "can_get_temp = True" and "posix" in lines[i-1])
i_bracket = i_can + 4  # blank, if can_get_temp, entry, stray "]"

assert lines[i_can+2].strip().startswith("if can_get_temp"), lines[i_can+1:i_can+3]
assert 'cpu_temperature' in lines[i_can+3]

ins1 = [
    "        elif os.name == 'nt' and self._windows_cpu_temp() is not None:",
    "            # Windows: WMI MSAcpi_ThermalZoneTemperature (many boards expose it)",
    "            can_get_temp = True",
]
ins2 = [
    "",
    "        # --- Optional sensors: battery ------------------------------------",
    "        try:",
    "            has_battery = hasattr(psutil, 'sensors_battery') and psutil.sensors_battery() is not None",
    "        except Exception:",
    "            has_battery = False",
    "        if has_battery:",
    "            self.all_sensors[\"battery\"] = {\"device\": \"Power\", \"label\": \"Battery\", \"unit\": \"%\", \"type\": \"battery\", \"var\": tk.StringVar(), \"history\": [], \"last_valid_reading\": None}",
    "",
    "        # --- Optional sensors: NVIDIA GPU (via nvidia-smi when present) ----",
    "        self._nvidia_smi = self._detect_nvidia_smi()",
    "        if self._nvidia_smi:",
    "            self.all_sensors[\"gpu_usage\"] = {\"device\": \"GPU\", \"label\": \"Usage\", \"unit\": \"%\", \"type\": \"gpu_usage\", \"var\": tk.StringVar(), \"history\": [], \"last_valid_reading\": None}",
    "            self.all_sensors[\"gpu_temperature\"] = {\"device\": \"GPU\", \"label\": \"Temperature\", \"unit\": \"\\u00b0C\", \"type\": \"gpu_temp\", \"var\": tk.StringVar(), \"history\": [], \"last_valid_reading\": None}",
]
lines[i_bracket+1:i_bracket+1] = ins2
lines[i_can+1:i_can+1] = ins1
open(P, "w", encoding="utf-8", newline="").write("\n".join(lines))
print("inserted OK")
